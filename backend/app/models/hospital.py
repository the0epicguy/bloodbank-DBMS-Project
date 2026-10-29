
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Hospital(Base):
    __tablename__ = "hospital"

    hospital_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    contact = Column(String(20), nullable=False)

    requests = relationship("Request", back_populates="hospital")
