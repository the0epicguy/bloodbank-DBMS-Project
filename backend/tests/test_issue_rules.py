"""
Tests for FEFO allocation, compatibility, manual issue and DB integrity
(Person 4). Needs MySQL - skipped automatically if it isn't reachable.

Run:  cd backend && python -m pytest tests/test_issue_rules.py -v
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.errors import ConflictError, NotFound, ValidationFailed
from app.schemas.issue import ManualIssueCreate
from app.services import issue_service
from tests.conftest import load_user


def _admin(db, w):
    return load_user(db, w.admin_id)


def _issued_keys(db):
    return [(r[0], r[1]) for r in db.execute(text("SELECT bank_id, unit_id FROM issue ORDER BY issue_id"))]


class TestFEFOOrdering:
    def test_earliest_expiry_is_issued_first(self, db, make, world):
        """3 compatible units expiring in +2 / +10 / +20 days -> the +2 unit goes first."""
        u20 = make.unit(world.bank, world.donor, "O-", "RBC", 20)
        u2 = make.unit(world.bank, world.donor, "O-", "RBC", 2)
        u10 = make.unit(world.bank, world.donor, "O-", "RBC", 10)
        rec = make.recipient("O-")
        req = make.request(world.hospital, rec, "RBC", 1)

        result = issue_service.auto_fulfil(db, req, _admin(db, world))

        assert [u.unit_id for u in result.issued_units] == [u2]
        assert result.request_status == "FULFILLED"

    def test_multi_unit_request_takes_soonest_expiring_in_order(self, db, make, world):
        u30 = make.unit(world.bank, world.donor, "O-", "RBC", 30)
        u5 = make.unit(world.bank, world.donor, "O-", "RBC", 5)
        u15 = make.unit(world.bank, world.donor, "O-", "RBC", 15)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 2)

        result = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert [u.unit_id for u in result.issued_units] == [u5, u15]
        assert u30 not in [u.unit_id for u in result.issued_units]

    def test_preview_matches_actual_allocation_and_changes_nothing(self, db, make, world):
        make.unit(world.bank, world.donor, "O-", "RBC", 9)
        make.unit(world.bank, world.donor, "O-", "RBC", 3)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)

        preview = issue_service.preview_fefo(db, req)
        assert db.execute(text("SELECT COUNT(*) FROM issue")).scalar() == 0
        result = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert [(u.bank_id, u.unit_id) for u in result.issued_units] == \
               [(u.bank_id, u.unit_id) for u in preview.recommended]


class TestExpiryAndStatus:
    def test_expired_units_are_never_allocated(self, db, make, world):
        make.unit(world.bank, world.donor, "O-", "RBC", -3)            # AVAILABLE but past expiry
        make.unit(world.bank, world.donor, "O-", "RBC", 10, status="EXPIRED")
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(ConflictError):
            issue_service.auto_fulfil(db, req, _admin(db, world))
        assert db.execute(text("SELECT COUNT(*) FROM issue")).scalar() == 0

    def test_discarded_and_issued_units_are_skipped(self, db, make, world):
        make.unit(world.bank, world.donor, "O-", "RBC", 3, status="DISCARDED")
        make.unit(world.bank, world.donor, "O-", "RBC", 4, status="ISSUED")
        good = make.unit(world.bank, world.donor, "O-", "RBC", 20)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        result = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert result.issued_units[0].unit_id == good

    def test_partial_fulfilment_then_completion(self, db, make, world):
        make.unit(world.bank, world.donor, "O-", "RBC", 10)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 3)

        r1 = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert (r1.request_status, r1.newly_issued, r1.remaining) == ("PARTIALLY_FULFILLED", 1, 2)

        make.unit(world.bank, world.donor, "O-", "RBC", 11)
        make.unit(world.bank, world.donor, "O-", "RBC", 12)
        r2 = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert (r2.request_status, r2.total_issued, r2.remaining) == ("FULFILLED", 3, 0)
        assert db.execute(text("SELECT status FROM request WHERE request_id=:r"), {"r": req}).scalar() == "FULFILLED"

    def test_issued_unit_is_marked_issued(self, db, make, world):
        u = make.unit(world.bank, world.donor, "O-", "RBC", 7)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        issue_service.auto_fulfil(db, req, _admin(db, world))
        st = db.execute(text("SELECT status FROM blood_unit WHERE bank_id=:b AND unit_id=:u"),
                        {"b": world.bank, "u": u}).scalar()
        assert st == "ISSUED"

    def test_cancelled_and_fulfilled_requests_cannot_be_fulfilled(self, db, make, world):
        make.unit(world.bank, world.donor, "O-", "RBC", 7)
        cancelled = make.request(world.hospital, make.recipient("O-"), "RBC", 1, status="CANCELLED")
        with pytest.raises(ConflictError):
            issue_service.auto_fulfil(db, cancelled, _admin(db, world))
        with pytest.raises(NotFound):
            issue_service.auto_fulfil(db, 99999, _admin(db, world))


class TestCompatibility:
    def test_o_negative_recipient_gets_only_o_negative(self, db, make, world):
        make.unit(world.bank, world.donor, "A+", "RBC", 1)
        make.unit(world.bank, world.donor, "O+", "RBC", 2)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(ConflictError):          # only incompatible stock exists
            issue_service.auto_fulfil(db, req, _admin(db, world))

        u = make.unit(world.bank, world.donor, "O-", "RBC", 30)
        result = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert result.issued_units[0].unit_id == u
        assert result.issued_units[0].blood_group == "O-"

    def test_ab_positive_recipient_can_take_any_group(self, db, make, world):
        make.unit(world.bank, world.donor, "B-", "RBC", 3)
        make.unit(world.bank, world.donor, "A+", "RBC", 6)
        req = make.request(world.hospital, make.recipient("AB+"), "RBC", 2)
        result = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert sorted(u.blood_group for u in result.issued_units) == ["A+", "B-"]

    def test_plasma_uses_reverse_rules(self, db, make, world):
        make.unit(world.bank, world.donor, "AB+", "PLASMA", 100)   # universal plasma donor
        req = make.request(world.hospital, make.recipient("O-"), "PLASMA", 1)
        result = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert result.issued_units[0].blood_group == "AB+"

    def test_component_must_match(self, db, make, world):
        make.unit(world.bank, world.donor, "O-", "PLASMA", 100)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(ConflictError):
            issue_service.auto_fulfil(db, req, _admin(db, world))

    def test_tie_on_expiry_prefers_exact_group(self, db, make, world):
        make.unit(world.bank, world.donor, "O-", "RBC", 10)
        exact = make.unit(world.bank, world.donor, "A+", "RBC", 10)
        req = make.request(world.hospital, make.recipient("A+"), "RBC", 1)
        result = issue_service.auto_fulfil(db, req, _admin(db, world))
        assert result.issued_units[0].unit_id == exact


class TestManualIssue:
    def test_valid_manual_issue(self, db, make, world):
        u = make.unit(world.bank, world.donor, "O-", "RBC", 10)
        req = make.request(world.hospital, make.recipient("A+"), "RBC", 1)
        res = issue_service.manual_issue(
            db, ManualIssueCreate(request_id=req, bank_id=world.bank, unit_id=u), _admin(db, world))
        assert res.request_status == "FULFILLED"

    def test_incompatible_unit_rejected(self, db, make, world):
        u = make.unit(world.bank, world.donor, "A+", "RBC", 10)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(ValidationFailed):
            issue_service.manual_issue(
                db, ManualIssueCreate(request_id=req, bank_id=world.bank, unit_id=u), _admin(db, world))

    def test_expired_unit_rejected(self, db, make, world):
        u = make.unit(world.bank, world.donor, "O-", "RBC", -1)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(ValidationFailed):
            issue_service.manual_issue(
                db, ManualIssueCreate(request_id=req, bank_id=world.bank, unit_id=u), _admin(db, world))

    def test_wrong_component_rejected(self, db, make, world):
        u = make.unit(world.bank, world.donor, "O-", "PLASMA", 10)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(ValidationFailed):
            issue_service.manual_issue(
                db, ManualIssueCreate(request_id=req, bank_id=world.bank, unit_id=u), _admin(db, world))

    def test_same_bag_cannot_be_issued_twice(self, db, make, world):
        u = make.unit(world.bank, world.donor, "O-", "RBC", 10)
        r1 = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        r2 = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        issue_service.manual_issue(
            db, ManualIssueCreate(request_id=r1, bank_id=world.bank, unit_id=u), _admin(db, world))
        with pytest.raises(ConflictError):
            issue_service.manual_issue(
                db, ManualIssueCreate(request_id=r2, bank_id=world.bank, unit_id=u), _admin(db, world))

    def test_unknown_unit_404(self, db, make, world):
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(NotFound):
            issue_service.manual_issue(
                db, ManualIssueCreate(request_id=req, bank_id=world.bank, unit_id=999), _admin(db, world))

    def test_cannot_issue_more_than_requested(self, db, make, world):
        u1 = make.unit(world.bank, world.donor, "O-", "RBC", 10)
        u2 = make.unit(world.bank, world.donor, "O-", "RBC", 11)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        issue_service.manual_issue(
            db, ManualIssueCreate(request_id=req, bank_id=world.bank, unit_id=u1), _admin(db, world))
        with pytest.raises(ConflictError):
            issue_service.manual_issue(
                db, ManualIssueCreate(request_id=req, bank_id=world.bank, unit_id=u2), _admin(db, world))


class TestDatabaseSafetyNet:
    """Even raw SQL (bypassing Python) cannot break the issue rules."""

    def test_trigger_blocks_issue_of_non_available_unit(self, db, make, world):
        u = make.unit(world.bank, world.donor, "O-", "RBC", 10, status="DISCARDED")
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(DBAPIError):
            db.execute(text("INSERT INTO issue (request_id,bank_id,unit_id) VALUES (:r,:b,:u)"),
                       {"r": req, "b": world.bank, "u": u})
            db.commit()
        db.rollback()

    def test_trigger_blocks_issue_of_expired_unit(self, db, make, world):
        u = make.unit(world.bank, world.donor, "O-", "RBC", -2)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)
        with pytest.raises(DBAPIError):
            db.execute(text("INSERT INTO issue (request_id,bank_id,unit_id) VALUES (:r,:b,:u)"),
                       {"r": req, "b": world.bank, "u": u})
            db.commit()
        db.rollback()

    def test_unique_constraint_blocks_double_issue(self, db, make, world):
        u = make.unit(world.bank, world.donor, "O-", "RBC", 10)
        req = make.request(world.hospital, make.recipient("O-"), "RBC", 2)
        db.execute(text("INSERT INTO issue (request_id,bank_id,unit_id) VALUES (:r,:b,:u)"),
                   {"r": req, "b": world.bank, "u": u})
        db.commit()
        # unit status is still AVAILABLE here (raw insert), so only UNIQUE can stop it
        with pytest.raises(DBAPIError):
            db.execute(text("INSERT INTO issue (request_id,bank_id,unit_id) VALUES (:r,:b,:u)"),
                       {"r": req, "b": world.bank, "u": u})
            db.commit()
        db.rollback()
