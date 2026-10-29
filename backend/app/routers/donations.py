"""
Donations Router - API endpoint for recording donations.

Endpoints:
    POST /donations - Record a new blood donation
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.donor import DonationCreate, DonationResponse
from app.services import donation_service

router = APIRouter(
    prefix="/donations",
    tags=["Donations"],
)


@router.post("/", response_model=DonationResponse, status_code=201)
def record_donation(
    data: DonationCreate,
    db: Session = Depends(get_db),
):
    """
    Record a new blood donation.

    This endpoint performs the full donation workflow:
        1. Validates that the donor exists
        2. Validates that the blood bank exists
        3. Checks donor eligibility (age + 90-day gap)
        4. Creates a new blood unit in the inventory
        5. Updates the donor's last_donation_date

    All steps happen in a single database transaction.
    If any step fails, everything is rolled back.
    """
    return donation_service.record_donation(db, data)
