"""
End-to-end lifecycle through the real HTTP API (Person 4):

    Donor -> Donation (blood unit) -> Request -> login -> FEFO issue -> audit log -> reports

Needs MySQL - skipped automatically if it isn't reachable.

Run:  cd backend && python -m pytest tests/test_end_to_end_flow.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.database import get_db
from app.main import app


@pytest.fixture()
def client(SessionFactory, db):
    def override():
        s = SessionFactory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client, role):
    r = client.post(f"/auth/demo-login/{role}")
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_full_lifecycle(client, db, make):
    bank = make.bank("E2E Bank")
    hospital = make.hospital("E2E Hospital")
    recipient = make.recipient("A+", "E2E Patient")

    # 1. A donor registers and donates (Person 1's API)
    r = client.post("/donors/", json={"name": "Dana Donor", "blood_group": "O-",
                                      "phone": "9123456789", "dob": "1992-04-01"})
    assert r.status_code == 201, r.text
    donor_id = r.json()["donor_id"]
    r = client.post("/donations/", json={"donor_id": donor_id, "bank_id": bank,
                                         "volume_ml": 450, "component_type": "RBC"})
    assert r.status_code == 201, r.text
    unit_id = r.json()["unit_id"]

    # 2. A hospital requests blood (Person 3's part - inserted directly here)
    request_id = make.request(hospital, recipient, "RBC", 1, "EMERGENCY")

    # 3. Bank staff logs in and fulfils with FEFO
    staff = _login(client, "BANK_STAFF")
    preview = client.get(f"/requests/{request_id}/fefo-preview", headers=staff).json()
    assert [(u["bank_id"], u["unit_id"]) for u in preview["recommended"]] == [(bank, unit_id)]

    r = client.post(f"/requests/{request_id}/auto-fulfil", headers=staff)
    assert r.status_code == 201, r.text
    assert r.json()["request_status"] == "FULFILLED"

    # 4. Database state is consistent
    assert db.execute(text("SELECT status FROM blood_unit WHERE bank_id=:b AND unit_id=:u"),
                      {"b": bank, "u": unit_id}).scalar() == "ISSUED"
    assert db.execute(text("SELECT status FROM request WHERE request_id=:r"),
                      {"r": request_id}).scalar() == "FULFILLED"

    # 5. Audit log shows the full custody trail
    log = client.get("/issues/", headers=staff).json()
    assert log["total"] == 1
    row = log["items"][0]
    assert (row["donor_name"], row["recipient_name"], row["hospital_name"]) == \
           ("Dana Donor", "E2E Patient", "E2E Hospital")
    assert row["issued_by_name"] == "Ravi Bank-Staff"

    # 6. Reports reflect it
    summary = client.get("/reports/summary", headers=staff).json()
    assert summary["total_issued"] == 1 and summary["available_units"] == 0
    metrics = client.get("/reports/fulfillment-metrics", headers=staff).json()
    emergency = next(x for x in metrics["by_urgency"] if x["urgency"] == "EMERGENCY")
    assert emergency["fulfilled"] == 1 and emergency["fulfillment_rate_pct"] == 100.0

    # 7. Same request cannot be fulfilled again
    assert client.post(f"/requests/{request_id}/auto-fulfil", headers=staff).status_code == 409


def test_role_based_access(client, db, make):
    admin = _login(client, "ADMIN")
    hospital_user = _login(client, "HOSPITAL_STAFF")
    donor_user = _login(client, "DONOR")

    assert client.get("/issues/").status_code == 401                       # no token
    assert client.get("/issues/", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get("/issues/", headers=donor_user).status_code == 403   # donors: no audit log
    assert client.get("/issues/", headers=hospital_user).status_code == 200
    assert client.get("/reports/summary", headers=hospital_user).status_code == 403
    assert client.get("/reports/summary", headers=admin).status_code == 200
    assert client.post("/requests/1/auto-fulfil", headers=hospital_user).status_code == 403
    assert client.get("/auth/me", headers=donor_user).json()["role"] == "DONOR"


def test_hospital_staff_only_sees_own_hospital(client, db, make):
    bank = make.bank()
    h1 = make.hospital("H1")          # demo hospital user is linked to hospital_id 1
    h2 = make.hospital("H2")
    donor = make.donor("O-")
    rec = make.recipient("O-")
    r1 = make.request(h1, rec, "RBC", 1)
    r2 = make.request(h2, rec, "RBC", 1)
    make.unit(bank, donor, "O-", "RBC", 5)
    make.unit(bank, donor, "O-", "RBC", 6)

    staff = _login(client, "BANK_STAFF")
    client.post(f"/requests/{r1}/auto-fulfil", headers=staff)
    client.post(f"/requests/{r2}/auto-fulfil", headers=staff)

    assert client.get("/issues/", headers=staff).json()["total"] == 2
    own = client.get("/issues/", headers=_login(client, "HOSPITAL_STAFF")).json()
    assert own["total"] == 1 and own["items"][0]["hospital_name"] == "H1"


def test_login_with_password(client, db, make):
    make.user("ADMIN", "real_admin")      # password pw12345
    ok = client.post("/auth/login", json={"username": "real_admin", "password": "pw12345"})
    assert ok.status_code == 200 and ok.json()["role"] == "ADMIN"
    assert client.post("/auth/login", json={"username": "real_admin", "password": "bad"}).status_code == 401
    assert client.post("/auth/login", json={"username": "ghost", "password": "pw12345"}).status_code == 401
    assert "password_hash" not in ok.text
