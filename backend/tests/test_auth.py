from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import Role, User


def _make_user(db: Session, email: str, password: str, role: Role) -> User:
    user = User(
        email=email,
        full_name="Test User",
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    return user


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_login_and_me(client: TestClient, db_session: Session) -> None:
    _make_user(db_session, "admin@x.com", "secret123", Role.admin)

    resp = client.post(
        "/api/auth/login",
        data={"username": "admin@x.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "admin@x.com"
    assert body["role"] == "admin"


def test_login_wrong_password(client: TestClient, db_session: Session) -> None:
    _make_user(db_session, "d@x.com", "secret123", Role.driver)
    resp = client.post(
        "/api/auth/login", data={"username": "d@x.com", "password": "nope"}
    )
    assert resp.status_code == 401


def test_me_requires_token(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401
