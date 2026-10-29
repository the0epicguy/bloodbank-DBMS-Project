"""
services/expiry_service.py
==========================
Expiry sweep service: transitions all AVAILABLE blood units past their
expiry_date to EXPIRED status.

Can be triggered:
  - Via the API endpoint POST /api/v1/inventory/expire-sweep (manual trigger).
  - Via a scheduled job (e.g. APScheduler or a cron script calling this directly).
"""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import inventory_repo
from app.schemas.inventory import ExpirySweepResult


async def run_expiry_sweep(db: AsyncSession) -> ExpirySweepResult:
    """
    Find all AVAILABLE units where expiry_date < today,
    mark them EXPIRED, and return a summary of the operation.

    The MySQL trigger `trg_after_issue_insert` handles ISSUED status updates;
    this sweep only targets units that were never allocated.
    """
    swept_units = await inventory_repo.sweep_expired_units(db)

    expired_ids = [
        {"bank_id": u.bank_id, "unit_id": u.unit_id}
        for u in swept_units
    ]

    return ExpirySweepResult(
        swept_count=len(swept_units),
        expired_unit_ids=expired_ids,
    )
