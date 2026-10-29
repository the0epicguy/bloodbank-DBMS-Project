"""
repositories/inventory_repo.py
All raw database access for blood_bank and blood_unit (sync SQLAlchemy).
"""

from datetime import date

from sqlalchemy import and_, func, select, text
from sqlalchemy.orm import Session

from app.core.enums import BloodGroup, ComponentType, UnitStatus
from app.models.blood_bank import BloodBank
from app.models.blood_unit import BloodUnit


# ── Blood Bank ────────────────────────────────────────────────────────────────

def get_all_banks(db: Session) -> list[BloodBank]:
    return list(db.execute(select(BloodBank).order_by(BloodBank.name)).scalars().all())


def get_bank_by_id(db: Session, bank_id: int) -> BloodBank | None:
    return db.get(BloodBank, bank_id)


def get_bank_by_email(db: Session, email: str) -> BloodBank | None:
    return db.execute(select(BloodBank).where(BloodBank.email == email)).scalar_one_or_none()


def create_bank(db: Session, **kwargs) -> BloodBank:
    bank = BloodBank(**kwargs)
    db.add(bank)
    db.flush()
    db.refresh(bank)
    return bank


def update_bank(db: Session, bank_id: int, **kwargs) -> BloodBank | None:
    bank = get_bank_by_id(db, bank_id)
    if bank is None:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(bank, key, value)
    db.flush()
    db.refresh(bank)
    return bank


def delete_bank(db: Session, bank_id: int) -> bool:
    bank = get_bank_by_id(db, bank_id)
    if bank is None:
        return False
    db.delete(bank)
    db.flush()
    return True


# ── Blood Unit ────────────────────────────────────────────────────────────────

def get_next_unit_id(db: Session, bank_id: int) -> int:
    """
    Atomically compute the next per-bank unit_id.
    Locks the blood_bank row to serialise concurrent donations.
    """
    db.execute(select(BloodBank).where(BloodBank.bank_id == bank_id).with_for_update())
    result = db.execute(
        select(func.coalesce(func.max(BloodUnit.unit_id), 0)).where(BloodUnit.bank_id == bank_id)
    )
    return int(result.scalar_one()) + 1


def create_unit(db: Session, **kwargs) -> BloodUnit:
    unit = BloodUnit(**kwargs)
    db.add(unit)
    db.flush()
    db.refresh(unit)
    return unit


def get_unit(db: Session, bank_id: int, unit_id: int) -> BloodUnit | None:
    return db.get(BloodUnit, (bank_id, unit_id))


def get_units_for_bank(
    db: Session,
    bank_id: int,
    blood_group: BloodGroup | None = None,
    component_type: ComponentType | None = None,
    status: UnitStatus | None = None,
    expiring_within_days: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[BloodUnit]:
    filters = [BloodUnit.bank_id == bank_id]
    if blood_group:
        filters.append(BloodUnit.blood_group == blood_group)
    if component_type:
        filters.append(BloodUnit.component_type == component_type)
    if status:
        filters.append(BloodUnit.status == status)
    if expiring_within_days is not None:
        cutoff = func.date_add(func.current_date(), text(f"INTERVAL {expiring_within_days} DAY"))
        filters.append(
            and_(BloodUnit.expiry_date >= func.current_date(), BloodUnit.expiry_date <= cutoff)
        )
    result = db.execute(
        select(BloodUnit).where(and_(*filters)).order_by(BloodUnit.expiry_date.asc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


def get_available_units_for_fefo(
    db: Session,
    compatible_groups: list,
    component_type: ComponentType,
    limit: int,
    lock: bool = True,
) -> list[BloodUnit]:
    group_values = [g.value if hasattr(g, "value") else g for g in compatible_groups]
    stmt = (
        select(BloodUnit)
        .where(
            BloodUnit.status == UnitStatus.AVAILABLE,
            BloodUnit.component_type == component_type,
            BloodUnit.blood_group.in_(group_values),
            BloodUnit.expiry_date >= func.current_date(),
        )
        .order_by(BloodUnit.expiry_date.asc())
        .limit(limit)
    )
    if lock:
        stmt = stmt.with_for_update(skip_locked=True)
    return list(db.execute(stmt).scalars().all())


def update_unit_status(
    db: Session, bank_id: int, unit_id: int, new_status: UnitStatus, discard_reason: str | None = None
) -> BloodUnit | None:
    unit = get_unit(db, bank_id, unit_id)
    if unit is None:
        return None
    unit.status = new_status
    if discard_reason is not None:
        unit.discard_reason = discard_reason
    db.flush()
    db.refresh(unit)
    return unit


def sweep_expired_units(db: Session) -> list[BloodUnit]:
    result = db.execute(
        select(BloodUnit).where(
            BloodUnit.status == UnitStatus.AVAILABLE,
            BloodUnit.expiry_date < func.current_date(),
        )
    )
    expired = list(result.scalars().all())
    for unit in expired:
        unit.status = UnitStatus.EXPIRED
    db.flush()
    return expired


def get_stock_summary(db: Session, bank_id: int | None = None) -> list[dict]:
    filters = [BloodUnit.status == UnitStatus.AVAILABLE, BloodUnit.expiry_date >= func.current_date()]
    if bank_id is not None:
        filters.append(BloodUnit.bank_id == bank_id)
    result = db.execute(
        select(
            BloodUnit.bank_id,
            BloodUnit.blood_group,
            BloodUnit.component_type,
            func.count().label("available_units"),
            func.min(BloodUnit.expiry_date).label("earliest_expiry"),
        )
        .where(and_(*filters))
        .group_by(BloodUnit.bank_id, BloodUnit.blood_group, BloodUnit.component_type)
        .order_by(BloodUnit.bank_id, BloodUnit.blood_group, BloodUnit.component_type)
    )
    return [row._asdict() for row in result.all()]
