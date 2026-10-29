"""
Report Service (Person 4) - read-only aggregations for the dashboard.

    stock_distribution()    available units per blood group vs. critical reserve
    expiring_soon()         units expiring within 7 / 14 days
    fulfillment_metrics()   fulfilment %, turnaround by urgency
    dashboard_summary()     headline numbers for the metric cards
"""

from datetime import date, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import BloodGroup, ComponentType
from app.models.blood_bank import BloodBank
from app.models.blood_unit import BloodUnit
from app.models.donor import Donor
from app.models.issue import Issue
from app.models.request import Request

GROUPS = [g.value for g in BloodGroup]
COMPONENTS = [c.value for c in ComponentType]
URGENCIES = ["EMERGENCY", "URGENT", "ROUTINE"]


def _usable():
    """Filter for units that can actually be given out today."""
    return (BloodUnit.status == "AVAILABLE", BloodUnit.expiry_date >= date.today())


def _stock_status(total: int, threshold: int) -> str:
    if total < threshold:
        return "CRITICAL"
    if total < threshold * 2:
        return "LOW"
    return "HEALTHY"


def stock_distribution(db: Session) -> dict:
    threshold = settings.CRITICAL_STOCK_THRESHOLD
    rows = (
        db.query(BloodUnit.blood_group, BloodUnit.component_type, func.count())
        .filter(*_usable())
        .group_by(BloodUnit.blood_group, BloodUnit.component_type)
        .all()
    )
    table = {g: {c: 0 for c in COMPONENTS} for g in GROUPS}
    for group, comp, n in rows:
        table[group][comp] = n

    groups = []
    for g in GROUPS:
        total = sum(table[g].values())
        groups.append({
            "blood_group": g,
            "total": total,
            "status": _stock_status(total, threshold),
            "components": table[g],
        })
    return {
        "critical_threshold": threshold,
        "total_available": sum(x["total"] for x in groups),
        "critical_groups": [x["blood_group"] for x in groups if x["status"] == "CRITICAL"],
        "groups": groups,
    }


def expiring_soon(db: Session) -> dict:
    today = date.today()
    rows = (
        db.query(BloodUnit, BloodBank.name)
        .join(BloodBank, BloodBank.bank_id == BloodUnit.bank_id)
        .filter(
            BloodUnit.status == "AVAILABLE",
            BloodUnit.expiry_date >= today,
            BloodUnit.expiry_date <= today + timedelta(days=14),
        )
        .order_by(BloodUnit.expiry_date, BloodUnit.bank_id, BloodUnit.unit_id)
        .all()
    )
    within_7, within_14 = [], []
    for u, bank_name in rows:
        days = (u.expiry_date - today).days
        item = {
            "bank_id": u.bank_id, "unit_id": u.unit_id, "bank_name": bank_name,
            "blood_group": u.blood_group, "component_type": u.component_type,
            "expiry_date": u.expiry_date.isoformat(), "days_to_expiry": days,
        }
        (within_7 if days <= 7 else within_14).append(item)

    # AVAILABLE units whose date has passed: they still need an expiry sweep (Person 2)
    unswept = (
        db.query(func.count())
        .select_from(BloodUnit)
        .filter(BloodUnit.status == "AVAILABLE", BloodUnit.expiry_date < today)
        .scalar()
    ) or 0
    return {
        "within_7_days": within_7,
        "within_14_days": within_14,       # days 8-14
        "count_7_days": len(within_7),
        "count_14_days": len(within_14),
        "expired_not_swept": unswept,
    }


def fulfillment_metrics(db: Session) -> dict:
    # 1) request counts per urgency
    req_rows = (
        db.query(
            Request.urgency,
            func.count(),
            func.sum(case((Request.status == "FULFILLED", 1), else_=0)),
            func.sum(case((Request.status == "PARTIALLY_FULFILLED", 1), else_=0)),
            func.sum(case((Request.status == "PENDING", 1), else_=0)),
            func.sum(case((Request.status == "CANCELLED", 1), else_=0)),
            func.sum(case((Request.status != "CANCELLED", Request.quantity), else_=0)),
        )
        .group_by(Request.urgency)
        .all()
    )
    # 2) units issued per urgency
    issued_rows = (
        db.query(Request.urgency, func.count(Issue.issue_id))
        .join(Issue, Issue.request_id == Request.request_id)
        .group_by(Request.urgency)
        .all()
    )
    issued = {u: n for u, n in issued_rows}

    # 3) average days from request_date to the LAST issue, for fulfilled requests
    last_issue = (
        db.query(Issue.request_id.label("rid"), func.max(Issue.issue_date).label("last"))
        .group_by(Issue.request_id)
        .subquery()
    )
    turn_rows = (
        db.query(
            Request.urgency,
            func.avg(func.datediff(func.date(last_issue.c.last), Request.request_date)),
        )
        .join(last_issue, last_issue.c.rid == Request.request_id)
        .filter(Request.status == "FULFILLED")
        .group_by(Request.urgency)
        .all()
    )
    turnaround = {u: (float(v) if v is not None else None) for u, v in turn_rows}

    data = {u: None for u in URGENCIES}
    for urg, total, ful, part, pend, canc, units_req in req_rows:
        units_req = int(units_req or 0)
        units_iss = int(issued.get(urg, 0))
        data[urg] = {
            "urgency": urg,
            "total_requests": int(total),
            "fulfilled": int(ful or 0),
            "partially_fulfilled": int(part or 0),
            "pending": int(pend or 0),
            "cancelled": int(canc or 0),
            "units_requested": units_req,
            "units_issued": units_iss,
            "fulfillment_rate_pct": round(units_iss * 100.0 / units_req, 1) if units_req else 0.0,
            "avg_turnaround_days": (round(turnaround[urg], 2) if turnaround.get(urg) is not None else None),
        }
    for urg in URGENCIES:
        if data[urg] is None:
            data[urg] = {
                "urgency": urg, "total_requests": 0, "fulfilled": 0,
                "partially_fulfilled": 0, "pending": 0, "cancelled": 0,
                "units_requested": 0, "units_issued": 0,
                "fulfillment_rate_pct": 0.0, "avg_turnaround_days": None,
            }
    all_req = sum(d["units_requested"] for d in data.values())
    all_iss = sum(d["units_issued"] for d in data.values())
    return {
        "by_urgency": [data[u] for u in URGENCIES],
        "overall_fulfillment_rate_pct": round(all_iss * 100.0 / all_req, 1) if all_req else 0.0,
    }


def dashboard_summary(db: Session) -> dict:
    today = date.today()
    month_start = today.replace(day=1)

    available = db.query(func.count()).select_from(BloodUnit).filter(*_usable()).scalar() or 0
    exp7 = (
        db.query(func.count()).select_from(BloodUnit)
        .filter(BloodUnit.status == "AVAILABLE", BloodUnit.expiry_date >= today,
                BloodUnit.expiry_date <= today + timedelta(days=7))
        .scalar()
    ) or 0
    open_q = db.query(func.count()).select_from(Request).filter(
        Request.status.in_(["PENDING", "PARTIALLY_FULFILLED"]))
    open_requests = open_q.scalar() or 0
    emergency_open = open_q.filter(Request.urgency == "EMERGENCY").scalar() or 0
    issued_month = (
        db.query(func.count(Issue.issue_id)).filter(Issue.issue_date >= month_start).scalar()
    ) or 0
    total_issued = db.query(func.count(Issue.issue_id)).scalar() or 0
    donors = db.query(func.count(Donor.donor_id)).scalar() or 0
    banks = db.query(func.count(BloodBank.bank_id)).scalar() or 0

    return {
        "available_units": available,
        "expiring_7_days": exp7,
        "open_requests": open_requests,
        "emergency_open": emergency_open,
        "issued_this_month": issued_month,
        "total_issued": total_issued,
        "total_donors": donors,
        "total_banks": banks,
    }
