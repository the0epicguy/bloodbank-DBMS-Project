"""
Donor Router - API endpoints for donor management.

Endpoints:
    GET    /donors             - List all donors (with filters)
    POST   /donors             - Create a new donor
    GET    /donors/{id}        - Get a specific donor
    PUT    /donors/{id}        - Update a donor
    DELETE /donors/{id}        - Delete a donor
    GET    /donors/{id}/eligibility - Check donation eligibility
    GET    /donors/{id}/history     - Get donation history
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.schemas.donor import (
    DonorCreate,
    DonorUpdate,
    DonorResponse,
    DonorEligibility,
)
from app.services import donor_service

router = APIRouter(
    prefix="/donors",
    tags=["Donors"],
)


@router.get("/", response_model=list[DonorResponse])
def list_donors(
    skip: int = Query(0, ge=0, description="Records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records"),
    blood_group: Optional[str] = Query(None, description="Filter by blood group"),
    search: Optional[str] = Query(None, description="Search by name or phone"),
    db: Session = Depends(get_db),
):
    """
    List all donors with optional filtering.

    - **blood_group**: Filter by specific blood group (e.g. "A+", "O-")
    - **search**: Search in donor name or phone number
    - **skip/limit**: Pagination
    """
    donors = donor_service.get_all_donors(db, skip, limit, blood_group, search)
    return donors


@router.post("/", response_model=DonorResponse, status_code=201)
def create_donor(
    data: DonorCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new blood donor.

    Required fields: name, blood_group, phone, dob
    Phone must be unique across all donors.
    """
    return donor_service.create_donor(db, data)


@router.get("/{donor_id}", response_model=DonorResponse)
def get_donor(
    donor_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific donor by ID."""
    return donor_service.get_donor(db, donor_id)


@router.put("/{donor_id}", response_model=DonorResponse)
def update_donor(
    donor_id: int,
    data: DonorUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a donor's information.
    Only send the fields you want to change.
    """
    return donor_service.update_donor(db, donor_id, data)


@router.delete("/{donor_id}", status_code=204)
def delete_donor(
    donor_id: int,
    db: Session = Depends(get_db),
):
    """Delete a donor by ID."""
    donor_service.delete_donor(db, donor_id)


@router.get("/{donor_id}/eligibility", response_model=DonorEligibility)
def check_eligibility(
    donor_id: int,
    db: Session = Depends(get_db),
):
    """
    Check if a donor is eligible to donate blood.

    Rules:
        - Age must be 18-65
        - At least 90 days since last donation
    """
    return donor_service.check_eligibility(db, donor_id)


@router.get("/{donor_id}/history")
def get_donation_history(
    donor_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the full donation history for a donor.
    Returns all blood units donated, ordered by date (newest first).
    """
    units = donor_service.get_donation_history(db, donor_id)
    return [
        {
            "bank_id": u.bank_id,
            "unit_id": u.unit_id,
            "volume_ml": u.volume_ml,
            "donation_date": u.donation_date.isoformat(),
            "blood_group": u.blood_group,
            "component_type": u.component_type,
            "collection_date": u.collection_date.isoformat(),
            "expiry_date": u.expiry_date.isoformat(),
            "status": u.status,
        }
        for u in units
    ]
