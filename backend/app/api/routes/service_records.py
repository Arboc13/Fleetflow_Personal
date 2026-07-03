from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import admin_only, get_current_user, get_db, manager_or_admin
from app.models.user import User
from app.schemas.service import (
    ServiceRecordCreate,
    ServiceRecordRead,
    ServiceRecordUpdate,
)
from app.services.service_record import crud

router = APIRouter(prefix="/service-records", tags=["service-records"])


@router.get("", response_model=list[ServiceRecordRead])
def list_service_records(
    vehicle_id: int | None = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.list(db, vehicle_id=vehicle_id, include_deleted=include_deleted)


@router.get("/{record_id}", response_model=ServiceRecordRead)
def get_service_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.get(db, record_id)


@router.post("", response_model=ServiceRecordRead, status_code=status.HTTP_201_CREATED)
def create_service_record(
    data: ServiceRecordCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return crud.create(db, data.model_dump())


@router.patch("/{record_id}", response_model=ServiceRecordRead)
def update_service_record(
    record_id: int,
    data: ServiceRecordUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return crud.update(db, record_id, data.model_dump(exclude_unset=True))


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_service_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> None:
    crud.soft_delete(db, record_id)


@router.delete("/{record_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_service_record(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> None:
    crud.hard_delete(db, record_id)
