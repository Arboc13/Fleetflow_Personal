from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate
from app.services.audit import record_change


def list_vehicles(db: Session, *, include_deleted: bool = False) -> list[Vehicle]:
    stmt = select(Vehicle)
    if not include_deleted:
        stmt = stmt.where(Vehicle.deleted_at.is_(None))
    return list(db.scalars(stmt.order_by(Vehicle.id)))


def get_vehicle(db: Session, vehicle_id: int, *, include_deleted: bool = False) -> Vehicle:
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None or (vehicle.deleted_at is not None and not include_deleted):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


def create_vehicle(db: Session, data: VehicleCreate) -> Vehicle:
    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A vehicle with this plate or VIN already exists.",
        ) from exc
    db.refresh(vehicle)
    return vehicle


def update_vehicle(
    db: Session, vehicle_id: int, data: VehicleUpdate, *, editor_id: int | None
) -> Vehicle:
    vehicle = get_vehicle(db, vehicle_id)
    changes = data.model_dump(exclude_unset=True)

    # Audit manual odometer edits (NFR-1).
    if "current_km" in changes and changes["current_km"] != vehicle.current_km:
        record_change(
            db,
            entity="vehicle",
            entity_id=vehicle.id,
            field="current_km",
            old_value=vehicle.current_km,
            new_value=changes["current_km"],
            user_id=editor_id,
        )

    for field, value in changes.items():
        setattr(vehicle, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Update violates a uniqueness constraint.",
        ) from exc
    db.refresh(vehicle)
    return vehicle


def soft_delete_vehicle(db: Session, vehicle_id: int) -> None:
    """Hide a vehicle (Fleet Manager + Admin). Reversible."""
    import datetime as dt

    vehicle = get_vehicle(db, vehicle_id)
    vehicle.deleted_at = dt.datetime.now(dt.timezone.utc)
    db.commit()


def hard_delete_vehicle(db: Session, vehicle_id: int) -> None:
    """Permanently delete a vehicle (Admin only)."""
    vehicle = get_vehicle(db, vehicle_id, include_deleted=True)
    db.delete(vehicle)
    db.commit()
