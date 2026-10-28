"""
tests/test_unit_sequential_id.py
=================================
Tests for the per-bank composite unit_id generation logic.
Person 2 owns these tests.

These tests verify:
  - unit_id starts at 1 for a fresh bank.
  - unit_id increments sequentially within the same bank.
  - unit_id is bank-scoped (different banks have independent counters).
  - Expiry computation is correct for all component types.
  - Discard business rule guards are enforced.
"""

import pytest
from datetime import date, timedelta

from app.core.enums import BloodGroup, ComponentType, UnitStatus, SHELF_LIFE_DAYS
from app.services.unit_service import _compute_expiry_date


# ============================================================================
# Expiry date computation (pure logic — no DB needed)
# ============================================================================

class TestExpiryComputation:
    """Verify shelf-life standards are applied correctly."""

    BASE_DATE = date(2025, 1, 1)

    @pytest.mark.parametrize("component, expected_days", [
        (ComponentType.WHOLE_BLOOD, 35),
        (ComponentType.RBC,         42),
        (ComponentType.PLATELETS,   5),
        (ComponentType.PLASMA,      365),
    ])
    def test_expiry_date_computed_correctly(self, component, expected_days):
        expiry = _compute_expiry_date(component, self.BASE_DATE)
        assert expiry == self.BASE_DATE + timedelta(days=expected_days), (
            f"{component}: expected +{expected_days} days, "
            f"got {(expiry - self.BASE_DATE).days}"
        )

    def test_plasma_longest_shelf_life(self):
        """Plasma must outlast all other components."""
        base = date(2025, 6, 1)
        expiries = {c: _compute_expiry_date(c, base) for c in ComponentType}
        assert expiries[ComponentType.PLASMA] == max(expiries.values())

    def test_platelets_shortest_shelf_life(self):
        """Platelets must expire soonest."""
        base = date(2025, 6, 1)
        expiries = {c: _compute_expiry_date(c, base) for c in ComponentType}
        assert expiries[ComponentType.PLATELETS] == min(expiries.values())

    def test_shelf_life_matches_constants(self):
        """_compute_expiry_date must agree with SHELF_LIFE_DAYS constant."""
        base = date(2025, 3, 15)
        for component in ComponentType:
            expiry = _compute_expiry_date(component, base)
            expected = base + timedelta(days=SHELF_LIFE_DAYS[component])
            assert expiry == expected


# ============================================================================
# Unit ID generation logic (integration — requires a real or mock DB session)
# These are stubs that will be filled out by Person 2 once the test DB is set up.
# ============================================================================

class TestUnitIdGeneration:
    """
    These tests are intentionally skipped until the test database fixture is
    configured by Person 4 (conftest.py with a test MySQL DB or SQLite fallback).
    Remove the skip marks once conftest.py is in place.
    """

    @pytest.mark.skip(reason="Requires DB fixture from Person 4's conftest.py")
    async def test_first_unit_in_bank_has_id_1(self, db_session, sample_bank, sample_donor):
        from app.services.unit_service import create_unit
        unit = await create_unit(
            db=db_session,
            bank_id=sample_bank.bank_id,
            donor_id=sample_donor.donor_id,
            volume_ml=450,
            blood_group=BloodGroup.O_POS,
            component_type=ComponentType.WHOLE_BLOOD,
            donation_date=date.today(),
        )
        assert unit.unit_id == 1

    @pytest.mark.skip(reason="Requires DB fixture from Person 4's conftest.py")
    async def test_second_unit_in_same_bank_has_id_2(self, db_session, sample_bank, sample_donor):
        from app.services.unit_service import create_unit
        u1 = await create_unit(
            db=db_session,
            bank_id=sample_bank.bank_id,
            donor_id=sample_donor.donor_id,
            volume_ml=300,
            blood_group=BloodGroup.A_NEG,
            component_type=ComponentType.RBC,
            donation_date=date.today(),
        )
        u2 = await create_unit(
            db=db_session,
            bank_id=sample_bank.bank_id,
            donor_id=sample_donor.donor_id,
            volume_ml=300,
            blood_group=BloodGroup.A_NEG,
            component_type=ComponentType.RBC,
            donation_date=date.today(),
        )
        assert u1.unit_id == 1
        assert u2.unit_id == 2

    @pytest.mark.skip(reason="Requires DB fixture from Person 4's conftest.py")
    async def test_unit_id_is_bank_scoped(self, db_session, sample_bank, second_bank, sample_donor):
        """Units in different banks should both start their counters at 1."""
        from app.services.unit_service import create_unit
        u_bank1 = await create_unit(db=db_session, bank_id=sample_bank.bank_id,
                                    donor_id=sample_donor.donor_id, volume_ml=400,
                                    blood_group=BloodGroup.B_POS,
                                    component_type=ComponentType.PLATELETS,
                                    donation_date=date.today())
        u_bank2 = await create_unit(db=db_session, bank_id=second_bank.bank_id,
                                    donor_id=sample_donor.donor_id, volume_ml=400,
                                    blood_group=BloodGroup.B_POS,
                                    component_type=ComponentType.PLATELETS,
                                    donation_date=date.today())
        # Both should have unit_id = 1 in their respective bank contexts
        assert u_bank1.unit_id == 1
        assert u_bank2.unit_id == 1
