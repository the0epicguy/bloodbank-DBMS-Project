"""
Enum definitions shared across the entire Blood Bank Management System.
Mirrors the MySQL 8.0 schema ENUM columns and supports both string and Enum access.
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


# Alias for compatibility with Person 2 & 4 schemas
UrgencyLevel = Urgency


class RequestStatus(str, enum.Enum):
    """Request fulfilment status."""
    PENDING = "PENDING"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class UserRole(str, enum.Enum):
    """RBAC user roles."""
    ADMIN = "ADMIN"
    BANK_STAFF = "BANK_STAFF"
    HOSPITAL_STAFF = "HOSPITAL_STAFF"
    DONOR = "DONOR"


# Medical shelf-life standards (in days from collection date)
SHELF_LIFE_DAYS = {
    ComponentType.WHOLE_BLOOD: 35,
    ComponentType.RBC: 35,
    ComponentType.PLATELETS: 5,
    ComponentType.PLASMA: 365,
    "WHOLE_BLOOD": 35,
    "RBC": 35,
    "PLATELETS": 5,
    "PLASMA": 365,
}
