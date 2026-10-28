# Blood Bank Management System

> **DBMS Project** — 4-person team implementation  
> Stack: FastAPI · MySQL 8.0 · React + Vite + TypeScript + Tailwind CSS

---

## Quick Start

### Prerequisites
- Python 3.12+
- MySQL 8.0 (active locally — `sudo service mysql start`)
- Node.js 18+

---

### 1. Database Setup

```bash
# Log into MySQL and create the database
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS bloodbank_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Apply the full schema (DDL + triggers + views)
mysql -u root -p bloodbank_db < db/schema.sql
```

---

### 2. Backend Setup (FastAPI)

```bash
cd backend

# Install python3-venv if needed
sudo apt install -y python3.12-venv

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env — set MYSQL_PASSWORD to your local root password

# Run the API server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

### 3. Frontend Setup (React + Vite + Tailwind)

```bash
cd frontend

# Install Node dependencies
npm install

# Start dev server
npm run dev
```

Frontend available at: http://localhost:5173

---

### 4. Running Tests

```bash
cd backend
source venv/bin/activate

# Run compatibility tests (no DB needed)
pytest tests/test_compatibility.py tests/test_unit_sequential_id.py -v

# Run all tests (requires MySQL test DB)
# Create: mysql -u root -p -e "CREATE DATABASE bloodbank_test;"
pytest -v
```

---

## Project Structure

```
bloodbank/
├── .env.example              # Environment variable template
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── core/             # Config, DB, enums, errors, compatibility
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── repositories/     # DB access layer
│   │   ├── services/         # Business logic
│   │   └── routers/          # FastAPI route handlers
│   ├── tests/                # pytest test suite
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/              # Axios API client + per-module functions
        ├── pages/            # React page components
        │   └── inventory/    # P2: InventoryDashboard, BankList, ExpirySweepAction
        └── types/index.ts    # Shared TypeScript interfaces
```

---

## Team Module Ownership

| Person | Branch | Owns |
|---|---|---|
| **P1** | `feat/p1-donors-db` | Donor CRUD, Donation workflow, DB schema + seed |
| **P2** | `feat/p2-inventory-core` | Blood Banks, Inventory, Backend core + compatibility |
| **P3** | `feat/p3-requests-ui` | Hospitals, Recipients, Requests, Frontend shell |
| **P4** | `feat/p4-issues-reports-auth` | Issues, Reports, JWT Auth, QA tests |

---

## Key API Endpoints (Person 2)

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/v1/banks` | List all blood banks with live stock count |
| `POST` | `/api/v1/banks` | Register new blood bank |
| `PUT` | `/api/v1/banks/{id}` | Update bank details |
| `DELETE` | `/api/v1/banks/{id}` | Delete blood bank |
| `GET` | `/api/v1/inventory/banks/{id}/units` | List units with FEFO filters |
| `GET` | `/api/v1/inventory/summary` | Global Blood Group × Component matrix |
| `POST` | `/api/v1/inventory/expire-sweep` | Batch expiry sweep |
| `PATCH` | `/api/v1/inventory/units/{bank_id}/{unit_id}/discard` | Discard unit |
