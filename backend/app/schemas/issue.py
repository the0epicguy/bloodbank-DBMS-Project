"""
Pydantic schemas for Issues (Person 4).
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class ManualIssueCreate(BaseModel):
    """Body of POST /issues/manual - hand one specific bag to a request."""
    request_id: int
    bank_id: int
    unit_id: int


class IssueResponse(BaseModel):
    """One row of the audit log (full custody trail of an issued bag)."""
    issue_id: int
    issue_date: datetime
    request_id: int
    bank_id: int
    unit_id: int
    bank_name: str
    blood_group: str
    component_type: str
    expiry_date: date
    donor_name: str
    recipient_name: str
    recipient_blood_group: str
    hospital_id: int
    hospital_name: str
    urgency: str
    issued_by_name: Optional[str] = None


class IssueListResponse(BaseModel):
    total: int
    items: list[IssueResponse]


class FEFOUnit(BaseModel):
    """A unit recommended by the First-Expired-First-Out algorithm."""
    bank_id: int
    unit_id: int
    bank_name: str
    blood_group: str
    component_type: str
    expiry_date: date
    days_to_expiry: int
    exact_group_match: bool


class FEFOPreview(BaseModel):
    request_id: int
    recipient_blood_group: str
    component_type: str
    quantity: int
    already_issued: int
    remaining: int
    compatible_groups: list[str]
    recommended: list[FEFOUnit]
    shortfall: int = Field(..., description="Units we cannot cover from current stock")


class IssuedUnit(BaseModel):
    issue_id: int
    bank_id: int
    unit_id: int
    blood_group: str
    expiry_date: date


class FulfilResult(BaseModel):
    """Result of auto-fulfil or manual issue."""
    request_id: int
    request_status: str
    quantity_requested: int
    total_issued: int
    newly_issued: int
    remaining: int
    issued_units: list[IssuedUnit]
    message: str


class PendingRequest(BaseModel):
    """An open request that can still receive blood (for the fulfil modal)."""
    request_id: int
    hospital_id: int
    hospital_name: str
    recipient_name: str
    blood_group: str
    component_type: str
    quantity: int
    issued_units: int
    remaining: int
    urgency: str
    status: str
    request_date: date
