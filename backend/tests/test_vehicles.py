from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import Role

VALID = {
    "plate": "B-123-ABC",
    "vin": "WVWZZZ1JZXW000001",
    "make": "VW",
    "model": "Golf",
    "year": 2020,
    "fuel_type": "diesel",
    "tank_capacity_l": 55,
    "current_km": 10000,
}


def test_create_and_list_vehicle(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.fleet_manager)
    resp = client.post("/api/vehicles", json=VALID, headers=hdr)
    assert resp.status_code == 201, resp.text
    assert resp.json()["plate"] == "B-123-ABC"

    lst = client.get("/api/vehicles", headers=hdr)
    assert lst.status_code == 200
    assert len(lst.json()) == 1


def test_future_year_rejected(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    assert client.post("/api/vehicles", json={**VALID, "year": 2099}, headers=hdr).status_code == 422


def test_plate_normalized_and_validated(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    ok = client.post("/api/vehicles", json={**VALID, "plate": "cj-99-xyz"}, headers=hdr)
    assert ok.status_code == 201
    assert ok.json()["plate"] == "CJ-99-XYZ"  # upper-cased

    bad = client.post("/api/vehicles", json={**VALID, "plate": "123-ABC"}, headers=hdr)
    assert bad.status_code == 422


def test_invalid_vin_rejected(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    bad = client.post("/api/vehicles", json={**VALID, "vin": "SHORTVIN"}, headers=hdr)
    assert bad.status_code == 422


def test_duplicate_plate_conflict(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    client.post("/api/vehicles", json=VALID, headers=hdr)
    dup = client.post(
        "/api/vehicles", json={**VALID, "vin": "WVWZZZ1JZXW000002"}, headers=hdr
    )
    assert dup.status_code == 409


def test_driver_cannot_create_vehicle(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.driver)
    resp = client.post("/api/vehicles", json=VALID, headers=hdr)
    assert resp.status_code == 403


def test_odometer_edit_is_audited(
    client: TestClient, auth_headers, db_session: Session
) -> None:
    hdr = auth_headers(Role.fleet_manager)
    vid = client.post("/api/vehicles", json=VALID, headers=hdr).json()["id"]

    resp = client.patch(
        f"/api/vehicles/{vid}", json={"current_km": 12345}, headers=hdr
    )
    assert resp.status_code == 200
    assert resp.json()["current_km"] == 12345

    logs = db_session.scalars(
        select(AuditLog).where(AuditLog.entity == "vehicle")
    ).all()
    assert len(logs) == 1
    assert logs[0].field == "current_km"
    assert logs[0].old_value == "10000"
    assert logs[0].new_value == "12345"


def test_soft_delete_hides_vehicle(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.fleet_manager)
    vid = client.post("/api/vehicles", json=VALID, headers=hdr).json()["id"]

    assert client.delete(f"/api/vehicles/{vid}", headers=hdr).status_code == 204
    assert client.get("/api/vehicles", headers=hdr).json() == []
    assert len(client.get("/api/vehicles?include_deleted=true", headers=hdr).json()) == 1


def test_only_admin_hard_deletes(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    manager = auth_headers(Role.fleet_manager)
    vid = client.post("/api/vehicles", json=VALID, headers=admin).json()["id"]

    assert client.delete(f"/api/vehicles/{vid}/permanent", headers=manager).status_code == 403
    assert client.delete(f"/api/vehicles/{vid}/permanent", headers=admin).status_code == 204
