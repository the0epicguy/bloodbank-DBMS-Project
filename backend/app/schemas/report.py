from pydantic import BaseModel

class StockDistributionItem(BaseModel):
    blood_group: str
    component_type: str
    available_units: int

class ExpiringUnitItem(BaseModel):
    bank_id: int
    bank_name: str
    unit_id: int
    blood_group: str
    component_type: str
    expiry_date: str
    days_to_expiry: int

class UrgencyMetricItem(BaseModel):
    urgency: str
    total_requests: int
    fulfilled_requests: int
    fulfillment_pct: float

class FulfillmentMetricsResponse(BaseModel):
    total_requests: int
    fulfilled_requests: int
    fulfillment_pct: float
    by_urgency: list[UrgencyMetricItem]
