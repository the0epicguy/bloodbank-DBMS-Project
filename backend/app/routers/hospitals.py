
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.hospital import HospitalCreate, HospitalUpdate, HospitalResponse
from app.services import hospital_service

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.get("/", response_model=list[HospitalResponse])
def list_hospitals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return hospital_service.get_all_hospitals(db, skip, limit, search)


@router.post("/", response_model=HospitalResponse, status_code=201)
def create_hospital(data: HospitalCreate, db: Session = Depends(get_db)):
    return hospital_service.create_hospital(db, data)


@router.get("/{hospital_id}", response_model=HospitalResponse)
def get_hospital(hospital_id: int, db: Session = Depends(get_db)):
    return hospital_service.get_hospital(db, hospital_id)


@router.put("/{hospital_id}", response_model=HospitalResponse)
def update_hospital(
    hospital_id: int, data: HospitalUpdate, db: Session = Depends(get_db)
):
    return hospital_service.update_hospital(db, hospital_id, data)


@router.delete("/{hospital_id}", status_code=204)
def delete_hospital(hospital_id: int, db: Session = Depends(get_db)):
    hospital_service.delete_hospital(db, hospital_id)
