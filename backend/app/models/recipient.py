
from sqlalchemy import Column, Integer, String, Enum, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import BloodGroup


class Recipient(Base):
    __tablename__ = "recipient"

    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 120", name="ck_recipient_age"),
    )

    recipient_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    blood_group = Column(
        Enum(
            BloodGroup,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            name="blood_group",
        ),
        nullable=False,
    )

    requests = relationship("Request", back_populates="recipient")
