from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.user import Role, User

DRIVER = {
    "email": "ion.popescu@example.com",
    "full_name": "Ion Popescu",
    "password": "drivepass1",
    "cnp": "1900101223344",
    "phone": "0722000111",
    "license_number": "123456",
    "license_category": "B",
    "license_expiry": "2030-01-01",
}


def test_create_driver_creates_login_and_masks_cnp(
    client: TestClient, auth_headers, db_session: Session
) -> None:
    hdr = auth_headers(Role.admin)
    resp = client.post("/api/drivers", json=DRIVER, headers=hdr)
    assert resp.status_code == 201, resp.text
    body = resp.json()

    # CNP is masked — raw value never appears.
    assert body["cnp_masked"] == "*********3344"
    assert "1900101223344" not in resp.text

    # A linked login user was created with role=driver.
    user = db_session.scalar(select(User).where(User.email == DRIVER["email"]))
    assert user is not None and user.role == Role.driver

    # Stored CNP is encrypted, not plaintext.
    driver = db_session.scalar(select(Driver))
    assert driver.cnp_encrypted != DRIVER["cnp"]


def test_created_driver_can_log_in(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    client.post("/api/drivers", json=DRIVER, headers=hdr)
    login = client.post(
        "/api/auth/login",
        data={"username": DRIVER["email"], "password": DRIVER["password"]},
    )
    assert login.status_code == 200


def test_invalid_cnp_rejected(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    resp = client.post("/api/drivers", json={**DRIVER, "cnp": "123"}, headers=hdr)
    assert resp.status_code == 422


def test_driver_role_cannot_list_drivers(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.driver)
    assert client.get("/api/drivers", headers=hdr).status_code == 403


def test_soft_delete_disables_login(
    client: TestClient, auth_headers, db_session: Session
) -> None:
    hdr = auth_headers(Role.admin)
    did = client.post("/api/drivers", json=DRIVER, headers=hdr).json()["id"]

    assert client.delete(f"/api/drivers/{did}", headers=hdr).status_code == 204
    # Login now blocked (inactive user).
    login = client.post(
        "/api/auth/login",
        data={"username": DRIVER["email"], "password": DRIVER["password"]},
    )
    assert login.status_code == 403
