
from sqlalchemy.orm import Session

from app.models.recipient import Recipient
from app.repositories import recipient_repo
from app.schemas.recipient import RecipientCreate, RecipientUpdate
from app.core.enums import BloodGroup
from app.core.errors import NotFound, ConflictError


def get_all_recipients(
    db: Session, skip=0, limit=100,
    blood_group: BloodGroup | None = None, search=None
):
    return recipient_repo.get_all(db, skip, limit, blood_group, search)


def get_recipient(db: Session, recipient_id: int) -> Recipient:
    recipient = recipient_repo.get_by_id(db, recipient_id)
    if not recipient:
        raise NotFound(f"Recipient with ID {recipient_id} not found")
    return recipient


def create_recipient(db: Session, data: RecipientCreate) -> Recipient:
    recipient = Recipient(**data.model_dump())
    return recipient_repo.create(db, recipient)


def update_recipient(db: Session, recipient_id: int, data: RecipientUpdate):
    recipient = get_recipient(db, recipient_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(recipient, field, value)
    return recipient_repo.update(db, recipient)


def delete_recipient(db: Session, recipient_id: int):
    recipient = get_recipient(db, recipient_id)
    if recipient.requests:
        raise ConflictError("Cannot delete a recipient that has blood requests")
    recipient_repo.delete(db, recipient)
