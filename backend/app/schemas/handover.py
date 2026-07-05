from pydantic import BaseModel, ConfigDict, Field

from app.models.handover import HandoverDirection, HandoverStatus


class HandoverReportCreate(BaseModel):
    allocation_id: int
    direction: HandoverDirection
    km: int = Field(ge=0)
    fuel_level_pct: int = Field(ge=0, le=100)
    visual_observations: str | None = None
    cleanliness: str | None = Field(default=None, max_length=50)


class HandoverReportUpdate(BaseModel):
    """Editable only while the report is in 'draft' (rule 2.3)."""

    km: int | None = Field(default=None, ge=0)
    fuel_level_pct: int | None = Field(default=None, ge=0, le=100)
    visual_observations: str | None = None
    cleanliness: str | None = Field(default=None, max_length=50)


class HandoverReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    allocation_id: int
    direction: HandoverDirection
    km: int
    fuel_level_pct: int
    visual_observations: str | None
    cleanliness: str | None
    status: HandoverStatus
