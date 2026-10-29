
from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.request import Request
from app.repositories import request_repo, hospital_repo, recipient_repo
from app.schemas.request import RequestCreate
from app.core.enums import RequestStatus, Urgency
from app.core.errors import NotFound, ConflictError


def get_all_requests(
    db: Session,
    skip=0,
    limit=100,
    status: RequestStatus | None = None,
    urgency: Urgency | None = None,
    hospital_id: int | None = None,
    request_date: date | None = None,
):
    return request_repo.get_all(
        db, skip, limit, status, urgency, hospital_id, request_date
    )


def get_request(db: Session, request_id: int) -> Request:
    request = request_repo.get_by_id(db, request_id)
    if not request:
        raise NotFound(f"Request with ID {request_id} not found")
    return request


def create_request(db: Session, data: RequestCreate) -> Request:
    if not hospital_repo.get_by_id(db, data.hospital_id):
        raise NotFound(f"Hospital with ID {data.hospital_id} not found")

    if not recipient_repo.get_by_id(db, data.recipient_id):
        raise NotFound(f"Recipient with ID {data.recipient_id} not found")

    request = Request(
        hospital_id=data.hospital_id,
        recipient_id=data.recipient_id,
        component_type=data.component_type,
        quantity=data.quantity,
        urgency=data.urgency,
        status=RequestStatus.PENDING,
    )
    return request_repo.create(db, request)


def recompute_status(db: Session, request_id: int) -> RequestStatus:
    """Recalculate status after blood units are issued."""
    request = get_request(db, request_id)

    if request.status == RequestStatus.CANCELLED:
        return request.status

    issued = db.execute(
        text(
            "SELECT COALESCE(SUM(quantity_issued), 0) "
            "FROM issue WHERE request_id = :request_id"
        ),
        {"request_id": request_id},
    ).scalar() or 0

    if issued >= request.quantity:
        request.status = RequestStatus.FULFILLED
    elif issued > 0:
        request.status = RequestStatus.PARTIALLY_FULFILLED
    else:
        request.status = RequestStatus.PENDING

    request_repo.update(db, request)
    return request.status


def cancel_request(db: Session, request_id: int) -> Request:
    request = get_request(db, request_id)

    if request.status == RequestStatus.CANCELLED:
        raise ConflictError("Request is already cancelled")

    issued = db.execute(
        text(
            "SELECT COALESCE(SUM(quantity_issued), 0) "
            "FROM issue WHERE request_id = :request_id"
        ),
        {"request_id": request_id},
    ).scalar() or 0

    if issued > 0:
        raise ConflictError("Cannot cancel a request after blood has been issued")

    request.status = RequestStatus.CANCELLED
    return request_repo.update(db, request)
