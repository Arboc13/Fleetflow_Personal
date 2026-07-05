import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import Role
from app.services.alerts import add_months, run_alert_scan

VEHICLE = {
    "plate": "B-100-AAA", "vin": "WVWZZZ1JZXW111111", "make": "Dacia", "model": "Logan",
    "year": 2021, "fuel_type": "petrol", "tank_capacity_l": 50, "current_km": 34600,
}
DRIVER = {
    "email": "sofer@example.com", "full_name": "Sofer Unu", "password": "drivepass1",
    "cnp": "1900101223344", "license_number": "L-123", "license_category": "B",
    "license_expiry": "2030-01-01",
}


def _iso(days: int) -> str:
    return (dt.date.today() + dt.timedelta(days=days)).isoformat()


def test_add_months_handles_month_end() -> None:
    assert add_months(dt.date(2026, 1, 31), 1) == dt.date(2026, 2, 28)
    assert add_months(dt.date(2026, 12, 15), 1) == dt.date(2027, 1, 15)


def test_document_expiry_alert_and_dedup(client: TestClient, auth_headers, db_session: Session) -> None:
    admin = auth_headers(Role.admin)
    vid = client.post("/api/vehicles", json=VEHICLE, headers=admin).json()["id"]
    # Expires in 3 days -> critical (stage 5).
    client.post(
        "/api/documents",
        json={"type": "RCA", "series_number": "RO-1", "cost": 100,
              "issue_date": "2026-01-01", "expiry_date": _iso(3), "vehicle_id": vid},
        headers=admin,
    )

    assert run_alert_scan(db_session) == 1
    assert run_alert_scan(db_session) == 0  # dedup: same stage, no duplicate

    notes = client.get("/api/notifications", headers=admin).json()
    assert len(notes) == 1
    assert notes[0]["severity"] == "critical"
    assert notes[0]["type"] == "document_expiry"


def test_maintenance_km_rule_and_cold_start(client: TestClient, auth_headers, db_session: Session) -> None:
    admin = auth_headers(Role.admin)
    vid = client.post("/api/vehicles", json=VEHICLE, headers=admin).json()["id"]
    # due at 20000 + 15000 = 35000; current 34600 -> km_to_due = 400 (< 1000).
    # last_service_date today -> time rule far away, so km triggers. No trip
    # sheets exist -> avg_daily_km = 0 -> cold-start guard, must not crash.
    client.post(
        "/api/maintenance-rules",
        json={"name": "Oil", "interval_km": 15000, "interval_months": 12,
              "last_service_km": 20000, "last_service_date": dt.date.today().isoformat(),
              "vehicle_id": vid},
        headers=admin,
    )
    assert run_alert_scan(db_session) == 1
    note = client.get("/api/notifications", headers=admin).json()[0]
    assert note["type"] == "maintenance_due"
    assert "km to service" in note["message"]


def test_license_alert_reaches_driver_not_unrelated_manager(
    client: TestClient, auth_headers, db_session: Session
) -> None:
    admin = auth_headers(Role.admin)
    client.post("/api/drivers", json={**DRIVER, "license_expiry": _iso(10)}, headers=admin)

    run_alert_scan(db_session)

    # The driver themselves gets it.
    dlogin = client.post(
        "/api/auth/login",
        data={"username": DRIVER["email"], "password": DRIVER["password"]},
    ).json()["access_token"]
    dhdr = {"Authorization": f"Bearer {dlogin}"}
    dnotes = client.get("/api/notifications", headers=dhdr).json()
    assert len(dnotes) == 1
    assert dnotes[0]["type"] == "license_expiry"


def test_notification_center_mark_read(client: TestClient, auth_headers, db_session: Session) -> None:
    admin = auth_headers(Role.admin)
    vid = client.post("/api/vehicles", json=VEHICLE, headers=admin).json()["id"]
    client.post(
        "/api/documents",
        json={"type": "ITP", "series_number": "X", "cost": 0,
              "issue_date": "2026-01-01", "expiry_date": _iso(2), "vehicle_id": vid},
        headers=admin,
    )
    run_alert_scan(db_session)

    assert client.get("/api/notifications/unread-count", headers=admin).json()["unread"] == 1
    nid = client.get("/api/notifications", headers=admin).json()[0]["id"]
    assert client.post(f"/api/notifications/{nid}/read", headers=admin).status_code == 200
    assert client.get("/api/notifications/unread-count", headers=admin).json()["unread"] == 0


def test_alerts_run_endpoint_rbac(client: TestClient, auth_headers) -> None:
    assert client.post("/api/alerts/run", headers=auth_headers(Role.driver)).status_code == 403
    assert client.post("/api/alerts/run", headers=auth_headers(Role.admin)).status_code == 200
