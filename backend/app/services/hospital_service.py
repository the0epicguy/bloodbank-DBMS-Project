
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.repositories import hospital_repo
from app.schemas.hospital import HospitalCreate, HospitalUpdate
from app.core.errors import NotFound, ConflictError


def get_all_hospitals(db: Session, skip=0, limit=100, search=None):
    return hospital_repo.get_all(db, skip, limit, search)


def get_hospital(db: Session, hospital_id: int) -> Hospital:
    hospital = hospital_repo.get_by_id(db, hospital_id)
    if not hospital:
        raise NotFound(f"Hospital with ID {hospital_id} not found")
    return hospital


def create_hospital(db: Session, data: HospitalCreate) -> Hospital:
    hospital = Hospital(**data.model_dump())
    return hospital_repo.create(db, hospital)


def update_hospital(db: Session, hospital_id: int, data: HospitalUpdate):
    hospital = get_hospital(db, hospital_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(hospital, field, value)
    return hospital_repo.update(db, hospital)


def delete_hospital(db: Session, hospital_id: int):
    hospital = get_hospital(db, hospital_id)
    if hospital.requests:
        raise ConflictError("Cannot delete a hospital that has blood requests")
    hospital_repo.delete(db, hospital)
