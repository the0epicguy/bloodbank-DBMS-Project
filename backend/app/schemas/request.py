
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ComponentType, Urgency, RequestStatus


class RequestCreate(BaseModel):
    hospital_id: int = Field(gt=0)
    recipient_id: int = Field(gt=0)
    component_type: ComponentType
    quantity: int = Field(gt=0)
    urgency: Urgency = Urgency.ROUTINE


class RequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: int
    hospital_id: int
    recipient_id: int
    component_type: ComponentType
    quantity: int
    urgency: Urgency
    request_date: date
    status: RequestStatus
