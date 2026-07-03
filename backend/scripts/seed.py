"""Seed the database with a first admin user.

Run (from backend/, with the DB up and migrations applied):
    python -m scripts.seed
"""
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import Role, User

DEFAULT_ADMIN_EMAIL = "admin@fleetflow.local"
DEFAULT_ADMIN_PASSWORD = "admin123"  # change after first login


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))
        if existing:
            print(f"Admin already exists: {DEFAULT_ADMIN_EMAIL}")
            return
        db.add(
            User(
                email=DEFAULT_ADMIN_EMAIL,
                full_name="Fleet Admin",
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                role=Role.admin,
            )
        )
        db.commit()
        print(
            f"Created admin user: {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
