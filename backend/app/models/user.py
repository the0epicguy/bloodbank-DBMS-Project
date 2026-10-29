"""
UserAccount ORM model (Person 4 - Auth).

Maps to the `user_account` table (see db/migrations/002_person4_auth_issues.sql).

role           - ADMIN | BANK_STAFF | HOSPITAL_STAFF | DONOR
entity_ref_id  - which bank / hospital / donor this user belongs to
                 (NULL for ADMIN)
"""

from sqlalchemy import Column, Integer, String, DateTime, Enum, func
from app.core.database import Base


class UserAccount(Base):
    __tablename__ = "user_account"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(
        Enum("ADMIN", "BANK_STAFF", "HOSPITAL_STAFF", "DONOR", name="role_enum"),
        nullable=False,
    )
    entity_ref_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<UserAccount(id={self.user_id}, username='{self.username}', role='{self.role}')>"
