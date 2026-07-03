# FleetFlow — Implementation Plan

## Context

The PDF (`Caiet de Sarcini 3.pdf`) is the spec for **FleetFlow**, a fleet management system for an internship project at Holisun: a multi-user web platform managing vehicles, drivers, allocations, legal documents (RCA/CASCO/ITP/Rovinietă), service history, fuel imports from CSV/Excel, predictive maintenance alerts, and cost-per-km (TCO) reports. The company left the tech stack to the student's choice; the goal is to build it locally on the user's PC, with a driver-friendly interface usable from a phone.

**Research finding on the "two apps" question:** every comparable product — commercial (Fleetio, Samsara) and open-source (fleetms, LubeLogger, Odoo Fleet, Fleetbase) — uses **one backend + one web application**. Mobile access is a responsive web UI / PWA (fleetms, LubeLogger, Odoo) or a thin native client on the same API (Samsara's driver app). None maintain two independent applications. The spec itself mandates a "web-based platform" with dual responsive design (NFR-3).

**Decision: one codebase, two experiences.** A single React app with two role-based UIs: a desktop dashboard for Admin/Fleet Manager and a mobile-first driver UI, installable as a PWA ("Add to Home Screen") on the phone. The phone reaches the app over Wi-Fi at `http://<PC-IP>:5173`. This gives the "separate app on my phone" feel with zero duplicate code and no app store.

## Recommended Stack

| Layer | Choice | Why (spec-driven) |
|---|---|---|
| Backend | **Python 3.12 + FastAPI** | Fast to learn; async; auto OpenAPI docs; `BackgroundTasks` for non-blocking notifications (F-501) |
| Database | **PostgreSQL 16** (via Docker Desktop) | `EXCLUDE USING gist` range constraints enforce no-overlap allocations at DB level (rule 2.1 + NFR-2 concurrency); real transactions for crash-safe imports (NFR-2 availability) |
| ORM/Migrations | SQLAlchemy 2 + Alembic | Standard, well-documented |
| Background jobs | **APScheduler** (in-process, SQLAlchemy job store) | Daily alert scans without Redis/Celery infrastructure — right size for a local app |
| CSV/Excel parsing | **pandas + openpyxl** | Strongest tooling for the fuel-import parser (F-402) and native-number Excel exports (F-602) — the main reason Python wins here |
| PDF export | **ReportLab** / `xhtml2pdf` (HTML→PDF, pure Python) | Print-optimized reports (F-602) — see note below on why not WeasyPrint |
| Auth | JWT (**PyJWT**) + **pwdlib** bcrypt | Password hashing (NFR-1), role claims for RBAC. _Changed from python-jose/passlib: passlib needs the `crypt` stdlib module removed in Python 3.13; PyJWT/pwdlib are what current FastAPI docs use._ |
| Frontend | **React 18 + Vite + TypeScript + Tailwind CSS** | One responsive codebase; Tailwind breakpoints for the dual design; `vite-plugin-pwa` for installability |
| Charts/UI | Recharts + Headless UI | Dashboard indicators (red/yellow status) |

Alternatives considered and rejected: Node/NestJS (weaker Excel/CSV tooling), React Native driver app (second codebase, unnecessary — no offline/hardware requirement in spec).

**Note on PDF export — WeasyPrint dropped for Windows-local build.** WeasyPrint (originally considered) depends on native GTK/Pango/Cairo system libraries that are notoriously painful to install and get working on Windows 10, and the spec requires building locally on this PC. To avoid a day lost to DLL/GTK errors, the plan now uses a **pure-Python PDF path (ReportLab, or `xhtml2pdf` if we want to reuse the HTML report template)** — installs cleanly via `pip` with no system dependencies. If print fidelity later proves insufficient, the fallback is browser print-to-PDF (render report as HTML, print from the browser), which also needs no native libraries.

**Installation location convention (this PC):** any tool or runtime that must be installed on this machine — Python, Node.js, PostgreSQL/Docker Desktop, etc. — is installed under the **`D:\` drive, NOT `C:\`**. Choose the custom/advanced installer option and point the install path to `D:\` (e.g. `D:\Python`, `D:\PostgreSQL`, `D:\Docker`). The project itself already lives in `D:\Holisun_Project_Fable`.

## Repository Layout (monorepo, new git repo in `D:\Holisun_Project_Fable`)

```
fleetflow/
├── backend/
│   ├── app/
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic DTOs
│   │   ├── api/           # routers per module
│   │   ├── services/      # business rules (allocation, alerts, imports, reports)
│   │   ├── core/          # config, security, deps
│   │   └── jobs/          # APScheduler tasks
│   ├── alembic/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   └── src/
│       ├── pages/admin/   # desktop dashboard UI
│       ├── pages/driver/  # mobile-first driver UI
│       └── api/           # generated client from OpenAPI
├── docker-compose.yml     # PostgreSQL only (app runs natively for dev)
└── sample-data/           # seed script + test CSV files (incl. corrupt rows)
```

## Data Model (key tables)

- `users` (email, password_hash, role: admin | fleet_manager | driver)
- `drivers` (contact, CNP **encrypted at rest + masked in API** per NFR-1, license number/series/category/expiry) — linked 1:1 to a `users` row for driver logins
- `vehicles` (plate — regex-validated `^[A-Z]{1,2}-\d{2,3}-[A-Z]{3}$`, VIN — exactly 17 chars, make, model, year, fuel_type, current_km, status: active | in_service | unavailable, **tank_capacity_l**, **fuel_card_number** — both needed by the fuel parser)
- `allocations` (vehicle_id, driver_id, `period tstzrange`, type: permanent | trip, status)
  - **Rule 2.1 enforced in the DB**: two exclusion constraints with `btree_gist` — `EXCLUDE (vehicle_id WITH =, period WITH &&)` and `EXCLUDE (driver_id WITH =, period WITH &&)`. Concurrency-safe by construction (NFR-2); service layer translates constraint violations into friendly 409 errors.
- `handover_reports` (proces-verbal: allocation_id, direction: handover | return, km, fuel_level_pct, visual_observations, cleanliness, status: draft | closed)
  - **Rule 2.3 immutability**: same DB trigger as trip sheets — rejects UPDATE/DELETE on rows with status = 'closed' (spec 2.3 makes *both* the foaie de parcurs and the proces-verbal read-only once closed), plus service-layer check for clean error messages.
- `trip_sheets` (foaie de parcurs: vehicle, driver, depart/arrive datetime, start_km, end_km CHECK end > start, status: draft | closed)
  - **Rule 2.3 immutability**: DB trigger rejects UPDATE/DELETE on rows with status = 'closed' (plus service-layer check for clean error messages). Closing a trip sheet updates `vehicles.current_km`.
- `vehicle_documents` (type: RCA | CASCO | ITP | Rovinieta, series_number, issuer, cost, issue_date, expiry_date)
- `service_records` (date, km_at_service, work_description, parts_replaced, cost)
- `maintenance_rules` (vehicle_id, interval_km e.g. 15000, interval_months e.g. 12, last_service_km/date)
- `fuel_transactions` (vehicle_id, datetime, liters, price, odometer_reported, station, import_batch_id, is_suspect + suspect_reason)
- `import_batches` (filename, status, total/imported/rejected row counts, error_report JSON)
- `notifications` (user_id, type, severity, message, read_at)
- `audit_log` (entity, entity_id, field, old_value, new_value, user_id, timestamp) — written on every manual odometer edit (NFR-1)

**Deletion policy (NFR-1 — Fleet Manager has no permanent-delete right):** business entities (vehicles, drivers, documents, service records, allocations) carry a `deleted_at` nullable column (soft delete). The **Fleet Manager** role can only soft-delete (hide) records; the API blocks hard `DELETE` for this role. Only the **Admin** role may issue a permanent delete. RBAC guards enforce this per-route, and default queries filter out soft-deleted rows.

## Core Algorithms

**Predictive alert engine (rule 2.2 + F-502)** — APScheduler daily job (+ on-demand trigger after each import/trip-sheet close):
1. Documents & licenses: alert at 30/15/5 days before `expiry_date`.
2. Maintenance dual rule: `km_to_due = (last_service_km + interval_km) − current_km`; `days_to_due = (last_service_date + interval_months) − today`. Estimate `days_until_km_due = km_to_due / avg_daily_km` (average from last 30 days of trip sheets). Alert when **either** `km_to_due < 1000` **or** `days_to_due < 30` — first condition wins.
   - **Cold-start guard**: when `avg_daily_km` is 0 or null (new vehicle, or no trip sheets in the last 30 days), skip the `days_until_km_due` estimate and treat it as "unknown" rather than dividing by zero. The two hard triggers (`km_to_due < 1000`, `days_to_due < 30`) still apply — the estimate is only for prioritization, so its absence must never crash the daily job.
3. Insert `notifications` rows (dashboard bell + red/yellow dashboard indicators). Delivery runs in background — never blocks a request (F-501).

**Fuel import parser (F-402, NFR-2)**:
1. Upload endpoint stores the file, creates `import_batch`, and processes it as a background task in chunks (UI polls batch status — no timeout on 5000+ rows).
2. pandas reads CSV/XLSX; per-row validation; reconcile to vehicle by plate **or** fuel card number.
3. Suspect detection: `liters > tank_capacity_l`, or reported odometer inconsistent with the vehicle's km history (lower than last known, or implausible jump).
4. Bad rows are rejected into the batch's error report; valid rows commit **in one transaction** — a crash mid-import rolls back cleanly, no partial/duplicate data.

**TCO report (F-601)**: `cost_per_km = (fuel + service + document costs in period) / km driven in period` (from closed trip sheets), plus fleet utilization % (active vs. in-service/unallocated days). Export via openpyxl (real numeric cells, not strings) and WeasyPrint PDF (F-602).

## Milestones (build order)

1. **Scaffold**: git init, docker-compose PostgreSQL, FastAPI skeleton + Alembic, Vite React app, JWT auth + RBAC guards, seed script.
2. **Module 1**: vehicles + drivers CRUD with live plate/VIN validation (non-blocking form feedback, NFR-3), CNP masking, audit log on odometer edits.
3. **Module 2**: allocations with exclusion constraints + handover reports + immutability triggers. *Test: two overlapping allocations must be impossible, even issued concurrently.*
4. **Module 3**: documents + service records + maintenance rules.
5. **Module 4**: trip sheets + fuel import parser with error reporting.
6. **Module 5**: alert engine (APScheduler) + notification center.
7. **Module 6**: TCO + utilization reports, xlsx/PDF export.
8. **Dual UI + PWA**: driver mobile pages (big buttons, numeric keypads), admin dashboard (red/yellow indicators), `vite-plugin-pwa`, bind dev servers to `0.0.0.0` for phone access over LAN.

## Verification

- **Business rules**: automated pytest suite — overlapping allocation attempts (including two concurrent requests) must fail; closed trip sheets must reject edits/deletes (Definition of Done #2).
- **Parser robustness**: import `sample-data/` CSVs containing corrupt rows, nulls, over-capacity liters — verify rejected rows land in the error report and valid rows import (DoD #3).
- **Crash consistency**: kill the backend mid-import; on restart the batch has no partial rows.
- **Reports**: hand-computed TCO for the seed dataset matches app output; exported .xlsx opens in Excel with numeric cells usable in formulas (DoD #4).
- **Phone test**: open `http://<PC-IP>:5173` from the phone on the same Wi-Fi, log in as a driver, complete a handover report and trip sheet; install via Add to Home Screen.
