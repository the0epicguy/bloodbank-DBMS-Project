
from sqlalchemy import (
    Column,
    Integer,
    Date,
    Enum,
    ForeignKey,
    CheckConstraint,
    text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.enums import ComponentType, Urgency, RequestStatus


class Request(Base):
    __tablename__ = "request"

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_request_quantity"),
    )

    request_id = Column(Integer, primary_key=True, autoincrement=True)

    hospital_id = Column(
        Integer,
        ForeignKey("hospital.hospital_id"),
        nullable=False,
    )
    recipient_id = Column(
        Integer,
        ForeignKey("recipient.recipient_id"),
        nullable=False,
    )

    component_type = Column(
        Enum(
            ComponentType,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            name="component_type",
        ),
        nullable=False,
    )
    quantity = Column(Integer, nullable=False)

    urgency = Column(
        Enum(
            Urgency,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            name="urgency",
        ),
        nullable=False,
        server_default="ROUTINE",
    )

    request_date = Column(
        Date,
        nullable=False,
        server_default=text("CURRENT_DATE"),
    )

    status = Column(
        Enum(
            RequestStatus,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
            name="request_status",
        ),
        nullable=False,
        server_default="PENDING",
    )

    hospital = relationship("Hospital", back_populates="requests")
    recipient = relationship("Recipient", back_populates="requests")
