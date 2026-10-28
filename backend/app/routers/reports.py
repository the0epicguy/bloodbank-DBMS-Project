from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.schemas.report import StockDistributionItem, ExpiringUnitItem, FulfillmentMetricsResponse
from app.services.report_service import stock_distribution, expiring_soon, fulfillment_metrics

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/stock-distribution", response_model=list[StockDistributionItem])
async def stock_report(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("ADMIN", "BANK_STAFF", "HOSPITAL_STAFF"))):
    return await stock_distribution(db)

@router.get("/expiring-soon", response_model=list[ExpiringUnitItem])
async def expiring_report(days: int = Query(7, ge=1, le=30), db: AsyncSession = Depends(get_db),
                          user: User = Depends(require_roles("ADMIN", "BANK_STAFF"))):
    return await expiring_soon(db, days)

@router.get("/fulfillment-metrics", response_model=FulfillmentMetricsResponse)
async def metrics_report(db: AsyncSession = Depends(get_db), user: User = Depends(require_roles("ADMIN", "BANK_STAFF", "HOSPITAL_STAFF"))):
    return await fulfillment_metrics(db)
