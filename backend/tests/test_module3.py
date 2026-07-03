from fastapi.testclient import TestClient

from app.models.user import Role

VEHICLE = {
    "plate": "B-100-AAA",
    "vin": "WVWZZZ1JZXW111111",
    "make": "Dacia",
    "model": "Logan",
    "year": 2021,
    "fuel_type": "petrol",
    "tank_capacity_l": 50,
    "current_km": 20000,
}

DOCUMENT = {
    "type": "RCA",
    "series_number": "RO-12345",
    "issuer": "Allianz",
    "cost": 450.50,
    "issue_date": "2026-01-01",
    "expiry_date": "2027-01-01",
}

SERVICE = {
    "date": "2026-03-15",
    "km_at_service": 20000,
    "work_description": "Oil + filters",
    "parts_replaced": "oil filter, air filter",
    "cost": 320,
}

RULE = {
    "name": "Major service",
    "interval_km": 15000,
    "interval_months": 12,
    "last_service_km": 20000,
    "last_service_date": "2026-03-15",
}


def _new_vehicle(client: TestClient, hdr: dict) -> int:
    return client.post("/api/vehicles", json=VEHICLE, headers=hdr).json()["id"]


# --- Documents ---------------------------------------------------------------

def test_create_document(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.fleet_manager)
    vid = _new_vehicle(client, hdr)
    resp = client.post("/api/documents", json={**DOCUMENT, "vehicle_id": vid}, headers=hdr)
    assert resp.status_code == 201, resp.text
    assert resp.json()["type"] == "RCA"


def test_document_expiry_before_issue_rejected(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    vid = _new_vehicle(client, hdr)
    bad = {**DOCUMENT, "vehicle_id": vid, "expiry_date": "2025-01-01"}
    assert client.post("/api/documents", json=bad, headers=hdr).status_code == 422


def test_document_bad_patch_dates_hits_db_check(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    vid = _new_vehicle(client, hdr)
    did = client.post(
        "/api/documents", json={**DOCUMENT, "vehicle_id": vid}, headers=hdr
    ).json()["id"]
    # Only expiry sent — pydantic can't cross-check; DB CHECK catches it -> 400.
    resp = client.patch(f"/api/documents/{did}", json={"expiry_date": "2000-01-01"}, headers=hdr)
    assert resp.status_code == 400


def test_document_unknown_vehicle_404(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    resp = client.post("/api/documents", json={**DOCUMENT, "vehicle_id": 9999}, headers=hdr)
    assert resp.status_code == 404


def test_document_rbac_and_soft_delete(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    driver = auth_headers(Role.driver)
    vid = _new_vehicle(client, admin)

    assert client.post(
        "/api/documents", json={**DOCUMENT, "vehicle_id": vid}, headers=driver
    ).status_code == 403

    did = client.post(
        "/api/documents", json={**DOCUMENT, "vehicle_id": vid}, headers=admin
    ).json()["id"]
    assert client.delete(f"/api/documents/{did}", headers=admin).status_code == 204
    assert client.get(f"/api/documents?vehicle_id={vid}", headers=admin).json() == []


# --- Service records ---------------------------------------------------------

def test_create_and_filter_service_records(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.fleet_manager)
    vid = _new_vehicle(client, hdr)
    assert client.post(
        "/api/service-records", json={**SERVICE, "vehicle_id": vid}, headers=hdr
    ).status_code == 201
    listed = client.get(f"/api/service-records?vehicle_id={vid}", headers=hdr)
    assert len(listed.json()) == 1


def test_service_negative_km_rejected(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    vid = _new_vehicle(client, hdr)
    bad = {**SERVICE, "vehicle_id": vid, "km_at_service": -5}
    assert client.post("/api/service-records", json=bad, headers=hdr).status_code == 422


# --- Maintenance rules -------------------------------------------------------

def test_create_maintenance_rule(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    vid = _new_vehicle(client, hdr)
    resp = client.post(
        "/api/maintenance-rules", json={**RULE, "vehicle_id": vid}, headers=hdr
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["interval_km"] == 15000


def test_rule_zero_interval_rejected(client: TestClient, auth_headers) -> None:
    hdr = auth_headers(Role.admin)
    vid = _new_vehicle(client, hdr)
    bad = {**RULE, "vehicle_id": vid, "interval_km": 0}
    assert client.post("/api/maintenance-rules", json=bad, headers=hdr).status_code == 422
