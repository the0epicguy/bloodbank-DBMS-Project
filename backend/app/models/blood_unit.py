"""
models/blood_unit.py
====================
SQLAlchemy ORM model for the `blood_unit` table.

This is a WEAK ENTITY: its primary key is the composite (bank_id, unit_id),
where unit_id is a per-bank sequential integer managed by unit_service.create_unit().

Person 2 owns this model.
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import BloodGroup, ComponentType, UnitStatus


class BloodUnit(Base):
    __tablename__ = "blood_unit"

    # Composite primary key (bank_id, unit_id) — weak entity identity
    bank_id:        Mapped[int]    = mapped_column(
        Integer,
        ForeignKey("blood_bank.bank_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    unit_id:        Mapped[int]    = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        comment="Per-bank sequential counter assigned by unit_service",
    )

    # FK to Donor — the 'donates' relationship attribute
    donor_id:       Mapped[int]    = mapped_column(
        Integer,
        ForeignKey("donor.donor_id", ondelete="RESTRICT"),
        nullable=False,
    )

    volume_ml:      Mapped[int]    = mapped_column(Integer, nullable=False)
    blood_group:    Mapped[BloodGroup] = mapped_column(
        SAEnum(BloodGroup, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    component_type: Mapped[ComponentType] = mapped_column(
        SAEnum(ComponentType, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    donation_date:  Mapped[date]   = mapped_column(Date, nullable=False)
    collection_date:Mapped[date]   = mapped_column(Date, nullable=False)
    expiry_date:    Mapped[date]   = mapped_column(Date, nullable=False)
    status:         Mapped[UnitStatus] = mapped_column(
        SAEnum(UnitStatus, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=UnitStatus.AVAILABLE,
        server_default=UnitStatus.AVAILABLE.value,
    )
    discard_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at:     Mapped[datetime]   = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Table-level constraints (mirrors DDL)
    __table_args__ = (
        CheckConstraint("volume_ml BETWEEN 50 AND 600", name="chk_unit_volume"),
        CheckConstraint("expiry_date > collection_date",  name="chk_unit_expiry"),
        UniqueConstraint("bank_id", "unit_id", name="uq_blood_unit_pk"),  # explicit for clarity
    )

    # Relationships
    bank:  Mapped["BloodBank"] = relationship(  # noqa: F821
        "BloodBank", back_populates="units", lazy="select"
    )
    donor: Mapped["Donor"] = relationship(  # noqa: F821
        "Donor", back_populates="blood_units", lazy="select"
    )
