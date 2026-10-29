# Blood Bank Management System: 4-Person Implementation Plan

## 1. What the ER diagram says

| Entity | Key | Notes |
|---|---|---|
| HOSPITAL | hospital_id | 1 hospital raises N requests |
| RECIPIENT | recipient_id | 1 recipient has N requests |
| DONOR | donor_id | 1 donor donates N blood units (relationship attributes: `volume`, `donation_date`) |
| BLOOD BANK | bank_id | 1 bank has N blood units |
| BLOOD UNIT (weak) | (bank_id, unit_id) | `unit_id` is a partial key, identified by its blood bank |
| REQUEST | request_id | 1 request is fulfilled by N issues |
| ISSUE (weak/associative) | issue_id | Links a REQUEST to a BLOOD UNIT (1 unit to N issues, 1 request to N issues) |

**Assumptions to confirm with your instructor:**

- A physical bag is issued once, so one active issue per unit is enforced in the service layer.
- `quantity_issued` is stored as the number of units, normally 1 per issue row. If your course means millilitres, change the column name only.

---

## 2. Tech stack (swappable)

- **DB:** PostgreSQL 16, with plain SQL migrations
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic
- **Frontend:** React + Vite + TypeScript, TanStack Query, React Router, Tailwind
- **Tests:** pytest, Vitest
- **Tooling:** Docker Compose, GitHub Actions, ruff, prettier

---

## 3. Repository layout (create this on Day 0)

```
bloodbank/
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/
│   └── CONTRACTS.md           # DDL + integration contracts (sections 4 and 7)
├── db/
│   ├── migrations/            # 001_...sql
│   └── seed/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # config.py, database.py, errors.py, enums.py, compatibility.py
│   │   ├── models/            # donor.py, blood_bank.py, blood_unit.py, hospital.py, recipient.py, request.py, issue.py
│   │   ├── schemas/           # one pydantic file per entity
│   │   ├── repositories/      # DB access only
│   │   ├── services/          # business rules
│   │   └── routers/           # donors.py, donations.py, banks.py, units.py, hospitals.py,
│   │                          # recipients.py, requests.py, issues.py, reports.py
│   └── tests/
└── frontend/
    └── src/
        ├── api/               # client.ts + one file per module
        ├── components/        # DataTable, FormField, StatusBadge, Modal
        ├── pages/             # donors/, inventory/, requests/, issues/, dashboard/
        └── App.tsx
```

---

## 4. Shared database schema (agreed by all four, then frozen)

```sql
CREATE TYPE blood_group_t    AS ENUM ('A+','A-','B+','B-','AB+','AB-','O+','O-');
CREATE TYPE component_t      AS ENUM ('WHOLE_BLOOD','RBC','PLATELETS','PLASMA');
CREATE TYPE unit_status_t    AS ENUM ('AVAILABLE','RESERVED','ISSUED','EXPIRED','DISCARDED');
CREATE TYPE urgency_t        AS ENUM ('ROUTINE','URGENT','EMERGENCY');
CREATE TYPE request_status_t AS ENUM ('PENDING','PARTIALLY_FULFILLED','FULFILLED','CANCELLED');

CREATE TABLE blood_bank (
  bank_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL,
  address TEXT NOT NULL, contact VARCHAR(20) NOT NULL);

CREATE TABLE hospital (
  hospital_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL,
  address TEXT NOT NULL, contact VARCHAR(20) NOT NULL);

CREATE TABLE recipient (
  recipient_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL,
  age INT CHECK (age BETWEEN 0 AND 120), blood_group blood_group_t NOT NULL);

CREATE TABLE donor (
  donor_id SERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL,
  blood_group blood_group_t NOT NULL, phone VARCHAR(15) UNIQUE NOT NULL,
  dob DATE NOT NULL, last_donation_date DATE);

CREATE TABLE blood_unit (
  bank_id INT REFERENCES blood_bank ON DELETE CASCADE,
  unit_id INT,                                   -- partial key, per-bank counter
  donor_id INT NOT NULL REFERENCES donor,        -- "donates" relationship
  volume_ml INT NOT NULL CHECK (volume_ml BETWEEN 50 AND 600),
  donation_date DATE NOT NULL,
  blood_group blood_group_t NOT NULL,
  component_type component_t NOT NULL,
  collection_date DATE NOT NULL,
  expiry_date DATE NOT NULL CHECK (expiry_date > collection_date),
  status unit_status_t NOT NULL DEFAULT 'AVAILABLE',
  PRIMARY KEY (bank_id, unit_id));

CREATE TABLE request (
  request_id SERIAL PRIMARY KEY,
  hospital_id INT NOT NULL REFERENCES hospital,
  recipient_id INT NOT NULL REFERENCES recipient,
  component_type component_t NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  urgency urgency_t NOT NULL DEFAULT 'ROUTINE',
  request_date DATE NOT NULL DEFAULT CURRENT_DATE,
  status request_status_t NOT NULL DEFAULT 'PENDING');

CREATE TABLE issue (
  issue_id SERIAL PRIMARY KEY,
  request_id INT NOT NULL REFERENCES request,
  bank_id INT NOT NULL, unit_id INT NOT NULL,
  issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
  quantity_issued INT NOT NULL DEFAULT 1 CHECK (quantity_issued > 0),
  FOREIGN KEY (bank_id, unit_id) REFERENCES blood_unit);

CREATE INDEX idx_unit_search    ON blood_unit (blood_group, component_type, status, expiry_date);
CREATE INDEX idx_request_status ON request (status, urgency);
```

---

## 5. Business rules (shared constants in `core/`)

- **Donor eligibility:** age 18-65, at least 90 days since `last_donation_date` (configurable constant).
- **Expiry defaults:** whole blood and RBC 35 days, platelets 5 days, plasma 365 days (frozen), computed from `collection_date`.
- **Compatibility:** `compatibility.py` holds the ABO/Rh matrix. RBC and whole blood follow the standard donor-to-recipient table. Plasma follows the reverse ABO logic. Platelets are preferably the same group.
- **Allocation:** pick the earliest-expiring compatible units first (FEFO), using `SELECT ... FOR UPDATE SKIP LOCKED` inside one transaction.
- **Request status:** PENDING, then PARTIALLY_FULFILLED while issued < quantity, then FULFILLED when issued == quantity.
- **Unit lifecycle:** AVAILABLE, then ISSUED. An expiry job sets AVAILABLE units past `expiry_date` to EXPIRED.

---

## 6. Work split (4 equal vertical slices)

Each person gets: one core domain (tables, API, UI), one shared foundation task, one non-trivial workflow, and tests.

### Person 1: Donors, donations, database foundation

**Foundation:** `docker-compose.yml`, Postgres setup, migrations (section 4 DDL), seed script (10 banks/hospitals, 50 donors, 100 units), `.env.example`.

**Domain files:** `models/donor.py`, `schemas/donor.py`, `repositories/donor_repo.py`, `services/donor_service.py`, `services/donation_service.py`, `routers/donors.py`, `routers/donations.py`

| Endpoint | Purpose |
|---|---|
| `POST/GET/PUT/DELETE /donors` | CRUD, search by group and phone |
| `GET /donors/{id}/eligibility` | Rule check (age, 90-day gap) |
| `POST /donations` | Records a donation: validates eligibility, calls P2's `unit_service.create_unit()`, updates `last_donation_date`, all in one transaction |
| `GET /donors/{id}/history` | Donation history |

**Frontend:** `pages/donors/` (list with filters, form, detail with history, "Record donation" modal).

**Tests:** eligibility edge cases, donation transaction rollback, duplicate phone.

### Person 2: Blood banks, blood units (inventory), backend core

**Foundation:** `core/` (config, DB session, global error handler, enums, `compatibility.py`, date and expiry utilities), `main.py`, router registration.

**Domain files:** `models/blood_bank.py`, `models/blood_unit.py`, matching schemas, repos, `services/unit_service.py`, `services/expiry_service.py`, `routers/banks.py`, `routers/units.py`

| Endpoint | Purpose |
|---|---|
| `CRUD /banks` | Blood bank management |
| `GET /banks/{id}/units` | Filter by group, component, status, expiring within N days |
| `GET /banks/{id}/inventory-summary` | Counts grouped by group and component |
| `POST /units/expire-sweep` | Marks expired units |
| `PATCH /units/{bank_id}/{unit_id}/discard` | Discard a unit with a reason |
| Internal: `create_unit()` | Allocates the per-bank `unit_id` (lock the bank row, then `max+1`), computes expiry |
| Internal: `find_compatible_units()` | Used by P4 |

**Frontend:** `pages/inventory/` (bank list, inventory grid with colour-coded expiry, low-stock indicator).

**Tests:** unit_id uniqueness under concurrency, expiry calculation, compatibility matrix (all 64 pairs).

### Person 3: Hospitals, recipients, requests, frontend shell

**Foundation:** React app setup (Vite, router, Tailwind), `api/client.ts`, reusable `DataTable`, `FormField`, `Modal`, `StatusBadge`, layout and navigation.

**Domain files:** `models/hospital.py`, `models/recipient.py`, `models/request.py`, schemas, repos, `services/request_service.py`, `routers/hospitals.py`, `routers/recipients.py`, `routers/requests.py`

| Endpoint | Purpose |
|---|---|
| `CRUD /hospitals`, `CRUD /recipients` | Master data |
| `POST /requests` | Validates that the recipient exists and the component fits the recipient's group |
| `GET /requests` | Filter by status, urgency, hospital, date. EMERGENCY sorts first |
| `PATCH /requests/{id}/cancel` | Only allowed if no units are issued |
| `GET /requests/{id}` | Includes issued units (join to issue) |
| Internal: `recompute_status(request_id)` | Used by P4 after each issue |

**Frontend:** `pages/requests/` (create-request form with hospital and recipient pickers, queue view, detail page).

**Tests:** status transitions, cancel guard, validation errors.

### Person 4: Issues, reports, QA and CI

**Foundation:** GitHub Actions (ruff, pytest, Vitest, build), pytest fixtures with a test DB, optional simple auth (JWT with admin and staff roles), final README and ER-to-schema mapping doc.

**Domain files:** `models/issue.py`, `schemas/issue.py`, `repositories/issue_repo.py`, `services/issue_service.py`, `services/report_service.py`, `routers/issues.py`, `routers/reports.py`

| Endpoint | Purpose |
|---|---|
| `POST /requests/{id}/fulfil` | Auto-allocate: lock compatible AVAILABLE units (FEFO), create issue rows, set units to ISSUED, call `recompute_status`. One transaction, partial fulfilment allowed |
| `POST /issues` | Manual issue of a specific unit (validates compatibility, status and expiry) |
| `GET /issues`, `GET /issues/{id}` | Issue records |
| `GET /reports/stock` | Stock by group and component per bank |
| `GET /reports/expiring?days=7` | Units nearing expiry |
| `GET /reports/requests-summary` | Counts by status and urgency |
| `GET /reports/donor-activity` | Top donors and monthly donations |

**Frontend:** `pages/issues/` (issue history, fulfil dialog showing proposed units), `pages/dashboard/` (stat cards and charts).

**Tests:** concurrent fulfilment (two requests for the last unit), expired unit rejection, partial fulfilment, end-to-end flow.

---

## 7. Integration contracts (agree on Day 0, do not change without telling everyone)

| Provider | Function | Consumer |
|---|---|---|
| P2 | `unit_service.create_unit(db, bank_id, donor_id, volume_ml, component, blood_group, donation_date) -> BloodUnit` | P1 |
| P2 | `unit_service.find_compatible_units(db, recipient_group, component, limit, lock=True) -> list[BloodUnit]` | P4 |
| P3 | `request_service.recompute_status(db, request_id) -> RequestStatus` | P4 |
| P1 | `donor_service.is_eligible(donor) -> (bool, reason)` | own module and tests |
| P2 | `core/errors.py`: `NotFound`, `ConflictError`, `ValidationFailed` (mapped to 404/409/422) | everyone |

Each person writes a stub of their provided functions on Day 1 so others can code against them.

---

## 8. Timeline

| Phase | Time | Everyone |
|---|---|---|
| 0. Kickoff | Day 1 | Create repo, agree on the DDL and contracts, set up branches |
| 1. Foundations | Days 2-4 | P1 DB and seed, P2 core, P3 UI shell, P4 CI and fixtures |
| 2. Domain CRUD | Days 5-9 | Each builds their entities (API, UI, unit tests) |
| 3. Workflows | Days 10-13 | Donation (P1), expiry and inventory (P2), requests (P3), fulfilment and reports (P4) |
| 4. Integration | Days 14-16 | End-to-end tests, bug bash, cross-review |
| 5. Polish | Days 17-18 | Docs, ER mapping, demo data, presentation |

---

## 9. Git workflow

- Branches: `main` (protected), `feat/p1-donors`, `feat/p2-inventory`, etc. Merge through PRs, and every PR needs one review from a different person.
- Review pairs rotate: P1↔P2, P3↔P4 in week 1, then P1↔P3, P2↔P4.
- Commit prefixes: `feat:`, `fix:`, `test:`, `docs:`.
- Only P1 edits migrations. Others request schema changes via an issue.

---

## 10. Demo flow (acceptance test for the whole team)

1. Register a donor and check eligibility.
2. Record a donation, which creates a unit in a blood bank and updates `last_donation_date`.
3. View it in the inventory with the correct expiry date.
4. A hospital raises an EMERGENCY request for a recipient.
5. Fulfil it: compatible FEFO units are issued, units become ISSUED, request becomes FULFILLED (or PARTIALLY_FULFILLED).
6. The dashboard and reports reflect the change.
7. Run the expiry sweep and confirm that expired units drop out of availability.

---

## 11. Tips for working in an IDE (Cursor, VS Code + Copilot, or PyCharm)

- Commit the DDL from section 4 and the contracts from section 7 into the repo as `docs/CONTRACTS.md`. Point your AI assistant at it each time, since it keeps everyone's generated code consistent.
- Work file by file in this order: model, schema, repo, service, router, test, then the frontend API file and page.
- A good prompt template:

  > Following docs/CONTRACTS.md, implement `services/donation_service.py` for Person 1: [rules]. Use the existing `core/errors.py`. Include pytest tests.
