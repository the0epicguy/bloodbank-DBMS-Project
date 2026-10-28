from datetime import datetime
from pydantic import BaseModel, Field

class ManualIssueRequest(BaseModel):
    request_id: int = Field(gt=0)
    bank_id: int = Field(gt=0)
    unit_id: int = Field(gt=0)
    notes: str | None = None

class IssueResponse(BaseModel):
    issue_id: int
    request_id: int
    bank_id: int
    unit_id: int
    issue_date: datetime
    quantity_issued: int
    notes: str | None = None

class AllocationResponse(BaseModel):
    request_id: int
    requested_units: int
    issued_now: int
    remaining_units: int
    status: str
    allocated: list[dict]
