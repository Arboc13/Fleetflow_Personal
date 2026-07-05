from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import admin_only, get_current_user, get_db, manager_or_admin
from app.models.user import User
from app.schemas.allocation import AllocationCreate, AllocationRead, AllocationUpdate
from app.services import allocation as svc

router = APIRouter(prefix="/allocations", tags=["allocations"])


@router.get("", response_model=list[AllocationRead])
def list_allocations(
    vehicle_id: int | None = None,
    driver_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.list_allocations(db, user, vehicle_id=vehicle_id, driver_id=driver_id)


@router.get("/{allocation_id}", response_model=AllocationRead)
def get_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.get_allocation_for_user(db, allocation_id, user)


@router.post("", response_model=AllocationRead, status_code=status.HTTP_201_CREATED)
def create_allocation(
    data: AllocationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return svc.create_allocation(db, data)


@router.patch("/{allocation_id}", response_model=AllocationRead)
def update_allocation(
    allocation_id: int,
    data: AllocationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return svc.update_allocation(db, allocation_id, data)


@router.delete("/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> None:
    svc.soft_delete_allocation(db, allocation_id)


@router.delete("/{allocation_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_allocation(
    allocation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> None:
    svc.hard_delete_allocation(db, allocation_id)
