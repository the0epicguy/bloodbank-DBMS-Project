"""
services/unit_service.py  (sync version)
Business logic for blood unit creation, FEFO allocation, and inventory queries.

INTEGRATION CONTRACTS:
  CONTRACT 1 (for Person 1): create_unit(db, bank_id, donor_id, volume_ml, blood_group, component_type, donation_date)
  CONTRACT 2 (for Person 4): find_compatible_units(db, recipient_group, component, limit, lock=True)
  CONTRACT 3 (for P3 & P4): get_compatible_donor_groups(recipient_group, component)
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.compatibility import get_compatible_donor_groups
from app.core.enums import BloodGroup, ComponentType, SHELF_LIFE_DAYS, UnitStatus
from app.core.errors import ConflictError, NotFound, ValidationFailed
from app.models.blood_unit import BloodUnit
from app.repositories import inventory_repo

__all__ = ["create_unit", "find_compatible_units", "get_compatible_donor_groups"]


def _compute_expiry_date(component_type: ComponentType, collection_date: date) -> date:
    key = component_type.value if hasattr(component_type, "value") else component_type
    return collection_date + timedelta(days=SHELF_LIFE_DAYS[key])


# ── CONTRACT 1 ────────────────────────────────────────────────────────────────

def create_unit(
    db: Session,
    bank_id: int,
    donor_id: int,
    volume_ml: int,
    blood_group: BloodGroup,
    component_type: ComponentType,
    donation_date: date,
    collection_date: date | None = None,
) -> BloodUnit:
    bank = inventory_repo.get_bank_by_id(db, bank_id)
    if bank is None:
        raise NotFound(f"Blood bank with id={bank_id} not found.")
    if not (50 <= volume_ml <= 600):
        raise ValidationFailed(f"volume_ml={volume_ml} must be between 50 and 600 ml.")
    if collection_date is None:
        collection_date = donation_date
    expiry_date = _compute_expiry_date(component_type, collection_date)
    next_unit_id = inventory_repo.get_next_unit_id(db, bank_id)
    return inventory_repo.create_unit(
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


# ── CONTRACT 2 ────────────────────────────────────────────────────────────────

def find_compatible_units(
    db: Session,
    recipient_group: BloodGroup,
    component: ComponentType,
    limit: int,
    lock: bool = True,
) -> list[BloodUnit]:
    if limit < 1:
        raise ValidationFailed("Allocation limit must be at least 1.")
    compatible = get_compatible_donor_groups(recipient_group, component)
    return inventory_repo.get_available_units_for_fefo(db, compatible, component, limit, lock)


# ── Internal service helpers ───────────────────────────────────────────────────

def get_all_banks_with_stock(db: Session):
    from app.core.config import settings

    banks = inventory_repo.get_all_banks(db)
    summary_rows = inventory_repo.get_stock_summary(db)

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
        result.append({
            "bank_id": bank.bank_id,
            "name": bank.name,
            "address": bank.address,
            "city": bank.city,
            "contact": bank.contact,
            "email": bank.email,
            "created_at": bank.created_at,
            "available_units": available_by_bank.get(bank.bank_id, 0),
            "expiring_soon": expiring_by_bank.get(bank.bank_id, 0),
        })
    return result


def get_inventory_for_bank(
    db: Session,
    bank_id: int,
    blood_group=None,
    component_type=None,
    status=None,
    expiring_within_days=None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    bank = inventory_repo.get_bank_by_id(db, bank_id)
    if bank is None:
        raise NotFound(f"Blood bank with id={bank_id} not found.")
    units = inventory_repo.get_units_for_bank(
        db, bank_id=bank_id, blood_group=blood_group, component_type=component_type,
        status=status, expiring_within_days=expiring_within_days, skip=skip, limit=limit,
    )
    today = date.today()
    result = []
    for u in units:
        d = {c.name: getattr(u, c.name) for c in u.__table__.columns}
        d["days_to_expiry"] = (u.expiry_date - today).days
        result.append(d)
    return result


def discard_unit(db: Session, bank_id: int, unit_id: int, reason: str) -> BloodUnit:
    unit = inventory_repo.get_unit(db, bank_id, unit_id)
    if unit is None:
        raise NotFound(f"Blood unit ({bank_id}, {unit_id}) not found.")
    if unit.status in (UnitStatus.ISSUED, UnitStatus.DISCARDED):
        raise ConflictError(f"Cannot discard a unit with status '{unit.status.value}'.")
    updated = inventory_repo.update_unit_status(db, bank_id, unit_id, UnitStatus.DISCARDED, discard_reason=reason)
    return updated
