"""
Enum definitions shared across the application.

These Python enums mirror the MySQL ENUM columns in the schema.
They are used in SQLAlchemy models and Pydantic schemas for type safety.
"""

import enum


class BloodGroup(str, enum.Enum):
    """ABO + Rh blood group types."""
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"


class ComponentType(str, enum.Enum):
    """Blood component types."""
    WHOLE_BLOOD = "WHOLE_BLOOD"
    RBC = "RBC"
    PLATELETS = "PLATELETS"
    PLASMA = "PLASMA"


class UnitStatus(str, enum.Enum):
    """Lifecycle status of a blood unit."""
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    ISSUED = "ISSUED"
    EXPIRED = "EXPIRED"
    DISCARDED = "DISCARDED"


class Urgency(str, enum.Enum):
    """Request urgency levels."""
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class RequestStatus(str, enum.Enum):
    """Request fulfilment status."""
    PENDING = "PENDING"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
