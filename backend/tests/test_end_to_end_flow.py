import asyncio
from datetime import date, timedelta
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import HTTPException
import pytest
from app.core.database import Base
from app.models.user import User
from app.models.issue import Issue
from app.models.domain import BloodBank, Hospital, Donor, Recipient, BloodUnit, Request
from app.services.issue_service import auto_fulfil, manual_issue, get_open_requests, get_candidate_units

async def _run_full_lifecycle():
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
        # 1. Seed Master Entities
        bank = BloodBank(bank_id=1, name="Apex Regional Blood Bank")
        hospital = Hospital(hospital_id=1, name="City Trauma Center")
        donor = Donor(donor_id=1, name="Jane Doe")
        recipient = Recipient(recipient_id=1, name="John Patient")
        db.add_all([bank, hospital, donor, recipient])
        await db.commit()

        # 2. Seed Units with different expiry dates to test FEFO ordering
        # Unit 1: Expires in 3 days (Should be allocated FIRST)
        unit1 = BloodUnit(
            bank_id=1, unit_id=1, donor_id=1, volume_ml=450, blood_group="O+",
            component_type="RBC", donation_date=today - timedelta(days=20),
            collection_date=today - timedelta(days=20), expiry_date=today + timedelta(days=3),
            status="AVAILABLE"
        )
        # Unit 2: Expires in 15 days (Should be allocated SECOND)
        unit2 = BloodUnit(
            bank_id=1, unit_id=2, donor_id=1, volume_ml=450, blood_group="O+",
            component_type="RBC", donation_date=today - timedelta(days=10),
            collection_date=today - timedelta(days=10), expiry_date=today + timedelta(days=15),
            status="AVAILABLE"
        )
        # Unit 3: Universal donor O- RBC, expires in 25 days
        unit3 = BloodUnit(
            bank_id=1, unit_id=3, donor_id=1, volume_ml=450, blood_group="O-",
            component_type="RBC", donation_date=today - timedelta(days=5),
            collection_date=today - timedelta(days=5), expiry_date=today + timedelta(days=25),
            status="AVAILABLE"
        )
        # Unit 4: Expired unit (Should NEVER be allocated)
        unit4 = BloodUnit(
            bank_id=1, unit_id=4, donor_id=1, volume_ml=450, blood_group="O+",
            component_type="RBC", donation_date=today - timedelta(days=45),
            collection_date=today - timedelta(days=45), expiry_date=today - timedelta(days=1),
            status="EXPIRED"
        )
        db.add_all([unit1, unit2, unit3, unit4])
        await db.commit()

        # 3. Create Emergency Request for 2 units of O+ RBC
        req = Request(
            request_id=1, hospital_id=1, recipient_id=1, blood_group="O+",
            component_type="RBC", quantity=2, urgency="EMERGENCY",
            request_date=today, status="PENDING", notes="Critical trauma surgery"
        )
        db.add(req)
        await db.commit()

        # 4. Verify candidate units preview in FEFO order
        candidates = await get_candidate_units(db, req.request_id)
        assert len(candidates) == 3  # unit1, unit2, unit3 (unit4 is EXPIRED and excluded)
        assert candidates[0]["unit_id"] == 1  # earliest expiry first
        assert candidates[0]["days_to_expiry"] == 3

        # 5. Execute Automated FEFO Allocation
        result = await auto_fulfil(db, req.request_id)
        assert result["status"] == "FULFILLED"
        assert result["issued_now"] == 2
        assert result["remaining_units"] == 0
        assert len(result["allocated"]) == 2
        # Verify FEFO priority: unit 1 (+3 days) then unit 2 (+15 days)
        assert result["allocated"][0]["unit_id"] == 1
        assert result["allocated"][1]["unit_id"] == 2

        # 6. Verify database state
        await db.refresh(unit1)
        await db.refresh(unit2)
        await db.refresh(unit3)
        await db.refresh(req)
        assert unit1.status == "ISSUED"
        assert unit2.status == "ISSUED"
        assert unit3.status == "AVAILABLE"
        assert req.status == "FULFILLED"

        # 7. Verify subsequent auto_fulfil reports request already fulfilled
        second_run = await auto_fulfil(db, req.request_id)
        assert second_run["issued_now"] == 0
        assert second_run["remaining_units"] == 0

    await engine.dispose()

async def _run_manual_issue_validations():
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
        bank = BloodBank(bank_id=1, name="Bank A")
        hospital = Hospital(hospital_id=1, name="Hospital A")
        recipient = Recipient(recipient_id=1, name="Patient A")
        donor = Donor(donor_id=1, name="Donor A")
        db.add_all([bank, hospital, recipient, donor])
        await db.commit()

        # O- recipient request (Can only receive O-)
        req = Request(
            request_id=10, hospital_id=1, recipient_id=1, blood_group="O-",
            component_type="RBC", quantity=1, urgency="URGENT",
            request_date=today, status="PENDING"
        )
        # Unit with A+ group (Incompatible for O- recipient)
        incompat_unit = BloodUnit(
            bank_id=1, unit_id=10, donor_id=1, volume_ml=450, blood_group="A+",
            component_type="RBC", donation_date=today, collection_date=today,
            expiry_date=today + timedelta(days=30), status="AVAILABLE"
        )
        db.add_all([req, incompat_unit])
        await db.commit()

        # Attempt manual issue with incompatible blood unit -> must fail with HTTP 422
        with pytest.raises(HTTPException) as exc:
            await manual_issue(db, request_id=10, bank_id=1, unit_id=10)
        assert exc.value.status_code == 422
        assert "incompatible" in exc.value.detail.lower()

    await engine.dispose()

def test_full_lifecycle_donor_to_issue():
    """End-to-end lifecycle test: Donor -> Unit -> Request -> FEFO Issue."""
    asyncio.run(_run_full_lifecycle())

def test_manual_issue_validations():
    """Validates compatibility and rejection of incompatible groups on manual issue."""
    asyncio.run(_run_manual_issue_validations())
