from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.issue import Issue
from app.models.domain import Request, BloodUnit, Recipient, Hospital, BloodBank
from app.schemas.issue import ManualIssueRequest, IssueResponse, AllocationResponse
from app.services.issue_service import auto_fulfil, manual_issue, get_open_requests, get_candidate_units

router = APIRouter(tags=["Issues"])

@router.get("/requests/open", response_model=list[dict])
async def list_open_requests(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await get_open_requests(db)

@router.get("/requests/{request_id}/candidate-units", response_model=list[dict])
async def list_candidate_units(request_id: int, db: AsyncSession = Depends(get_db),
                               user: User = Depends(require_roles("ADMIN", "BANK_STAFF"))):
    return await get_candidate_units(db, request_id)

@router.post("/requests/{request_id}/auto-fulfil", response_model=AllocationResponse)
async def auto_fulfil_request(request_id: int, db: AsyncSession = Depends(get_db),
                              user: User = Depends(require_roles("ADMIN", "BANK_STAFF"))):
    return await auto_fulfil(db, request_id)

@router.post("/issues/manual", response_model=IssueResponse)
async def issue_manual(payload: ManualIssueRequest, db: AsyncSession = Depends(get_db),
                       user: User = Depends(require_roles("ADMIN", "BANK_STAFF"))):
    return await manual_issue(db, payload.request_id, payload.bank_id, payload.unit_id, payload.notes)

@router.get("/issues", response_model=list[dict])
async def issue_log(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    from app.repositories.issue_repo import IssueRepository
    return await IssueRepository.get_audit_log(db, skip, limit)
