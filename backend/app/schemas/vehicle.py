import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.vehicle import FuelType, VehicleStatus

# Romanian plate, e.g. B-123-ABC or CJ-99-XYZ
PLATE_RE = re.compile(r"^[A-Z]{1,2}-\d{2,3}-[A-Z]{3}$")
# 17-char VIN, excluding letters I, O, Q (ISO 3779)
VIN_RE = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")


class VehicleBase(BaseModel):
    plate: str
    vin: str
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1950, le=2100)
    fuel_type: FuelType
    tank_capacity_l: float = Field(gt=0)
    fuel_card_number: str | None = None
    status: VehicleStatus = VehicleStatus.active

    @field_validator("plate", mode="before")
    @classmethod
    def validate_plate(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("plate must be a string")
        v = v.strip().upper()
        if not PLATE_RE.match(v):
            raise ValueError(
                "Invalid plate. Expected format like 'B-123-ABC' or 'CJ-99-XYZ'."
            )
        return v

    @field_validator("vin", mode="before")
    @classmethod
    def validate_vin(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("vin must be a string")
        v = v.strip().upper()
        if not VIN_RE.match(v):
            raise ValueError(
                "Invalid VIN. Must be exactly 17 characters (A-Z except I/O/Q, 0-9)."
            )
        return v


class VehicleCreate(VehicleBase):
    current_km: int = Field(default=0, ge=0)


class VehicleUpdate(BaseModel):
    """All fields optional — PATCH semantics. Editing current_km is audited."""

    make: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    year: int | None = Field(default=None, ge=1950, le=2100)
    fuel_type: FuelType | None = None
    tank_capacity_l: float | None = Field(default=None, gt=0)
    fuel_card_number: str | None = None
    status: VehicleStatus | None = None
    current_km: int | None = Field(default=None, ge=0)


class VehicleRead(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    current_km: int
