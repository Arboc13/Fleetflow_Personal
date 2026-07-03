from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — register all models on Base.metadata
from app.core.deps import get_db
from app.core.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.user import Role, User


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Isolated in-memory SQLite DB per test.

    Enough for auth/RBAC/CRUD tests. Postgres-specific rules (allocation
    overlap, immutability triggers) get their own integration tests.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = testing_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_user(db: Session, email: str, password: str, role: Role) -> User:
    user = User(
        email=email,
        full_name="Test User",
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def auth_headers(client: TestClient, db_session: Session):
    """Factory: create a user of a given role and return their auth headers."""

    def _make(role: Role = Role.admin, email: str | None = None) -> dict[str, str]:
        email = email or f"{role.value}@x.com"
        make_user(db_session, email, "secret123", role)
        resp = client.post(
            "/api/auth/login", data={"username": email, "password": "secret123"}
        )
        assert resp.status_code == 200, resp.text
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    return _make
