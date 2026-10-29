# Blood Bank Management System: Comprehensive 4-Person Implementation Plan
**Database Management System (DBMS) Project Specification & Engineering Blueprint**

---

## 1. Executive Summary & Design Decisions

### 1.1 Confirmed Architecture Decisions
| Dimension | Decision | Rationale |
|---|---|---|
| **Database Engine** | **MySQL 8.0 (InnoDB)** | Native support for transactions, foreign keys, `SELECT ... FOR UPDATE SKIP LOCKED`, triggers, and views. |
| **Team Structure** | **4 Strict Vertical Slices** | Clear module boundaries, explicit contracts, and isolated Git feature branches for 4 team members. |
| **Backend Framework** | **FastAPI (Python 3.12)** | Async endpoints, automatic OpenAPI documentation, Pydantic v2 schemas, SQLAlchemy 2.0 ORM. |
| **Frontend Framework** | **React + Vite + TypeScript + Tailwind CSS** | Fast modern SPA, component-driven, responsive medical-grade dashboard theme. |
| **Authentication & RBAC**| **JWT Auth + 1-Click Quick-Login** | Real JWT security with instant demo logins (`Admin`, `Bank Staff`, `Hospital Staff`, `Donor`). |
| **Integrity Model** | **Hybrid (MySQL Triggers & Views + Python Service Layer)** | Course-level DBMS triggers and views demonstrate DB mastery; Python validation provides clean UI error messages. |
| **Execution Mode** | **Local Development Primary, Docker Secondary** | Fast local iteration on Ubuntu 24.04 (MySQL 8.0 active) + Docker Compose for portability. |

---

## 2. Relational Schema & MySQL 8.0 DDL Specification

### 2.1 Entity-Relationship (ER) to Relational Mapping

```
+--------------------+        1:N         +--------------------+
|      HOSPITAL      | -----------------> |      REQUEST       |
+--------------------+                    +--------------------+
                                                     | 1:N
+--------------------+        1:N                    v
|     RECIPIENT      | -----------------> +--------------------+
+--------------------+                    |       ISSUE        |
                                          +--------------------+
+--------------------+        1:N                    ^
|       DONOR        | -----------------+            | 1:N (Weak)
+--------------------+                  |            |
                                        v            |
+--------------------+  1:N (Weak)  +--------------------+
|     BLOOD BANK     | -----------> |     BLOOD UNIT     |
+--------------------+              +--------------------+
```

- **Weak Entity**: `BLOOD UNIT` is identified by the composite key `(bank_id, unit_id)`, where `unit_id` is a sequential integer counter per blood bank.
- **Associative Entity**: `ISSUE` bridges `REQUEST` and `BLOOD UNIT`, tracking physical unit allocation.
- **Transitivity & Foreign Keys**: `ON DELETE RESTRICT` protects audit trails; `ON DELETE CASCADE` cascades bank-level deletions if required.

### 2.2 Complete MySQL 8.0 DDL

```sql
-- ============================================================================
-- Blood Bank Management System: DDL Initialization Script (MySQL 8.0+)
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS issue;
DROP TABLE IF EXISTS request;
DROP TABLE IF EXISTS blood_unit;
DROP TABLE IF EXISTS donor;
DROP TABLE IF EXISTS recipient;
DROP TABLE IF EXISTS hospital;
DROP TABLE IF EXISTS blood_bank;
DROP TABLE IF EXISTS user_account;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------------------------------------------------------
-- 1. User Accounts (Authentication & Role-Based Access Control)
-- ----------------------------------------------------------------------------
CREATE TABLE user_account (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100) NOT NULL,
    role          ENUM('ADMIN', 'BANK_STAFF', 'HOSPITAL_STAFF', 'DONOR') NOT NULL,
    entity_ref_id INT DEFAULT NULL, -- Links to bank_id, hospital_id, or donor_id
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2. Blood Bank Entity
-- ----------------------------------------------------------------------------
CREATE TABLE blood_bank (
    bank_id      INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(120) NOT NULL,
    address      TEXT NOT NULL,
    city         VARCHAR(60) NOT NULL,
    contact      VARCHAR(20) NOT NULL,
    email        VARCHAR(100) UNIQUE,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3. Hospital Entity
-- ----------------------------------------------------------------------------
CREATE TABLE hospital (
    hospital_id  INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(120) NOT NULL,
    address      TEXT NOT NULL,
    city         VARCHAR(60) NOT NULL,
    contact      VARCHAR(20) NOT NULL,
    email        VARCHAR(100) UNIQUE,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4. Recipient Entity
-- ----------------------------------------------------------------------------
CREATE TABLE recipient (
    recipient_id INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    age          INT NOT NULL,
    gender       ENUM('MALE', 'FEMALE', 'OTHER') NOT NULL,
    blood_group  ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    hospital_id  INT DEFAULT NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_recipient_age CHECK (age BETWEEN 0 AND 120),
    CONSTRAINT fk_recipient_hospital FOREIGN KEY (hospital_id) 
        REFERENCES hospital(hospital_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5. Donor Entity
-- ----------------------------------------------------------------------------
CREATE TABLE donor (
    donor_id           INT AUTO_INCREMENT PRIMARY KEY,
    name               VARCHAR(100) NOT NULL,
    blood_group        ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    phone              VARCHAR(15) NOT NULL UNIQUE,
    email              VARCHAR(100) UNIQUE,
    dob                DATE NOT NULL,
    gender             ENUM('MALE', 'FEMALE', 'OTHER') NOT NULL,
    last_donation_date DATE DEFAULT NULL,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6. Blood Unit Entity (Weak Entity dependent on Blood Bank)
-- ----------------------------------------------------------------------------
CREATE TABLE blood_unit (
    bank_id          INT NOT NULL,
    unit_id          INT NOT NULL, -- Per-bank sequential counter (1, 2, 3...)
    donor_id         INT NOT NULL,
    volume_ml        INT NOT NULL,
    blood_group      ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    component_type   ENUM('WHOLE_BLOOD','RBC','PLATELETS','PLASMA') NOT NULL,
    donation_date    DATE NOT NULL,
    collection_date  DATE NOT NULL,
    expiry_date      DATE NOT NULL,
    status           ENUM('AVAILABLE','RESERVED','ISSUED','EXPIRED','DISCARDED') NOT NULL DEFAULT 'AVAILABLE',
    discard_reason   TEXT DEFAULT NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (bank_id, unit_id),
    CONSTRAINT chk_unit_volume CHECK (volume_ml BETWEEN 50 AND 600),
    CONSTRAINT chk_unit_expiry CHECK (expiry_date > collection_date),
    CONSTRAINT fk_unit_bank FOREIGN KEY (bank_id) 
        REFERENCES blood_bank(bank_id) ON DELETE CASCADE,
    CONSTRAINT fk_unit_donor FOREIGN KEY (donor_id) 
        REFERENCES donor(donor_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 7. Request Entity
-- ----------------------------------------------------------------------------
CREATE TABLE request (
    request_id       INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id      INT NOT NULL,
    recipient_id     INT NOT NULL,
    blood_group      ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') NOT NULL,
    component_type   ENUM('WHOLE_BLOOD','RBC','PLATELETS','PLASMA') NOT NULL,
    quantity         INT NOT NULL,
    urgency          ENUM('ROUTINE','URGENT','EMERGENCY') NOT NULL DEFAULT 'ROUTINE',
    request_date     DATE NOT NULL,
    status           ENUM('PENDING','PARTIALLY_FULFILLED','FULFILLED','CANCELLED') NOT NULL DEFAULT 'PENDING',
    notes            TEXT DEFAULT NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_request_qty CHECK (quantity > 0),
    CONSTRAINT fk_request_hospital FOREIGN KEY (hospital_id) 
        REFERENCES hospital(hospital_id) ON DELETE RESTRICT,
    CONSTRAINT fk_request_recipient FOREIGN KEY (recipient_id) 
        REFERENCES recipient(recipient_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 8. Issue Entity (Associative Entity: Request <-> Blood Unit)
-- ----------------------------------------------------------------------------
CREATE TABLE issue (
    issue_id         INT AUTO_INCREMENT PRIMARY KEY,
    request_id       INT NOT NULL,
    bank_id          INT NOT NULL,
    unit_id          INT NOT NULL,
    issue_date       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quantity_issued  INT NOT NULL DEFAULT 1,
    notes            TEXT DEFAULT NULL,
    CONSTRAINT chk_issue_qty CHECK (quantity_issued = 1),
    CONSTRAINT uq_unit_single_issue UNIQUE (bank_id, unit_id), -- Physical bag can only ever be issued once!
    CONSTRAINT fk_issue_request FOREIGN KEY (request_id) 
        REFERENCES request(request_id) ON DELETE RESTRICT,
    CONSTRAINT fk_issue_unit FOREIGN KEY (bank_id, unit_id) 
        REFERENCES blood_unit(bank_id, unit_id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- Performance Indexes for Optimization & Concurrency
-- ----------------------------------------------------------------------------
CREATE INDEX idx_unit_fefo ON blood_unit (blood_group, component_type, status, expiry_date);
CREATE INDEX idx_unit_bank_status ON blood_unit (bank_id, status);
CREATE INDEX idx_request_queue ON request (status, urgency, request_date);
CREATE INDEX idx_issue_req ON issue (request_id);
```

### 2.3 MySQL Triggers & Stored Views

```sql
DELIMITER //

-- Trigger 1: Automatically update donor's last_donation_date upon new blood unit insertion
CREATE TRIGGER trg_after_donation_insert
AFTER INSERT ON blood_unit
FOR EACH ROW
BEGIN
    UPDATE donor
    SET last_donation_date = NEW.donation_date
    WHERE donor_id = NEW.donor_id
      AND (last_donation_date IS NULL OR last_donation_date < NEW.donation_date);
END //

-- Trigger 2: Automatically recompute request status and mark unit as ISSUED upon issue creation
CREATE TRIGGER trg_after_issue_insert
AFTER INSERT ON issue
FOR EACH ROW
BEGIN
    DECLARE total_requested INT;
    DECLARE total_issued INT;

    -- Update the blood unit status to ISSUED
    UPDATE blood_unit 
    SET status = 'ISSUED' 
    WHERE bank_id = NEW.bank_id AND unit_id = NEW.unit_id;

    -- Compute total units issued so far for this request
    SELECT quantity INTO total_requested FROM request WHERE request_id = NEW.request_id;
    SELECT COUNT(*) INTO total_issued FROM issue WHERE request_id = NEW.request_id;

    -- Update request status
    IF total_issued >= total_requested THEN
        UPDATE request SET status = 'FULFILLED' WHERE request_id = NEW.request_id;
    ELSE
        UPDATE request SET status = 'PARTIALLY_FULFILLED' WHERE request_id = NEW.request_id;
    END IF;
END //

DELIMITER ;

-- View 1: Available Stock Matrix
CREATE OR REPLACE VIEW vw_available_stock AS
SELECT 
    b.bank_id,
    b.name AS bank_name,
    u.blood_group,
    u.component_type,
    COUNT(*) AS available_units,
    MIN(u.expiry_date) AS earliest_expiry
FROM blood_unit u
JOIN blood_bank b ON u.bank_id = b.bank_id
WHERE u.status = 'AVAILABLE' AND u.expiry_date >= CURRENT_DATE()
GROUP BY b.bank_id, b.name, u.blood_group, u.component_type;

-- View 2: Request Fulfillment Progress
CREATE OR REPLACE VIEW vw_request_status_summary AS
SELECT 
    r.request_id,
    h.name AS hospital_name,
    rec.name AS recipient_name,
    r.blood_group,
    r.component_type,
    r.quantity AS requested_units,
    COALESCE(COUNT(i.issue_id), 0) AS issued_units,
    (r.quantity - COALESCE(COUNT(i.issue_id), 0)) AS remaining_units,
    r.urgency,
    r.status
FROM request r
JOIN hospital h ON r.hospital_id = h.hospital_id
JOIN recipient rec ON r.recipient_id = rec.recipient_id
LEFT JOIN issue i ON r.request_id = i.request_id
GROUP BY r.request_id, h.name, rec.name, r.blood_group, r.component_type, r.quantity, r.urgency, r.status;
```

---

## 3. Medical Rules & Concurrency Engines

### 3.1 Transfusion Compatibility Matrix (ABO/Rh)
Implemented in `core/compatibility.py` and validated at service boundaries:

```python
# ABO/Rh compatibility rules for Red Blood Cells (RBC) & Whole Blood:
RBC_COMPATIBILITY = {
    "O-":  ["O-"],
    "O+":  ["O-", "O+"],
    "A-":  ["O-", "A-"],
    "A+":  ["O-", "O+", "A-", "A+"],
    "B-":  ["O-", "B-"],
    "B+":  ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"] # Universal Recipient
}

# Plasma rules (Reverse ABO logic):
PLASMA_COMPATIBILITY = {
    "O-":  ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"], # Universal Plasma Recipient
    "O+":  ["O+", "A+", "B+", "AB+"],
    "A-":  ["A-", "A+", "AB-", "AB+"],
    "A+":  ["A+", "AB+"],
    "B-":  ["B-", "B+", "AB-", "AB+"],
    "B+":  ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"] # Universal Plasma Donor
}

# Platelets preferably identical group, with secondary cross-compatibility fallback:
PLATELETS_COMPATIBILITY = RBC_COMPATIBILITY
```

### 3.2 Expiry Shelf-Life Standards
- **WHOLE_BLOOD**: 35 days from `collection_date`.
- **RBC**: 42 days from `collection_date`.
- **PLATELETS**: 5 days from `collection_date`.
- **PLASMA**: 365 days from `collection_date`.

### 3.3 Atomic Concurrency Protocols (MySQL InnoDB)
1. **FEFO Allocation (`SELECT ... FOR UPDATE SKIP LOCKED`)**:
   When fulfilling a request, query candidate units ordered by `expiry_date ASC`. `SKIP LOCKED` ensures that if two nurses/operators concurrently fulfill emergency requests, neither will block or double-allocate the same blood bag.
2. **Weak Entity `unit_id` Generation**:
   Within the transaction creating a unit, lock the parent `blood_bank` row:
   ```sql
   SELECT bank_id FROM blood_bank WHERE bank_id = :bank_id FOR UPDATE;
   SELECT COALESCE(MAX(unit_id), 0) + 1 FROM blood_unit WHERE bank_id = :bank_id;
   ```

---

## 4. Strict 4-Person Work Breakdown & Module Ownership

The system is decomposed into 4 independent vertical slices. Each member owns specific backend models, schemas, repositories, services, API routers, frontend pages, and tests.

```
                                  TEAM WORKFLOW ARCHITECTURE
+--------------------------------------------------------------------------------------------------+
| PERSON 1: Donors, Donations & DB Foundation                                                      |
| Backend: models/donor.py, schemas/donor.py, repos/donor_repo.py, services/donor_service.py       |
| API: /api/v1/donors, /api/v1/donations                                                           |
| Frontend: src/pages/donors/ (Donor List, Registration, Eligibility Badge, Donation Modal)        |
| Foundation: db/schema.sql, db/seed.py, db/connection.py                                          |
+--------------------------------------------------------------------------------------------------+
| PERSON 2: Blood Banks, Cold Storage Inventory & Backend Core                                     |
| Backend: models/blood_bank.py, models/blood_unit.py, services/unit_service.py, expiry_service.py  |
| API: /api/v1/banks, /api/v1/inventory, /api/v1/inventory/expire-sweep                            |
| Frontend: src/pages/inventory/ (Bank Selector, Cold Storage Rack Grid, Expiry Color Alerts)       |
| Foundation: core/config.py, core/errors.py, core/compatibility.py, core/enums.py                 |
+--------------------------------------------------------------------------------------------------+
| PERSON 3: Hospitals, Recipients, Requests & Frontend Shell                                       |
| Backend: models/hospital.py, models/recipient.py, models/request.py, services/request_service.py |
| API: /api/v1/hospitals, /api/v1/recipients, /api/v1/requests                                     |
| Frontend: src/pages/requests/ (Urgency Queue, New Request Modal, Recipient Master Table)         |
| Foundation: src/components/ (Navbar, Sidebar, DataTable, Modal, StatusBadge), src/api/client.ts |
+--------------------------------------------------------------------------------------------------+
| PERSON 4: Issues, Reports, Auth & QA Automation                                                  |
| Backend: models/issue.py, models/user.py, services/issue_service.py, services/report_service.py  |
| API: /api/v1/issues, /api/v1/reports/*, /api/v1/auth/*                                           |
| Frontend: src/pages/issues/ (Issue Audit Log, FEFO Allocation Modal), src/pages/dashboard/       |
| Foundation: JWT Auth Engine, 1-Click Quick Login, Pytest suite, Concurrency test scripts         |
+--------------------------------------------------------------------------------------------------+
```

### 4.1 Detailed Person Responsibilities

#### Person 1: Donors, Donations & Database Foundation
- **Git Branch**: `feat/p1-donors-db`
- **Database Responsibilities**:
  - `db/schema.sql`: Full MySQL 8.0 DDL with triggers, views, and indexes.
  - `db/seed.py`: Synthetic generator creating 10 banks, 20 hospitals, 50 donors, 150 blood units.
- **Backend Responsibilities**:
  - `models/donor.py`
  - `schemas/donor.py`: `DonorCreate`, `DonorResponse`, `DonationCreate`, `EligibilityResponse`.
  - `repositories/donor_repo.py`: CRUD, search by phone, blood group filter.
  - `services/donor_service.py`: Check 18-65 age eligibility and 90-day donation interval.
  - `services/donation_service.py`: Atomic donation transaction (validates eligibility, invokes P2's `create_unit()`, updates `last_donation_date`).
  - `routers/donors.py` & `routers/donations.py`.
- **Frontend Responsibilities**:
  - `pages/donors/DonorList.tsx`: Searchable table with blood group badges and donation history drawer.
  - `pages/donors/DonorFormModal.tsx`: Register donor.
  - `pages/donors/RecordDonationModal.tsx`: Collect blood bag parameters with live eligibility check.
- **Unit & Integration Tests**:
  - `tests/test_donor_eligibility.py` (Underage, overage, < 90-day cooldown).
  - `tests/test_donation_transaction.py` (Atomic rollback test).

#### Person 2: Blood Banks, Cold Storage Inventory & Backend Core
- **Git Branch**: `feat/p2-inventory-core`
- **Core Framework Responsibilities**:
  - `core/config.py`: Environment variable loading (MySQL connection strings, JWT secret).
  - `core/database.py`: SQLAlchemy 2.0 async engine session maker with MySQL `aiomysql`.
  - `core/errors.py`: Custom HTTP exception handlers (404 NotFound, 409 Conflict, 422 Unprocessable).
  - `core/enums.py`: BloodGroup, ComponentType, UnitStatus, UrgencyLevel, RequestStatus.
  - `core/compatibility.py`: 64-pair ABO/Rh medical compatibility evaluator.
- **Domain Responsibilities**:
  - `models/blood_bank.py`, `models/blood_unit.py`.
  - `schemas/inventory.py`: `BloodBankCreate`, `BloodBankResponse`, `UnitResponse`, `DiscardUnitRequest`.
  - `repositories/inventory_repo.py`: Weak entity lock-and-increment unit generator, filter by bank and expiry.
  - `services/unit_service.py`: Contract provider for `create_unit()` and `find_compatible_units()`.
  - `services/expiry_service.py`: Background or API-triggered sweep setting past-expiry units to `EXPIRED`.
  - `routers/banks.py` & `routers/inventory.py`.
- **Frontend Responsibilities**:
  - `pages/inventory/InventoryDashboard.tsx`: Interactive cold storage visualizer with color-coded shelf-life (Green > Amber > Red).
  - `pages/inventory/BankList.tsx`: Manage blood bank centers.
  - `pages/inventory/ExpirySweepAction.tsx`: One-click batch expiry sweeper button.
- **Unit & Integration Tests**:
  - `tests/test_compatibility.py`: Full ABO/Rh matrix test suite.
  - `tests/test_unit_sequential_id.py`: Per-bank composite key generation under race conditions.

#### Person 3: Hospitals, Recipients, Requests & Frontend Shell
- **Git Branch**: `feat/p3-requests-ui`
- **Frontend Shell Responsibilities**:
  - React + Vite + TypeScript + Tailwind CSS configuration.
  - `components/layout/AppLayout.tsx`: Responsive navigation sidebar, top bar with user profile.
  - `components/common/DataTable.tsx`: Reusable sorting, pagination, search input.
  - `components/common/StatusBadge.tsx`: Color-coded badges for urgency, unit status, request status.
  - `components/common/Modal.tsx`: Accessible dialog wrapper.
  - `api/client.ts`: Axios client configured with JWT interceptors.
- **Backend Responsibilities**:
  - `models/hospital.py`, `models/recipient.py`, `models/request.py`.
  - `schemas/hospital.py`, `schemas/recipient.py`, `schemas/request.py`.
  - `repositories/request_repo.py`: Filtering by urgency (`EMERGENCY` first), status, hospital.
  - `services/request_service.py`: Request creation with compatibility check against recipient group; status recomputations.
  - `routers/hospitals.py`, `routers/recipients.py`, `routers/requests.py`.
- **Frontend Responsibilities**:
  - `pages/requests/RequestQueue.tsx`: Urgency-triage board (EMERGENCY glowing crimson, URGENT amber, ROUTINE blue).
  - `pages/requests/NewRequestModal.tsx`: Form with linked hospital and recipient selector.
  - `pages/recipients/RecipientList.tsx`: Patient master roster.
- **Unit & Integration Tests**:
  - `tests/test_request_validation.py`: Reject invalid blood component requests.
  - `tests/test_request_status_transitions.py`: Verify transition from `PENDING` -> `PARTIALLY_FULFILLED` -> `FULFILLED`.

#### Person 4: Issues, Reports, Auth & QA Automation
- **Git Branch**: `feat/p4-issues-reports-auth`
- **Auth & Security Responsibilities**:
  - `models/user.py`, `schemas/auth.py`, `core/security.py`: Password hashing (bcrypt), JWT generation/validation.
  - `routers/auth.py`: `/login`, `/me`, and `/demo-login/{role}`.
  - `pages/auth/LoginPage.tsx`: Sleek login page with 4 instant "1-Click Quick Login" buttons.
- **Fulfillment & Reporting Responsibilities**:
  - `models/issue.py`, `schemas/issue.py`.
  - `repositories/issue_repo.py`: Issue creation, audit logs.
  - `services/issue_service.py`: Automated FEFO allocation using `SELECT ... FOR UPDATE SKIP LOCKED`, manual unit issue with compatibility validation.
  - `services/report_service.py`: Aggregations for blood stock distribution, expiring units, fulfillment rates.
  - `routers/issues.py` & `routers/reports.py`.
- **Frontend Responsibilities**:
  - `pages/issues/IssueLog.tsx`: Full audit log of all issued units.
  - `pages/issues/FulfillRequestModal.tsx`: Displays FEFO recommended units with 1-click allocation.
  - `pages/dashboard/ExecutiveDashboard.tsx`: Metric cards, stock charts, urgency alerts.
- **Testing & QA Responsibilities**:
  - `tests/test_concurrency_fefo.py`: Simulates 2 concurrent requests competing for the last blood unit.
  - `tests/test_end_to_end_flow.py`: Full lifecycle test (Donor -> Unit -> Request -> Issue).

---

## 5. Formal Integration Contracts Between Members

To ensure all 4 team members can develop concurrently without blocking each other, these Python function signatures and schemas are frozen on Day 1:

| Provider | Signature / Interface | Consumer | Purpose |
|---|---|---|---|
| **P2** | `async def create_unit(db, bank_id: int, donor_id: int, volume_ml: int, blood_group: BloodGroup, component_type: ComponentType, donation_date: date) -> BloodUnit` | **P1** | Called by `donation_service` to generate a new `BloodUnit` with sequential `unit_id` and correct expiry. |
| **P2** | `async def find_compatible_units(db, recipient_group: BloodGroup, component: ComponentType, limit: int, lock: bool = True) -> list[BloodUnit]` | **P4** | Called by `issue_service` to query FEFO compatible units with `SKIP LOCKED`. |
| **P2** | `def get_compatible_donor_groups(recipient_group: BloodGroup, component: ComponentType) -> list[BloodGroup]` | **P3, P4** | Returns list of compatible donor groups from `core/compatibility.py`. |
| **P3** | `async def recompute_request_status(db, request_id: int) -> RequestStatus` | **P4** | Called after issue insertion to synchronize request status. |
| **P1** | `async def check_donor_eligibility(db, donor_id: int) -> tuple[bool, str, int]` | **P1, P4** | Returns `(is_eligible, reason, days_remaining)`. |
| **P4** | `def get_current_user(token: str) -> User` | **All** | FastAPI dependency for endpoint role authorization. |

---

## 6. RESTful API Specification

### 6.1 Authentication (`/api/v1/auth`)
- `POST /login`: Standard OAuth2 / JSON login returning `{ access_token, token_type, role, user }`.
- `POST /demo-login/{role}`: 1-Click login for roles: `ADMIN`, `BANK_STAFF`, `HOSPITAL_STAFF`, `DONOR`.
- `GET /me`: Returns current authenticated user and linked entity profile.

### 6.2 Donors & Donations (`/api/v1/donors`, `/api/v1/donations`)
- `GET /donors`: Filter by `blood_group`, `search` (name, phone), pagination (`skip`, `limit`).
- `POST /donors`: Create donor record.
- `GET /donors/{id}`: Detailed donor profile with complete donation history.
- `GET /donors/{id}/eligibility`: Pre-flight check (age 18-65, days since last donation).
- `POST /donations`: Record donation transaction:
  - Input: `{ donor_id, bank_id, volume_ml, component_type, donation_date }`.
  - Atomically validates eligibility, creates unit via P2, updates donor's `last_donation_date`.

### 6.3 Banks & Cold Storage Inventory (`/api/v1/banks`, `/api/v1/inventory`)
- `GET /banks`: List all blood banks with aggregated available units.
- `POST /banks`: Register new blood bank.
- `GET /banks/{id}/units`: List inventory with filters: `blood_group`, `component`, `status`, `expiring_in_days`.
- `GET /inventory/summary`: Stock matrix aggregated across banks (Group × Component).
- `POST /inventory/expire-sweep`: Batch sweep setting expired units to `EXPIRED`.
- `PATCH /inventory/units/{bank_id}/{unit_id}/discard`: Mark unit as `DISCARDED` with mandatory `reason`.

### 6.4 Hospitals, Recipients & Requests (`/api/v1/hospitals`, `/api/v1/recipients`, `/api/v1/requests`)
- `GET /hospitals`, `POST /hospitals`: Master hospital directory.
- `GET /recipients`, `POST /recipients`: Patient directory.
- `GET /requests`: Filter by `status`, `urgency`, `hospital_id`. Sorted with `EMERGENCY` priority.
- `POST /requests`: Create request: `{ hospital_id, recipient_id, blood_group, component_type, quantity, urgency, notes }`.
- `GET /requests/{id}`: Detailed request with progress bar and list of allocated issues.
- `PATCH /requests/{id}/cancel`: Cancel a pending request (prevented if any units are already issued).

### 6.5 Issues & Reports (`/api/v1/issues`, `/api/v1/reports`)
- `POST /requests/{id}/auto-fulfil`: Execute automated FEFO allocation algorithm (issues available units, updates statuses).
- `POST /issues/manual`: Manually allocate a specific unit `(bank_id, unit_id)` to a request with compatibility checks.
- `GET /issues`: Audit log of all issued units with timestamps, recipient, and hospital names.
- `GET /reports/stock-distribution`: Current units by blood group vs critical reserve threshold.
- `GET /reports/expiring-soon`: Units expiring within 7 and 14 days.
- `GET /reports/fulfillment-metrics`: Turnaround times and fulfillment percentages by urgency level.

---

## 7. Frontend Architecture & Design System

### 7.1 Tech Stack & Directory Structure
```
frontend/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── src/
│   ├── api/
│   │   ├── client.ts             # Axios instance + JWT interceptor
│   │   ├── auth.ts
│   │   ├── donors.ts
│   │   ├── inventory.ts
│   │   ├── requests.ts
│   │   └── issues.ts
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Navbar.tsx
│   │   │   └── Sidebar.tsx
│   │   └── common/
│   │       ├── DataTable.tsx
│   │       ├── Modal.tsx
│   │       ├── StatusBadge.tsx
│   │       └── StatCard.tsx
│   ├── pages/
│   │   ├── auth/LoginPage.tsx
│   │   ├── dashboard/DashboardPage.tsx
│   │   ├── donors/DonorListPage.tsx
│   │   ├── inventory/InventoryPage.tsx
│   │   ├── requests/RequestListPage.tsx
│   │   └── issues/IssueListPage.tsx
│   ├── types/
│   │   └── index.ts              # TypeScript interfaces mirroring Pydantic schemas
│   ├── App.tsx
│   └── main.tsx
```

### 7.2 Medical Visual Language
- **Color Palette**:
  - Slate Background: `#0f172a` (Dark mode) / `#f8fafc` (Light mode)
  - Crimson Blood Accent: `#e11d48`
  - Emerald Available Stock: `#10b981`
  - Amber Warning / Urgent: `#f59e0b`
  - Ruby Emergency: `#ef4444`
- **Typography**: Inter / Outfit for ultra-crisp tabular numbers and clinical readability.
- **Visual Features**:
  - Live pulse animation on `EMERGENCY` request badges.
  - Expiry shelf-life progress bars on cold storage inventory cards.
  - 1-Click login buttons on the login screen for rapid professor presentation.

---

## 8. Step-by-Step Implementation Roadmap

```
                                IMPLEMENTATION PHASES
+-----------------------------------------------------------------------------------+
| PHASE 1: DB Foundation, MySQL Setup & Repository Scaffolding (Day 1 - 2)          |
| - Verify local MySQL 8.0 instance and create database `bloodbank_db`.             |
| - Execute `db/schema.sql` (Tables, Foreign Keys, Checks, Triggers, Views).        |
| - Build `db/seed.py` with Faker to populate 10 banks, 20 hospitals, 50 donors,   |
|   150 blood units with realistic dates.                                           |
| - Configure Python venv with FastAPI, SQLAlchemy 2.0, aiomysql, Pydantic v2.      |
| - Initialize React + Vite + TypeScript + Tailwind CSS shell.                      |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| PHASE 2: Core Framework & Integration Stubs (Day 3 - 4)                           |
| - Implement `core/database.py`, `core/config.py`, `core/errors.py`, `core/enums.py`|
| - Implement `core/compatibility.py` (ABO/Rh 64-pair matrix).                      |
| - Create stub functions for all Section 5 contracts so teammates can code in      |
|   parallel without missing dependencies.                                          |
| - Set up `api/client.ts` and common UI layout (Sidebar, Navbar, DataTable).       |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| PHASE 3: Domain Slices Implementation (Day 5 - 10)                                |
| - Person 1: Donor registry, eligibility checker, donation transaction engine.     |
| - Person 2: Blood bank management, cold storage grid, expiry sweep worker.        |
| - Person 3: Hospital & recipient management, emergency request triage queue.      |
| - Person 4: FEFO allocation engine, issue audit logging, analytics reports.       |
| - Person 4 (Security): JWT Auth + 1-Click Quick Login interface.                  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| PHASE 4: Integration, Testing & Concurrency Verification (Day 11 - 13)            |
| - Connect frontend UI views to backend REST endpoints.                            |
| - Run pytest test suite:                                                          |
|   - Donor age / 90-day cooldown eligibility tests.                                |
|   - Concurrency test: 2 simultaneous requests for the last blood unit.            |
|   - Expiry test: verify expired units cannot be allocated.                        |
|   - Rollback test: verify donation failures roll back unit creation cleanly.      |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| PHASE 5: Demo Polish & Academic DBMS Deliverables (Day 14 - 15)                   |
| - Polish UI micro-interactions, responsive views, and quick-login workflow.       |
| - Generate Academic DBMS Documentation:                                           |
|   - ER Diagram to Relational Schema Mapping Document.                             |
|   - Normalization proofs to 3NF / BCNF.                                           |
|   - 10 Advanced SQL Analytical Queries (Joins, Aggregates, Window Functions).     |
| - Package optional `docker-compose.yml` for 1-command evaluator launch.           |
+-----------------------------------------------------------------------------------+
```

---

## 9. Comprehensive Testing Strategy

### 9.1 Pytest Automated Suite
- `test_donor_eligibility`:
  - Donor age < 18 -> Rejected.
  - Donor age > 65 -> Rejected.
  - `last_donation_date` within 90 days -> Rejected with remaining days calculation.
  - First-time donor -> Eligible.
- `test_inventory_concurrency`:
  - 10 parallel asynchronous tasks requesting the same blood bag.
  - Assert exactly 1 task succeeds; 9 tasks gracefully receive stock exhausted or next compatible unit without deadlocks.
- `test_fefo_ordering`:
  - Seed 3 compatible units with expiry dates in +2 days, +10 days, and +20 days.
  - Assert automated allocation selects the +2 days unit first.
- `test_compatibility_rules`:
  - O- recipient requests RBC -> Only O- allocated.
  - AB+ recipient requests RBC -> O-, A-, B-, AB+, etc. can be allocated.
  - O- recipient requests Plasma -> AB+ or any group can be allocated.

---

## 10. Academic DBMS Evaluation Queries (For Lab Viva / Presentation)

These 5 ready-to-run queries demonstrate complex relational operations for the course evaluation:

```sql
-- Query 1: Critical Stock Alert (Groups with < 5 available units per bank)
SELECT 
    b.name AS bank_name,
    u.blood_group,
    u.component_type,
    COUNT(u.unit_id) AS current_stock
FROM blood_unit u
JOIN blood_bank b ON u.bank_id = b.bank_id
WHERE u.status = 'AVAILABLE' AND u.expiry_date >= CURRENT_DATE()
GROUP BY b.bank_id, b.name, u.blood_group, u.component_type
HAVING COUNT(u.unit_id) < 5
ORDER BY current_stock ASC;

-- Query 2: Units Expiring Within Next 7 Days (FEFO Prioritization)
SELECT 
    b.name AS bank_name,
    u.bank_id,
    u.unit_id,
    u.blood_group,
    u.component_type,
    u.expiry_date,
    DATEDIFF(u.expiry_date, CURRENT_DATE()) AS days_to_expiry
FROM blood_unit u
JOIN blood_bank b ON u.bank_id = b.bank_id
WHERE u.status = 'AVAILABLE' 
  AND u.expiry_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY u.expiry_date ASC;

-- Query 3: Hospital Emergency Demand vs Fulfillment Percentage
SELECT 
    h.name AS hospital_name,
    COUNT(r.request_id) AS total_emergency_requests,
    SUM(r.quantity) AS total_units_demanded,
    SUM(CASE WHEN r.status = 'FULFILLED' THEN r.quantity ELSE 0 END) AS total_units_fulfilled,
    ROUND((SUM(CASE WHEN r.status = 'FULFILLED' THEN r.quantity ELSE 0 END) / SUM(r.quantity)) * 100, 2) AS fulfillment_rate_pct
FROM request r
JOIN hospital h ON r.hospital_id = h.hospital_id
WHERE r.urgency = 'EMERGENCY'
GROUP BY h.hospital_id, h.name
ORDER BY total_emergency_requests DESC;

-- Query 4: Top Donors Ranked by Donation Frequency (Window Function)
SELECT 
    d.donor_id,
    d.name,
    d.blood_group,
    COUNT(u.unit_id) AS total_donations,
    MAX(u.donation_date) AS most_recent_donation,
    DENSE_RANK() OVER (ORDER BY COUNT(u.unit_id) DESC) as donor_rank
FROM donor d
JOIN blood_unit u ON d.donor_id = u.donor_id
GROUP BY d.donor_id, d.name, d.blood_group;

-- Query 5: Full Custody Audit Trail (End-to-End Tracing)
SELECT 
    i.issue_id,
    i.issue_date,
    u.bank_id,
    u.unit_id,
    u.blood_group,
    u.component_type,
    d.name AS donor_name,
    b.name AS blood_bank_name,
    rec.name AS recipient_name,
    h.name AS hospital_name,
    r.urgency
FROM issue i
JOIN blood_unit u ON i.bank_id = u.bank_id AND i.unit_id = u.unit_id
JOIN donor d ON u.donor_id = d.donor_id
JOIN blood_bank b ON u.bank_id = b.bank_id
JOIN request r ON i.request_id = r.request_id
JOIN recipient rec ON r.recipient_id = rec.recipient_id
JOIN hospital h ON r.hospital_id = h.hospital_id
ORDER BY i.issue_date DESC;
```
