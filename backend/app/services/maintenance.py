from app.models.maintenance import MaintenanceRule
from app.services.crud import VehicleChildCRUD

crud: VehicleChildCRUD[MaintenanceRule] = VehicleChildCRUD(
    MaintenanceRule, not_found="Maintenance rule not found"
)
