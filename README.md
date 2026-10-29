# Blood Bank Management System

A full-stack DBMS course project built by a team of 4, merged into one unified codebase.

## 👥 Team Ownership

| Person | Branch | Modules |
|--------|--------|---------|
| Om (P1) | `dev-om` | Donors, Donations, Tests |
| Advait (P2) | `dev-advait-p2` | Blood Banks, Inventory, Expiry Sweep |
| Bhoomi (P3) | `dev-bhoomi-p3` | Hospitals, Recipients, Blood Requests |
| P4 | — | Auth, Issues, Reports, Executive Dashboard |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python), SQLAlchemy (sync), PyJWT, bcrypt |
| Database | MySQL 8+ |
| Frontend | React 18 (JSX), React Router 6, Vite 5 |

---

## ⚙️ Setup

### 1. Database

```bash
# Create the database
mysql -u root -p -e "CREATE DATABASE bloodbank;"

# Apply migrations in order
mysql -u root -p bloodbank < db/migrations/001_create_tables.sql
mysql -u root -p bloodbank < db/migrations/002_person4_auth_issues.sql

# Seed sample data
mysql -u root -p bloodbank < db/seed/seed_data.sql
mysql -u root -p bloodbank < db/seed/seed_person4.sql
```

### 2. Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env → set DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, JWT_SECRET

# Run
uvicorn app.main:app --reload
# → http://localhost:8000
# → API docs: http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend

npm install
npm run dev
# → http://localhost:5173
```

---

## 🔑 Demo Logins

With the backend running and `ALLOW_DEMO_LOGIN=true` in `.env`, use the 1-click demo login on the login page:

| Role | Username | Password |
|------|----------|----------|
| Admin | demo_admin | demo1234 |
| Bank Staff | demo_bank | demo1234 |
| Hospital Staff | demo_hospital | demo1234 |
| Donor | demo_donor | demo1234 |

---

## 📡 API Endpoints

| Method | Path | Description | Owner |
|--------|------|-------------|-------|
| POST | `/auth/login` | Login | P4 |
| POST | `/auth/demo-login/{role}` | 1-click demo | P4 |
| GET | `/auth/me` | Current user | P4 |
| GET/POST | `/donors/` | List / Create donors | P1 |
| GET/PUT/DELETE | `/donors/{id}` | Donor detail | P1 |
| GET | `/donors/{id}/eligibility` | Eligibility check | P1 |
| GET | `/donors/{id}/history` | Donation history | P1 |
| POST | `/donations/` | Record donation | P1 |
| GET/POST | `/banks/` | List / Create blood banks | P2 |
| GET/PUT/DELETE | `/banks/{id}` | Bank detail | P2 |
| GET | `/inventory/summary` | Stock summary | P2 |
| GET | `/inventory/global-summary` | Global totals | P2 |
| POST | `/inventory/expiry-sweep` | Expire stale units | P2 |
| GET/POST | `/hospitals/` | List / Create hospitals | P3 |
| GET/PUT/DELETE | `/hospitals/{id}` | Hospital detail | P3 |
| GET/POST | `/recipients/` | List / Create recipients | P3 |
| GET/PUT/DELETE | `/recipients/{id}` | Recipient detail | P3 |
| GET/POST | `/requests/` | List / Create requests | P3 |
| PATCH | `/requests/{id}/cancel` | Cancel request | P3 |
| GET | `/requests/{id}/fefo-preview` | FEFO preview | P4 |
| POST | `/requests/{id}/auto-fulfil` | Auto-fulfil (FEFO) | P4 |
| GET | `/issues/` | Issue log | P4 |
| POST | `/issues/manual` | Manual issue | P4 |
| GET | `/reports/summary` | Dashboard summary | P4 |
| GET | `/reports/stock-distribution` | Stock per blood group | P4 |
| GET | `/reports/expiring-soon` | Expiring units | P4 |
| GET | `/reports/fulfillment-metrics` | Fulfillment % | P4 |

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/test_donor.py -v   # 17 tests — no DB required
```

---

## 📁 Project Structure

```
bloodbank-merged-all/
├── db/
│   ├── schema.sql
│   ├── migrations/
│   └── seed/
├── backend/
│   ├── app/
│   │   ├── core/         # config, database, enums, errors, security
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── repositories/ # DB query layer
│   │   ├── services/     # Business logic
│   │   ├── routers/      # FastAPI routers (10 routers)
│   │   └── main.py       # App entry point
│   ├── tests/
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/client.js # Unified API client
    │   ├── auth/         # AuthContext (P4)
    │   └── pages/
    │       ├── auth/     # Login (P4)
    │       ├── dashboard/# Executive Dashboard (P4)
    │       ├── donors/   # DonorList, DonorDetail (P1)
    │       ├── inventory/# BankList, InventoryDashboard, ExpirySweepAction (P2)
    │       ├── P3Manager.jsx # Hospitals, Recipients, Requests (P3)
    │       └── issues/   # IssueLog, FulfillRequestModal (P4)
    ├── package.json
    └── vite.config.js
```
