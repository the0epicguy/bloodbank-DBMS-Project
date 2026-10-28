from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, Text, ForeignKey, UniqueConstraint, func
from app.core.database import Base

class Issue(Base):
    __tablename__ = "issue"
    __table_args__ = (UniqueConstraint("bank_id", "unit_id", name="uq_unit_single_issue"),)
    issue_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("request.request_id", ondelete="RESTRICT"))
    bank_id: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_id: Mapped[int] = mapped_column(Integer, nullable=False)
    issue_date: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    quantity_issued: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
