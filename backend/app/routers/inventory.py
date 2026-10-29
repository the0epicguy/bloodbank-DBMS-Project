"""
routers/inventory.py
====================
Blood unit / cold-storage inventory endpoints.

Prefix: /api/v1/inventory
Tag:    inventory
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import BloodGroup, ComponentType, UnitStatus
from app.core.errors import NotFoundError
from app.repositories import inventory_repo
from app.schemas.inventory import (
    BloodUnitResponse,
    DiscardUnitRequest,
    ExpirySweepResult,
    GlobalInventorySummary,
    BankInventorySummary,
    StockCell,
)
from app.services import expiry_service, unit_service

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


# ---------------------------------------------------------------------------
# GET /api/v1/inventory/banks/{bank_id}/units
# ---------------------------------------------------------------------------
@router.get(
    "/banks/{bank_id}/units",
    response_model=list[BloodUnitResponse],
    summary="List blood units for a specific bank",
    description=(
        "Filterable by blood_group, component_type, status, and "
        "expiring_within_days. Results are sorted by expiry_date ascending (FEFO order)."
    ),
)
async def list_units_for_bank(
    bank_id: int,
    blood_group: BloodGroup | None = Query(None, description="Filter by blood group"),
    component_type: ComponentType | None = Query(None, description="Filter by component type"),
    status: UnitStatus | None = Query(None, description="Filter by unit status"),
    expiring_within_days: int | None = Query(
        None, ge=1, description="Only units expiring within this many days"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    return await unit_service.get_inventory_for_bank(
        db,
        bank_id=bank_id,
        blood_group=blood_group,
        component_type=component_type,
        status=status,
        expiring_within_days=expiring_within_days,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/inventory/summary
# ---------------------------------------------------------------------------
@router.get(
    "/summary",
    response_model=GlobalInventorySummary,
    summary="Global stock matrix (Blood Group × Component Type per bank)",
    description=(
        "Returns a nested summary: per-bank matrix of available unit counts "
        "by blood group and component. Low-stock alerts included for groups "
        "below the configured threshold."
    ),
)
async def global_inventory_summary(
    bank_id: int | None = Query(None, description="Scope to a specific bank"),
    db: AsyncSession = Depends(get_db),
):
    from app.core.config import settings

    if bank_id is not None:
        bank = await inventory_repo.get_bank_by_id(db, bank_id)
        if bank is None:
            raise NotFoundError(f"Blood bank with id={bank_id} not found.")

    raw_rows = await inventory_repo.get_stock_summary(db, bank_id=bank_id)

    # Group by bank
    from collections import defaultdict
    banks_lookup: dict[int, dict] = {}
    all_banks = await inventory_repo.get_all_banks(db)
    banks_map = {b.bank_id: b.name for b in all_banks}

    matrix_by_bank: dict[int, list[StockCell]] = defaultdict(list)
    low_stock: list[StockCell] = []

    for row in raw_rows:
        cell = StockCell(
            blood_group=row["blood_group"],
            component_type=row["component_type"],
            available_units=row["available_units"],
            earliest_expiry=row["earliest_expiry"],
        )
        matrix_by_bank[row["bank_id"]].append(cell)
        if row["available_units"] < settings.LOW_STOCK_THRESHOLD:
            low_stock.append(cell)

    bank_summaries = [
        BankInventorySummary(
            bank_id=bid,
            bank_name=banks_map.get(bid, "Unknown"),
            matrix=cells,
        )
        for bid, cells in matrix_by_bank.items()
    ]

    total_available = sum(r["available_units"] for r in raw_rows)

    return GlobalInventorySummary(
        banks=bank_summaries,
        total_available=total_available,
        low_stock_alerts=low_stock,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/inventory/expire-sweep
# ---------------------------------------------------------------------------
@router.post(
    "/expire-sweep",
    response_model=ExpirySweepResult,
    summary="Run expiry sweep — mark past-expiry AVAILABLE units as EXPIRED",
    description=(
        "Scans all AVAILABLE blood units and transitions any with "
        "expiry_date < TODAY to EXPIRED. Safe to run multiple times."
    ),
)
async def run_expire_sweep(db: AsyncSession = Depends(get_db)):
    return await expiry_service.run_expiry_sweep(db)


# ---------------------------------------------------------------------------
# GET /api/v1/inventory/units/{bank_id}/{unit_id}
# ---------------------------------------------------------------------------
@router.get(
    "/units/{bank_id}/{unit_id}",
    response_model=BloodUnitResponse,
    summary="Get a single blood unit by its composite key",
)
async def get_unit(
    bank_id: int,
    unit_id: int,
    db: AsyncSession = Depends(get_db),
):
    from datetime import date

    unit = await inventory_repo.get_unit(db, bank_id, unit_id)
    if unit is None:
        raise NotFoundError(f"Blood unit ({bank_id}, {unit_id}) not found.")

    d = {c.name: getattr(unit, c.name) for c in unit.__table__.columns}
    d["days_to_expiry"] = (unit.expiry_date - date.today()).days
    return d


# ---------------------------------------------------------------------------
# PATCH /api/v1/inventory/units/{bank_id}/{unit_id}/discard
# ---------------------------------------------------------------------------
@router.patch(
    "/units/{bank_id}/{unit_id}/discard",
    response_model=BloodUnitResponse,
    summary="Discard a blood unit with an audit reason",
    description=(
        "Sets the unit status to DISCARDED. A mandatory reason string is "
        "required for full audit trail. Cannot discard an already ISSUED unit."
    ),
)
async def discard_unit(
    bank_id: int,
    unit_id: int,
    payload: DiscardUnitRequest,
    db: AsyncSession = Depends(get_db),
):
    from datetime import date

    unit = await unit_service.discard_unit(db, bank_id, unit_id, payload.reason)
    d = {c.name: getattr(unit, c.name) for c in unit.__table__.columns}
    d["days_to_expiry"] = (unit.expiry_date - date.today()).days
    return d
