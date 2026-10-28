from datetime import date, timedelta
from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.domain import BloodUnit, Request, BloodBank
from app.models.issue import Issue

async def stock_distribution(db: AsyncSession) -> list[dict]:
    stmt = select(BloodUnit.blood_group, BloodUnit.component_type,
                  func.count().label("available_units")).where(
        BloodUnit.status == "AVAILABLE", BloodUnit.expiry_date >= date.today()
    ).group_by(BloodUnit.blood_group, BloodUnit.component_type).order_by(BloodUnit.blood_group)
    rows = (await db.execute(stmt)).all()
    return [{"blood_group": r.blood_group, "component_type": r.component_type, "available_units": r.available_units} for r in rows]

async def expiring_soon(db: AsyncSession, days: int = 7) -> list[dict]:
    cutoff = date.today() + timedelta(days=days)
    stmt = select(BloodUnit, BloodBank.name.label("bank_name")).join(
        BloodBank, BloodBank.bank_id == BloodUnit.bank_id
    ).where(BloodUnit.status == "AVAILABLE", BloodUnit.expiry_date >= date.today(),
            BloodUnit.expiry_date <= cutoff).order_by(BloodUnit.expiry_date)
    rows = (await db.execute(stmt)).all()
    return [{"bank_id": u.bank_id, "bank_name": bank_name, "unit_id": u.unit_id,
             "blood_group": u.blood_group, "component_type": u.component_type,
             "expiry_date": str(u.expiry_date), "days_to_expiry": (u.expiry_date-date.today()).days}
            for u, bank_name in rows]

async def fulfillment_metrics(db: AsyncSession) -> dict:
    total = await db.scalar(select(func.count(Request.request_id))) or 0
    fulfilled = await db.scalar(select(func.count(Request.request_id)).where(Request.status == "FULFILLED")) or 0
    rows = (await db.execute(select(Request.urgency, func.count(Request.request_id).label("total"),
        func.sum(case((Request.status == "FULFILLED", 1), else_=0)).label("fulfilled"))
        .group_by(Request.urgency))).all()
    by_urgency = []
    for row in rows:
        count = int(row.total or 0)
        done = int(row.fulfilled or 0)
        by_urgency.append({"urgency": row.urgency, "total_requests": count,
                           "fulfilled_requests": done,
                           "fulfillment_pct": round(done/count*100, 2) if count else 0})
    return {"total_requests": total, "fulfilled_requests": fulfilled,
            "fulfillment_pct": round(fulfilled/total*100, 2) if total else 0,
            "by_urgency": by_urgency}
