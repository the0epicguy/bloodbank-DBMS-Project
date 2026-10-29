"""
tests/conftest.py
=================
Shared pytest fixtures.

Person 4 (QA) owns the DB-level fixtures below.
Person 2 provides the pure-logic fixtures used by test_compatibility.py
and the synchronous parts of test_unit_sequential_id.py.

To activate the DB fixtures:
  1. Create a test MySQL database: CREATE DATABASE bloodbank_test;
  2. Set TEST_DATABASE_URL in your .env:
     TEST_DATABASE_URL=mysql+aiomysql://root:<pw>@localhost:3306/bloodbank_test
  3. Remove the @pytest.mark.skip decorators in test_unit_sequential_id.py.
"""

import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy import text

# ---------------------------------------------------------------------------
# Inline test DB URL — override with env var if available
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "mysql+aiomysql://root:@localhost:3306/bloodbank_test",
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create a SQLAlchemy async engine pointed at the test database.
    All tables are created fresh for the session and dropped afterwards.
    """
    from app.core.database import Base
    # Import all models so Base.metadata is populated
    import app.models.blood_bank   # noqa: F401
    import app.models.blood_unit   # noqa: F401

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """
    Yield a fresh AsyncSession for each individual test, rolling back
    all changes after the test finishes so tests are isolated.
    """
    SessionLocal = async_sessionmaker(
        bind=test_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with SessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def sample_bank(db_session):
    """A persisted BloodBank instance for use in tests."""
    from app.repositories.inventory_repo import create_bank
    bank = await create_bank(
        db_session,
        name="Test Central Blood Bank",
        address="123 Test Lane",
        city="TestCity",
        contact="+91-9999999999",
        email="test.bank@example.com",
    )
    await db_session.flush()
    return bank


@pytest_asyncio.fixture
async def second_bank(db_session):
    """A second persisted BloodBank for bank-scoping tests."""
    from app.repositories.inventory_repo import create_bank
    bank = await create_bank(
        db_session,
        name="Test Secondary Bank",
        address="456 Another Road",
        city="TestCity",
        contact="+91-8888888888",
        email=None,
    )
    await db_session.flush()
    return bank


@pytest_asyncio.fixture
async def sample_donor(db_session):
    """
    A minimal donor row — Person 1 will expand this fixture
    once their donor model is in place.
    """
    from sqlalchemy import text
    await db_session.execute(
        text(
            "INSERT INTO donor (name, blood_group, phone, dob, gender) "
            "VALUES (:name, :bg, :phone, :dob, :gender)"
        ),
        {
            "name":  "Test Donor",
            "bg":    "O+",
            "phone": "+91-7777777777",
            "dob":   "1990-01-01",
            "gender":"MALE",
        },
    )
    await db_session.flush()
    result = await db_session.execute(
        text("SELECT donor_id FROM donor WHERE phone = '+91-7777777777'")
    )
    row = result.fetchone()

    # Return a minimal object so tests can access .donor_id
    class _FakeDonor:
        donor_id = row[0]

    return _FakeDonor()
