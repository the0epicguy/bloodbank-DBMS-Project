"""
Donation Service - business logic for recording donations.

A donation is the act of a donor giving blood at a blood bank.
This service orchestrates:
    1. Validate the donor exists
    2. Check eligibility (age + 90-day gap)
    3. Create a blood unit (in the blood_unit table)
    4. Update donor's last_donation_date
    5. All in one database transaction (if anything fails, everything rolls back)

Integration Point:
    This service calls unit_service.create_unit() which is owned by Person 2.
    For now, we have a local implementation that Person 2 will replace.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta

from app.models.donor import Donor
from app.models.blood_unit import BloodUnit
from app.models.blood_bank import BloodBank
from app.schemas.donor import DonationCreate, DonationResponse
from app.services import donor_service
from app.core.errors import NotFound, ValidationFailed


# Expiry defaults (days from collection_date)
EXPIRY_DAYS = {
    "WHOLE_BLOOD": 35,
    "RBC": 35,
    "PLATELETS": 5,
    "PLASMA": 365,
}


def _compute_expiry(component_type: str, collection_date: date) -> date:
    """
    Compute the expiry date based on component type.

    Rules from section 5 of the plan:
        - Whole blood and RBC: 35 days
        - Platelets: 5 days
        - Plasma: 365 days (frozen)
    """
    days = EXPIRY_DAYS.get(component_type, 35)
    return collection_date + timedelta(days=days)


def _get_next_unit_id(db: Session, bank_id: int) -> int:
    """
    Get the next unit_id for a bank.

    Since unit_id is a partial key (per-bank counter), we find
    the current max unit_id for that bank and add 1.

    Note: Person 2 will implement this with proper row locking.
    """
    max_id = (
        db.query(func.max(BloodUnit.unit_id))
        .filter(BloodUnit.bank_id == bank_id)
        .scalar()
    )
    return (max_id or 0) + 1


def record_donation(db: Session, data: DonationCreate) -> DonationResponse:
    """
    Record a new donation.

    Full workflow:
        1. Check that the donor exists
        2. Check that the blood bank exists
        3. Verify donor eligibility
        4. Create a blood unit
        5. Update donor's last_donation_date
        6. Commit everything as one transaction

    If any step fails, the entire transaction is rolled back.
    """
    # Step 1: Get the donor (raises NotFound if missing)
    donor = donor_service.get_donor(db, data.donor_id)

    # Step 2: Check blood bank exists
    bank = db.query(BloodBank).filter(BloodBank.bank_id == data.bank_id).first()
    if not bank:
        raise NotFound(f"Blood bank with ID {data.bank_id} not found")

    # Step 3: Check eligibility
    eligible, reason = donor_service.is_eligible(donor)
    if not eligible:
        raise ValidationFailed(f"Donor is not eligible: {reason}")

    # Step 4: Validate component type
    valid_components = ["WHOLE_BLOOD", "RBC", "PLATELETS", "PLASMA"]
    if data.component_type not in valid_components:
        raise ValidationFailed(
            f"Invalid component type '{data.component_type}'. "
            f"Must be one of: {', '.join(valid_components)}"
        )

    # Step 5: Create the blood unit
    today = date.today()
    next_unit_id = _get_next_unit_id(db, data.bank_id)
    expiry = _compute_expiry(data.component_type, today)

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

    # Step 6: Update donor's last_donation_date
    donor.last_donation_date = today

    # Step 7: Commit the transaction (both unit creation and donor update)
    try:
        db.commit()
        db.refresh(blood_unit)
        db.refresh(donor)
    except Exception as e:
        db.rollback()
        raise ValidationFailed(f"Failed to record donation: {str(e)}")

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
