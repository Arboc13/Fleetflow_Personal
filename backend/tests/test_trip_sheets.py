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

DRIVER = {
    "email": "sofer@example.com",
    "full_name": "Sofer Unu",
    "password": "drivepass1",
    "cnp": "1900101223344",
    "license_number": "123456",
    "license_category": "B",
    "license_expiry": "2030-01-01",
}


def _setup(client: TestClient, admin: dict) -> tuple[int, int]:
    vid = client.post("/api/vehicles", json=VEHICLE, headers=admin).json()["id"]
    did = client.post("/api/drivers", json=DRIVER, headers=admin).json()["id"]
    return vid, did


def _driver_headers(client: TestClient) -> dict:
    resp = client.post(
        "/api/auth/login",
        data={"username": DRIVER["email"], "password": DRIVER["password"]},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def test_create_and_close_updates_odometer(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    vid, did = _setup(client, admin)

    trip = client.post(
        "/api/trip-sheets",
        json={
            "vehicle_id": vid,
            "driver_id": did,
            "departure_at": "2026-06-01T08:00:00",
            "start_km": 20000,
            "purpose": "Delivery",
        },
        headers=admin,
    ).json()
    assert trip["status"] == "draft"

    closed = client.post(
        f"/api/trip-sheets/{trip['id']}/close",
        json={"arrival_at": "2026-06-01T17:00:00", "end_km": 20250},
        headers=admin,
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"

    # Vehicle odometer advanced to end_km.
    veh = client.get(f"/api/vehicles/{vid}", headers=admin).json()
    assert veh["current_km"] == 20250


def test_closed_trip_sheet_is_immutable(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    vid, did = _setup(client, admin)
    tid = client.post(
        "/api/trip-sheets",
        json={"vehicle_id": vid, "driver_id": did, "departure_at": "2026-06-01T08:00:00", "start_km": 20000},
        headers=admin,
    ).json()["id"]
    client.post(
        f"/api/trip-sheets/{tid}/close",
        json={"arrival_at": "2026-06-01T17:00:00", "end_km": 20250},
        headers=admin,
    )

    assert client.patch(f"/api/trip-sheets/{tid}", json={"purpose": "x"}, headers=admin).status_code == 409
    assert client.post(
        f"/api/trip-sheets/{tid}/close",
        json={"arrival_at": "2026-06-01T18:00:00", "end_km": 20300},
        headers=admin,
    ).status_code == 409
    assert client.delete(f"/api/trip-sheets/{tid}", headers=admin).status_code == 409
    assert client.delete(f"/api/trip-sheets/{tid}/permanent", headers=admin).status_code == 409


def test_end_km_must_exceed_start(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    vid, did = _setup(client, admin)
    tid = client.post(
        "/api/trip-sheets",
        json={"vehicle_id": vid, "driver_id": did, "departure_at": "2026-06-01T08:00:00", "start_km": 20000},
        headers=admin,
    ).json()["id"]
    resp = client.post(
        f"/api/trip-sheets/{tid}/close",
        json={"arrival_at": "2026-06-01T17:00:00", "end_km": 19900},
        headers=admin,
    )
    assert resp.status_code == 422


def test_driver_creates_own_and_cannot_see_others(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    vid, did = _setup(client, admin)
    driver = _driver_headers(client)

    # Driver omits driver_id — it's forced to their own profile.
    own = client.post(
        "/api/trip-sheets",
        json={"vehicle_id": vid, "departure_at": "2026-06-02T08:00:00", "start_km": 20000},
        headers=driver,
    )
    assert own.status_code == 201
    assert own.json()["driver_id"] == did

    # A trip sheet for another driver_id, created by admin, is not visible/editable.
    other_did = client.post(
        "/api/drivers",
        json={**DRIVER, "email": "alt@example.com", "cnp": "1900101223355"},
        headers=admin,
    ).json()["id"]
    other_tid = client.post(
        "/api/trip-sheets",
        json={"vehicle_id": vid, "driver_id": other_did, "departure_at": "2026-06-02T08:00:00", "start_km": 20000},
        headers=admin,
    ).json()["id"]

    assert client.get(f"/api/trip-sheets/{other_tid}", headers=driver).status_code == 403
    listed = client.get("/api/trip-sheets", headers=driver).json()
    assert [t["driver_id"] for t in listed] == [did]
