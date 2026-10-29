from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.models.recipient import Recipient
from app.core.enums import BloodGroup


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    blood_group: Optional[BloodGroup] = None,
    search: Optional[str] = None,
) -> list[Recipient]:
    query = db.query(Recipient)

    if blood_group is not None:
        query = query.filter(Recipient.blood_group == blood_group)

    if search:
        query = query.filter(
            or_(
                Recipient.name.ilike(f"%{search}%"),
            )
        )

    return (
        query.order_by(Recipient.recipient_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_by_id(db: Session, recipient_id: int) -> Optional[Recipient]:
    return (
        db.query(Recipient)
        .filter(Recipient.recipient_id == recipient_id)
        .first()
    )


def create(db: Session, recipient: Recipient) -> Recipient:
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient


def update(db: Session, recipient: Recipient) -> Recipient:
    db.commit()
    db.refresh(recipient)
    return recipient


def delete(db: Session, recipient: Recipient) -> None:
    db.delete(recipient)
    db.commit()
    