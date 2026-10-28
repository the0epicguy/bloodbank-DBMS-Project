from datetime import date
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.issue import Issue
from app.models.domain import Request, BloodUnit, Hospital, Recipient, BloodBank

class IssueRepository:
    """Repository handling all database access for issues and audit trails."""

    @staticmethod
    async def create(db: AsyncSession, issue: Issue) -> Issue:
        db.add(issue)
        await db.flush()
        return issue

    @staticmethod
    async def get_by_id(db: AsyncSession, issue_id: int) -> Issue | None:
        return await db.scalar(select(Issue).where(Issue.issue_id == issue_id))

    @staticmethod
    async def count_by_request(db: AsyncSession, request_id: int) -> int:
        return await db.scalar(select(func.count(Issue.issue_id)).where(Issue.request_id == request_id)) or 0

    @staticmethod
    async def get_audit_log(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[dict]:
        stmt = (
            select(Issue, Request, BloodUnit, Hospital, Recipient, BloodBank)
            .join(Request, Request.request_id == Issue.request_id)
            .join(BloodUnit, (BloodUnit.bank_id == Issue.bank_id) & (BloodUnit.unit_id == Issue.unit_id))
            .join(Hospital, Hospital.hospital_id == Request.hospital_id)
            .join(Recipient, Recipient.recipient_id == Request.recipient_id)
            .join(BloodBank, BloodBank.bank_id == Issue.bank_id)
            .order_by(desc(Issue.issue_date))
            .offset(skip)
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        return [
            {
                "issue_id": i.issue_id,
                "request_id": i.request_id,
                "bank_id": i.bank_id,
                "unit_id": i.unit_id,
                "issue_date": i.issue_date.isoformat() if i.issue_date else None,
                "quantity_issued": i.quantity_issued,
                "notes": i.notes,
                "blood_group": u.blood_group,
                "component_type": u.component_type,
                "expiry_date": str(u.expiry_date),
                "bank_name": b.name,
                "hospital_name": h.name,
                "recipient_name": rec.name,
                "urgency": r.urgency,
            }
            for i, r, u, h, rec, b in rows
        ]

    @staticmethod
    async def find_fefo_candidates(
        db: AsyncSession,
        groups: list[str],
        component_type: str,
        limit: int,
        lock: bool = True
    ) -> list[BloodUnit]:
        stmt = (
            select(BloodUnit)
            .where(
                BloodUnit.blood_group.in_(groups),
                BloodUnit.component_type == component_type,
                BloodUnit.status == "AVAILABLE",
                BloodUnit.expiry_date >= date.today()
            )
            .order_by(BloodUnit.expiry_date.asc(), BloodUnit.bank_id.asc(), BloodUnit.unit_id.asc())
            .limit(limit)
        )
        if lock and db.bind and db.bind.dialect.name == "mysql":
            stmt = stmt.with_for_update(skip_locked=True)
        return list((await db.scalars(stmt)).all())
