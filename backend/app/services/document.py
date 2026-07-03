from app.models.document import VehicleDocument
from app.services.crud import VehicleChildCRUD

crud: VehicleChildCRUD[VehicleDocument] = VehicleChildCRUD(
    VehicleDocument, not_found="Document not found"
)
