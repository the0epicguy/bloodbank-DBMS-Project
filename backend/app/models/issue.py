"""
Issue ORM model (Person 4).

An ISSUE is the associative record linking a REQUEST to one physical
BLOOD UNIT. One row = one bag handed to a hospital.

    request (1) ----< issue >---- (1) blood_unit (bank_id, unit_id)

(bank_id, unit_id) is UNIQUE: the same bag can never be issued twice.
"""

from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, ForeignKeyConstraint, func,
)
from app.core.database import Base


class Issue(Base):
    __tablename__ = "issue"
    __table_args__ = (
        ForeignKeyConstraint(
            ["bank_id", "unit_id"],
            ["blood_unit.bank_id", "blood_unit.unit_id"],
        ),
    )

    issue_id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("request.request_id"), nullable=False)
    bank_id = Column(Integer, nullable=False)
    unit_id = Column(Integer, nullable=False)
    issue_date = Column(DateTime, nullable=False, server_default=func.now())
    quantity_issued = Column(Integer, nullable=False, default=1)
    issued_by = Column(Integer, ForeignKey("user_account.user_id"), nullable=True)

    def __repr__(self):
        return f"<Issue(id={self.issue_id}, request={self.request_id}, unit=({self.bank_id},{self.unit_id}))>"
