"""
services/expiry_service.py (sync version)
Batch sweep: marks AVAILABLE blood units past their expiry date as EXPIRED.
"""

from sqlalchemy.orm import Session
from app.repositories import inventory_repo


def sweep_expired(db: Session) -> dict:
    """
    Sweep all AVAILABLE blood units whose expiry_date < today and mark them EXPIRED.
    Returns a summary dict with the count and details.
    """
    swept = inventory_repo.sweep_expired_units(db)
    return {
        "swept_count": len(swept),
        "swept_units": [
            {
                "bank_id": u.bank_id,
                "unit_id": u.unit_id,
                "blood_group": u.blood_group,
                "component_type": u.component_type,
                "expiry_date": str(u.expiry_date),
            }
            for u in swept
        ],
    }
