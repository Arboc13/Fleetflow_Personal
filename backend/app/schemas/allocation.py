import datetime as dt

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.allocation import AllocationStatus, AllocationType


def _as_utc(value: dt.datetime) -> dt.datetime:
    """Treat naive datetimes as UTC so aware/naive values compare safely."""
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


class AllocationCreate(BaseModel):
    vehicle_id: int
    driver_id: int
    start_at: dt.datetime
    end_at: dt.datetime | None = None  # None = open-ended (permanent)
    type: AllocationType

    @model_validator(mode="after")
    def check_period(self) -> "AllocationCreate":
        if self.end_at is not None and _as_utc(self.end_at) <= _as_utc(self.start_at):
            raise ValueError("end_at must be after start_at")
        return self


class AllocationUpdate(BaseModel):
    """PATCH semantics. Changing the period re-runs the overlap check."""

    start_at: dt.datetime | None = None
    end_at: dt.datetime | None = None
    type: AllocationType | None = None


class AllocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    driver_id: int
    start_at: dt.datetime
    end_at: dt.datetime | None
    type: AllocationType
    status: AllocationStatus
