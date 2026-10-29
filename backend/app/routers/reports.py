"""
Reports Router (Person 4) - read-only analytics. ADMIN and BANK_STAFF only.

Endpoints:
    GET /reports/summary               - headline numbers for the dashboard cards
    GET /reports/stock-distribution    - units per blood group vs critical reserve
    GET /reports/expiring-soon         - units expiring within 7 and 14 days
    GET /reports/fulfillment-metrics   - fulfilment % and turnaround by urgency
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.services import report_service

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return report_service.dashboard_summary(db)


@router.get("/stock-distribution")
def stock_distribution(db: Session = Depends(get_db)):
    return report_service.stock_distribution(db)


@router.get("/expiring-soon")
def expiring_soon(db: Session = Depends(get_db)):
    return report_service.expiring_soon(db)


@router.get("/fulfillment-metrics")
def fulfillment_metrics(db: Session = Depends(get_db)):
    return report_service.fulfillment_metrics(db)
