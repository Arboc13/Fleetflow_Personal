import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class ServiceRecordBase(BaseModel):
    date: dt.date
    km_at_service: int = Field(ge=0)
    work_description: str = Field(min_length=1)
    parts_replaced: str | None = None
    cost: float = Field(default=0, ge=0)


class ServiceRecordCreate(ServiceRecordBase):
    vehicle_id: int


class ServiceRecordUpdate(BaseModel):
    date: dt.date | None = None
    km_at_service: int | None = Field(default=None, ge=0)
    work_description: str | None = Field(default=None, min_length=1)
    parts_replaced: str | None = None
    cost: float | None = Field(default=None, ge=0)


class ServiceRecordRead(ServiceRecordBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
