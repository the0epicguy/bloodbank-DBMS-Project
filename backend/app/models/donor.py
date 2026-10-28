"""
Donor ORM model.

Maps to the `donor` table in MySQL.

Columns:
    donor_id           - Auto-increment primary key
    name               - Full name of the donor
    blood_group        - ABO+Rh type (ENUM)
    phone              - Unique phone number
    dob                - Date of birth (used for age calculation)
    last_donation_date - When they last donated (NULL if never)

Relationships:
    blood_units - One donor can donate many blood units (1:N)
"""

from sqlalchemy import Column, Integer, String, Date, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.enums import BloodGroup


class Donor(Base):
    __tablename__ = "donor"

    donor_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    blood_group = Column(
        Enum(
            "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-",
            name="blood_group_enum",
        ),
        nullable=False,
    )
    phone = Column(String(15), unique=True, nullable=False)
    dob = Column(Date, nullable=False)
    last_donation_date = Column(Date, nullable=True, default=None)

    # Relationship: one donor → many blood units
    blood_units = relationship("BloodUnit", back_populates="donor", lazy="select")

    def __repr__(self):
        return f"<Donor(id={self.donor_id}, name='{self.name}', group='{self.blood_group}')>"
