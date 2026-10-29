"""
Donor Repository - database access for the donor table.

This layer ONLY talks to the database. No business logic here.
Business rules live in services/donor_service.py.

Pattern:
    Router → Service → Repository → Database
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.models.donor import Donor


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    blood_group: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Donor]:
    """
    Fetch all donors with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Max records to return
        blood_group: Filter by blood group (e.g. "A+")
        search: Search in name or phone
    """
    query = db.query(Donor)

    if blood_group:
        query = query.filter(Donor.blood_group == blood_group)

    if search:
        query = query.filter(
            or_(
                Donor.name.ilike(f"%{search}%"),
                Donor.phone.ilike(f"%{search}%"),
            )
        )

    return query.order_by(Donor.donor_id).offset(skip).limit(limit).all()


def get_by_id(db: Session, donor_id: int) -> Optional[Donor]:
    """Fetch a single donor by ID."""
    return db.query(Donor).filter(Donor.donor_id == donor_id).first()


def get_by_phone(db: Session, phone: str) -> Optional[Donor]:
    """Fetch a donor by phone number (unique field)."""
    return db.query(Donor).filter(Donor.phone == phone).first()


def create(db: Session, donor: Donor) -> Donor:
    """Insert a new donor into the database."""
    db.add(donor)
    db.commit()
    db.refresh(donor)
    return donor


def update(db: Session, donor: Donor) -> Donor:
    """Update an existing donor (the caller modifies fields first)."""
    db.commit()
    db.refresh(donor)
    return donor


def delete(db: Session, donor: Donor) -> None:
    """Delete a donor from the database."""
    db.delete(donor)
    db.commit()


def count(db: Session, blood_group: Optional[str] = None) -> int:
    """Count donors, optionally filtered by blood group."""
    query = db.query(Donor)
    if blood_group:
        query = query.filter(Donor.blood_group == blood_group)
    return query.count()
