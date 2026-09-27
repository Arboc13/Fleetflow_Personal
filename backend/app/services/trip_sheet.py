import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.trip_sheet import TripSheet, TripStatus
from app.models.user import Role, User
from app.schemas.trip_sheet import TripSheetClose, TripSheetCreate, TripSheetUpdate
from app.services.vehicle import get_vehicle

_CLOSED_MSG = "Closed trip sheets are immutable (rule 2.3)."


def _as_utc(value: dt.datetime) -> dt.datetime:
    """Treat naive datetimes as UTC so aware/naive values compare safely."""
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def _driver_for_user(db: Session, user: User) -> Driver:
    driver = db.scalar(select(Driver).where(Driver.user_id == user.id))
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No driver profile linked to this account.",
        )
    return driver


def _authorize(db: Session, trip: TripSheet, user: User) -> None:
    """Drivers may only touch their own trip sheets; managers/admins all."""
    if user.role == Role.driver and trip.driver_id != _driver_for_user(db, user).id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your trip sheet."
        )


def get_trip_sheet(db: Session, trip_id: int) -> TripSheet:
    trip = db.get(TripSheet, trip_id)
    if trip is None or trip.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip sheet not found")
    return trip


def get_trip_sheet_for_user(db: Session, trip_id: int, user: User) -> TripSheet:
    trip = get_trip_sheet(db, trip_id)
    _authorize(db, trip, user)
    return trip


def list_trip_sheets(
    db: Session,
    user: User,
    *,
    vehicle_id: int | None = None,
    driver_id: int | None = None,
    status_filter: TripStatus | None = None,
) -> list[TripSheet]:
    stmt = select(TripSheet).where(TripSheet.deleted_at.is_(None))
    if user.role == Role.driver:
        stmt = stmt.where(TripSheet.driver_id == _driver_for_user(db, user).id)
    elif driver_id is not None:
        stmt = stmt.where(TripSheet.driver_id == driver_id)
    if vehicle_id is not None:
        stmt = stmt.where(TripSheet.vehicle_id == vehicle_id)
    if status_filter is not None:
        stmt = stmt.where(TripSheet.status == status_filter)
    return list(db.scalars(stmt.order_by(TripSheet.id)))


def _check_start_km(start_km: int, vehicle_km: int) -> None:
    """A trip can't start below the vehicle's last known odometer reading."""
    if start_km < vehicle_km:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"start_km cannot be below the vehicle's odometer ({vehicle_km} km).",
        )


def create_trip_sheet(db: Session, data: TripSheetCreate, user: User) -> TripSheet:
    vehicle = get_vehicle(db, data.vehicle_id)  # 404 if missing
    _check_start_km(data.start_km, vehicle.current_km)

    if user.role == Role.driver:
        driver_id = _driver_for_user(db, user).id
    else:
        if data.driver_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="driver_id is required.",
            )
        if db.get(Driver, data.driver_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        driver_id = data.driver_id

    trip = TripSheet(
        vehicle_id=data.vehicle_id,
        driver_id=driver_id,
        departure_at=data.departure_at,
        start_km=data.start_km,
        purpose=data.purpose,
        status=TripStatus.draft,
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def update_trip_sheet(
    db: Session, trip_id: int, data: TripSheetUpdate, user: User
) -> TripSheet:
    trip = get_trip_sheet(db, trip_id)
    _authorize(db, trip, user)
    if trip.status == TripStatus.closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_CLOSED_MSG)

    changes = data.model_dump(exclude_unset=True)
    if changes.get("start_km") is not None:
        _check_start_km(changes["start_km"], get_vehicle(db, trip.vehicle_id).current_km)
    for field, value in changes.items():
        setattr(trip, field, value)
    db.commit()
    db.refresh(trip)
    return trip


def close_trip_sheet(
    db: Session, trip_id: int, data: TripSheetClose, user: User
) -> TripSheet:
    trip = get_trip_sheet(db, trip_id)
    _authorize(db, trip, user)
    if trip.status == TripStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Trip sheet already closed."
        )
    if data.end_km <= trip.start_km:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_km must be greater than start_km.",
        )
    if _as_utc(data.arrival_at) <= _as_utc(trip.departure_at):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="arrival_at must be after departure_at.",
        )

    trip.arrival_at = data.arrival_at
    trip.end_km = data.end_km
    trip.status = TripStatus.closed

    # Closing advances the vehicle odometer (rule 2.3).
    vehicle = get_vehicle(db, trip.vehicle_id)
    if data.end_km > vehicle.current_km:
        vehicle.current_km = data.end_km

    db.commit()
    db.refresh(trip)
    return trip


def _delete_guard(trip: TripSheet) -> None:
    if trip.status == TripStatus.closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_CLOSED_MSG)


def soft_delete_trip_sheet(db: Session, trip_id: int, user: User) -> None:
    trip = get_trip_sheet(db, trip_id)
    _authorize(db, trip, user)
    _delete_guard(trip)
    trip.deleted_at = dt.datetime.now(dt.timezone.utc)
    db.commit()


def hard_delete_trip_sheet(db: Session, trip_id: int) -> None:
    trip = get_trip_sheet(db, trip_id)
    _delete_guard(trip)  # closed sheets are legal records — never deletable
    db.delete(trip)
    db.commit()
