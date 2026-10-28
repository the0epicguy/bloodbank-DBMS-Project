from datetime import date
from sqlalchemy import select, func, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models.domain import BloodUnit, Request, Hospital, Recipient, BloodBank
from app.models.issue import Issue
from app.repositories.issue_repo import IssueRepository
from app.core.compatibility import compatible_groups

async def _refresh_request_status(db: AsyncSession, request: Request) -> int:
    issued = await IssueRepository.count_by_request(db, request.request_id)
    if issued >= request.quantity:
        request.status = "FULFILLED"
    elif issued > 0:
        request.status = "PARTIALLY_FULFILLED"
    elif request.status != "CANCELLED":
        request.status = "PENDING"
    return issued

async def get_open_requests(db: AsyncSession) -> list[dict]:
    """Fetch pending and partially fulfilled requests with recipient and hospital details."""
    stmt = (
        select(Request, Hospital.name.label("hospital_name"), Recipient.name.label("recipient_name"))
        .join(Hospital, Hospital.hospital_id == Request.hospital_id)
        .join(Recipient, Recipient.recipient_id == Request.recipient_id)
        .where(Request.status.in_(["PENDING", "PARTIALLY_FULFILLED"]))
        .order_by(
            case(
                (Request.urgency == "EMERGENCY", 1),
                (Request.urgency == "URGENT", 2),
                else_=3
            ),
            Request.request_id.asc()
        )
    )
    results = (await db.execute(stmt)).all()
    output = []
    for req, hosp_name, rec_name in results:
        issued = await db.scalar(select(func.count(Issue.issue_id)).where(Issue.request_id == req.request_id)) or 0
        output.append({
            "request_id": req.request_id,
            "hospital_id": req.hospital_id,
            "hospital_name": hosp_name,
            "recipient_id": req.recipient_id,
            "recipient_name": rec_name,
            "blood_group": req.blood_group,
            "component_type": req.component_type,
            "quantity": req.quantity,
            "issued_units": issued,
            "remaining_units": max(0, req.quantity - issued),
            "urgency": req.urgency,
            "status": req.status,
            "request_date": str(req.request_date),
            "notes": req.notes
        })
    return output

async def get_candidate_units(db: AsyncSession, request_id: int) -> list[dict]:
    """Find candidate units in FEFO order for a given request."""
    request = await db.scalar(select(Request).where(Request.request_id == request_id))
    if not request:
        raise HTTPException(404, "Request not found")
    groups = compatible_groups(request.blood_group, request.component_type)
    stmt = (
        select(BloodUnit, BloodBank.name.label("bank_name"))
        .join(BloodBank, BloodBank.bank_id == BloodUnit.bank_id)
        .where(
            BloodUnit.blood_group.in_(groups),
            BloodUnit.component_type == request.component_type,
            BloodUnit.status == "AVAILABLE",
            BloodUnit.expiry_date >= date.today()
        )
        .order_by(BloodUnit.expiry_date.asc(), BloodUnit.bank_id.asc(), BloodUnit.unit_id.asc())
        .limit(20)
    )
    rows = (await db.execute(stmt)).all()
    return [{
        "bank_id": u.bank_id,
        "bank_name": bank_name,
        "unit_id": u.unit_id,
        "blood_group": u.blood_group,
        "component_type": u.component_type,
        "volume_ml": u.volume_ml,
        "expiry_date": str(u.expiry_date),
        "days_to_expiry": (u.expiry_date - date.today()).days,
        "is_exact_match": u.blood_group == request.blood_group
    } for u, bank_name in rows]

async def auto_fulfil(db: AsyncSession, request_id: int) -> dict:
    """Allocate compatible units in FEFO order. MySQL locks candidates and skips rows locked elsewhere."""
    transaction = db.begin_nested() if db.in_transaction() else db.begin()
    async with transaction:
        stmt_req = select(Request).where(Request.request_id == request_id)
        if db.bind and db.bind.dialect.name == "mysql":
            stmt_req = stmt_req.with_for_update()
        request = await db.scalar(stmt_req)
        if request is None:
            raise HTTPException(404, "Request not found")
        if request.status == "CANCELLED":
            raise HTTPException(409, "Cancelled requests cannot be fulfilled")
        already_issued = await db.scalar(select(func.count(Issue.issue_id)).where(Issue.request_id == request_id)) or 0
        needed = max(0, request.quantity - already_issued)
        if needed == 0:
            return {"request_id": request_id, "requested_units": request.quantity, "issued_now": 0,
                    "remaining_units": 0, "status": "FULFILLED", "allocated": []}
        groups = compatible_groups(request.blood_group, request.component_type)
        stmt = select(BloodUnit).where(
            BloodUnit.blood_group.in_(groups),
            BloodUnit.component_type == request.component_type,
            BloodUnit.status == "AVAILABLE",
            BloodUnit.expiry_date >= date.today()
        ).order_by(BloodUnit.expiry_date.asc(), BloodUnit.bank_id.asc(), BloodUnit.unit_id.asc()).limit(needed)
        # MySQL 8/InnoDB supports SKIP LOCKED; SQLite development mode uses a normal select.
        if db.bind and db.bind.dialect.name == "mysql":
            stmt = stmt.with_for_update(skip_locked=True)
        units = list((await db.scalars(stmt)).all())
        allocated = []
        for unit in units:
            db.add(Issue(request_id=request_id, bank_id=unit.bank_id, unit_id=unit.unit_id, quantity_issued=1))
            unit.status = "ISSUED"
            allocated.append({"bank_id": unit.bank_id, "unit_id": unit.unit_id,
                              "blood_group": unit.blood_group, "component_type": unit.component_type,
                              "expiry_date": str(unit.expiry_date)})
        issued_after = already_issued + len(allocated)
        if issued_after >= request.quantity:
            request.status = "FULFILLED"
        elif issued_after > 0:
            request.status = "PARTIALLY_FULFILLED"
        await db.flush()
        return {"request_id": request_id, "requested_units": request.quantity, "issued_now": len(allocated),
                "remaining_units": max(0, request.quantity-issued_after), "status": request.status,
                "allocated": allocated}

async def manual_issue(db: AsyncSession, request_id: int, bank_id: int, unit_id: int, notes: str | None = None) -> Issue:
    transaction = db.begin_nested() if db.in_transaction() else db.begin()
    async with transaction:
        stmt_req = select(Request).where(Request.request_id == request_id)
        if db.bind and db.bind.dialect.name == "mysql":
            stmt_req = stmt_req.with_for_update()
        request = await db.scalar(stmt_req)
        if request is None:
            raise HTTPException(404, "Request not found")
        if request.status in ("CANCELLED", "FULFILLED"):
            raise HTTPException(409, "Request is not open for allocation")
        issued = await db.scalar(select(func.count(Issue.issue_id)).where(Issue.request_id == request_id)) or 0
        if issued >= request.quantity:
            raise HTTPException(409, "Request quantity already fulfilled")
        stmt = select(BloodUnit).where(BloodUnit.bank_id == bank_id, BloodUnit.unit_id == unit_id)
        if db.bind and db.bind.dialect.name == "mysql":
            stmt = stmt.with_for_update(skip_locked=True)
        unit = await db.scalar(stmt)
        if unit is None:
            raise HTTPException(404, "Blood unit not found")
        if unit.status != "AVAILABLE" or unit.expiry_date < date.today():
            raise HTTPException(409, "Blood unit is not available or has expired")
        if unit.component_type != request.component_type:
            raise HTTPException(422, "Blood component does not match request")
        if unit.blood_group not in compatible_groups(request.blood_group, request.component_type):
            raise HTTPException(422, "Blood group is incompatible with request")
        issue = Issue(request_id=request_id, bank_id=bank_id, unit_id=unit_id, notes=notes)
        db.add(issue)
        unit.status = "ISSUED"
        await db.flush()
        await _refresh_request_status(db, request)
        await db.flush()
        return issue
