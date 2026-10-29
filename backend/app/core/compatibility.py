"""
ABO/Rh transfusion compatibility rules.

NOTE (integration): this file is owned by Person 2 in the plan. It is included
here because Person 4's FEFO allocation needs it. If Person 2 already has a
version, keep THEIR file and just make sure it exposes
`get_compatible_donor_groups(recipient_group, component)`.

Maps: recipient blood group -> list of donor blood groups that may be given.
"""

RBC_COMPATIBILITY = {
    "O-":  ["O-"],
    "O+":  ["O-", "O+"],
    "A-":  ["O-", "A-"],
    "A+":  ["O-", "O+", "A-", "A+"],
    "B-":  ["O-", "B-"],
    "B+":  ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],  # universal recipient
}

# Plasma follows the reverse ABO logic.
PLASMA_COMPATIBILITY = {
    "O-":  ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
    "O+":  ["O+", "A+", "B+", "AB+"],
    "A-":  ["A-", "A+", "AB-", "AB+"],
    "A+":  ["A+", "AB+"],
    "B-":  ["B-", "B+", "AB-", "AB+"],
    "B+":  ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"],  # universal plasma donor
}

# Platelets / whole blood use the red-cell table (as defined in the project plan).
PLATELETS_COMPATIBILITY = RBC_COMPATIBILITY
WHOLE_BLOOD_COMPATIBILITY = RBC_COMPATIBILITY

_TABLES = {
    "RBC": RBC_COMPATIBILITY,
    "WHOLE_BLOOD": WHOLE_BLOOD_COMPATIBILITY,
    "PLATELETS": PLATELETS_COMPATIBILITY,
    "PLASMA": PLASMA_COMPATIBILITY,
}


def _val(x) -> str:
    """Accept plain strings or str-Enums (BloodGroup / ComponentType)."""
    return x.value if hasattr(x, "value") else str(x)


def get_compatible_donor_groups(recipient_group, component) -> list[str]:
    """
    Which donor blood groups can safely be given to this recipient
    for this component?   e.g. ("A+", "RBC") -> ["O-", "O+", "A-", "A+"]
    """
    table = _TABLES[_val(component)]
    return list(table[_val(recipient_group)])


def is_compatible(recipient_group, unit_group, component) -> bool:
    """True if a unit of `unit_group` can be given to `recipient_group`."""
    return _val(unit_group) in get_compatible_donor_groups(recipient_group, component)
