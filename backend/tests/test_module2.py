from fastapi.testclient import TestClient

from app.models.user import Role

V1 = {
    "plate": "B-100-AAA", "vin": "WVWZZZ1JZXW111111", "make": "Dacia", "model": "Logan",
    "year": 2021, "fuel_type": "petrol", "tank_capacity_l": 50, "current_km": 20000,
}
V2 = {
    "plate": "B-200-BBB", "vin": "WVWZZZ1JZXW222222", "make": "Ford", "model": "Focus",
    "year": 2022, "fuel_type": "diesel", "tank_capacity_l": 60, "current_km": 0,
}
D1 = {
    "email": "sofer@example.com", "full_name": "Sofer Unu", "password": "drivepass1",
    "cnp": "1900101223344", "license_number": "L-1", "license_category": "B",
    "license_expiry": "2030-01-01",
}
D2 = {**D1, "email": "sofer2@example.com", "cnp": "1900101223355", "license_number": "L-2"}


def _setup(client: TestClient, admin: dict) -> tuple[int, int, int, int]:
    v1 = client.post("/api/vehicles", json=V1, headers=admin).json()["id"]
    v2 = client.post("/api/vehicles", json=V2, headers=admin).json()["id"]
    d1 = client.post("/api/drivers", json=D1, headers=admin).json()["id"]
    d2 = client.post("/api/drivers", json=D2, headers=admin).json()["id"]
    return v1, v2, d1, d2


def _driver_headers(client: TestClient, creds: dict = D1) -> dict:
    resp = client.post(
        "/api/auth/login",
        data={"username": creds["email"], "password": creds["password"]},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _alloc(vid: int, did: int, start: str, end: str | None, type_: str = "trip") -> dict:
    return {"vehicle_id": vid, "driver_id": did, "start_at": start, "end_at": end, "type": type_}


def test_overlapping_allocations_rejected(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    v1, v2, d1, d2 = _setup(client, admin)

    ok = client.post(
        "/api/allocations",
        json=_alloc(v1, d1, "2026-06-01T08:00:00", "2026-06-10T08:00:00"),
        headers=admin,
    )
    assert ok.status_code == 201

    # Same vehicle, different driver, overlapping period -> vehicle conflict.
    resp = client.post(
        "/api/allocations",
        json=_alloc(v1, d2, "2026-06-05T08:00:00", "2026-06-15T08:00:00"),
        headers=admin,
    )
    assert resp.status_code == 409
    assert "vehicle" in resp.json()["detail"]

    # Different vehicle, same driver, overlapping period -> driver conflict.
    resp = client.post(
        "/api/allocations",
        json=_alloc(v2, d1, "2026-06-05T08:00:00", "2026-06-15T08:00:00"),
        headers=admin,
    )
    assert resp.status_code == 409
    assert "driver" in resp.json()["detail"]

    # Back-to-back (starts exactly when the first ends) is allowed.
    resp = client.post(
        "/api/allocations",
        json=_alloc(v1, d1, "2026-06-10T08:00:00", "2026-06-20T08:00:00"),
        headers=admin,
    )
    assert resp.status_code == 201


def test_open_ended_allocation_blocks_all_future(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    v1, _, d1, d2 = _setup(client, admin)

    assert client.post(
        "/api/allocations",
        json=_alloc(v1, d1, "2026-06-01T08:00:00", None, "permanent"),
        headers=admin,
    ).status_code == 201
    # Any later allocation of the same vehicle collides with the open period.
    assert client.post(
        "/api/allocations",
        json=_alloc(v1, d2, "2027-01-01T08:00:00", "2027-01-02T08:00:00"),
        headers=admin,
    ).status_code == 409


def test_period_validation_and_rbac(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    v1, _, d1, d2 = _setup(client, admin)

    # end before start -> 422 from the schema validator.
    assert client.post(
        "/api/allocations",
        json=_alloc(v1, d1, "2026-06-10T08:00:00", "2026-06-01T08:00:00"),
        headers=admin,
    ).status_code == 422

    # Drivers cannot create allocations, and only see their own.
    client.post(
        "/api/allocations",
        json=_alloc(v1, d1, "2026-06-01T08:00:00", "2026-06-10T08:00:00"),
        headers=admin,
    )
    driver = _driver_headers(client)
    assert client.post(
        "/api/allocations",
        json=_alloc(v1, d2, "2028-01-01T08:00:00", "2028-01-02T08:00:00"),
        headers=driver,
    ).status_code == 403
    listed = client.get("/api/allocations", headers=driver).json()
    assert [a["driver_id"] for a in listed] == [d1]


def test_handover_flow_immutability_and_allocation_end(
    client: TestClient, auth_headers
) -> None:
    admin = auth_headers(Role.admin)
    v1, _, d1, d2 = _setup(client, admin)
    aid = client.post(
        "/api/allocations",
        json=_alloc(v1, d1, "2026-06-01T08:00:00", None, "permanent"),
        headers=admin,
    ).json()["id"]

    driver = _driver_headers(client)
    report = client.post(
        "/api/handover-reports",
        json={"allocation_id": aid, "direction": "handover", "km": 20000,
              "fuel_level_pct": 80, "cleanliness": "clean"},
        headers=driver,
    )
    assert report.status_code == 201
    rid = report.json()["id"]

    # Draft is editable, closing freezes it (rule 2.3).
    assert client.patch(
        f"/api/handover-reports/{rid}", json={"km": 20005}, headers=driver
    ).status_code == 200
    assert client.post(f"/api/handover-reports/{rid}/close", headers=driver).status_code == 200
    assert client.patch(
        f"/api/handover-reports/{rid}", json={"km": 1}, headers=driver
    ).status_code == 409
    assert client.delete(f"/api/handover-reports/{rid}", headers=driver).status_code == 409
    assert client.delete(
        f"/api/handover-reports/{rid}/permanent", headers=admin
    ).status_code == 409

    # Another driver cannot touch reports on this allocation.
    other = _driver_headers(client, D2)
    assert client.get(f"/api/handover-reports/{rid}", headers=other).status_code == 403

    # Closing the RETURN report ends the allocation and sets its end date.
    ret = client.post(
        "/api/handover-reports",
        json={"allocation_id": aid, "direction": "return", "km": 20500,
              "fuel_level_pct": 50},
        headers=driver,
    ).json()
    client.post(f"/api/handover-reports/{ret['id']}/close", headers=driver)
    alloc = client.get(f"/api/allocations/{aid}", headers=admin).json()
    assert alloc["status"] == "ended"
    assert alloc["end_at"] is not None

    # The vehicle is free again: a new allocation after the end date works.
    assert client.post(
        "/api/allocations",
        json=_alloc(v1, d2, "2030-01-01T08:00:00", "2030-02-01T08:00:00"),
        headers=admin,
    ).status_code == 201
