"""
Issue Service (Person 4) - allocating blood units to requests.

Two ways to fulfil a request:
    auto_fulfil()   FEFO (First-Expired-First-Out): take the units that expire
                    soonest, among blood groups compatible with the recipient.
    manual_issue()  A person picks one specific bag; we validate it.

Safety (all inside ONE transaction, rolled back on any failure):
    1. The request row is locked        -> no over-issuing a request
    2. Unit rows are locked SKIP LOCKED -> no two operators get the same bag
    3. UNIQUE(bank_id, unit_id) + a DB trigger are the last line of defence

Integration notes (contracts from the plan):
    - find_compatible_units (P2)  : the FEFO query lives in issue_repo so this
      module works even before P2's unit_service lands.
    - recompute_request_status (P3): done by _sync_request_status below.
"""

import time
from datetime import date

from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.compatibility import get_compatible_donor_groups, is_compatible
from app.core.errors import ConflictError, NotFound, ValidationFailed
from app.models.request import Request
from app.models.user import UserAccount
from app.repositories import issue_repo
from app.schemas.issue import (
    FEFOPreview, FEFOUnit, FulfilResult, IssueListResponse, IssueResponse,
    IssuedUnit, ManualIssueCreate, PendingRequest,
)

MAX_DEADLOCK_RETRIES = 3
# MySQL error codes: 1213 = deadlock, 1205 = lock wait timeout
_RETRYABLE = {1213, 1205}


# ------------------------------------------------------------------ helpers
def _check_request_open(req: Request) -> None:
    if req.status == "CANCELLED":
        raise ConflictError(f"Request {req.request_id} is cancelled")
    if req.status == "FULFILLED":
        raise ConflictError(f"Request {req.request_id} is already fully fulfilled")


def _sync_request_status(db: Session, req: Request) -> int:
    """Recompute PENDING / PARTIALLY_FULFILLED / FULFILLED from the issue rows."""
    issued = issue_repo.count_issued(db, req.request_id)
    if issued >= req.quantity:
        req.status = "FULFILLED"
    elif issued > 0:
        req.status = "PARTIALLY_FULFILLED"
    else:
        req.status = "PENDING"
    return issued


def _issue_unit(db: Session, req: Request, unit, user: UserAccount):
    """
    Record one issue and flip the unit to ISSUED.
    The issue row goes in FIRST (flush) so the DB trigger can verify the unit
    is still AVAILABLE, then the unit is marked ISSUED.
    """
    issue = issue_repo.add_issue(db, req.request_id, unit.bank_id, unit.unit_id,
                                 user.user_id if user else None)
    unit.status = "ISSUED"
    db.flush()
    return IssuedUnit(
        issue_id=issue.issue_id, bank_id=unit.bank_id, unit_id=unit.unit_id,
        blood_group=unit.blood_group, expiry_date=unit.expiry_date,
    )


def _db_error_to_http(exc: DBAPIError):
    """Translate a database-level rejection into a clean API error."""
    msg = str(getattr(exc, "orig", exc))
    if "cannot be issued" in msg or "Duplicate entry" in msg:
        return ConflictError("That blood unit is no longer available")
    return ValidationFailed(f"Database rejected the issue: {msg}")


def _is_retryable(exc: Exception) -> bool:
    code = getattr(getattr(exc, "orig", None), "args", [None])[0]
    return isinstance(exc, OperationalError) and code in _RETRYABLE


# ---------------------------------------------------------------- FEFO read
def preview_fefo(db: Session, request_id: int) -> FEFOPreview:
    """Show which units auto-fulfil WOULD pick (no locks, nothing changes)."""
    req = issue_repo.get_request(db, request_id)
    if not req:
        raise NotFound(f"Request with ID {request_id} not found")
    recipient = issue_repo.get_recipient(db, req.recipient_id)

    groups = get_compatible_donor_groups(recipient.blood_group, req.component_type)
    issued = issue_repo.count_issued(db, request_id)
    remaining = max(req.quantity - issued, 0)

    units = []
    if remaining and req.status in ("PENDING", "PARTIALLY_FULFILLED"):
        units = issue_repo.find_fefo_candidates(
            db, groups, req.component_type, recipient.blood_group, remaining, lock=False
        )
    names = issue_repo.get_bank_names(db, list({u.bank_id for u in units}))
    today = date.today()
    recommended = [
        FEFOUnit(
            bank_id=u.bank_id, unit_id=u.unit_id, bank_name=names.get(u.bank_id, ""),
            blood_group=u.blood_group, component_type=u.component_type,
            expiry_date=u.expiry_date, days_to_expiry=(u.expiry_date - today).days,
            exact_group_match=(u.blood_group == recipient.blood_group),
        )
        for u in units
    ]
    return FEFOPreview(
        request_id=request_id, recipient_blood_group=recipient.blood_group,
        component_type=req.component_type, quantity=req.quantity,
        already_issued=issued, remaining=remaining, compatible_groups=groups,
        recommended=recommended, shortfall=max(remaining - len(recommended), 0),
    )


# ------------------------------------------------------------- auto-fulfil
def auto_fulfil(db: Session, request_id: int, user: UserAccount) -> FulfilResult:
    """
    Automatically fulfil a request with FEFO allocation.
    If stock only covers part of it, the request becomes PARTIALLY_FULFILLED.
    Retries a few times if MySQL reports a deadlock.
    """
    for attempt in range(1, MAX_DEADLOCK_RETRIES + 1):
        try:
            return _auto_fulfil_once(db, request_id, user)
        except OperationalError as exc:
            db.rollback()
            if _is_retryable(exc) and attempt < MAX_DEADLOCK_RETRIES:
                time.sleep(0.05 * attempt)
                continue
            raise ConflictError("Could not allocate blood right now (database busy). Please retry.")
        except IntegrityError as exc:
            db.rollback()
            raise _db_error_to_http(exc)
        except Exception:
            db.rollback()
            raise


def _auto_fulfil_once(db: Session, request_id: int, user: UserAccount) -> FulfilResult:
    req = issue_repo.get_request_for_update(db, request_id)
    if not req:
        raise NotFound(f"Request with ID {request_id} not found")
    _check_request_open(req)

    recipient = issue_repo.get_recipient(db, req.recipient_id)
    groups = get_compatible_donor_groups(recipient.blood_group, req.component_type)

    already = issue_repo.count_issued(db, request_id)
    remaining = req.quantity - already
    if remaining <= 0:
        _sync_request_status(db, req)
        db.commit()
        raise ConflictError(f"Request {request_id} already has all requested units")

    units = issue_repo.find_fefo_candidates(
        db, groups, req.component_type, recipient.blood_group, remaining, lock=True
    )
    if not units:
        db.rollback()
        raise ConflictError(
            f"No compatible {req.component_type} units available for blood group "
            f"{recipient.blood_group} (compatible donor groups: {', '.join(groups)})"
        )

    issued_units = [_issue_unit(db, req, u, user) for u in units]
    total = _sync_request_status(db, req)
    result = _build_result(req, total, issued_units)
    db.commit()
    return result


# ------------------------------------------------------------ manual issue
def manual_issue(db: Session, data: ManualIssueCreate, user: UserAccount) -> FulfilResult:
    """Issue one specific bag (bank_id, unit_id) to a request, with validation."""
    try:
        return _manual_issue_once(db, data, user)
    except (OperationalError, IntegrityError) as exc:
        db.rollback()
        if isinstance(exc, OperationalError) and _is_retryable(exc):
            raise ConflictError("Could not allocate blood right now (database busy). Please retry.")
        raise _db_error_to_http(exc)
    except Exception:
        db.rollback()
        raise


def _manual_issue_once(db: Session, data: ManualIssueCreate, user: UserAccount) -> FulfilResult:
    # Lock order is always: request first, then unit (avoids deadlocks)
    req = issue_repo.get_request_for_update(db, data.request_id)
    if not req:
        raise NotFound(f"Request with ID {data.request_id} not found")
    _check_request_open(req)

    unit = issue_repo.get_unit(db, data.bank_id, data.unit_id, lock=True)
    if not unit:
        raise NotFound(f"Blood unit ({data.bank_id}, {data.unit_id}) not found")

    if unit.status != "AVAILABLE":
        raise ConflictError(f"Unit is {unit.status}, only AVAILABLE units can be issued")
    if unit.expiry_date < date.today():
        raise ValidationFailed(f"Unit expired on {unit.expiry_date}; expired blood cannot be issued")
    if unit.component_type != req.component_type:
        raise ValidationFailed(
            f"Request needs {req.component_type} but this unit is {unit.component_type}"
        )

    recipient = issue_repo.get_recipient(db, req.recipient_id)
    if not is_compatible(unit.blood_group, recipient.blood_group, req.component_type):
        raise ValidationFailed(
            f"{unit.blood_group} {req.component_type} is not compatible with "
            f"recipient blood group {recipient.blood_group}"
        )

    if issue_repo.count_issued(db, req.request_id) >= req.quantity:
        raise ConflictError(f"Request {req.request_id} already has all requested units")

    issued = _issue_unit(db, req, unit, user)
    total = _sync_request_status(db, req)
    result = _build_result(req, total, [issued])
    db.commit()
    return result


def _build_result(req: Request, total_issued: int, issued_units: list[IssuedUnit]) -> FulfilResult:
    remaining = max(req.quantity - total_issued, 0)
    if remaining == 0:
        msg = f"Request fulfilled: {len(issued_units)} unit(s) issued."
    else:
        msg = (f"{len(issued_units)} unit(s) issued; {remaining} still needed "
               f"(request is {req.status}).")
    return FulfilResult(
        request_id=req.request_id, request_status=req.status,
        quantity_requested=req.quantity, total_issued=total_issued,
        newly_issued=len(issued_units), remaining=remaining,
        issued_units=issued_units, message=msg,
    )


# ------------------------------------------------------------- audit / lists
def list_issues(db: Session, user: UserAccount, **filters) -> IssueListResponse:
    """Audit log. Hospital staff only ever see their own hospital's issues."""
    if user.role == "HOSPITAL_STAFF" and user.entity_ref_id is not None:
        filters["hospital_id"] = user.entity_ref_id
    total, rows = issue_repo.list_issues(db, **filters)
    return IssueListResponse(total=total, items=[IssueResponse(**r) for r in rows])


def list_pending_requests(db: Session, user: UserAccount) -> list[PendingRequest]:
    hospital_id = user.entity_ref_id if user.role == "HOSPITAL_STAFF" else None
    out = []
    for r in issue_repo.list_pending_requests(db, hospital_id):
        out.append(PendingRequest(
            **{k: r[k] for k in (
                "request_id", "hospital_id", "hospital_name", "recipient_name",
                "blood_group", "component_type", "quantity", "issued_units",
                "urgency", "status", "request_date")},
            remaining=max(r["quantity"] - r["issued_units"], 0),
        ))
    return out
