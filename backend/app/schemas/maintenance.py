import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class MaintenanceRuleBase(BaseModel):
    name: str = Field(default="Service", min_length=1, max_length=100)
    interval_km: int = Field(gt=0)
    interval_months: int = Field(gt=0)
    last_service_km: int = Field(ge=0)
    last_service_date: dt.date


class MaintenanceRuleCreate(MaintenanceRuleBase):
    vehicle_id: int


class MaintenanceRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    interval_km: int | None = Field(default=None, gt=0)
    interval_months: int | None = Field(default=None, gt=0)
    last_service_km: int | None = Field(default=None, ge=0)
    last_service_date: dt.date | None = None


class MaintenanceRuleRead(MaintenanceRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
