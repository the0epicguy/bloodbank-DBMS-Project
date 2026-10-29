"""
BloodBank ORM model.

Maps to the `blood_bank` table in MySQL.
Defined here so the Donor → BloodUnit → BloodBank relationship chain works.
"""

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class BloodBank(Base):
    __tablename__ = "blood_bank"

    bank_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    contact = Column(String(20), nullable=False)

    # Relationship: one bank → many blood units
    blood_units = relationship("BloodUnit", back_populates="bank", lazy="select")

    def __repr__(self):
        return f"<BloodBank(id={self.bank_id}, name='{self.name}')>"
