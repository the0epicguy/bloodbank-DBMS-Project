"""
Recipient (patient) ORM model.

NOTE (integration): owned by Person 3. Minimal version matching
db/migrations/001 so Person 4's code can run on its own.
"""

from sqlalchemy import Column, Integer, String, Enum
from app.core.database import Base


class Recipient(Base):
    __tablename__ = "recipient"

    recipient_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    blood_group = Column(
        Enum("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", name="blood_group_recipient_enum"),
        nullable=False,
    )
