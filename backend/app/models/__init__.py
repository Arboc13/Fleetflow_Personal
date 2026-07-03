# Import all models here so Alembic autogenerate and Base.metadata see them.
from app.models.base import Base
from app.models.user import Role, User

__all__ = ["Base", "Role", "User"]
