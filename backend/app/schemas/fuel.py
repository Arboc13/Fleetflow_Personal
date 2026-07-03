import datetime as dt

from pydantic import BaseModel, ConfigDict

from app.models.fuel import ImportStatus


class ImportBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: ImportStatus
    total_rows: int
    imported_rows: int
    rejected_rows: int
    error_report: list | dict | None
    created_at: dt.datetime


class FuelTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    occurred_at: dt.datetime
    liters: float
    price: float | None
    odometer_reported: int | None
    station: str | None
    import_batch_id: int | None
    is_suspect: bool
    suspect_reason: str | None
