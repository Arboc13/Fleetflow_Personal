# Import all models here so Alembic autogenerate and Base.metadata see them.
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.driver import Driver
from app.models.user import Role, User
from app.models.vehicle import FuelType, Vehicle, VehicleStatus

__all__ = [
    "AuditLog",
    "Base",
    "Driver",
    "FuelType",
    "Role",
    "User",
    "Vehicle",
    "VehicleStatus",
]
