"""
repositories/inventory_repo.py
================================
All raw database access for blood_bank and blood_unit.

Rules:
  - No business logic here — only SQL / ORM queries.
  - All methods accept an AsyncSession and return ORM model instances or scalars.
  - The composite primary-key counter (unit_id) is computed here atomically.
"""

from datetime import date

from sqlalchemy import and_, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BloodGroup, ComponentType, UnitStatus
from app.models.blood_bank import BloodBank
from app.models.blood_unit import BloodUnit


# ===========================================================================
# Blood Bank repository
# ===========================================================================

async def get_all_banks(db: AsyncSession) -> list[BloodBank]:
    result = await db.execute(select(BloodBank).order_by(BloodBank.name))
    return list(result.scalars().all())


async def get_bank_by_id(db: AsyncSession, bank_id: int) -> BloodBank | None:
    return await db.get(BloodBank, bank_id)


async def get_bank_by_email(db: AsyncSession, email: str) -> BloodBank | None:
    result = await db.execute(
        select(BloodBank).where(BloodBank.email == email)
    )
    return result.scalar_one_or_none()


async def create_bank(db: AsyncSession, **kwargs) -> BloodBank:
    bank = BloodBank(**kwargs)
    db.add(bank)
    await db.flush()   # Populate bank_id without committing
    await db.refresh(bank)
    return bank


async def update_bank(
    db: AsyncSession, bank_id: int, **kwargs
) -> BloodBank | None:
    bank = await get_bank_by_id(db, bank_id)
    if bank is None:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(bank, key, value)
    await db.flush()
    await db.refresh(bank)
    return bank


async def delete_bank(db: AsyncSession, bank_id: int) -> bool:
    bank = await get_bank_by_id(db, bank_id)
    if bank is None:
        return False
    await db.delete(bank)
    await db.flush()
    return True


# ===========================================================================
# Blood Unit repository
# ===========================================================================

async def get_next_unit_id(db: AsyncSession, bank_id: int) -> int:
    """
    Atomically compute the next sequential unit_id for the given bank.

    Pattern:
      1. Lock the parent blood_bank row to serialise concurrent donations
         into the same bank (prevents duplicate unit_ids under race conditions).
      2. Take MAX(unit_id) + 1 from the locked snapshot.

    This is safe because InnoDB row locks are held until the transaction commits.
    """
    # Step 1: Lock the bank row
    await db.execute(
        select(BloodBank)
        .where(BloodBank.bank_id == bank_id)
        .with_for_update()
    )
    # Step 2: Compute next id
    result = await db.execute(
        select(func.coalesce(func.max(BloodUnit.unit_id), 0))
        .where(BloodUnit.bank_id == bank_id)
    )
    return int(result.scalar_one()) + 1


async def create_unit(db: AsyncSession, **kwargs) -> BloodUnit:
    """
    Insert a new BloodUnit row.  The caller (unit_service) must have already
    computed unit_id via get_next_unit_id() inside the same transaction.
    """
    unit = BloodUnit(**kwargs)
    db.add(unit)
    await db.flush()
    await db.refresh(unit)
    return unit


async def get_unit(
    db: AsyncSession, bank_id: int, unit_id: int
) -> BloodUnit | None:
    return await db.get(BloodUnit, (bank_id, unit_id))


async def get_units_for_bank(
    db: AsyncSession,
    bank_id: int,
    blood_group: BloodGroup | None = None,
    component_type: ComponentType | None = None,
    status: UnitStatus | None = None,
    expiring_within_days: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[BloodUnit]:
    """
    Fetch blood units for a bank with optional multi-dimensional filtering.
    """
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
            and_(BloodUnit.expiry_date >= func.current_date(),
                 BloodUnit.expiry_date <= cutoff)
        )

    result = await db.execute(
        select(BloodUnit)
        .where(and_(*filters))
        .order_by(BloodUnit.expiry_date.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_available_units_for_fefo(
    db: AsyncSession,
    compatible_groups: list[BloodGroup],
    component_type: ComponentType,
    limit: int,
    lock: bool = True,
) -> list[BloodUnit]:
    """
    FEFO query: retrieve earliest-expiring AVAILABLE compatible units.
    If lock=True, uses SELECT ... FOR UPDATE SKIP LOCKED to prevent
    double-allocation under concurrent requests.

    Called exclusively by unit_service.find_compatible_units() — which is
    the integration contract consumed by Person 4 (issue_service).
    """
    stmt = (
        select(BloodUnit)
        .where(
            BloodUnit.status == UnitStatus.AVAILABLE,
            BloodUnit.component_type == component_type,
            BloodUnit.blood_group.in_([g.value for g in compatible_groups]),
            BloodUnit.expiry_date >= func.current_date(),
        )
        .order_by(BloodUnit.expiry_date.asc())
        .limit(limit)
    )
    if lock:
        stmt = stmt.with_for_update(skip_locked=True)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_unit_status(
    db: AsyncSession,
    bank_id: int,
    unit_id: int,
    new_status: UnitStatus,
    discard_reason: str | None = None,
) -> BloodUnit | None:
    unit = await get_unit(db, bank_id, unit_id)
    if unit is None:
        return None
    unit.status = new_status
    if discard_reason is not None:
        unit.discard_reason = discard_reason
    await db.flush()
    await db.refresh(unit)
    return unit


async def sweep_expired_units(db: AsyncSession) -> list[BloodUnit]:
    """
    Transition all AVAILABLE units past their expiry_date to EXPIRED.
    Returns the list of swept units for the API response.
    """
    result = await db.execute(
        select(BloodUnit).where(
            BloodUnit.status == UnitStatus.AVAILABLE,
            BloodUnit.expiry_date < func.current_date(),
        )
    )
    expired_units = list(result.scalars().all())
    for unit in expired_units:
        unit.status = UnitStatus.EXPIRED
    await db.flush()
    return expired_units


async def get_stock_summary(
    db: AsyncSession,
    bank_id: int | None = None,
) -> list[dict]:
    """
    Aggregate available stock grouped by (bank_id, blood_group, component_type).
    Returns a list of dicts for the stock matrix view.
    If bank_id is given, scope to that bank; otherwise return global summary.
    """
    filters = [
        BloodUnit.status == UnitStatus.AVAILABLE,
        BloodUnit.expiry_date >= func.current_date(),
    ]
    if bank_id is not None:
        filters.append(BloodUnit.bank_id == bank_id)

    result = await db.execute(
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
