# Import all models here so Alembic autogenerate and Base.metadata see them.
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.document import DocumentType, VehicleDocument
from app.models.driver import Driver
from app.models.maintenance import MaintenanceRule
from app.models.service import ServiceRecord
from app.models.user import Role, User
from app.models.vehicle import FuelType, Vehicle, VehicleStatus

__all__ = [
    "AuditLog",
    "Base",
    "DocumentType",
    "Driver",
    "FuelType",
    "MaintenanceRule",
    "Role",
    "ServiceRecord",
    "User",
    "Vehicle",
    "VehicleDocument",
    "VehicleStatus",
]
