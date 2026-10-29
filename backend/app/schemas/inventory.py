"""
schemas/inventory.py
====================
Pydantic v2 request / response schemas for blood banks and blood units.
Person 2 owns these schemas.

Naming convention:
  *Create  — incoming body for POST
  *Update  — incoming body for PUT/PATCH
  *Response — outgoing JSON (used in route return types)
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.core.enums import BloodGroup, ComponentType, UnitStatus


# ============================================================
# Blood Bank schemas
# ============================================================

class BloodBankCreate(BaseModel):
    name:    str  = Field(..., min_length=2, max_length=120,
                          examples=["City Central Blood Bank"])
    address: str  = Field(..., min_length=5, examples=["12, Main Road, Block A"])
    city:    str  = Field(..., min_length=2, max_length=60, examples=["Mumbai"])
    contact: str  = Field(..., min_length=7, max_length=20,  examples=["+919876543210"])
    email:   EmailStr | None = Field(None, examples=["city.bank@example.com"])


class BloodBankUpdate(BaseModel):
    name:    str | None = Field(None, max_length=120)
    address: str | None = None
    city:    str | None = Field(None, max_length=60)
    contact: str | None = Field(None, max_length=20)
    email:   EmailStr | None = None


class BloodBankResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bank_id:     int
    name:        str
    address:     str
    city:        str
    contact:     str
    email:       str | None
    created_at:  datetime

    # Aggregated inventory counters injected by the repo/service layer
    available_units: int = Field(default=0,
                                 description="Total AVAILABLE units across all blood groups")
    expiring_soon:   int = Field(default=0,
                                 description="Units expiring within the warning window")


# ============================================================
# Blood Unit schemas
# ============================================================

class BloodUnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bank_id:         int
    unit_id:         int
    donor_id:        int
    volume_ml:       int
    blood_group:     BloodGroup
    component_type:  ComponentType
    donation_date:   date
    collection_date: date
    expiry_date:     date
    status:          UnitStatus
    discard_reason:  str | None
    created_at:      datetime

    # Computed field injected by the service layer
    days_to_expiry:  int = Field(
        default=0,
        description="Days remaining until expiry (negative = already expired)",
    )


class DiscardUnitRequest(BaseModel):
    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
        examples=["Contamination detected during quality check"],
    )


# ============================================================
# Inventory summary schemas
# ============================================================

class StockCell(BaseModel):
    """Single cell in the Blood Group × Component stock matrix."""
    model_config = ConfigDict(from_attributes=True)

    blood_group:     BloodGroup
    component_type:  ComponentType
    available_units: int
    earliest_expiry: date | None


class BankInventorySummary(BaseModel):
    bank_id:   int
    bank_name: str
    matrix:    list[StockCell]


class GlobalInventorySummary(BaseModel):
    banks: list[BankInventorySummary]
    total_available: int
    low_stock_alerts: list[StockCell] = Field(
        default_factory=list,
        description="Groups with units below the low-stock threshold",
    )


# ============================================================
# Expiry sweep schema
# ============================================================

class ExpirySweepResult(BaseModel):
    swept_count: int = Field(
        description="Number of units transitioned to EXPIRED status"
    )
    expired_unit_ids: list[dict] = Field(
        default_factory=list,
        description="List of {bank_id, unit_id} dicts for swept units",
    )
