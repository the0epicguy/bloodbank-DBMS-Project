from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import Base
from app.models.user import User
from app.models.issue import Issue
from app.models.domain import BloodBank, Hospital, Donor, Recipient, BloodUnit, Request
from app.core.security import hash_password

async def init_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def seed_demo_data(db: AsyncSession):
    # 1. Seed demo users
    demo_users = [
        ("demo_admin", "admin@example.test", "Demo Administrator", "ADMIN", None),
        ("demo_bank", "bank@example.test", "Demo Bank Staff", "BANK_STAFF", 1),
        ("demo_hospital", "hospital@example.test", "Demo Hospital Staff", "HOSPITAL_STAFF", 1),
        ("demo_donor", "donor@example.test", "Demo Donor", "DONOR", 1),
    ]
    for username, email, full_name, role, entity_id in demo_users:
        existing = await db.scalar(select(User).where(User.username == username))
        if not existing:
            db.add(User(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                entity_ref_id=entity_id,
                password_hash=hash_password("DemoOnly!123")
            ))

    # 2. Check if domain data exists
    bank_count = await db.scalar(select(func.count(BloodBank.bank_id))) or 0
    if bank_count == 0:
        banks = [
            BloodBank(bank_id=1, name="City Blood Centre"),
            BloodBank(bank_id=2, name="Red Cross Blood Bank"),
            BloodBank(bank_id=3, name="Lifeline Blood Bank"),
        ]
        db.add_all(banks)

        hospitals = [
            Hospital(hospital_id=1, name="Sahyadri Hospital"),
            Hospital(hospital_id=2, name="Ruby Hall Clinic"),
            Hospital(hospital_id=3, name="Jehangir Hospital"),
        ]
        db.add_all(hospitals)

        donors = [
            Donor(donor_id=1, name="Aarav Sharma"),
            Donor(donor_id=2, name="Aditya Kumar"),
            Donor(donor_id=3, name="Arjun Deshmukh"),
            Donor(donor_id=4, name="Reyansh Kulkarni"),
        ]
        db.add_all(donors)

        recipients = [
            Recipient(recipient_id=1, name="Patient Raj Kumar"),
            Recipient(recipient_id=2, name="Patient Meera Joshi"),
            Recipient(recipient_id=3, name="Patient Amit Shah"),
            Recipient(recipient_id=4, name="Patient Arun Patel"),
        ]
        db.add_all(recipients)

        today = date.today()
        units = [
            # Expiring in 2 days (FEFO should pick this first for O+/RBC)
            BloodUnit(bank_id=1, unit_id=1, donor_id=2, volume_ml=450, blood_group="O+",
                      component_type="RBC", donation_date=today - timedelta(days=30),
                      collection_date=today - timedelta(days=30), expiry_date=today + timedelta(days=2),
                      status="AVAILABLE"),
            # Expiring in 12 days
            BloodUnit(bank_id=1, unit_id=2, donor_id=2, volume_ml=450, blood_group="O+",
                      component_type="RBC", donation_date=today - timedelta(days=20),
                      collection_date=today - timedelta(days=20), expiry_date=today + timedelta(days=12),
                      status="AVAILABLE"),
            # Universal O- RBC, expiring in 5 days
            BloodUnit(bank_id=1, unit_id=3, donor_id=4, volume_ml=450, blood_group="O-",
                      component_type="RBC", donation_date=today - timedelta(days=25),
                      collection_date=today - timedelta(days=25), expiry_date=today + timedelta(days=5),
                      status="AVAILABLE"),
            # A+ RBC
            BloodUnit(bank_id=1, unit_id=4, donor_id=1, volume_ml=450, blood_group="A+",
                      component_type="RBC", donation_date=today - timedelta(days=15),
                      collection_date=today - timedelta(days=15), expiry_date=today + timedelta(days=8),
                      status="AVAILABLE"),
            # A- RBC
            BloodUnit(bank_id=1, unit_id=5, donor_id=3, volume_ml=450, blood_group="A-",
                      component_type="RBC", donation_date=today - timedelta(days=10),
                      collection_date=today - timedelta(days=10), expiry_date=today + timedelta(days=15),
                      status="AVAILABLE"),
            # B+ Whole blood
            BloodUnit(bank_id=1, unit_id=6, donor_id=2, volume_ml=450, blood_group="B+",
                      component_type="WHOLE_BLOOD", donation_date=today - timedelta(days=5),
                      collection_date=today - timedelta(days=5), expiry_date=today + timedelta(days=25),
                      status="AVAILABLE"),
            # Plasma
            BloodUnit(bank_id=1, unit_id=7, donor_id=1, volume_ml=250, blood_group="AB+",
                      component_type="PLASMA", donation_date=today - timedelta(days=30),
                      collection_date=today - timedelta(days=30), expiry_date=today + timedelta(days=200),
                      status="AVAILABLE"),
            # Past expiry unit
            BloodUnit(bank_id=1, unit_id=8, donor_id=2, volume_ml=200, blood_group="O+",
                      component_type="PLATELETS", donation_date=today - timedelta(days=10),
                      collection_date=today - timedelta(days=10), expiry_date=today - timedelta(days=2),
                      status="EXPIRED"),
            # Bank 2 units
            BloodUnit(bank_id=2, unit_id=1, donor_id=4, volume_ml=450, blood_group="O-",
                      component_type="RBC", donation_date=today - timedelta(days=8),
                      collection_date=today - timedelta(days=8), expiry_date=today + timedelta(days=20),
                      status="AVAILABLE"),
        ]
        db.add_all(units)

        requests = [
            Request(request_id=1, hospital_id=1, recipient_id=3, blood_group="O+",
                    component_type="RBC", quantity=2, urgency="EMERGENCY",
                    request_date=today, status="PENDING", notes="Accident trauma ICU patient"),
            Request(request_id=2, hospital_id=2, recipient_id=1, blood_group="A+",
                    component_type="RBC", quantity=1, urgency="URGENT",
                    request_date=today, status="PENDING", notes="Scheduled surgical procedure"),
            Request(request_id=3, hospital_id=1, recipient_id=2, blood_group="B+",
                    component_type="WHOLE_BLOOD", quantity=1, urgency="ROUTINE",
                    request_date=today, status="PENDING", notes="Pre-op reserve"),
        ]
        db.add_all(requests)

    await db.commit()
