
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import BloodGroup
from app.schemas.recipient import RecipientCreate, RecipientUpdate, RecipientResponse
from app.services import recipient_service

router = APIRouter(prefix="/recipients", tags=["Recipients"])


@router.get("/", response_model=list[RecipientResponse])
def list_recipients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    blood_group: BloodGroup | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return recipient_service.get_all_recipients(
        db, skip, limit, blood_group, search
    )


@router.post("/", response_model=RecipientResponse, status_code=201)
def create_recipient(data: RecipientCreate, db: Session = Depends(get_db)):
    return recipient_service.create_recipient(db, data)


@router.get("/{recipient_id}", response_model=RecipientResponse)
def get_recipient(recipient_id: int, db: Session = Depends(get_db)):
    return recipient_service.get_recipient(db, recipient_id)


@router.put("/{recipient_id}", response_model=RecipientResponse)
def update_recipient(
    recipient_id: int, data: RecipientUpdate, db: Session = Depends(get_db)
):
    return recipient_service.update_recipient(db, recipient_id, data)


@router.delete("/{recipient_id}", status_code=204)
def delete_recipient(recipient_id: int, db: Session = Depends(get_db)):
    recipient_service.delete_recipient(db, recipient_id)
