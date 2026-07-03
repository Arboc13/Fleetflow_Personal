from app.models.service import ServiceRecord
from app.services.crud import VehicleChildCRUD

crud: VehicleChildCRUD[ServiceRecord] = VehicleChildCRUD(
    ServiceRecord, not_found="Service record not found"
)
