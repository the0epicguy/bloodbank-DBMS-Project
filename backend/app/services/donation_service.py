"""
services/donation_service.py
Records a donation end-to-end: validates donor eligibility, uses P2's
inventory_repo.get_next_unit_id for atomic per-bank unit_id generation,
creates the BloodUnit row, and updates donor.last_donation_date.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.core.enums import SHELF_LIFE_DAYS
from app.core.errors import NotFound, ValidationFailed
from app.models.blood_bank import BloodBank
from app.models.blood_unit import BloodUnit
from app.repositories import inventory_repo
from app.schemas.donor import DonationCreate, DonationResponse
from app.services import donor_service


def _compute_expiry(component_type: str, donation_date: date) -> date:
    """Return the expiry date for a blood component given its collection date."""
    from datetime import timedelta
    days = SHELF_LIFE_DAYS.get(component_type, 35)
    return donation_date + timedelta(days=days)


def record_donation(db: Session, data: DonationCreate) -> DonationResponse:
    """
    Full donation workflow:
      1. Verify donor exists
      2. Verify blood bank exists
      3. Check donor eligibility (age 18-65, 90-day gap)
      4. Use inventory_repo.get_next_unit_id() for atomic per-bank counter (P2 contract)
      5. Create BloodUnit row
      6. Update donor.last_donation_date
    All runs inside one transaction (get_db() commits on success).
    """
    # 1. Donor
    donor = donor_service.get_donor(db, data.donor_id)

    # 2. Blood bank
    bank = inventory_repo.get_bank_by_id(db, data.bank_id)
    if not bank:
        raise NotFound(f"Blood bank with ID {data.bank_id} not found")

    # 3. Eligibility
    eligible, reason = donor_service.is_eligible(donor)
    if not eligible:
        raise ValidationFailed(f"Donor is not eligible: {reason}")

    # 4. Component validation
    valid_components = ["WHOLE_BLOOD", "RBC", "PLATELETS", "PLASMA"]
    if data.component_type not in valid_components:
        raise ValidationFailed(
            f"Invalid component type '{data.component_type}'. "
            f"Must be one of: {', '.join(valid_components)}"
        )

    today = date.today()
    expiry = _compute_expiry(data.component_type, today)

    # 5. Atomic per-bank unit_id (P2 contract – row-locks blood_bank)
    next_unit_id = inventory_repo.get_next_unit_id(db, data.bank_id)

    blood_unit = BloodUnit(
        bank_id=data.bank_id,
        unit_id=next_unit_id,
        donor_id=data.donor_id,
        volume_ml=data.volume_ml,
        donation_date=today,
        blood_group=donor.blood_group,
        component_type=data.component_type,
        collection_date=today,
        expiry_date=expiry,
        status="AVAILABLE",
    )
    db.add(blood_unit)

    # 6. Update donor cooldown
    donor.last_donation_date = today
    db.flush()
    db.refresh(blood_unit)

    return DonationResponse(
        message="Donation recorded successfully",
        donor_id=donor.donor_id,
        bank_id=blood_unit.bank_id,
        unit_id=blood_unit.unit_id,
        volume_ml=blood_unit.volume_ml,
        donation_date=blood_unit.donation_date,
        blood_group=blood_unit.blood_group,
        component_type=blood_unit.component_type,
        expiry_date=blood_unit.expiry_date,
    )
