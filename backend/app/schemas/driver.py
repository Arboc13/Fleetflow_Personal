import datetime as dt
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

CNP_RE = re.compile(r"^\d{13}$")


def _validate_cnp(v: str) -> str:
    if not isinstance(v, str) or not CNP_RE.match(v.strip()):
        raise ValueError("CNP must be exactly 13 digits.")
    return v.strip()


class DriverBase(BaseModel):
    phone: str | None = Field(default=None, max_length=30)
    license_number: str = Field(min_length=1, max_length=30)
    license_series: str | None = Field(default=None, max_length=10)
    license_category: str = Field(min_length=1, max_length=20)
    license_expiry: dt.date


class DriverCreate(DriverBase):
    # Creating a driver also creates the linked login account (role=driver).
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    cnp: str

    @field_validator("cnp", mode="before")
    @classmethod
    def validate_cnp(cls, v: str) -> str:
        return _validate_cnp(v)


class DriverUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=30)
    license_number: str | None = Field(default=None, min_length=1, max_length=30)
    license_series: str | None = Field(default=None, max_length=10)
    license_category: str | None = Field(default=None, min_length=1, max_length=20)
    license_expiry: dt.date | None = None
    cnp: str | None = None

    @field_validator("cnp", mode="before")
    @classmethod
    def validate_cnp(cls, v: str | None) -> str | None:
        return None if v is None else _validate_cnp(v)


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: EmailStr
    full_name: str
    phone: str | None
    cnp_masked: str  # never the raw CNP
    license_number: str
    license_series: str | None
    license_category: str
    license_expiry: dt.date
    is_active: bool
