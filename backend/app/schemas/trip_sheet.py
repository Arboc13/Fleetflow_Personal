import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models.trip_sheet import TripStatus


class TripSheetCreate(BaseModel):
    vehicle_id: int
    # Optional: forced to the caller's own driver profile when a driver creates it.
    driver_id: int | None = None
    departure_at: dt.datetime
    start_km: int = Field(ge=0)
    purpose: str | None = Field(default=None, max_length=255)


class TripSheetUpdate(BaseModel):
    """Editable only while the sheet is in 'draft' (rule 2.3)."""

    departure_at: dt.datetime | None = None
    start_km: int | None = Field(default=None, ge=0)
    purpose: str | None = Field(default=None, max_length=255)


class TripSheetClose(BaseModel):
    arrival_at: dt.datetime
    end_km: int = Field(ge=0)


class TripSheetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    driver_id: int
    departure_at: dt.datetime
    arrival_at: dt.datetime | None
    start_km: int
    end_km: int | None
    purpose: str | None
    status: TripStatus
