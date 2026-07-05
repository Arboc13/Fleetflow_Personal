"""Handover reports (proces-verbal). Immutable once closed (rule 2.3)."""
import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationStatus
from app.models.driver import Driver
from app.models.handover import HandoverDirection, HandoverReport, HandoverStatus
from app.models.user import Role, User
from app.schemas.handover import HandoverReportCreate, HandoverReportUpdate
from app.services.allocation import get_allocation

_CLOSED_MSG = "Closed handover reports are immutable (rule 2.3)."


def _authorize(db: Session, allocation: Allocation, user: User) -> None:
    """Drivers may only touch reports on their own allocations."""
    if user.role != Role.driver:
        return
    driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
    if driver is None or allocation.driver_id != driver.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your allocation."
        )


def get_report(db: Session, report_id: int) -> HandoverReport:
    report = db.get(HandoverReport, report_id)
    if report is None or report.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Handover report not found"
        )
    return report


def get_report_for_user(db: Session, report_id: int, user: User) -> HandoverReport:
    report = get_report(db, report_id)
    _authorize(db, get_allocation(db, report.allocation_id, include_deleted=True), user)
    return report


def list_reports(
    db: Session, user: User, *, allocation_id: int | None = None
) -> list[HandoverReport]:
    stmt = select(HandoverReport).where(HandoverReport.deleted_at.is_(None))
    if allocation_id is not None:
        stmt = stmt.where(HandoverReport.allocation_id == allocation_id)
    if user.role == Role.driver:
        driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
        if driver is None:
            return []
        stmt = stmt.join(Allocation).where(Allocation.driver_id == driver.id)
    return list(db.scalars(stmt.order_by(HandoverReport.id)))


def create_report(db: Session, data: HandoverReportCreate, user: User) -> HandoverReport:
    allocation = get_allocation(db, data.allocation_id)  # 404 if missing/deleted
    _authorize(db, allocation, user)

    report = HandoverReport(**data.model_dump(), status=HandoverStatus.draft)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def update_report(
    db: Session, report_id: int, data: HandoverReportUpdate, user: User
) -> HandoverReport:
    report = get_report_for_user(db, report_id, user)
    if report.status == HandoverStatus.closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_CLOSED_MSG)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    db.commit()
    db.refresh(report)
    return report


def close_report(db: Session, report_id: int, user: User) -> HandoverReport:
    report = get_report_for_user(db, report_id, user)
    if report.status == HandoverStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Handover report already closed."
        )

    report.status = HandoverStatus.closed

    # Closing the *return* report ends the allocation (vehicle is back).
    if report.direction == HandoverDirection.return_:
        allocation = get_allocation(db, report.allocation_id, include_deleted=True)
        allocation.status = AllocationStatus.ended
        if allocation.end_at is None:
            allocation.end_at = dt.datetime.now(dt.timezone.utc)

    db.commit()
    db.refresh(report)
    return report


def soft_delete_report(db: Session, report_id: int, user: User) -> None:
    report = get_report_for_user(db, report_id, user)
    if report.status == HandoverStatus.closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_CLOSED_MSG)
    report.deleted_at = dt.datetime.now(dt.timezone.utc)
    db.commit()


def hard_delete_report(db: Session, report_id: int) -> None:
    report = get_report(db, report_id)
    # Closed reports are legal records — never deletable (rule 2.3).
    if report.status == HandoverStatus.closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_CLOSED_MSG)
    db.delete(report)
    db.commit()
