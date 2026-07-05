"""Allocations (rule 2.1: a vehicle/driver can never be double-booked).

Overlap is checked here for friendly 409 messages; the Postgres EXCLUDE
constraints (migration 0006) remain the concurrency-safe backstop, so the
IntegrityError path also maps to 409.
"""
import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.driver import Driver
from app.models.user import Role, User
from app.schemas.allocation import AllocationCreate, AllocationUpdate

_OVERLAP_MSG = "Allocation overlaps an existing one for this {what} (rule 2.1)."


def _find_conflict(
    db: Session,
    *,
    vehicle_id: int,
    driver_id: int,
    start_at: dt.datetime,
    end_at: dt.datetime | None,
    exclude_id: int | None = None,
) -> Allocation | None:
    """First non-deleted allocation whose period intersects the given one."""
    conds = [
        Allocation.deleted_at.is_(None),
        or_(Allocation.vehicle_id == vehicle_id, Allocation.driver_id == driver_id),
        or_(Allocation.end_at.is_(None), Allocation.end_at > start_at),
    ]
    if end_at is not None:
        conds.append(Allocation.start_at < end_at)
    if exclude_id is not None:
        conds.append(Allocation.id != exclude_id)
    return db.scalar(select(Allocation).where(*conds).limit(1))


def _check_overlap(
    db: Session, alloc_id: int | None, vehicle_id: int, driver_id: int,
    start_at: dt.datetime, end_at: dt.datetime | None,
) -> None:
    conflict = _find_conflict(
        db, vehicle_id=vehicle_id, driver_id=driver_id,
        start_at=start_at, end_at=end_at, exclude_id=alloc_id,
    )
    if conflict is not None:
        what = "vehicle" if conflict.vehicle_id == vehicle_id else "driver"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=_OVERLAP_MSG.format(what=what)
        )


def _commit_or_409(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_OVERLAP_MSG.format(what="vehicle or driver"),
        ) from exc


def get_allocation(db: Session, alloc_id: int, *, include_deleted: bool = False) -> Allocation:
    alloc = db.get(Allocation, alloc_id)
    if alloc is None or (alloc.deleted_at is not None and not include_deleted):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    return alloc


def _own_driver_id(db: Session, user: User) -> int:
    driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No driver profile linked to this account.",
        )
    return driver.id


def get_allocation_for_user(db: Session, alloc_id: int, user: User) -> Allocation:
    alloc = get_allocation(db, alloc_id)
    if user.role == Role.driver and alloc.driver_id != _own_driver_id(db, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your allocation.")
    return alloc


def list_allocations(
    db: Session,
    user: User,
    *,
    vehicle_id: int | None = None,
    driver_id: int | None = None,
) -> list[Allocation]:
    stmt = select(Allocation).where(Allocation.deleted_at.is_(None))
    if user.role == Role.driver:
        stmt = stmt.where(Allocation.driver_id == _own_driver_id(db, user))
    elif driver_id is not None:
        stmt = stmt.where(Allocation.driver_id == driver_id)
    if vehicle_id is not None:
        stmt = stmt.where(Allocation.vehicle_id == vehicle_id)
    return list(db.scalars(stmt.order_by(Allocation.id)))


def create_allocation(db: Session, data: AllocationCreate) -> Allocation:
    from app.services.driver import get_driver
    from app.services.vehicle import get_vehicle

    get_vehicle(db, data.vehicle_id)  # 404 if missing/deleted
    get_driver(db, data.driver_id)
    _check_overlap(db, None, data.vehicle_id, data.driver_id, data.start_at, data.end_at)

    alloc = Allocation(**data.model_dump())
    db.add(alloc)
    _commit_or_409(db)
    db.refresh(alloc)
    return alloc


def update_allocation(db: Session, alloc_id: int, data: AllocationUpdate) -> Allocation:
    alloc = get_allocation(db, alloc_id)
    changes = data.model_dump(exclude_unset=True)

    new_start = changes.get("start_at", alloc.start_at)
    new_end = changes.get("end_at", alloc.end_at)
    if new_end is not None and new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_at must be after start_at.",
        )
    if "start_at" in changes or "end_at" in changes:
        _check_overlap(db, alloc.id, alloc.vehicle_id, alloc.driver_id, new_start, new_end)

    for field, value in changes.items():
        setattr(alloc, field, value)
    _commit_or_409(db)
    db.refresh(alloc)
    return alloc


def soft_delete_allocation(db: Session, alloc_id: int) -> None:
    alloc = get_allocation(db, alloc_id)
    alloc.deleted_at = dt.datetime.now(dt.timezone.utc)
    db.commit()


def hard_delete_allocation(db: Session, alloc_id: int) -> None:
    alloc = get_allocation(db, alloc_id, include_deleted=True)
    db.delete(alloc)
    db.commit()
