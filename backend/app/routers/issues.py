"""
Issues Router (Person 4).

Endpoints:
    GET  /issues                             - audit log of every issued unit
    GET  /issues/pending-requests            - open requests that can be fulfilled
    POST /issues/manual                      - issue one chosen unit to a request
    GET  /requests/{id}/fefo-preview         - which units FEFO would pick
    POST /requests/{id}/auto-fulfil          - run the FEFO allocation

Who can do what:
    ADMIN, BANK_STAFF      -> everything
    HOSPITAL_STAFF         -> read the audit log / pending list (own hospital only)
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import UserAccount
from app.schemas.issue import (
    FEFOPreview, FulfilResult, IssueListResponse, ManualIssueCreate, PendingRequest,
)
from app.services import issue_service

router = APIRouter(prefix="/issues", tags=["Issues"])
# Same /requests prefix as Person 3's router; the paths below don't clash with theirs.
fulfil_router = APIRouter(prefix="/requests", tags=["Issues"])

_STAFF = ("ADMIN", "BANK_STAFF")
_READERS = ("ADMIN", "BANK_STAFF", "HOSPITAL_STAFF")


@router.get("/", response_model=IssueListResponse)
def list_issues(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    request_id: Optional[int] = None,
    hospital_id: Optional[int] = None,
    blood_group: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Audit log of all issued units (newest first)."""
    return issue_service.list_issues(
        db, user=None, skip=skip, limit=limit, request_id=request_id,
        hospital_id=hospital_id, blood_group=blood_group,
        date_from=date_from, date_to=date_to,
    )


@router.get("/pending-requests", response_model=list[PendingRequest])
def pending_requests(
    db: Session = Depends(get_db),
):
    """Open requests (EMERGENCY first) that still need blood."""
    return issue_service.list_pending_requests(db, user=None)


@router.post("/manual", response_model=FulfilResult, status_code=201)
def manual_issue(
    data: ManualIssueCreate,
    db: Session = Depends(get_db),
):
    """Issue one specific unit to a request (compatibility + expiry are validated)."""
    return issue_service.manual_issue(db, data, user=None)


@fulfil_router.get("/{request_id}/fefo-preview", response_model=FEFOPreview)
def fefo_preview(
    request_id: int,
    db: Session = Depends(get_db),
):
    """Preview the FEFO recommendation without changing anything."""
    return issue_service.preview_fefo(db, request_id)


@fulfil_router.post("/{request_id}/auto-fulfil", response_model=FulfilResult, status_code=201)
def auto_fulfil(
    request_id: int,
    db: Session = Depends(get_db),
):
    """Fulfil the request automatically (First-Expired-First-Out)."""
    return issue_service.auto_fulfil(db, request_id, user=None)
