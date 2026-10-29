"""
models/blood_bank.py
====================
SQLAlchemy ORM model for the `blood_bank` table.
Person 2 owns this model.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
