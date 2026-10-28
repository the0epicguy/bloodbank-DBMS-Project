# Blood Bank Management System — Person 4 Implementation

Person 4 owns **Issues, Reports, Authentication, and QA Automation** as described in `BloodBank_Implementation_Plan.md`.

## Included
- FastAPI JWT authentication, bcrypt password hashing, `/login`, `/me`, and four demo-login roles.
- Role-aware route dependencies.
- Issue allocation service with FEFO ordering, transaction boundaries, unit compatibility checks, and `SELECT ... FOR UPDATE SKIP LOCKED` on MySQL 8.
- Issue audit log API.
- Stock distribution, expiring-soon, and fulfillment-metrics report APIs.
- React + TypeScript starter pages for login, issue log, FEFO fulfillment, and dashboard.
- Pytest tests for compatibility/FEFO behavior and auth routes, plus a concurrency integration test template.

## Requirements
- Python 3.12+
- MySQL 8.0+ (for row-locking allocation behavior)
- Node.js 20+ (frontend)
- Person 1/2/3 modules integrated for the complete project. This package contains adapters and assumes the shared tables in the project plan (`user_account`, `blood_unit`, `request`, `issue`, `blood_bank`, `donor`, `recipient`, `hospital`).

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows; on macOS/Linux use: cp .env.example .env
uvicorn app.main:app --reload
```
Configure `DATABASE_URL` and `JWT_SECRET` in `.env`. `DATABASE_URL` uses SQLAlchemy async syntax, e.g. `mysql+aiomysql://user:password@localhost:3306/bloodbank_db`.

Interactive API docs: http://127.0.0.1:8000/docs

## Run tests
```bash
pytest -q
```
The unit tests run without MySQL. The MySQL concurrency test is skipped unless `TEST_DATABASE_URL` is set to a disposable MySQL 8 database.

## Run frontend
```bash
cd frontend
npm install
npm run dev
```
Set `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1` in `frontend/.env.local` if needed.

## Demo logins
The backend creates demo users only when `SEED_DEMO_USERS=true`. Set a strong `JWT_SECRET` and enable demo users only for local classroom demos. Demo accounts are not suitable for production.

## Integration notes
- Request status recomputation is implemented locally in `issue_service.py`; coordinate with Person 3's `recompute_request_status(db, request_id)` contract if their module is available.
- Inventory compatibility is provided in `app/core/compatibility.py` as a standalone fallback. Replace/import Person 2's shared compatibility function at integration time to avoid duplicate rule sources.
- The `Issue` table enforces one issue per physical blood unit. Never delete issue audit records to “undo” an issue; use a documented correction workflow.
- This is an educational project scaffold, not clinical decision support. Real transfusion decisions require validated institutional rules and qualified professionals.
