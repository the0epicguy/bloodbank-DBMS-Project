# Person 4 Integration Checklist

- [ ] Confirm Person 1 ran the canonical schema and demo seed.
- [ ] Confirm Person 2 exports `find_compatible_units` / `get_compatible_donor_groups`; replace local compatibility fallback with the shared module.
- [ ] Confirm `blood_unit`, `request`, `hospital`, `recipient`, `blood_bank`, `donor`, `issue`, and `user_account` names/columns match.
- [ ] Use MySQL 8 + InnoDB to verify row locks; SQLite is only for light local development.
- [ ] Set `JWT_SECRET` from a secure random value; never commit `.env`.
- [ ] Set `SEED_DEMO_USERS=true` only for local demonstrations.
- [ ] Run `pytest -q`.
- [ ] Run two simultaneous allocation requests for one unit against a disposable MySQL database; assert the unit is issued once.
- [ ] Verify expired units and incompatible groups are rejected.
- [ ] Check role permissions for ADMIN, BANK_STAFF, HOSPITAL_STAFF, DONOR.
- [ ] Start frontend and verify login, dashboard, reports, and issue log against the running API.
