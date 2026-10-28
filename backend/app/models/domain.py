from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Date, DateTime, Text, Enum, ForeignKey, func
from app.core.database import Base

class BloodUnit(Base):
    __tablename__ = "blood_unit"
    bank_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    donor_id: Mapped[int] = mapped_column(Integer)
    volume_ml: Mapped[int] = mapped_column(Integer)
    blood_group: Mapped[str] = mapped_column(String(3))
    component_type: Mapped[str] = mapped_column(String(20))
    donation_date: Mapped[object] = mapped_column(Date)
    collection_date: Mapped[object] = mapped_column(Date)
    expiry_date: Mapped[object] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20))

class Request(Base):
    __tablename__ = "request"
    request_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hospital_id: Mapped[int] = mapped_column(Integer)
    recipient_id: Mapped[int] = mapped_column(Integer)
    blood_group: Mapped[str] = mapped_column(String(3))
    component_type: Mapped[str] = mapped_column(String(20))
    quantity: Mapped[int] = mapped_column(Integer)
    urgency: Mapped[str] = mapped_column(String(20))
    request_date: Mapped[object] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

class BloodBank(Base):
    __tablename__ = "blood_bank"
    bank_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))

class Donor(Base):
    __tablename__ = "donor"
    donor_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

class Recipient(Base):
    __tablename__ = "recipient"
    recipient_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

class Hospital(Base):
    __tablename__ = "hospital"
    hospital_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
