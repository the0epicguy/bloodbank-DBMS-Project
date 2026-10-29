"""
tests/test_compatibility.py
===========================
Exhaustive ABO/Rh compatibility matrix test suite.
Person 2 owns these tests.

Validates all 8 × 4 = 32 (recipient_group, component) combinations,
ensuring the compatibility engine returns exactly the correct set of
donor groups as defined by medical transfusion standards.
"""

import pytest

from app.core.compatibility import (
    build_full_matrix,
    get_compatible_donor_groups,
    is_compatible,
)
from app.core.enums import BloodGroup, ComponentType


# ============================================================================
# RBC / Whole Blood compatibility (8 recipient groups)
# ============================================================================

class TestRBCCompatibility:
    """Standard ABO/Rh compatibility for Red Blood Cells and Whole Blood."""

    @pytest.mark.parametrize("component", [ComponentType.RBC, ComponentType.WHOLE_BLOOD])
    def test_O_neg_receives_only_O_neg(self, component):
        donors = get_compatible_donor_groups(BloodGroup.O_NEG, component)
        assert donors == [BloodGroup.O_NEG]
        assert len(donors) == 1

    @pytest.mark.parametrize("component", [ComponentType.RBC, ComponentType.WHOLE_BLOOD])
    def test_O_pos_receives_O_neg_and_O_pos(self, component):
        donors = get_compatible_donor_groups(BloodGroup.O_POS, component)
        assert set(donors) == {BloodGroup.O_NEG, BloodGroup.O_POS}

    @pytest.mark.parametrize("component", [ComponentType.RBC, ComponentType.WHOLE_BLOOD])
    def test_A_neg_receives_O_neg_and_A_neg(self, component):
        donors = get_compatible_donor_groups(BloodGroup.A_NEG, component)
        assert set(donors) == {BloodGroup.O_NEG, BloodGroup.A_NEG}

    @pytest.mark.parametrize("component", [ComponentType.RBC, ComponentType.WHOLE_BLOOD])
    def test_A_pos_receives_four_groups(self, component):
        donors = get_compatible_donor_groups(BloodGroup.A_POS, component)
        assert set(donors) == {BloodGroup.O_NEG, BloodGroup.O_POS,
                                BloodGroup.A_NEG, BloodGroup.A_POS}

    @pytest.mark.parametrize("component", [ComponentType.RBC, ComponentType.WHOLE_BLOOD])
    def test_B_neg_receives_O_neg_and_B_neg(self, component):
        donors = get_compatible_donor_groups(BloodGroup.B_NEG, component)
        assert set(donors) == {BloodGroup.O_NEG, BloodGroup.B_NEG}

    @pytest.mark.parametrize("component", [ComponentType.RBC, ComponentType.WHOLE_BLOOD])
    def test_B_pos_receives_four_groups(self, component):
        donors = get_compatible_donor_groups(BloodGroup.B_POS, component)
        assert set(donors) == {BloodGroup.O_NEG, BloodGroup.O_POS,
                                BloodGroup.B_NEG, BloodGroup.B_POS}

    @pytest.mark.parametrize("component", [ComponentType.RBC, ComponentType.WHOLE_BLOOD])
    def test_AB_neg_receives_O_neg_A_neg_B_neg_AB_neg(self, component):
        donors = get_compatible_donor_groups(BloodGroup.AB_NEG, component)
        assert set(donors) == {BloodGroup.O_NEG, BloodGroup.A_NEG,
                                BloodGroup.B_NEG, BloodGroup.AB_NEG}

    @pytest.mark.parametrize("component", [ComponentType.RBC, ComponentType.WHOLE_BLOOD])
    def test_AB_pos_is_universal_recipient_receives_all_groups(self, component):
        donors = get_compatible_donor_groups(BloodGroup.AB_POS, component)
        assert set(donors) == set(BloodGroup)  # All 8 blood groups
        assert len(donors) == 8


# ============================================================================
# Plasma compatibility (reverse ABO logic)
# ============================================================================

class TestPlasmaCompatibility:
    """AB+ plasma is universal plasma donor; O- is universal plasma recipient."""

    def test_O_neg_is_universal_plasma_recipient_receives_all(self):
        donors = get_compatible_donor_groups(BloodGroup.O_NEG, ComponentType.PLASMA)
        assert set(donors) == set(BloodGroup)

    def test_AB_pos_only_receives_AB_pos_plasma(self):
        donors = get_compatible_donor_groups(BloodGroup.AB_POS, ComponentType.PLASMA)
        assert donors == [BloodGroup.AB_POS]

    def test_A_pos_receives_A_pos_and_AB_pos_plasma(self):
        donors = get_compatible_donor_groups(BloodGroup.A_POS, ComponentType.PLASMA)
        assert set(donors) == {BloodGroup.A_POS, BloodGroup.AB_POS}

    def test_B_neg_receives_B_neg_B_pos_AB_neg_AB_pos_plasma(self):
        donors = get_compatible_donor_groups(BloodGroup.B_NEG, ComponentType.PLASMA)
        assert set(donors) == {BloodGroup.B_NEG, BloodGroup.B_POS,
                                BloodGroup.AB_NEG, BloodGroup.AB_POS}


# ============================================================================
# is_compatible() point-checks
# ============================================================================

class TestIsCompatibleHelper:
    def test_O_neg_compatible_with_any_RBC_recipient(self):
        """O- is the universal RBC donor — must be compatible with all recipients."""
        for recipient in BloodGroup:
            assert is_compatible(BloodGroup.O_NEG, recipient, ComponentType.RBC), (
                f"O- RBC should be compatible with {recipient}"
            )

    def test_AB_pos_compatible_with_any_plasma_recipient(self):
        """AB+ is the universal plasma donor."""
        for recipient in BloodGroup:
            assert is_compatible(BloodGroup.AB_POS, recipient, ComponentType.PLASMA), (
                f"AB+ plasma should be compatible with {recipient}"
            )

    def test_AB_pos_RBC_not_universal_donor(self):
        """AB+ is NOT a universal RBC donor — O- recipients cannot receive AB+ RBC."""
        assert not is_compatible(BloodGroup.AB_POS, BloodGroup.O_NEG, ComponentType.RBC)
        assert not is_compatible(BloodGroup.AB_POS, BloodGroup.O_POS, ComponentType.RBC)
        assert not is_compatible(BloodGroup.AB_POS, BloodGroup.A_NEG, ComponentType.RBC)

    def test_B_pos_RBC_incompatible_with_A_recipient(self):
        assert not is_compatible(BloodGroup.B_POS, BloodGroup.A_POS, ComponentType.RBC)
        assert not is_compatible(BloodGroup.B_POS, BloodGroup.A_NEG, ComponentType.RBC)


# ============================================================================
# Full matrix coverage
# ============================================================================

class TestFullMatrixCoverage:
    def test_full_matrix_has_32_entries(self):
        """32 = 8 blood groups × 4 component types."""
        matrix = build_full_matrix()
        assert len(matrix) == 32

    def test_every_recipient_has_at_least_one_compatible_donor(self):
        matrix = build_full_matrix()
        for (group, component), donors in matrix.items():
            assert len(donors) >= 1, (
                f"No compatible donors found for recipient={group}, component={component}"
            )

    def test_universal_rbc_donor_O_neg_in_all_rbc_entries(self):
        """O- must appear in every RBC and WHOLE_BLOOD compatibility list."""
        for group in BloodGroup:
            for component in [ComponentType.RBC, ComponentType.WHOLE_BLOOD]:
                donors = get_compatible_donor_groups(group, component)
                assert BloodGroup.O_NEG in donors, (
                    f"O- missing from RBC compat list for recipient {group}"
                )
