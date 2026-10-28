import enum

class BloodGroup(str, enum.Enum):
    """ABO + Rh blood groups."""
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"

class ComponentType(str, enum.Enum):
    """Blood components."""
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
    """Request fulfillment status."""
    PENDING = "PENDING"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"

class UserRole(str, enum.Enum):
    """User account roles for RBAC."""
    ADMIN = "ADMIN"
    BANK_STAFF = "BANK_STAFF"
    HOSPITAL_STAFF = "HOSPITAL_STAFF"
    DONOR = "DONOR"
