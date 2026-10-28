"""
services/unit_service.py
========================
Business logic for blood unit creation, FEFO allocation, and inventory queries.

This module provides the INTEGRATION CONTRACTS promised to other team members:

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  CONTRACT 1 (for Person 1 - donation_service)                           │
  │  async def create_unit(db, bank_id, donor_id, volume_ml,               │
  │      blood_group, component_type, donation_date) -> BloodUnit            │
  │                                                                          │
  │  CONTRACT 2 (for Person 4 - issue_service)                              │
  │  async def find_compatible_units(db, recipient_group, component,        │
  │      limit, lock=True) -> list[BloodUnit]                               │
  │                                                                          │
  │  CONTRACT 3 (for Persons 3 & 4)                                         │
  │  def get_compatible_donor_groups(recipient_group, component)            │
  │      -> list[BloodGroup]                                                 │
  └──────────────────────────────────────────────────────────────────────────┘

DO NOT change the signatures of these three functions without notifying all team members.
"""

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.compatibility import get_compatible_donor_groups
from app.core.enums import (
    BloodGroup,
    ComponentType,
    SHELF_LIFE_DAYS,
    UnitStatus,
)
from app.core.errors import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from app.models.blood_unit import BloodUnit
from app.repositories import inventory_repo


# Re-export compatibility helper so other modules don't need to import core directly
__all__ = ["create_unit", "find_compatible_units", "get_compatible_donor_groups"]


def _compute_expiry_date(component_type: ComponentType, collection_date: date) -> date:
    """
    Compute expiry_date from collection_date based on medical shelf-life standards:
      WHOLE_BLOOD → +35 days
      RBC         → +42 days
      PLATELETS   → +5  days
      PLASMA      → +365 days
    """
    return collection_date + timedelta(days=SHELF_LIFE_DAYS[component_type])


# ---------------------------------------------------------------------------
# CONTRACT 1 — consumed by Person 1 (donation_service)
# ---------------------------------------------------------------------------

async def create_unit(
    db: AsyncSession,
    bank_id: int,
    donor_id: int,
    volume_ml: int,
    blood_group: BloodGroup,
    component_type: ComponentType,
    donation_date: date,
    collection_date: date | None = None,
) -> BloodUnit:
    """
    Create a new BloodUnit associated with a donation.

    Steps (all within the same transaction passed in by the caller):
      1. Verify the bank exists.
      2. Lock the bank row and compute the next sequential unit_id.
      3. Auto-compute expiry_date from collection_date + shelf-life.
      4. Insert and return the new BloodUnit.

    Raises:
      NotFoundError   — bank_id does not exist.
      ValidationError — volume_ml out of range.
    """
    # Validate bank exists
    bank = await inventory_repo.get_bank_by_id(db, bank_id)
    if bank is None:
        raise NotFoundError(f"Blood bank with id={bank_id} not found.")

    # Validate volume
    if not (50 <= volume_ml <= 600):
        raise ValidationError(f"volume_ml={volume_ml} must be between 50 and 600 ml.")

    # Default collection_date = donation_date
    if collection_date is None:
        collection_date = donation_date

    expiry_date = _compute_expiry_date(component_type, collection_date)

    # Atomic per-bank unit_id generation (bank row is locked inside this call)
    next_unit_id = await inventory_repo.get_next_unit_id(db, bank_id)

    unit = await inventory_repo.create_unit(
        db,
        bank_id=bank_id,
        unit_id=next_unit_id,
        donor_id=donor_id,
        volume_ml=volume_ml,
        blood_group=blood_group,
        component_type=component_type,
        donation_date=donation_date,
        collection_date=collection_date,
        expiry_date=expiry_date,
        status=UnitStatus.AVAILABLE,
    )
    return unit


# ---------------------------------------------------------------------------
# CONTRACT 2 — consumed by Person 4 (issue_service)
# ---------------------------------------------------------------------------

async def find_compatible_units(
    db: AsyncSession,
    recipient_group: BloodGroup,
    component: ComponentType,
    limit: int,
    lock: bool = True,
) -> list[BloodUnit]:
    """
    Return up to *limit* AVAILABLE blood units that are medically compatible
    with *recipient_group* for the requested *component*, ordered by expiry
    date ascending (FEFO — First-Expired, First-Out).

    If lock=True, rows are locked with SELECT ... FOR UPDATE SKIP LOCKED,
    so concurrent allocations cannot pick the same unit.

    Raises:
      ValidationError — limit < 1.
    """
    if limit < 1:
        raise ValidationError("Allocation limit must be at least 1.")

    compatible_groups = get_compatible_donor_groups(recipient_group, component)

    return await inventory_repo.get_available_units_for_fefo(
        db,
        compatible_groups=compatible_groups,
        component_type=component,
        limit=limit,
        lock=lock,
    )


# ---------------------------------------------------------------------------
# CONTRACT 3 — consumed by Persons 3 & 4
# ---------------------------------------------------------------------------
# get_compatible_donor_groups is directly re-exported from core/compatibility.py


# ---------------------------------------------------------------------------
# Internal service methods (used only by routers/banks.py & routers/inventory.py)
# ---------------------------------------------------------------------------

async def get_all_banks_with_stock(db: AsyncSession):
    """Return all blood banks annotated with available_units and expiring_soon counts."""
    from app.core.config import settings
    from datetime import timedelta

    banks = await inventory_repo.get_all_banks(db)
    summary_rows = await inventory_repo.get_stock_summary(db)

    # Build lookup: bank_id → total available & expiring_soon count
    available_by_bank: dict[int, int] = {}
    expiring_by_bank: dict[int, int] = {}
    today = date.today()
    warning_cutoff = today + timedelta(days=settings.EXPIRY_WARNING_DAYS)

    for row in summary_rows:
        bid = row["bank_id"]
        available_by_bank[bid] = available_by_bank.get(bid, 0) + row["available_units"]
        earliest = row["earliest_expiry"]
        if earliest and earliest <= warning_cutoff:
            expiring_by_bank[bid] = expiring_by_bank.get(bid, 0) + row["available_units"]

    result = []
    for bank in banks:
        bank_dict = {
            "bank_id":        bank.bank_id,
            "name":           bank.name,
            "address":        bank.address,
            "city":           bank.city,
            "contact":        bank.contact,
            "email":          bank.email,
            "created_at":     bank.created_at,
            "available_units": available_by_bank.get(bank.bank_id, 0),
            "expiring_soon":   expiring_by_bank.get(bank.bank_id, 0),
        }
        result.append(bank_dict)
    return result


async def get_inventory_for_bank(
    db: AsyncSession,
    bank_id: int,
    blood_group: BloodGroup | None = None,
    component_type: ComponentType | None = None,
    status: UnitStatus | None = None,
    expiring_within_days: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    """Return units for a bank, annotated with days_to_expiry."""
    bank = await inventory_repo.get_bank_by_id(db, bank_id)
    if bank is None:
        raise NotFoundError(f"Blood bank with id={bank_id} not found.")

    units = await inventory_repo.get_units_for_bank(
        db,
        bank_id=bank_id,
        blood_group=blood_group,
        component_type=component_type,
        status=status,
        expiring_within_days=expiring_within_days,
        skip=skip,
        limit=limit,
    )
    today = date.today()
    result = []
    for u in units:
        d = {c.name: getattr(u, c.name) for c in u.__table__.columns}
        d["days_to_expiry"] = (u.expiry_date - today).days
        result.append(d)
    return result


async def discard_unit(
    db: AsyncSession, bank_id: int, unit_id: int, reason: str
) -> BloodUnit:
    """Mark a unit as DISCARDED with a mandatory audit reason."""
    unit = await inventory_repo.get_unit(db, bank_id, unit_id)
    if unit is None:
        raise NotFoundError(f"Blood unit ({bank_id}, {unit_id}) not found.")

    if unit.status in (UnitStatus.ISSUED, UnitStatus.DISCARDED):
        raise ConflictError(
            f"Cannot discard a unit with status '{unit.status.value}'. "
            "Only AVAILABLE, RESERVED, or EXPIRED units can be discarded."
        )
    if unit.status == UnitStatus.ISSUED:
        raise BusinessRuleError("Cannot discard an already-issued blood unit.")

    updated = await inventory_repo.update_unit_status(
        db, bank_id, unit_id, UnitStatus.DISCARDED, discard_reason=reason
    )
    return updated
