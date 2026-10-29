"""
db_init.py
==========
Database initialization and seed utility.
Automatically ensures all tables exist and default seed data is loaded
if the database is fresh/empty (works across MySQL and SQLite).
"""

import logging
from datetime import date, timedelta
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logger = logging.getLogger("uvicorn.error")


def init_database(engine, Base):
    """
    Ensure all models are registered, tables are created,
    and seed records exist.
    """
    # Import all models so Base.metadata is complete
    import app.models.donor
    import app.models.blood_bank
    import app.models.blood_unit
    import app.models.hospital
    import app.models.recipient
    import app.models.request
    import app.models.issue
    import app.models.user

    from app.models.blood_bank import BloodBank
    from app.models.request import Request
    from app.models.user import UserAccount
    from app.core.security import hash_password
    from app.services.auth_service import DEMO_USERS, DEMO_PASSWORD

    # 1. Create tables if not present
    Base.metadata.create_all(bind=engine)

    # 2. Check if database already has seed data
    with Session(engine) as db:
        bank_count = db.query(BloodBank).count()
        if bank_count > 0:
            return  # Already seeded

        logger.info("[Database] Empty database detected. Loading seed data...")

        # 3. Load seed_data.sql
        seed_path = Path(__file__).resolve().parents[3] / "db" / "seed" / "seed_data.sql"
        if seed_path.exists():
            try:
                sql_text = seed_path.read_text(encoding="utf-8")
                stmts = [s.strip() for s in sql_text.split(";") if s.strip()]
                with engine.connect() as conn:
                    for stmt in stmts:
                        if stmt.upper().startswith("USE "):
                            continue
                        conn.execute(text(stmt))
                    conn.commit()
                logger.info("[Database] Loaded master seed data (banks, donors, hospitals, units, recipients).")
            except Exception as e:
                logger.warning(f"[Database] Could not execute seed_data.sql: {e}")

        # 4. Seed sample requests
        try:
            sample_requests = [
                Request(hospital_id=1, recipient_id=1, component_type="RBC", quantity=2, urgency="EMERGENCY", request_date=date.today(), status="PENDING"),
                Request(hospital_id=2, recipient_id=7, component_type="RBC", quantity=3, urgency="EMERGENCY", request_date=date.today(), status="PENDING"),
                Request(hospital_id=3, recipient_id=4, component_type="WHOLE_BLOOD", quantity=2, urgency="URGENT", request_date=date.today() - timedelta(days=1), status="PENDING"),
                Request(hospital_id=4, recipient_id=2, component_type="RBC", quantity=1, urgency="URGENT", request_date=date.today() - timedelta(days=1), status="PENDING"),
                Request(hospital_id=5, recipient_id=5, component_type="PLASMA", quantity=2, urgency="ROUTINE", request_date=date.today() - timedelta(days=2), status="PENDING"),
                Request(hospital_id=6, recipient_id=3, component_type="WHOLE_BLOOD", quantity=1, urgency="ROUTINE", request_date=date.today() - timedelta(days=3), status="PENDING"),
                Request(hospital_id=1, recipient_id=9, component_type="PLATELETS", quantity=2, urgency="URGENT", request_date=date.today(), status="PENDING"),
                Request(hospital_id=7, recipient_id=8, component_type="WHOLE_BLOOD", quantity=1, urgency="ROUTINE", request_date=date.today() - timedelta(days=5), status="CANCELLED"),
            ]
            db.add_all(sample_requests)

            # 5. Seed demo users
            for role, d in DEMO_USERS.items():
                existing = db.query(UserAccount).filter(UserAccount.username == d["username"]).first()
                if not existing:
                    user = UserAccount(
                        username=d["username"],
                        email=d["email"],
                        full_name=d["full_name"],
                        role=role,
                        entity_ref_id=d["entity_ref_id"],
                        password_hash=hash_password(DEMO_PASSWORD),
                    )
                    db.add(user)

            db.commit()
            logger.info("[Database] Seeded initial requests and demo user accounts.")
        except Exception as e:
            db.rollback()
            logger.warning(f"[Database] Could not seed requests or users: {e}")
