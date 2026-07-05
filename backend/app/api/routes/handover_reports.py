from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import admin_only, get_current_user, get_db
from app.models.user import User
from app.schemas.handover import (
    HandoverReportCreate,
    HandoverReportRead,
    HandoverReportUpdate,
)
from app.services import handover as svc

router = APIRouter(prefix="/handover-reports", tags=["handover-reports"])


@router.get("", response_model=list[HandoverReportRead])
def list_reports(
    allocation_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.list_reports(db, user, allocation_id=allocation_id)


@router.get("/{report_id}", response_model=HandoverReportRead)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.get_report_for_user(db, report_id, user)


@router.post("", response_model=HandoverReportRead, status_code=status.HTTP_201_CREATED)
def create_report(
    data: HandoverReportCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.create_report(db, data, user)


@router.patch("/{report_id}", response_model=HandoverReportRead)
def update_report(
    report_id: int,
    data: HandoverReportUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.update_report(db, report_id, data, user)


@router.post("/{report_id}/close", response_model=HandoverReportRead)
def close_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.close_report(db, report_id, user)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    svc.soft_delete_report(db, report_id, user)


@router.delete("/{report_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> None:
    svc.hard_delete_report(db, report_id)
