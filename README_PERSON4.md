# 🩸 Person 4 — Issues, Reports, Auth & QA

Adds login (JWT + 1‑click demo login), FEFO blood allocation, the issue audit log,
dashboard reports and automated tests on top of Person 1's foundation.

## What was added

| Area | Files |
|---|---|
| DB | `db/migrations/002_person4_auth_issues.sql` (user_account, issue hardening, trigger, 2 views), `db/seed/seed_person4.sql` (demo requests) |
| Auth | `core/security.py`, `models/user.py`, `schemas/auth.py`, `services/auth_service.py`, `routers/auth.py` |
| Issues | `models/issue.py`, `schemas/issue.py`, `repositories/issue_repo.py`, `services/issue_service.py`, `routers/issues.py` |
| Reports | `services/report_service.py`, `routers/reports.py` |
| Frontend | `auth/AuthContext.jsx`, `pages/auth/LoginPage.jsx`, `pages/issues/IssueLog.jsx`, `pages/issues/FulfillRequestModal.jsx`, `pages/dashboard/ExecutiveDashboard.jsx`; `App.jsx` + `api/client.js` + `index.css` extended |
| Tests | `tests/conftest.py`, `test_auth.py`, `test_issue_rules.py`, `test_concurrency_fefo.py`, `test_end_to_end_flow.py` |

Small edits to shared files: `core/config.py` (JWT + report settings), `core/errors.py` (401/403),
`main.py` (router registration), `requirements.txt` (bcrypt, PyJWT), `.env.example`,
`DonorDetail.jsx` (back button now goes to `/donors`).

## Stand‑in files for other people's parts (keep THEIR version if it exists)

My code needs these, so I added minimal versions that match `001_create_tables.sql`:

| File | Owner | Needed because |
|---|---|---|
| `core/compatibility.py` | Person 2 | FEFO needs `get_compatible_donor_groups()` |
| `models/hospital.py`, `models/recipient.py`, `models/request.py` | Person 3 | allocation reads the request + recipient blood group |

The FEFO query lives in `issue_repo.find_fefo_candidates` and the status recompute in
`issue_service._sync_request_status`, so nothing depends on P2/P3 services landing first.

## How to run

```bash
# database (in order)
mysql -u root -p < db/migrations/001_create_tables.sql
mysql -u root -p < db/migrations/002_person4_auth_issues.sql
mysql -u root -p < db/seed/seed_data.sql
mysql -u root -p < db/seed/seed_person4.sql      # sample requests

cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 and click a quick‑login button (demo password for all: `demo1234`).

## API

| Method | Endpoint | Roles |
|---|---|---|
| POST | `/auth/login`, `/auth/demo-login/{role}` | public |
| GET | `/auth/me` | any logged in |
| GET | `/issues/` (audit log; filters: request_id, hospital_id, blood_group, date_from, date_to) | ADMIN, BANK_STAFF, HOSPITAL_STAFF (own hospital only) |
| GET | `/issues/pending-requests` | same |
| GET | `/requests/{id}/fefo-preview` | ADMIN, BANK_STAFF |
| POST | `/requests/{id}/auto-fulfil` | ADMIN, BANK_STAFF |
| POST | `/issues/manual` | ADMIN, BANK_STAFF |
| GET | `/reports/summary`, `/stock-distribution`, `/expiring-soon`, `/fulfillment-metrics` | ADMIN, BANK_STAFF |

## How FEFO allocation stays safe (viva notes)

1. Request row locked (`SELECT … FOR UPDATE`) → a request can't be over‑issued.
2. Candidate units read in expiry order, then each is locked with `FOR UPDATE SKIP LOCKED`
   (re‑checking AVAILABLE + not expired) → two operators never get the same bag.
   *(Putting SKIP LOCKED directly on the sorted query locks every matching row before LIMIT,
   so concurrent operators wrongly see "no stock" — the concurrency test caught this.)*
3. `UNIQUE (bank_id, unit_id)` on `issue` + a `BEFORE INSERT` trigger enforce it inside MySQL itself.
4. Everything is one transaction; any failure rolls back.

## Tests

```bash
cd backend
python -m pytest tests -v
```
DB tests use a separate `bloodbank_test` database (rebuilt from the migrations; never touches `bloodbank`)
and are skipped automatically if MySQL isn't reachable. Override with `TEST_DB_NAME`.

Covers: FEFO ordering, expired/discarded units skipped, ABO/Rh rules (RBC + plasma), partial
fulfilment, manual‑issue validation, trigger/unique safety net, 2‑ and 10‑way races for the last unit,
the full Donor → Donation → Request → Issue lifecycle, and role‑based access.
