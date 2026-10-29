"""
models/blood_bank.py
SQLAlchemy ORM model for the `blood_bank` table.
Person 2 owns this model.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

BloodBank ORM model.

Maps to the `blood_bank` table in MySQL.
Defined here so the Donor → BloodUnit → BloodBank relationship chain works.
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class BloodBank(Base):
    __tablename__ = "blood_bank"

    bank_id:    Mapped[int]      = mapped_column(primary_key=True, autoincrement=True)
    name:       Mapped[str]      = mapped_column(String(120), nullable=False)
    address:    Mapped[str]      = mapped_column(Text, nullable=False)
    city:       Mapped[str]      = mapped_column(String(60), nullable=False)
    contact:    Mapped[str]      = mapped_column(String(20), nullable=False)
    email:      Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationship: one bank has many blood units
    units: Mapped[list["BloodUnit"]] = relationship(  # noqa: F821
        "BloodUnit",
        back_populates="bank",
        cascade="all, delete-orphan",
        lazy="select",
    )
    bank_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    contact = Column(String(20), nullable=False)

    # Relationship: one bank → many blood units
    blood_units = relationship("BloodUnit", back_populates="bank", lazy="select")

    def __repr__(self):
        return f"<BloodBank(id={self.bank_id}, name='{self.name}')>"
