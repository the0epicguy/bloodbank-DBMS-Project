"""
Issue Repository (Person 4) - database access for issues, FEFO lookup and
the request rows the allocation engine needs. No business rules here.

Pattern:  Router -> Service -> Repository -> Database
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.blood_bank import BloodBank
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor
from app.models.hospital import Hospital
from app.models.issue import Issue
from app.models.recipient import Recipient
from app.models.request import Request
from app.models.user import UserAccount


# ------------------------------------------------------------------ requests
def get_request_for_update(db: Session, request_id: int) -> Optional[Request]:
    """
    Load a request and LOCK its row (SELECT ... FOR UPDATE).
    Two people fulfilling the same request at the same time are serialised,
    so a request can never be over-issued.
    """
    return (
        db.query(Request)
        .filter(Request.request_id == request_id)
        .with_for_update()
        .first()
    )


def get_request(db: Session, request_id: int) -> Optional[Request]:
    return db.query(Request).filter(Request.request_id == request_id).first()


def get_recipient(db: Session, recipient_id: int) -> Optional[Recipient]:
    return db.query(Recipient).filter(Recipient.recipient_id == recipient_id).first()


def count_issued(db: Session, request_id: int) -> int:
    """How many bags have been issued to this request so far."""
    return (
        db.query(func.count(Issue.issue_id))
        .filter(Issue.request_id == request_id)
        .scalar()
    ) or 0


def list_pending_requests(db: Session, hospital_id: Optional[int] = None) -> list[dict]:
    """Open requests (PENDING / PARTIALLY_FULFILLED), EMERGENCY first."""
    issued = (
        select(Issue.request_id, func.count(Issue.issue_id).label("n"))
        .group_by(Issue.request_id)
        .subquery()
    )
    urgency_rank = case(
        (Request.urgency == "EMERGENCY", 0),
        (Request.urgency == "URGENT", 1),
        else_=2,
    )
    q = (
        select(
            Request.request_id, Request.hospital_id, Hospital.name.label("hospital_name"),
            Recipient.name.label("recipient_name"),
            Recipient.blood_group.label("blood_group"),
            Request.component_type, Request.quantity,
            func.coalesce(issued.c.n, 0).label("issued_units"),
            Request.urgency, Request.status, Request.request_date,
        )
        .join(Hospital, Hospital.hospital_id == Request.hospital_id)
        .join(Recipient, Recipient.recipient_id == Request.recipient_id)
        .outerjoin(issued, issued.c.request_id == Request.request_id)
        .where(Request.status.in_(["PENDING", "PARTIALLY_FULFILLED"]))
        .order_by(urgency_rank, Request.request_date, Request.request_id)
    )
    if hospital_id is not None:
        q = q.where(Request.hospital_id == hospital_id)
    return [dict(r._mapping) for r in db.execute(q)]


# -------------------------------------------------------------------- units
CANDIDATE_SCAN_CAP = 500  # how many FEFO-ordered candidates we are willing to try to lock


def find_fefo_candidates(
    db: Session,
    donor_groups: list[str],
    component: str,
    recipient_group: str,
    limit: int,
    lock: bool = True,
) -> list[BloodUnit]:
    """
    First-Expired-First-Out: usable units, earliest expiry first.

    - only AVAILABLE units that have NOT expired
    - only blood groups compatible with the recipient
    - ties on expiry: prefer the recipient's own group (keeps O- for those who need it)

    lock=False  -> plain read (used for the preview).
    lock=True   -> every unit returned is LOCKED with `FOR UPDATE SKIP LOCKED`:
                   a bag another transaction is already allocating is skipped
                   instead of waited for, so two operators can never get the same bag.

    Why two steps?  The FEFO ordering needs a sort (several blood groups, so no
    single index gives the order). If we put `FOR UPDATE SKIP LOCKED` on that
    sorted query, MySQL locks EVERY matching row before applying LIMIT, and a
    second operator would then see "no stock" even though other bags exist.
    So we (1) read the candidate keys in FEFO order without locking, then
    (2) lock them one by one, re-checking AVAILABLE/not-expired on the locked row,
    and stop as soon as we hold `limit` units.
    """
    exact_first = case((BloodUnit.blood_group == recipient_group, 0), else_=1)
    today = date.today()
    base = (
        db.query(BloodUnit)
        .filter(
            BloodUnit.status == "AVAILABLE",
            BloodUnit.expiry_date >= today,
            BloodUnit.component_type == component,
            BloodUnit.blood_group.in_(donor_groups),
        )
        .order_by(BloodUnit.expiry_date.asc(), exact_first, BloodUnit.bank_id, BloodUnit.unit_id)
    )
    if not lock:
        return base.limit(limit).all()

    keys = (
        base.with_entities(BloodUnit.bank_id, BloodUnit.unit_id)
        .limit(CANDIDATE_SCAN_CAP)
        .all()
    )
    chosen: list[BloodUnit] = []
    for bank_id, unit_id in keys:
        unit = (
            db.query(BloodUnit)
            .filter(
                BloodUnit.bank_id == bank_id,
                BloodUnit.unit_id == unit_id,
                BloodUnit.status == "AVAILABLE",       # re-check on the locked row
                BloodUnit.expiry_date >= today,
            )
            .populate_existing()
            .with_for_update(skip_locked=True)
            .first()
        )
        if unit is not None:
            chosen.append(unit)
            if len(chosen) == limit:
                break
    return chosen


def get_unit(db: Session, bank_id: int, unit_id: int, lock: bool = False) -> Optional[BloodUnit]:
    q = db.query(BloodUnit).filter(BloodUnit.bank_id == bank_id, BloodUnit.unit_id == unit_id)
    if lock:
        q = q.with_for_update()
    return q.first()


def get_bank_names(db: Session, bank_ids: list[int]) -> dict[int, str]:
    if not bank_ids:
        return {}
    rows = db.query(BloodBank.bank_id, BloodBank.name).filter(BloodBank.bank_id.in_(bank_ids)).all()
    return {b: n for b, n in rows}


# ------------------------------------------------------------------- issues
def add_issue(db: Session, request_id: int, bank_id: int, unit_id: int,
              issued_by: Optional[int]) -> Issue:
    """Insert an issue row (caller commits). Flushes so the id is available."""
    issue = Issue(
        request_id=request_id, bank_id=bank_id, unit_id=unit_id,
        quantity_issued=1, issued_by=issued_by,
    )
    db.add(issue)
    db.flush()
    return issue


def _audit_query():
    """The full custody trail: issue -> unit -> donor/bank, request -> recipient/hospital."""
    return (
        select(
            Issue.issue_id, Issue.issue_date, Issue.request_id, Issue.bank_id, Issue.unit_id,
            BloodBank.name.label("bank_name"),
            BloodUnit.blood_group, BloodUnit.component_type, BloodUnit.expiry_date,
            Donor.name.label("donor_name"),
            Recipient.name.label("recipient_name"),
            Recipient.blood_group.label("recipient_blood_group"),
            Hospital.hospital_id, Hospital.name.label("hospital_name"),
            Request.urgency,
            UserAccount.full_name.label("issued_by_name"),
        )
        .join(BloodUnit, (BloodUnit.bank_id == Issue.bank_id) & (BloodUnit.unit_id == Issue.unit_id))
        .join(BloodBank, BloodBank.bank_id == BloodUnit.bank_id)
        .join(Donor, Donor.donor_id == BloodUnit.donor_id)
        .join(Request, Request.request_id == Issue.request_id)
        .join(Recipient, Recipient.recipient_id == Request.recipient_id)
        .join(Hospital, Hospital.hospital_id == Request.hospital_id)
        .outerjoin(UserAccount, UserAccount.user_id == Issue.issued_by)
    )


def list_issues(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    request_id: Optional[int] = None,
    hospital_id: Optional[int] = None,
    blood_group: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> tuple[int, list[dict]]:
    """Audit log, newest first. Returns (total_count, page_of_rows)."""
    q = _audit_query()
    if request_id is not None:
        q = q.where(Issue.request_id == request_id)
    if hospital_id is not None:
        q = q.where(Hospital.hospital_id == hospital_id)
    if blood_group:
        q = q.where(BloodUnit.blood_group == blood_group)
    if date_from:
        q = q.where(Issue.issue_date >= date_from)
    if date_to:
        q = q.where(Issue.issue_date < date_to + timedelta(days=1))

    total = db.execute(select(func.count()).select_from(q.subquery())).scalar() or 0
    rows = db.execute(
        q.order_by(Issue.issue_date.desc(), Issue.issue_id.desc()).offset(skip).limit(limit)
    )
    return total, [dict(r._mapping) for r in rows]
