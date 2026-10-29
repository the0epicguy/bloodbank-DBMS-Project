"""
core/compatibility.py
=====================
ABO / Rh Transfusion Compatibility Engine.

Medical rules:
  - RBC / Whole Blood: donor antigens must be absent from recipient's plasma.
    Universal donor = O-  | Universal recipient = AB+
  - Plasma:           reverse ABO logic ΓÇö donor antibodies must not attack recipient.
    Universal donor = AB+ | Universal recipient = O-
  - Platelets:        preferably same group; falls back to RBC compatibility.

Usage:
    from app.core.compatibility import get_compatible_donor_groups
    groups = get_compatible_donor_groups(BloodGroup.A_POS, ComponentType.RBC)
    # ΓåÆ ["O-", "O+", "A-", "A+"]
"""

from app.core.enums import BloodGroup, ComponentType


# ---------------------------------------------------------------------------
# Raw compatibility tables (recipient ΓåÆ list of compatible donor groups)
# ---------------------------------------------------------------------------

# RBC and Whole Blood: standard donor-to-recipient compatibility
_RBC_COMPAT: dict[BloodGroup, list[BloodGroup]] = {
    BloodGroup.O_NEG:  [BloodGroup.O_NEG],
    BloodGroup.O_POS:  [BloodGroup.O_NEG, BloodGroup.O_POS],
    BloodGroup.A_NEG:  [BloodGroup.O_NEG, BloodGroup.A_NEG],
    BloodGroup.A_POS:  [BloodGroup.O_NEG, BloodGroup.O_POS,
                        BloodGroup.A_NEG, BloodGroup.A_POS],
    BloodGroup.B_NEG:  [BloodGroup.O_NEG, BloodGroup.B_NEG],
    BloodGroup.B_POS:  [BloodGroup.O_NEG, BloodGroup.O_POS,
                        BloodGroup.B_NEG, BloodGroup.B_POS],
    BloodGroup.AB_NEG: [BloodGroup.O_NEG, BloodGroup.A_NEG,
                        BloodGroup.B_NEG, BloodGroup.AB_NEG],
    BloodGroup.AB_POS: [BloodGroup.O_NEG, BloodGroup.O_POS,
                        BloodGroup.A_NEG, BloodGroup.A_POS,
                        BloodGroup.B_NEG, BloodGroup.B_POS,
                        BloodGroup.AB_NEG, BloodGroup.AB_POS],  # Universal recipient
}

# Plasma: reverse ABO ΓÇö recipient needs plasma without anti-A or anti-B antibodies
# AB+ plasma (no antibodies) ΓåÆ universal donor.  O- plasma ΓåÆ only for O-.
_PLASMA_COMPAT: dict[BloodGroup, list[BloodGroup]] = {
    BloodGroup.O_NEG:  [BloodGroup.O_NEG, BloodGroup.O_POS,
                        BloodGroup.A_NEG, BloodGroup.A_POS,
                        BloodGroup.B_NEG, BloodGroup.B_POS,
                        BloodGroup.AB_NEG, BloodGroup.AB_POS],  # Universal plasma recipient
    BloodGroup.O_POS:  [BloodGroup.O_POS, BloodGroup.A_POS,
                        BloodGroup.B_POS, BloodGroup.AB_POS],
    BloodGroup.A_NEG:  [BloodGroup.A_NEG, BloodGroup.A_POS,
                        BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.A_POS:  [BloodGroup.A_POS, BloodGroup.AB_POS],
    BloodGroup.B_NEG:  [BloodGroup.B_NEG, BloodGroup.B_POS,
                        BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.B_POS:  [BloodGroup.B_POS, BloodGroup.AB_POS],
    BloodGroup.AB_NEG: [BloodGroup.AB_NEG, BloodGroup.AB_POS],
    BloodGroup.AB_POS: [BloodGroup.AB_POS],  # Universal plasma donor
}

# Platelets: ideally same-group; fall back to RBC compatibility
_PLATELETS_COMPAT: dict[BloodGroup, list[BloodGroup]] = _RBC_COMPAT


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_compatible_donor_groups(
    recipient_group: BloodGroup,
    component: ComponentType,
) -> list[BloodGroup]:
    """
    Return a list of donor blood groups whose units can safely be transfused
    to a recipient of *recipient_group* for the given *component*.

    Used by:
      - Person 4 (issue_service) for FEFO query filtering.
      - Person 3 (request_service) for validation.
    """
    if component == ComponentType.PLASMA:
        return _PLASMA_COMPAT[recipient_group]
    if component == ComponentType.PLATELETS:
        return _PLATELETS_COMPAT[recipient_group]
    # WHOLE_BLOOD and RBC use the same table
    return _RBC_COMPAT[recipient_group]


def is_compatible(
    donor_group: BloodGroup,
    recipient_group: BloodGroup,
    component: ComponentType,
) -> bool:
    """
    Return True if a unit with *donor_group* can be given to *recipient_group*
    for the specified *component*.
    """
    return donor_group in get_compatible_donor_groups(recipient_group, component)


# ---------------------------------------------------------------------------
# Full 64-pair matrix (for tests & documentation)
# ---------------------------------------------------------------------------

def build_full_matrix() -> dict[tuple[BloodGroup, ComponentType], list[BloodGroup]]:
    """
    Build and return the full (recipient_group, component) ΓåÆ [donor_groups] matrix.
    Useful for test coverage verification.
    """
    matrix: dict[tuple[BloodGroup, ComponentType], list[BloodGroup]] = {}
    for group in BloodGroup:
        for component in ComponentType:
            matrix[(group, component)] = get_compatible_donor_groups(group, component)
    return matrix
