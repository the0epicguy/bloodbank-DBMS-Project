"""
Tests for Donor Service - eligibility edge cases, CRUD, and validation.

These tests don't need a real database. We test the business logic
functions directly by creating Donor objects in memory.

Run with:
    cd backend
    python -m pytest tests/ -v
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

# We need to mock the database before importing services
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestDonorEligibility:
    """
    Test the is_eligible() function from donor_service.

    Business Rules:
        1. Age must be 18-65 (calculated from dob)
        2. At least 90 days since last_donation_date
    """

    def _make_donor(self, dob, last_donation_date=None):
        """Helper: create a mock Donor object."""
        donor = MagicMock()
        donor.dob = dob
        donor.last_donation_date = last_donation_date
        donor.donor_id = 1
        donor.name = "Test Donor"
        return donor

    def test_eligible_donor_no_previous_donation(self):
        """A 25-year-old who has never donated should be eligible."""
        from app.services.donor_service import is_eligible

        dob = date.today() - timedelta(days=25 * 365)
        donor = self._make_donor(dob=dob, last_donation_date=None)

        eligible, reason = is_eligible(donor)
        assert eligible is True
        assert "eligible" in reason.lower()

    def test_eligible_donor_with_old_donation(self):
        """Donor who donated 100 days ago should be eligible (> 90 days)."""
        from app.services.donor_service import is_eligible

        dob = date.today() - timedelta(days=30 * 365)
        last_donation = date.today() - timedelta(days=100)
        donor = self._make_donor(dob=dob, last_donation_date=last_donation)

        eligible, reason = is_eligible(donor)
        assert eligible is True

    def test_ineligible_too_young(self):
        """A 16-year-old should NOT be eligible."""
        from app.services.donor_service import is_eligible

        dob = date.today() - timedelta(days=16 * 365)
        donor = self._make_donor(dob=dob)

        eligible, reason = is_eligible(donor)
        assert eligible is False
        assert "minimum age" in reason.lower() or "18" in reason

    def test_ineligible_too_old(self):
        """A 70-year-old should NOT be eligible."""
        from app.services.donor_service import is_eligible

        dob = date.today() - timedelta(days=70 * 365)
        donor = self._make_donor(dob=dob)

        eligible, reason = is_eligible(donor)
        assert eligible is False
        assert "maximum age" in reason.lower() or "65" in reason

    def test_ineligible_recent_donation(self):
        """Donor who donated 30 days ago should NOT be eligible (< 90 days)."""
        from app.services.donor_service import is_eligible

        dob = date.today() - timedelta(days=30 * 365)
        last_donation = date.today() - timedelta(days=30)
        donor = self._make_donor(dob=dob, last_donation_date=last_donation)

        eligible, reason = is_eligible(donor)
        assert eligible is False
        assert "60" in reason or "days" in reason.lower()

    def test_edge_case_exactly_18(self):
        """Donor who is exactly 18 today should be eligible."""
        from app.services.donor_service import is_eligible

        dob = date.today().replace(year=date.today().year - 18)
        donor = self._make_donor(dob=dob)

        eligible, reason = is_eligible(donor)
        assert eligible is True

    def test_edge_case_exactly_65(self):
        """Donor who is exactly 65 today should be eligible."""
        from app.services.donor_service import is_eligible

        dob = date.today().replace(year=date.today().year - 65)
        donor = self._make_donor(dob=dob)

        eligible, reason = is_eligible(donor)
        assert eligible is True

    def test_edge_case_exactly_90_days(self):
        """Donor who donated exactly 90 days ago should be eligible."""
        from app.services.donor_service import is_eligible

        dob = date.today() - timedelta(days=30 * 365)
        last_donation = date.today() - timedelta(days=90)
        donor = self._make_donor(dob=dob, last_donation_date=last_donation)

        eligible, reason = is_eligible(donor)
        assert eligible is True

    def test_edge_case_89_days(self):
        """Donor who donated 89 days ago should NOT be eligible."""
        from app.services.donor_service import is_eligible

        dob = date.today() - timedelta(days=30 * 365)
        last_donation = date.today() - timedelta(days=89)
        donor = self._make_donor(dob=dob, last_donation_date=last_donation)

        eligible, reason = is_eligible(donor)
        assert eligible is False


class TestDonationExpiry:
    """
    Test expiry date computation.

    Rules:
        - WHOLE_BLOOD: 35 days
        - RBC: 35 days
        - PLATELETS: 5 days
        - PLASMA: 365 days
    """

    def test_whole_blood_expiry(self):
        from app.services.donation_service import _compute_expiry

        today = date(2026, 10, 1)
        assert _compute_expiry("WHOLE_BLOOD", today) == date(2026, 11, 5)

    def test_rbc_expiry(self):
        from app.services.donation_service import _compute_expiry

        today = date(2026, 10, 1)
        assert _compute_expiry("RBC", today) == date(2026, 11, 5)

    def test_platelet_expiry(self):
        from app.services.donation_service import _compute_expiry

        today = date(2026, 10, 1)
        assert _compute_expiry("PLATELETS", today) == date(2026, 10, 6)

    def test_plasma_expiry(self):
        from app.services.donation_service import _compute_expiry

        today = date(2026, 10, 1)
        assert _compute_expiry("PLASMA", today) == date(2027, 10, 1)


class TestDonorSchema:
    """
    Test Pydantic schema validation.
    """

    def test_valid_donor_create(self):
        from app.schemas.donor import DonorCreate

        data = DonorCreate(
            name="Test Donor",
            blood_group="A+",
            phone="9876543210",
            dob="2000-01-15",
        )
        assert data.name == "Test Donor"
        assert data.phone == "9876543210"

    def test_invalid_phone(self):
        from app.schemas.donor import DonorCreate

        with pytest.raises(Exception):
            DonorCreate(
                name="Test",
                blood_group="A+",
                phone="abc",  # invalid - too short and non-numeric
                dob="2000-01-15",
            )

    def test_future_dob_rejected(self):
        from app.schemas.donor import DonorCreate

        with pytest.raises(Exception):
            DonorCreate(
                name="Test",
                blood_group="A+",
                phone="9876543210",
                dob="2030-01-15",  # future date
            )

    def test_donation_volume_bounds(self):
        from app.schemas.donor import DonationCreate

        # Valid
        d = DonationCreate(donor_id=1, bank_id=1, volume_ml=450)
        assert d.volume_ml == 450

        # Too low
        with pytest.raises(Exception):
            DonationCreate(donor_id=1, bank_id=1, volume_ml=10)

        # Too high
        with pytest.raises(Exception):
            DonationCreate(donor_id=1, bank_id=1, volume_ml=1000)
