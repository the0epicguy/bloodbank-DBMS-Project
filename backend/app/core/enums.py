"""
core/enums.py
=============
Canonical Python enumerations that mirror the MySQL ENUM columns exactly.
Import from here — never hard-code string literals anywhere else.
"""

from enum import Enum


class BloodGroup(str, Enum):
    A_POS  = "A+"
    A_NEG  = "A-"
    B_POS  = "B+"
    B_NEG  = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS  = "O+"
    O_NEG  = "O-"


class ComponentType(str, Enum):
    WHOLE_BLOOD = "WHOLE_BLOOD"
    RBC         = "RBC"
    PLATELETS   = "PLATELETS"
    PLASMA      = "PLASMA"


class UnitStatus(str, Enum):
    AVAILABLE  = "AVAILABLE"
    RESERVED   = "RESERVED"
    ISSUED     = "ISSUED"
    EXPIRED    = "EXPIRED"
    DISCARDED  = "DISCARDED"


class UrgencyLevel(str, Enum):
    ROUTINE   = "ROUTINE"
    URGENT    = "URGENT"
    EMERGENCY = "EMERGENCY"


class RequestStatus(str, Enum):
    PENDING               = "PENDING"
    PARTIALLY_FULFILLED   = "PARTIALLY_FULFILLED"
    FULFILLED             = "FULFILLED"
    CANCELLED             = "CANCELLED"


class UserRole(str, Enum):
    ADMIN           = "ADMIN"
    BANK_STAFF      = "BANK_STAFF"
    HOSPITAL_STAFF  = "HOSPITAL_STAFF"
    DONOR           = "DONOR"


class Gender(str, Enum):
    MALE   = "MALE"
    FEMALE = "FEMALE"
    OTHER  = "OTHER"


# ------------------------------------------------------------------
# Expiry shelf-life constants (in days, from collection_date)
# ------------------------------------------------------------------
SHELF_LIFE_DAYS: dict[ComponentType, int] = {
    ComponentType.WHOLE_BLOOD: 35,
    ComponentType.RBC:         42,
    ComponentType.PLATELETS:   5,
    ComponentType.PLASMA:      365,
}

# Minimum inter-donation interval (days)
MIN_DONATION_INTERVAL_DAYS = 90

# Donor age eligibility window
DONOR_MIN_AGE = 18
DONOR_MAX_AGE = 65
