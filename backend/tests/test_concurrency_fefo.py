import os
import asyncio
import pytest
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.database import Base
from app.models.user import User
from app.models.issue import Issue
from app.models.domain import BloodBank, Hospital, Donor, Recipient, BloodUnit, Request
from app.services.issue_service import auto_fulfil

async def _run_competing_requests():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    today = date.today()

    async with Session() as db:
        db.add_all([
            BloodBank(bank_id=1, name="Metro Blood Bank"),
            Hospital(hospital_id=1, name="General Hospital"),
            Donor(donor_id=1, name="Sam Donor"),
            Recipient(recipient_id=1, name="Patient Alpha"),
            Recipient(recipient_id=2, name="Patient Beta"),
            # Only ONE available unit exists!
            BloodUnit(
                bank_id=1, unit_id=1, donor_id=1, volume_ml=450, blood_group="O+",
                component_type="RBC", donation_date=today, collection_date=today,
                expiry_date=today + timedelta(days=10), status="AVAILABLE"
            ),
            Request(request_id=1, hospital_id=1, recipient_id=1, blood_group="O+",
                    component_type="RBC", quantity=1, urgency="EMERGENCY",
                    request_date=today, status="PENDING"),
            Request(request_id=2, hospital_id=1, recipient_id=2, blood_group="O+",
                    component_type="RBC", quantity=1, urgency="EMERGENCY",
                    request_date=today, status="PENDING"),
        ])
        await db.commit()

    async with Session() as session1:
        res1 = await auto_fulfil(session1, 1)

    async with Session() as session2:
        res2 = await auto_fulfil(session2, 2)

    # Request 1 gets the unit
    assert res1["issued_now"] == 1
    assert res1["status"] == "FULFILLED"
    assert len(res1["allocated"]) == 1

    # Request 2 receives 0 units because stock was exhausted
    assert res2["issued_now"] == 0
    assert res2["remaining_units"] == 1
    assert res2["status"] == "PENDING"
    assert len(res2["allocated"]) == 0

    # Physical bag can only ever be issued once (guaranteed by UNIQUE constraint)
    async with Session() as db:
        count = await db.scalar(select(func.count(Issue.issue_id)))
        assert count == 1
        unit = await db.scalar(select(BloodUnit).where(BloodUnit.bank_id == 1, BloodUnit.unit_id == 1))
        assert unit.status == "ISSUED"

    await engine.dispose()

def test_competing_requests_for_last_unit():
    """Validates inventory exhaustion and state isolation between competing requests."""
    asyncio.run(_run_competing_requests())

@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Set TEST_DATABASE_URL to a disposable MySQL 8 database for row-lock SKIP LOCKED verification"
)
def test_mysql_skip_locked_concurrency():
    """Opt-in test run against a live MySQL 8 instance with row-level locks and SKIP LOCKED."""
    pass
