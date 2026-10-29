"""
Request ORM model (a hospital asks for blood for a recipient).

NOTE (integration): owned by Person 3. Minimal version matching
db/migrations/001 so Person 4's FEFO allocation can run on its own.
The blood group needed is the RECIPIENT's blood group.
"""

from sqlalchemy import Column, Integer, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Request(Base):
    __tablename__ = "request"

    request_id = Column(Integer, primary_key=True, autoincrement=True)
    hospital_id = Column(Integer, ForeignKey("hospital.hospital_id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("recipient.recipient_id"), nullable=False)
    component_type = Column(
        Enum("WHOLE_BLOOD", "RBC", "PLATELETS", "PLASMA", name="component_request_enum"),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)
    urgency = Column(
        Enum("ROUTINE", "URGENT", "EMERGENCY", name="urgency_enum"),
        nullable=False, default="ROUTINE",
    )
    request_date = Column(Date, nullable=False)
    status = Column(
        Enum("PENDING", "PARTIALLY_FULFILLED", "FULFILLED", "CANCELLED", name="request_status_enum"),
        nullable=False, default="PENDING",
    )

    hospital = relationship("Hospital", lazy="select")
    recipient = relationship("Recipient", lazy="select")
