# Person 4 scope (from project plan)

**Person 4: Issues, Reports, Auth & QA Automation**
- Branch: `feat/p4-issues-reports-auth`
- Backend: `models/issue.py`, `models/user.py`, `schemas/issue.py`, `schemas/auth.py`, issue repository/service, report service, auth/issues/reports routers.
- Auth: bcrypt password hashing, JWT generation/validation, `/login`, `/me`, `/demo-login/{role}` for ADMIN, BANK_STAFF, HOSPITAL_STAFF, DONOR.
- Fulfillment: FEFO allocation using MySQL `SELECT ... FOR UPDATE SKIP LOCKED`; manual issue with compatibility validation.
- Reports: stock distribution, expiring-soon, fulfillment metrics.
- Frontend: login quick-login buttons, issue audit log, FEFO fulfillment workflow, executive dashboard.
- QA: concurrency test for two requests competing for the last unit and end-to-end Donor → Unit → Request → Issue lifecycle.

This implementation is a module package and expects the shared database tables and Person 1–3 contracts to be integrated for a full application.
