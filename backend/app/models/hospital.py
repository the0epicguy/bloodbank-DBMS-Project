"""
Hospital ORM model.

NOTE (integration): owned by Person 3. Included here (minimal, matching
db/migrations/001) so Person 4's issue/report code can run on its own.
If Person 3 already has models/hospital.py, keep theirs.
"""

from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class Hospital(Base):
    __tablename__ = "hospital"

    hospital_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    contact = Column(String(20), nullable=False)
