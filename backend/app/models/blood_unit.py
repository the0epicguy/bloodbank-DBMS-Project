"""
BloodUnit ORM model.

Maps to the `blood_unit` table in MySQL.
This is a WEAK ENTITY — identified by composite PK (bank_id, unit_id).

Defined here so relationships from Donor and BloodBank resolve correctly.
Person 2 will expand this model with service logic.
"""

from sqlalchemy import Column, Integer, String, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class BloodUnit(Base):
    __tablename__ = "blood_unit"

    bank_id = Column(
        Integer, ForeignKey("blood_bank.bank_id", ondelete="CASCADE"),
        primary_key=True,
    )
    unit_id = Column(Integer, primary_key=True)
    donor_id = Column(Integer, ForeignKey("donor.donor_id"), nullable=False)
    volume_ml = Column(Integer, nullable=False)
    donation_date = Column(Date, nullable=False)
    blood_group = Column(
        Enum(
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-",
            name="blood_group_unit_enum",
        ),
        nullable=False,
    )
    component_type = Column(
        Enum("WHOLE_BLOOD", "RBC", "PLATELETS", "PLASMA", name="component_enum"),
        nullable=False,
    )
    collection_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(
        Enum(
            "AVAILABLE", "RESERVED", "ISSUED", "EXPIRED", "DISCARDED",
            name="status_enum",
        ),
        nullable=False,
        default="AVAILABLE",
    )

    # Relationships
    donor = relationship("Donor", back_populates="blood_units", lazy="select")
    bank = relationship("BloodBank", back_populates="blood_units", lazy="select")

    def __repr__(self):
        return f"<BloodUnit(bank={self.bank_id}, unit={self.unit_id}, group='{self.blood_group}')>"
