"""
routers/banks.py (sync version)
Blood bank CRUD endpoints — Prefix: /banks
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ConflictError, NotFound
from app.repositories import inventory_repo
from app.schemas.inventory import BloodBankCreate, BloodBankResponse, BloodBankUpdate
from app.services import unit_service

router = APIRouter(prefix="/banks", tags=["banks"])


@router.get("", response_model=list[BloodBankResponse], summary="List all blood banks")
def list_banks(db: Session = Depends(get_db)):
    return unit_service.get_all_banks_with_stock(db)


@router.get("/{bank_id}", response_model=BloodBankResponse, summary="Get a single blood bank")
def get_bank(bank_id: int, db: Session = Depends(get_db)):
    results = unit_service.get_all_banks_with_stock(db)
    bank = next((b for b in results if b["bank_id"] == bank_id), None)
    if bank is None:
        raise NotFound(f"Blood bank with id={bank_id} not found.")
    return bank


@router.post("", response_model=BloodBankResponse, status_code=status.HTTP_201_CREATED, summary="Register a new blood bank")
def create_bank(payload: BloodBankCreate, db: Session = Depends(get_db)):
    if payload.email:
        existing = inventory_repo.get_bank_by_email(db, payload.email)
        if existing:
            raise ConflictError(f"A blood bank with email '{payload.email}' already exists.")
    bank = inventory_repo.create_bank(db, **payload.model_dump())
    return {
        **{c.name: getattr(bank, c.name) for c in bank.__table__.columns},
        "available_units": 0,
        "expiring_soon": 0,
    }


@router.put("/{bank_id}", response_model=BloodBankResponse, summary="Update a blood bank")
def update_bank(bank_id: int, payload: BloodBankUpdate, db: Session = Depends(get_db)):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "email" in updates:
        existing = inventory_repo.get_bank_by_email(db, updates["email"])
        if existing and existing.bank_id != bank_id:
            raise ConflictError(f"Email '{updates['email']}' is already in use.")
    bank = inventory_repo.update_bank(db, bank_id, **updates)
    if bank is None:
        raise NotFound(f"Blood bank with id={bank_id} not found.")
    results = unit_service.get_all_banks_with_stock(db)
    return next(b for b in results if b["bank_id"] == bank_id)


@router.delete("/{bank_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a blood bank")
def delete_bank(bank_id: int, db: Session = Depends(get_db)):
    deleted = inventory_repo.delete_bank(db, bank_id)
    if not deleted:
        raise NotFound(f"Blood bank with id={bank_id} not found.")
