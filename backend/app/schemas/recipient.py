
from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import BloodGroup


class RecipientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=120)
    blood_group: BloodGroup


class RecipientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=120)
    blood_group: BloodGroup | None = None


class RecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recipient_id: int
    name: str
    age: int | None
    blood_group: BloodGroup

