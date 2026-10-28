"""
Donor Service - business logic for donor operations.

Contains:
    - Donor CRUD with validation
    - Eligibility checking (age 18-65, 90-day donation gap)
    - Donation history retrieval

Business Rules:
    1. Phone number must be unique across all donors
    2. Donor must be between 18-65 years old to be eligible
    3. At least 90 days must pass since last donation
    4. Date of birth must be in the past
"""

from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional, Tuple

from app.models.donor import Donor
from app.models.blood_unit import BloodUnit
from app.repositories import donor_repo
from app.schemas.donor import DonorCreate, DonorUpdate, DonorEligibility
from app.core.errors import NotFound, ConflictError, ValidationFailed
from app.core.config import settings


def get_all_donors(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    blood_group: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Donor]:
    """Get all donors with optional filtering."""
    return donor_repo.get_all(db, skip, limit, blood_group, search)


def get_donor(db: Session, donor_id: int) -> Donor:
    """
    Get a single donor by ID.
    Raises NotFound if donor doesn't exist.
    """
    donor = donor_repo.get_by_id(db, donor_id)
    if not donor:
        raise NotFound(f"Donor with ID {donor_id} not found")
    return donor


def create_donor(db: Session, data: DonorCreate) -> Donor:
    """
    Create a new donor.
    Raises ConflictError if phone number already exists.
    """
    # Check for duplicate phone
    existing = donor_repo.get_by_phone(db, data.phone)
    if existing:
        raise ConflictError(
            f"A donor with phone number '{data.phone}' already exists "
            f"(Donor ID: {existing.donor_id})"
        )

    # Create the ORM model from the schema data
    donor = Donor(
        name=data.name,
        blood_group=data.blood_group.value,
        phone=data.phone,
        dob=data.dob,
    )

    return donor_repo.create(db, donor)


def update_donor(db: Session, donor_id: int, data: DonorUpdate) -> Donor:
    """
    Update a donor's information.
    Only updates fields that are provided (not None).
    """
    donor = get_donor(db, donor_id)

    # If phone is being changed, check it's not taken by someone else
    if data.phone and data.phone != donor.phone:
        existing = donor_repo.get_by_phone(db, data.phone)
        if existing and existing.donor_id != donor_id:
            raise ConflictError(
                f"Phone number '{data.phone}' is already in use by Donor ID {existing.donor_id}"
            )

    # Update only provided fields
    if data.name is not None:
        donor.name = data.name
    if data.blood_group is not None:
        donor.blood_group = data.blood_group.value
    if data.phone is not None:
        donor.phone = data.phone
    if data.dob is not None:
        donor.dob = data.dob

    return donor_repo.update(db, donor)


def delete_donor(db: Session, donor_id: int) -> None:
    """Delete a donor by ID."""
    donor = get_donor(db, donor_id)
    donor_repo.delete(db, donor)


def is_eligible(donor: Donor) -> Tuple[bool, str]:
    """
    Check if a donor is eligible to donate blood.

    Rules:
        1. Age must be between 18 and 65 (inclusive)
        2. At least 90 days since last donation (if they have donated before)

    Returns:
        (is_eligible: bool, reason: str)
    """
    today = date.today()

    # Calculate age from date of birth
    age = today.year - donor.dob.year
    # Adjust if birthday hasn't occurred yet this year
    if (today.month, today.day) < (donor.dob.month, donor.dob.day):
        age -= 1

    # Rule 1: Age check
    if age < settings.MIN_DONOR_AGE:
        return False, f"Donor is {age} years old. Minimum age is {settings.MIN_DONOR_AGE}."

    if age > settings.MAX_DONOR_AGE:
        return False, f"Donor is {age} years old. Maximum age is {settings.MAX_DONOR_AGE}."

    # Rule 2: Donation gap check
    if donor.last_donation_date:
        days_since = (today - donor.last_donation_date).days
        if days_since < settings.DONATION_GAP_DAYS:
            days_remaining = settings.DONATION_GAP_DAYS - days_since
            return False, (
                f"Last donation was {days_since} days ago. "
                f"Must wait {days_remaining} more days "
                f"(minimum gap: {settings.DONATION_GAP_DAYS} days)."
            )

    return True, "Donor is eligible to donate."


def check_eligibility(db: Session, donor_id: int) -> DonorEligibility:
    """
    Check eligibility for a specific donor.
    Returns an eligibility response object.
    """
    donor = get_donor(db, donor_id)
    eligible, reason = is_eligible(donor)

    return DonorEligibility(
        donor_id=donor.donor_id,
        name=donor.name,
        is_eligible=eligible,
        reason=reason,
    )


def get_donation_history(db: Session, donor_id: int) -> list[BloodUnit]:
    """
    Get the donation history for a donor.
    Returns all blood units donated by this donor, ordered by date (newest first).
    """
    donor = get_donor(db, donor_id)

    return (
        db.query(BloodUnit)
        .filter(BloodUnit.donor_id == donor_id)
        .order_by(BloodUnit.donation_date.desc())
        .all()
    )
