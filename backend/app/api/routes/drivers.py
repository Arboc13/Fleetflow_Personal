from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import (
    admin_only,
    get_current_user,
    get_db,
    manager_or_admin,
)
from app.models.user import User
from app.schemas.driver import DriverCreate, DriverRead, DriverUpdate
from app.services import driver as svc

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("", response_model=list[DriverRead])
def list_drivers(
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> list[DriverRead]:
    return [svc.build_driver_read(d) for d in svc.list_drivers(db, include_deleted=include_deleted)]


@router.get("/{driver_id}", response_model=DriverRead)
def get_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> DriverRead:
    return svc.build_driver_read(svc.get_driver(db, driver_id))


@router.post("", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
def create_driver(
    data: DriverCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> DriverRead:
    return svc.build_driver_read(svc.create_driver(db, data))


@router.patch("/{driver_id}", response_model=DriverRead)
def update_driver(
    driver_id: int,
    data: DriverUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> DriverRead:
    return svc.build_driver_read(svc.update_driver(db, driver_id, data))


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> None:
    svc.soft_delete_driver(db, driver_id)


@router.delete("/{driver_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> None:
    svc.hard_delete_driver(db, driver_id)
