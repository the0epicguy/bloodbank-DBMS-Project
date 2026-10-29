
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import RequestStatus, Urgency
from app.schemas.request import RequestCreate, RequestResponse
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["Blood Requests"])


@router.get("/", response_model=list[RequestResponse])
def list_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: RequestStatus | None = None,
    urgency: Urgency | None = None,
    hospital_id: int | None = Query(None, gt=0),
    request_date: date | None = None,
    db: Session = Depends(get_db),
):
    return request_service.get_all_requests(
        db, skip, limit, status, urgency, hospital_id, request_date
    )


@router.post("/", response_model=RequestResponse, status_code=201)
def create_request(data: RequestCreate, db: Session = Depends(get_db)):
    return request_service.create_request(db, data)


@router.get("/{request_id}", response_model=RequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    return request_service.get_request(db, request_id)


@router.patch("/{request_id}/cancel", response_model=RequestResponse)
def cancel_request(request_id: int, db: Session = Depends(get_db)):
    return request_service.cancel_request(db, request_id)
