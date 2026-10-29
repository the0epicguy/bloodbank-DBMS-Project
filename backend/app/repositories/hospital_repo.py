from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.models.hospital import Hospital


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
) -> list[Hospital]:
    query = db.query(Hospital)

    if search:
        query = query.filter(
            or_(
                Hospital.name.ilike(f"%{search}%"),
                Hospital.address.ilike(f"%{search}%"),
                Hospital.contact.ilike(f"%{search}%"),
            )
        )

    return (
        query.order_by(Hospital.hospital_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_by_id(db: Session, hospital_id: int) -> Optional[Hospital]:
    return (
        db.query(Hospital)
        .filter(Hospital.hospital_id == hospital_id)
        .first()
    )


def create(db: Session, hospital: Hospital) -> Hospital:
    db.add(hospital)
    db.commit()
    db.refresh(hospital)
    return hospital


def update(db: Session, hospital: Hospital) -> Hospital:
    db.commit()
    db.refresh(hospital)
    return hospital


def delete(db: Session, hospital: Hospital) -> None:
    db.delete(hospital)
    db.commit()