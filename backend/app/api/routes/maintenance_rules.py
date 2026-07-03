from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import admin_only, get_current_user, get_db, manager_or_admin
from app.models.user import User
from app.schemas.maintenance import (
    MaintenanceRuleCreate,
    MaintenanceRuleRead,
    MaintenanceRuleUpdate,
)
from app.services.maintenance import crud

router = APIRouter(prefix="/maintenance-rules", tags=["maintenance-rules"])


@router.get("", response_model=list[MaintenanceRuleRead])
def list_rules(
    vehicle_id: int | None = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.list(db, vehicle_id=vehicle_id, include_deleted=include_deleted)


@router.get("/{rule_id}", response_model=MaintenanceRuleRead)
def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.get(db, rule_id)


@router.post("", response_model=MaintenanceRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    data: MaintenanceRuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return crud.create(db, data.model_dump())


@router.patch("/{rule_id}", response_model=MaintenanceRuleRead)
def update_rule(
    rule_id: int,
    data: MaintenanceRuleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
):
    return crud.update(db, rule_id, data.model_dump(exclude_unset=True))


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(manager_or_admin),
) -> None:
    crud.soft_delete(db, rule_id)


@router.delete("/{rule_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> None:
    crud.hard_delete(db, rule_id)
