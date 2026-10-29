from datetime import date
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.request import Request
from app.core.enums import RequestStatus, Urgency


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[RequestStatus] = None,
    urgency: Optional[Urgency] = None,
    hospital_id: Optional[int] = None,
    request_date: Optional[date] = None,
) -> list[Request]:
    query = db.query(Request)

    if status is not None:
        query = query.filter(Request.status == status)

    if urgency is not None:
        query = query.filter(Request.urgency == urgency)

    if hospital_id is not None:
        query = query.filter(Request.hospital_id == hospital_id)

    if request_date is not None:
        query = query.filter(Request.request_date == request_date)

    urgency_order = {
        Urgency.EMERGENCY: 0,
        Urgency.URGENT: 1,
        Urgency.ROUTINE: 2,
    }

    # Apply urgency ordering in SQL so pagination stays correct.
    from sqlalchemy import case

    return (
        query.order_by(
            case(urgency_order, value=Request.urgency, else_=3),
            Request.request_date.asc(),
            Request.request_id.asc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_by_id(db: Session, request_id: int) -> Optional[Request]:
    return (
        db.query(Request)
        .options(
            joinedload(Request.hospital),
            joinedload(Request.recipient),
        )
        .filter(Request.request_id == request_id)
        .first()
    )


def create(db: Session, request: Request) -> Request:
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def update(db: Session, request: Request) -> Request:
    db.commit()
    db.refresh(request)
    return request


def delete(db: Session, request: Request) -> None:
    db.delete(request)
    db.commit()