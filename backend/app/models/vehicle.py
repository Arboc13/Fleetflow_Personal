import enum

from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin


class FuelType(str, enum.Enum):
    petrol = "petrol"
    diesel = "diesel"
    electric = "electric"
    hybrid = "hybrid"
    lpg = "lpg"


class VehicleStatus(str, enum.Enum):
    active = "active"
    in_service = "in_service"
    unavailable = "unavailable"


class Vehicle(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("current_km >= 0", name="ck_vehicle_km_nonneg"),
        CheckConstraint("tank_capacity_l > 0", name="ck_vehicle_tank_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plate: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    vin: Mapped[str] = mapped_column(String(17), unique=True, index=True, nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_type: Mapped[FuelType] = mapped_column(
        SAEnum(FuelType, name="fuel_type"), nullable=False
    )
    current_km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(VehicleStatus, name="vehicle_status"),
        nullable=False,
        default=VehicleStatus.active,
    )
    # Both needed by the fuel-import parser (F-402).
    tank_capacity_l: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_card_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Vehicle {self.id} {self.plate}>"
