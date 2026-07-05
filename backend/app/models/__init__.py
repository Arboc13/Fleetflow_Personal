# Import all models here so Alembic autogenerate and Base.metadata see them.
from app.models.allocation import Allocation, AllocationStatus, AllocationType
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.document import DocumentType, VehicleDocument
from app.models.driver import Driver
from app.models.handover import HandoverDirection, HandoverReport, HandoverStatus
from app.models.fuel import FuelTransaction, ImportBatch, ImportStatus
from app.models.maintenance import MaintenanceRule
from app.models.notification import Notification, Severity
from app.models.service import ServiceRecord
from app.models.trip_sheet import TripSheet, TripStatus
from app.models.user import Role, User
from app.models.vehicle import FuelType, Vehicle, VehicleStatus

__all__ = [
    "Allocation",
    "AllocationStatus",
    "AllocationType",
    "AuditLog",
    "Base",
    "DocumentType",
    "Driver",
    "FuelTransaction",
    "HandoverDirection",
    "HandoverReport",
    "HandoverStatus",
    "FuelType",
    "ImportBatch",
    "ImportStatus",
    "MaintenanceRule",
    "Notification",
    "Role",
    "ServiceRecord",
    "Severity",
    "TripSheet",
    "TripStatus",
    "User",
    "Vehicle",
    "VehicleDocument",
    "VehicleStatus",
]
