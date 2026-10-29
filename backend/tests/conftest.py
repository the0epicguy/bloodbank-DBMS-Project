"""
Shared pytest fixtures for the DATABASE tests (Person 4).

These tests run against a REAL MySQL 8 database called `bloodbank_test`
(never your real `bloodbank` data). It is dropped and rebuilt from
db/migrations/001 + 002 at the start of the test run.

Connection settings come from your .env (DB_HOST, DB_USER, DB_PASSWORD ...).
Override the database name with TEST_DB_NAME. If MySQL isn't reachable the
database tests are SKIPPED (not failed), so `pytest` still works anywhere.
"""

import os
import itertools
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings  # noqa: E402

TEST_DB_NAME = os.environ.get("TEST_DB_NAME", "bloodbank_test")
MIGRATIONS = Path(__file__).resolve().parents[2] / "db" / "migrations"

TABLES = ["issue", "request", "blood_unit", "donor", "recipient",
          "hospital", "blood_bank", "user_account"]


def _server_url(db: str = "") -> str:
    return (f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
            f"@{settings.DB_HOST}:{settings.DB_PORT}/{db}")


def _split_sql(script: str) -> list[str]:
    """Split a .sql file into statements, honouring `DELIMITER //` blocks."""
    statements, delimiter, buf = [], ";", []
    for line in script.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER"):
            delimiter = stripped.split()[1]
            continue
        if not stripped or stripped.startswith("--"):
            continue
        buf.append(line)
        if stripped.endswith(delimiter):
            stmt = "\n".join(buf).rstrip()
            statements.append(stmt[: -len(delimiter)].strip())
            buf = []
    return [s for s in statements if s]


@pytest.fixture(scope="session")
def engine():
    try:
        root = create_engine(_server_url(), isolation_level="AUTOCOMMIT")
        with root.connect() as c:
            c.execute(text(f"DROP DATABASE IF EXISTS `{TEST_DB_NAME}`"))
            c.execute(text(f"CREATE DATABASE `{TEST_DB_NAME}`"))
    except Exception as exc:  # MySQL not available
        pytest.skip(f"MySQL not reachable, skipping DB tests: {exc}")

    eng = create_engine(_server_url(TEST_DB_NAME), pool_size=20, max_overflow=20,
                        pool_pre_ping=True)
    with eng.connect() as c:
        c = c.execution_options(isolation_level="AUTOCOMMIT")
        for f in sorted(MIGRATIONS.glob("*.sql")):
            sql = f.read_text()
            # the migrations are written for the `bloodbank` database
            sql = re.sub(r"CREATE DATABASE IF NOT EXISTS bloodbank;", "", sql)
            sql = re.sub(r"USE bloodbank;", "", sql)
            for stmt in _split_sql(sql):
                c.exec_driver_sql(stmt)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def SessionFactory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db(SessionFactory, engine):
    """A clean database + a session. Every test starts with empty tables."""
    with engine.connect() as c:
        c = c.execution_options(isolation_level="AUTOCOMMIT")
        c.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 0")
        for t in TABLES:
            c.exec_driver_sql(f"TRUNCATE TABLE {t}")
        c.exec_driver_sql("SET FOREIGN_KEY_CHECKS = 1")
    session = SessionFactory()
    yield session
    session.rollback()
    session.close()


# ------------------------------------------------------------ data helpers
_phone_counter = itertools.count(9100000000)


class Factory:
    """Tiny helpers to insert rows the tests need."""

    def __init__(self, db):
        self.db = db

    def _insert(self, sql, **params):
        r = self.db.execute(text(sql), params)
        self.db.commit()
        return r.lastrowid

    def bank(self, name="Test Bank"):
        return self._insert("INSERT INTO blood_bank (name,address,contact) VALUES (:n,'addr','123')", n=name)

    def hospital(self, name="Test Hospital"):
        return self._insert("INSERT INTO hospital (name,address,contact) VALUES (:n,'addr','123')", n=name)

    def donor(self, group="O-", phone=None):
        phone = phone or str(next(_phone_counter))
        return self._insert(
            "INSERT INTO donor (name,blood_group,phone,dob) VALUES ('Test Donor',:g,:p,'1990-01-01')",
            g=group, p=phone)

    def recipient(self, group="A+", name="Test Patient"):
        return self._insert(
            "INSERT INTO recipient (name,age,blood_group) VALUES (:n,40,:g)", n=name, g=group)

    def unit(self, bank_id, donor_id, group="O-", component="RBC", days_to_expiry=10,
             status="AVAILABLE", unit_id=None):
        if unit_id is None:
            unit_id = (self.db.execute(
                text("SELECT COALESCE(MAX(unit_id),0)+1 FROM blood_unit WHERE bank_id=:b"),
                {"b": bank_id}).scalar())
        today = date.today()
        collected = today - timedelta(days=5)
        expiry = today + timedelta(days=days_to_expiry)
        self.db.execute(text(
            "INSERT INTO blood_unit (bank_id,unit_id,donor_id,volume_ml,donation_date,blood_group,"
            "component_type,collection_date,expiry_date,status) VALUES "
            "(:b,:u,:d,450,:c,:g,:comp,:c,:e,:s)"),
            dict(b=bank_id, u=unit_id, d=donor_id, c=collected, g=group, comp=component,
                 e=expiry, s=status))
        self.db.commit()
        return unit_id

    def request(self, hospital_id, recipient_id, component="RBC", quantity=1,
                urgency="ROUTINE", status="PENDING"):
        return self._insert(
            "INSERT INTO request (hospital_id,recipient_id,component_type,quantity,urgency,"
            "request_date,status) VALUES (:h,:r,:c,:q,:u,CURRENT_DATE,:s)",
            h=hospital_id, r=recipient_id, c=component, q=quantity, u=urgency, s=status)

    def user(self, role="ADMIN", username=None):
        from app.core.security import hash_password
        username = username or f"user_{role.lower()}"
        return self._insert(
            "INSERT INTO user_account (username,email,password_hash,full_name,role) "
            "VALUES (:u,:e,:p,:f,:r)",
            u=username, e=f"{username}@x.com", p=hash_password("pw12345"), f=username, r=role)


@pytest.fixture()
def make(db):
    return Factory(db)


@pytest.fixture()
def world(make):
    """A small ready-made world: 1 bank, 1 hospital, 1 donor, 1 admin user."""
    class W: ...
    w = W()
    w.bank = make.bank()
    w.hospital = make.hospital()
    w.donor = make.donor("O-", phone="9000000001")
    w.admin_id = make.user("ADMIN", "admin_t")
    return w


def load_user(db, user_id):
    from app.models.user import UserAccount
    return db.query(UserAccount).filter(UserAccount.user_id == user_id).one()
