from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import Role


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: Role


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    email: str  # output: don't re-validate stored emails (e.g. seeded *.local)
    id: int
    is_active: bool
