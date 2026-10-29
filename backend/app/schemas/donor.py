"""
Pydantic schemas for Donor validation.

These schemas are used for:
    - Request body validation (what comes IN from the client)
    - Response serialization (what goes OUT to the client)

Naming convention:
    DonorCreate   → POST request body (creating a new donor)
    DonorUpdate   → PUT request body (updating an existing donor)
    DonorResponse → GET response body (returning donor data)
    DonorEligibility → GET response for eligibility check
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from app.core.enums import BloodGroup


class DonorCreate(BaseModel):
    """Schema for creating a new donor."""
    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    blood_group: BloodGroup = Field(..., description="ABO+Rh blood group")
    phone: str = Field(
        ..., min_length=10, max_length=15,
        description="Unique phone number (10-15 digits)",
    )
    dob: date = Field(..., description="Date of birth (YYYY-MM-DD)")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Phone must contain only digits."""
        cleaned = v.replace("+", "").replace("-", "").replace(" ", "")
        if not cleaned.isdigit():
            raise ValueError("Phone must contain only digits (and optional +/-)")
        return v

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        """Date of birth must be in the past."""
        if v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


class DonorUpdate(BaseModel):
    """Schema for updating a donor. All fields are optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    blood_group: Optional[BloodGroup] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=15)
    dob: Optional[date] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.replace("+", "").replace("-", "").replace(" ", "")
            if not cleaned.isdigit():
                raise ValueError("Phone must contain only digits (and optional +/-)")
        return v


class DonorResponse(BaseModel):
    """Schema for returning donor data in API responses."""
    donor_id: int
    name: str
    blood_group: str
    phone: str
    dob: date
    last_donation_date: Optional[date] = None

    class Config:
        from_attributes = True  # allows creating from ORM model


class DonorEligibility(BaseModel):
    """Schema for the eligibility check response."""
    donor_id: int
    name: str
    is_eligible: bool
    reason: str


class DonationCreate(BaseModel):
    """
    Schema for recording a new donation.

    The donor donates blood at a specific bank.
    This triggers:
        1. Eligibility check
        2. Blood unit creation (calls P2's unit_service)
        3. Update of donor's last_donation_date
    """
    donor_id: int = Field(..., description="ID of the donor")
    bank_id: int = Field(..., description="ID of the blood bank")
    volume_ml: int = Field(
        ..., ge=50, le=600,
        description="Volume donated in millilitres (50-600)",
    )
    component_type: str = Field(
        default="WHOLE_BLOOD",
        description="Component type: WHOLE_BLOOD, RBC, PLATELETS, PLASMA",
    )


class DonationResponse(BaseModel):
    """Response after recording a donation."""
    message: str
    donor_id: int
    bank_id: int
    unit_id: int
    volume_ml: int
    donation_date: date
    blood_group: str
    component_type: str
    expiry_date: date
