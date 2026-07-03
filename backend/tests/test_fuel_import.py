from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.api.routes.fuel_imports as fi_route
from app.models.fuel import FuelTransaction, ImportBatch, ImportStatus
from app.models.user import Role
from app.services import fuel_import as fi_svc

CSV = """date,plate,fuel_card,liters,price,odometer,station
2026-06-01,B-100-AAA,,45.5,7.20,20100,OMV
2026-06-02,,CARD-001,40,7.10,,Petrom
2026-06-03,B-100-AAA,,80,7.00,20300,Rompetrol
2026-06-04,B-100-AAA,,30,7.00,19000,MOL
2026-06-05,X-999-ZZZ,,30,7.00,21000,Lukoil
2026-06-06,B-100-AAA,,abc,7.00,21000,OMV
,B-100-AAA,,25,7.00,21050,OMV
"""

V1 = {
    "plate": "B-100-AAA", "vin": "WVWZZZ1JZXW111111", "make": "Dacia", "model": "Logan",
    "year": 2021, "fuel_type": "petrol", "tank_capacity_l": 50, "current_km": 20000,
}
V2 = {
    "plate": "B-200-BBB", "vin": "WVWZZZ1JZXW222222", "make": "Ford", "model": "Focus",
    "year": 2022, "fuel_type": "diesel", "tank_capacity_l": 60, "current_km": 0,
    "fuel_card_number": "CARD-001",
}


def _make_vehicles(client: TestClient, hdr: dict) -> None:
    assert client.post("/api/vehicles", json=V1, headers=hdr).status_code == 201
    assert client.post("/api/vehicles", json=V2, headers=hdr).status_code == 201


def test_process_import_core(
    client: TestClient, auth_headers, db_session: Session, tmp_path: Path
) -> None:
    _make_vehicles(client, auth_headers(Role.admin))

    path = tmp_path / "fuel.csv"
    path.write_text(CSV, encoding="utf-8")
    batch = ImportBatch(filename="fuel.csv", status=ImportStatus.pending)
    db_session.add(batch)
    db_session.commit()

    result = fi_svc.process_import(db_session, batch.id, str(path))

    assert result.status == ImportStatus.completed
    assert result.total_rows == 7
    assert result.imported_rows == 4
    assert result.rejected_rows == 3

    rejected_rows = {e["row"] for e in result.error_report}
    assert rejected_rows == {5, 6, 7}

    txns = db_session.scalars(select(FuelTransaction)).all()
    assert len(txns) == 4
    suspects = {t.suspect_reason for t in txns if t.is_suspect}
    assert any("tank capacity" in (r or "") for r in suspects)
    assert any("below last known" in (r or "") for r in suspects)
    assert sum(t.is_suspect for t in txns) == 2


def test_process_import_fatal_is_atomic(
    db_session: Session, tmp_path: Path
) -> None:
    batch = ImportBatch(filename="missing.csv", status=ImportStatus.pending)
    db_session.add(batch)
    db_session.commit()

    # Non-existent file -> pandas raises -> batch marked failed, no partial rows.
    try:
        fi_svc.process_import(db_session, batch.id, str(tmp_path / "nope.csv"))
    except Exception:  # noqa: BLE001
        pass

    db_session.refresh(batch)
    assert batch.status == ImportStatus.failed
    assert db_session.scalars(select(FuelTransaction)).all() == []


def test_upload_endpoint_end_to_end(
    client: TestClient, auth_headers, db_session: Session, monkeypatch
) -> None:
    admin = auth_headers(Role.admin)
    _make_vehicles(client, admin)

    # Run the "background" parse synchronously against the test session.
    monkeypatch.setattr(
        fi_route,
        "run_import_in_background",
        lambda batch_id, path: fi_svc.process_import(db_session, batch_id, path),
    )

    files = {"file": ("fuel.csv", CSV.encode(), "text/csv")}
    resp = client.post("/api/fuel-imports", files=files, headers=admin)
    assert resp.status_code == 202
    batch_id = resp.json()["id"]

    status = client.get(f"/api/fuel-imports/{batch_id}", headers=admin).json()
    assert status["status"] == "completed"
    assert status["imported_rows"] == 4

    suspects = client.get(
        f"/api/fuel-transactions?batch_id={batch_id}&suspect_only=true", headers=admin
    ).json()
    assert len(suspects) == 2


def test_upload_rejects_bad_extension(client: TestClient, auth_headers) -> None:
    admin = auth_headers(Role.admin)
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    assert client.post("/api/fuel-imports", files=files, headers=admin).status_code == 400


def test_upload_requires_manager(client: TestClient, auth_headers) -> None:
    driver = auth_headers(Role.driver)
    files = {"file": ("fuel.csv", CSV.encode(), "text/csv")}
    assert client.post("/api/fuel-imports", files=files, headers=driver).status_code == 403
