
from pydantic import BaseModel, ConfigDict, Field


class HospitalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1)
    contact: str = Field(min_length=1, max_length=20)


class HospitalUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    address: str | None = Field(default=None, min_length=1)
    contact: str | None = Field(default=None, min_length=1, max_length=20)


class HospitalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hospital_id: int
    name: str
    address: str
    contact: str
