"""
routers/banks.py
================
Blood bank CRUD endpoints.

Prefix: /api/v1/banks
Tag:    banks
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import ConflictError, NotFoundError
from app.repositories import inventory_repo
from app.schemas.inventory import (
    BloodBankCreate,
    BloodBankResponse,
    BloodBankUpdate,
)
from app.services import unit_service

router = APIRouter(prefix="/api/v1/banks", tags=["banks"])


# ---------------------------------------------------------------------------
# GET /api/v1/banks
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=list[BloodBankResponse],
    summary="List all blood banks",
    description=(
        "Returns every registered blood bank, each annotated with the "
        "current count of AVAILABLE blood units and units expiring within "
        "the configured warning window."
    ),
)
async def list_banks(db: AsyncSession = Depends(get_db)):
    return await unit_service.get_all_banks_with_stock(db)


# ---------------------------------------------------------------------------
# GET /api/v1/banks/{bank_id}
# ---------------------------------------------------------------------------
@router.get(
    "/{bank_id}",
    response_model=BloodBankResponse,
    summary="Get a single blood bank by ID",
)
async def get_bank(bank_id: int, db: AsyncSession = Depends(get_db)):
    results = await unit_service.get_all_banks_with_stock(db)
    bank = next((b for b in results if b["bank_id"] == bank_id), None)
    if bank is None:
        raise NotFoundError(f"Blood bank with id={bank_id} not found.")
    return bank


# ---------------------------------------------------------------------------
# POST /api/v1/banks
# ---------------------------------------------------------------------------
@router.post(
    "",
    response_model=BloodBankResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new blood bank",
)
async def create_bank(
    payload: BloodBankCreate,
    db: AsyncSession = Depends(get_db),
):
    # Check email uniqueness
    if payload.email:
        existing = await inventory_repo.get_bank_by_email(db, payload.email)
        if existing:
            raise ConflictError(f"A blood bank with email '{payload.email}' already exists.")

    bank = await inventory_repo.create_bank(db, **payload.model_dump())
    return {
        **{c.name: getattr(bank, c.name) for c in bank.__table__.columns},
        "available_units": 0,
        "expiring_soon": 0,
    }


# ---------------------------------------------------------------------------
# PUT /api/v1/banks/{bank_id}
# ---------------------------------------------------------------------------
@router.put(
    "/{bank_id}",
    response_model=BloodBankResponse,
    summary="Update a blood bank's details",
)
async def update_bank(
    bank_id: int,
    payload: BloodBankUpdate,
    db: AsyncSession = Depends(get_db),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if "email" in updates:
        existing = await inventory_repo.get_bank_by_email(db, updates["email"])
        if existing and existing.bank_id != bank_id:
            raise ConflictError(f"Email '{updates['email']}' is already in use.")

    bank = await inventory_repo.update_bank(db, bank_id, **updates)
    if bank is None:
        raise NotFoundError(f"Blood bank with id={bank_id} not found.")

    results = await unit_service.get_all_banks_with_stock(db)
    return next(b for b in results if b["bank_id"] == bank_id)


# ---------------------------------------------------------------------------
# DELETE /api/v1/banks/{bank_id}
# ---------------------------------------------------------------------------
@router.delete(
    "/{bank_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a blood bank (cascades to all its blood units)",
)
async def delete_bank(bank_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await inventory_repo.delete_bank(db, bank_id)
    if not deleted:
        raise NotFoundError(f"Blood bank with id={bank_id} not found.")
