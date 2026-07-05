from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import admin_only, get_current_user, get_db
from app.models.trip_sheet import TripStatus
from app.models.user import User
from app.schemas.trip_sheet import (
    TripSheetClose,
    TripSheetCreate,
    TripSheetRead,
    TripSheetUpdate,
)
from app.services import trip_sheet as svc
from app.services.alerts import run_alert_scan_in_background

router = APIRouter(prefix="/trip-sheets", tags=["trip-sheets"])


@router.get("", response_model=list[TripSheetRead])
def list_trip_sheets(
    vehicle_id: int | None = None,
    driver_id: int | None = None,
    status_filter: TripStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.list_trip_sheets(
        db, user, vehicle_id=vehicle_id, driver_id=driver_id, status_filter=status_filter
    )


@router.get("/{trip_id}", response_model=TripSheetRead)
def get_trip_sheet(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.get_trip_sheet_for_user(db, trip_id, user)


@router.post("", response_model=TripSheetRead, status_code=status.HTTP_201_CREATED)
def create_trip_sheet(
    data: TripSheetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.create_trip_sheet(db, data, user)


@router.patch("/{trip_id}", response_model=TripSheetRead)
def update_trip_sheet(
    trip_id: int,
    data: TripSheetUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return svc.update_trip_sheet(db, trip_id, data, user)


@router.post("/{trip_id}/close", response_model=TripSheetRead)
def close_trip_sheet(
    trip_id: int,
    data: TripSheetClose,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = svc.close_trip_sheet(db, trip_id, data, user)
    # Closing advances the odometer, which may cross a maintenance threshold.
    background_tasks.add_task(run_alert_scan_in_background)
    return trip


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def soft_delete_trip_sheet(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    svc.soft_delete_trip_sheet(db, trip_id, user)


@router.delete("/{trip_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_trip_sheet(
    trip_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> None:
    svc.hard_delete_trip_sheet(db, trip_id)
