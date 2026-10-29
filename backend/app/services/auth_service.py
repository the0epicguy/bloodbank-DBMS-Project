"""
Auth Service (Person 4) - login, demo quick-login, current-user profile.
"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFound, Unauthorized, Forbidden, ValidationFailed
from app.core.security import (
    ROLES, create_access_token, hash_password, verify_password,
)
from app.models.user import UserAccount
from app.schemas.auth import TokenResponse, UserResponse

# One ready-made account per role for the 1-click demo login.
# entity_ref_id = 1 links BANK_STAFF -> bank 1, HOSPITAL_STAFF -> hospital 1,
# DONOR -> donor 1 (these exist in db/seed/seed_data.sql).
DEMO_USERS = {
    "ADMIN": dict(
        username="demo_admin", email="admin@bloodbank.demo",
        full_name="Dr. Asha Admin", entity_ref_id=None,
    ),
    "BANK_STAFF": dict(
        username="demo_bank", email="bank@bloodbank.demo",
        full_name="Ravi Bank-Staff", entity_ref_id=1,
    ),
    "HOSPITAL_STAFF": dict(
        username="demo_hospital", email="hospital@bloodbank.demo",
        full_name="Nisha Hospital-Staff", entity_ref_id=1,
    ),
    "DONOR": dict(
        username="demo_donor", email="donor@bloodbank.demo",
        full_name="Aarav Sharma", entity_ref_id=1,
    ),
}
DEMO_PASSWORD = "demo1234"


def _token_for(user: UserAccount) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.user_id, user.role),
        role=user.role,
        user=UserResponse.model_validate(user),
    )


def login(db: Session, username: str, password: str) -> TokenResponse:
    """Check username + password and return a token."""
    user = db.query(UserAccount).filter(UserAccount.username == username).first()
    # same message for "no such user" and "wrong password" (don't leak which)
    if user is None or not verify_password(password, user.password_hash):
        raise Unauthorized("Incorrect username or password")
    return _token_for(user)


def demo_login(db: Session, role: str) -> TokenResponse:
    """
    1-click login for presentations. Creates the demo user for that role
    on first use, so nothing has to be seeded by hand.
    """
    if not settings.ALLOW_DEMO_LOGIN:
        raise Forbidden("Demo login is disabled")

    role = role.upper()
    if role not in ROLES:
        raise ValidationFailed(f"Unknown role '{role}'. Use one of: {', '.join(ROLES)}")

    info = DEMO_USERS[role]
    user = db.query(UserAccount).filter(UserAccount.username == info["username"]).first()
    if user is None:
        user = UserAccount(
            username=info["username"],
            email=info["email"],
            full_name=info["full_name"],
            role=role,
            entity_ref_id=info["entity_ref_id"],
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return _token_for(user)


def create_user(
    db: Session, username: str, email: str, password: str,
    full_name: str, role: str, entity_ref_id=None,
) -> UserAccount:
    """Create a user (used by the seed script / admin tools)."""
    if role not in ROLES:
        raise ValidationFailed(f"Unknown role '{role}'")
    user = UserAccount(
        username=username, email=email, full_name=full_name, role=role,
        entity_ref_id=entity_ref_id, password_hash=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
