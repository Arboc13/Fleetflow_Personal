import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.document import DocumentType


class DocumentBase(BaseModel):
    type: DocumentType
    series_number: str = Field(min_length=1, max_length=50)
    issuer: str | None = Field(default=None, max_length=120)
    cost: float = Field(default=0, ge=0)
    issue_date: dt.date
    expiry_date: dt.date

    @model_validator(mode="after")
    def check_dates(self) -> "DocumentBase":
        if self.expiry_date <= self.issue_date:
            raise ValueError("expiry_date must be after issue_date")
        return self


class DocumentCreate(DocumentBase):
    vehicle_id: int


class DocumentUpdate(BaseModel):
    type: DocumentType | None = None
    series_number: str | None = Field(default=None, min_length=1, max_length=50)
    issuer: str | None = Field(default=None, max_length=120)
    cost: float | None = Field(default=None, ge=0)
    issue_date: dt.date | None = None
    expiry_date: dt.date | None = None


class DocumentRead(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
