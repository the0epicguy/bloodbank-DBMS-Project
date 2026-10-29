"""
routers/inventory.py (sync version)
Blood unit / cold-storage inventory endpoints — Prefix: /inventory
"""

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.enums import BloodGroup, ComponentType, UnitStatus
from app.core.errors import NotFound
from app.repositories import inventory_repo
from app.schemas.inventory import (
    BloodUnitResponse,
    DiscardUnitRequest,
    ExpirySweepResult,
)
from app.services import expiry_service, unit_service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get(
    "/banks/{bank_id}/units",
    response_model=list[BloodUnitResponse],
    summary="List blood units for a bank (FEFO order)",
)
def list_units_for_bank(
    bank_id: int,
    blood_group: BloodGroup | None = Query(None),
    component_type: ComponentType | None = Query(None),
    status: UnitStatus | None = Query(None),
    expiring_within_days: int | None = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return unit_service.get_inventory_for_bank(
        db,
        bank_id=bank_id,
        blood_group=blood_group,
        component_type=component_type,
        status=status,
        expiring_within_days=expiring_within_days,
        skip=skip,
        limit=limit,
    )


@router.get("/summary", summary="Global stock matrix")
def global_inventory_summary(
    bank_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    if bank_id is not None and inventory_repo.get_bank_by_id(db, bank_id) is None:
        raise NotFound(f"Blood bank with id={bank_id} not found.")

    raw_rows = inventory_repo.get_stock_summary(db, bank_id=bank_id)
    all_banks = inventory_repo.get_all_banks(db)
    banks_map = {b.bank_id: b.name for b in all_banks}

    matrix_by_bank: dict[int, list] = defaultdict(list)
    low_stock = []

    for row in raw_rows:
        cell = {
            "blood_group": row["blood_group"],
            "component_type": row["component_type"],
            "available_units": row["available_units"],
            "earliest_expiry": row["earliest_expiry"],
        }
        matrix_by_bank[row["bank_id"]].append(cell)
        if row["available_units"] < settings.CRITICAL_STOCK_THRESHOLD:
            low_stock.append(cell)

    bank_summaries = [
        {"bank_id": bid, "bank_name": banks_map.get(bid, "Unknown"), "matrix": cells}
        for bid, cells in matrix_by_bank.items()
    ]

    return {
        "banks": bank_summaries,
        "total_available": sum(r["available_units"] for r in raw_rows),
        "low_stock_alerts": low_stock,
    }


@router.post("/expire-sweep", response_model=ExpirySweepResult, summary="Batch expiry sweep")
def run_expire_sweep(db: Session = Depends(get_db)):
    return expiry_service.sweep_expired(db)


@router.get("/units/{bank_id}/{unit_id}", response_model=BloodUnitResponse, summary="Get a single blood unit")
def get_unit(bank_id: int, unit_id: int, db: Session = Depends(get_db)):
    unit = inventory_repo.get_unit(db, bank_id, unit_id)
    if unit is None:
        raise NotFound(f"Blood unit ({bank_id}, {unit_id}) not found.")
    d = {c.name: getattr(unit, c.name) for c in unit.__table__.columns}
    d["days_to_expiry"] = (unit.expiry_date - date.today()).days
    return d


@router.patch("/units/{bank_id}/{unit_id}/discard", response_model=BloodUnitResponse, summary="Discard a unit")
def discard_unit(bank_id: int, unit_id: int, payload: DiscardUnitRequest, db: Session = Depends(get_db)):
    unit = unit_service.discard_unit(db, bank_id, unit_id, payload.reason)
    d = {c.name: getattr(unit, c.name) for c in unit.__table__.columns}
    d["days_to_expiry"] = (unit.expiry_date - date.today()).days
    return d
