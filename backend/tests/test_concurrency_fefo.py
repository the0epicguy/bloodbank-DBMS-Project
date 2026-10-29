"""
Concurrency tests (Person 4): many operators competing for the same blood.

Each thread uses its OWN database session/connection, exactly like separate
web requests would. `SELECT ... FOR UPDATE SKIP LOCKED` + the UNIQUE
constraint must guarantee a bag is never given out twice.

Run:  cd backend && python -m pytest tests/test_concurrency_fefo.py -v
"""

import threading
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import text

from app.core.errors import ConflictError
from app.services import issue_service
from tests.conftest import load_user


def _race(SessionFactory, request_ids, admin_id):
    """Fire auto_fulfil for every request at (almost) the same instant."""
    barrier = threading.Barrier(len(request_ids))

    def worker(rid):
        s = SessionFactory()
        try:
            user = load_user(s, admin_id)
            barrier.wait()
            issue_service.auto_fulfil(s, rid, user)
            return "ok"
        except ConflictError as exc:
            # only "no stock" counts as a clean loss; "database busy" etc. must fail the test
            return "no_stock" if "No compatible" in str(exc.detail) else f"error: {exc.detail}"
        finally:
            s.close()

    with ThreadPoolExecutor(max_workers=len(request_ids)) as pool:
        return list(pool.map(worker, request_ids))


def test_two_requests_compete_for_the_last_unit(db, make, world, SessionFactory):
    """2 simultaneous requests, 1 compatible unit -> exactly 1 wins, 1 gets 'no stock'."""
    make.unit(world.bank, world.donor, "O-", "RBC", 10)
    rec = make.recipient("O-")
    r1 = make.request(world.hospital, rec, "RBC", 1, "EMERGENCY")
    r2 = make.request(world.hospital, rec, "RBC", 1, "EMERGENCY")

    results = _race(SessionFactory, [r1, r2], world.admin_id)

    assert sorted(results) == ["no_stock", "ok"]
    assert db.execute(text("SELECT COUNT(*) FROM issue")).scalar() == 1
    assert db.execute(text("SELECT COUNT(*) FROM blood_unit WHERE status='ISSUED'")).scalar() == 1


def test_ten_requests_one_unit(db, make, world, SessionFactory):
    """10 parallel requests for the same single bag -> exactly 1 succeeds, no deadlock crash."""
    make.unit(world.bank, world.donor, "O-", "RBC", 10)
    rec = make.recipient("O-")
    reqs = [make.request(world.hospital, rec, "RBC", 1) for _ in range(10)]

    results = _race(SessionFactory, reqs, world.admin_id)

    assert results.count("ok") == 1
    assert results.count("no_stock") == 9
    assert db.execute(text("SELECT COUNT(*) FROM issue")).scalar() == 1


def test_no_unit_is_ever_issued_twice_under_load(db, make, world, SessionFactory):
    """8 requests, 5 units: exactly 5 succeed and every bag is issued exactly once."""
    for d in range(5):
        make.unit(world.bank, world.donor, "O-", "RBC", 5 + d)
    rec = make.recipient("O-")
    reqs = [make.request(world.hospital, rec, "RBC", 1) for _ in range(8)]

    results = _race(SessionFactory, reqs, world.admin_id)

    assert results.count("ok") == 5
    rows = db.execute(text("SELECT bank_id, unit_id, COUNT(*) FROM issue GROUP BY bank_id, unit_id")).all()
    assert len(rows) == 5
    assert all(n == 1 for _, _, n in rows)
    # every request that succeeded is FULFILLED, the others stay PENDING
    assert db.execute(text("SELECT COUNT(*) FROM request WHERE status='FULFILLED'")).scalar() == 5
    assert db.execute(text("SELECT COUNT(*) FROM request WHERE status='PENDING'")).scalar() == 3


def test_same_request_fulfilled_twice_at_once_is_not_over_issued(db, make, world, SessionFactory):
    """Two operators click 'fulfil' on the SAME request (qty 1) with plenty of stock."""
    for d in range(4):
        make.unit(world.bank, world.donor, "O-", "RBC", 5 + d)
    req = make.request(world.hospital, make.recipient("O-"), "RBC", 1)

    results = _race(SessionFactory, [req, req], world.admin_id)

    assert results.count("ok") == 1
    assert db.execute(text("SELECT COUNT(*) FROM issue WHERE request_id=:r"), {"r": req}).scalar() == 1
