from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import (
    admin_only,
    get_current_user,
    get_db,
    manager_or_admin,
)
from app.models.user import User
from app.schemas.vehicle import VehicleCreate, VehicleRead, VehicleUpdate
from app.services import vehicle as svc

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleRead])
def list_vehicles(
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list:
    return svc.list_vehicles(db, include_deleted=include_deleted)


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return svc.get_vehicle(db, vehicle_id)


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    data: VehicleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return svc.create_vehicle(db, data)


@router.patch("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    db: Session = Depends(get_db),
    editor: User = Depends(manager_or_admin),
):
    return svc.update_vehicle(db, vehicle_id, data, editor_id=editor.id)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> None:
    svc.soft_delete_vehicle(db, vehicle_id)


@router.delete("/{vehicle_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> None:
    svc.hard_delete_vehicle(db, vehicle_id)
