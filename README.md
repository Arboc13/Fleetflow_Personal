# FleetFlow

Fleet management system (Holisun internship project). Vehicles, drivers,
allocations, legal documents, service history, fuel imports, predictive
maintenance alerts, and cost-per-km (TCO) reports.

One codebase, two experiences: a desktop admin dashboard and a mobile-first
driver PWA on the same API. See [`PLAN.md`](PLAN.md) for the full design.

## Stack

- **Backend:** Python 3.12+ · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL 16
- **Auth:** JWT (PyJWT) + bcrypt (pwdlib), role-based access control
- **Frontend:** React 18 · Vite · TypeScript · Tailwind · vite-plugin-pwa · Recharts
- **Infra:** Docker Compose (PostgreSQL only; app runs natively in dev)

## Prerequisites

- Python 3.12+ (3.13 works) — installed
- Docker Desktop — **required**, install on `D:\`
- Node.js 20+ — **required for the frontend**, install on `D:\`

## Backend — quick start

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Set up the backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env            # then edit SECRET_KEY

# 3. Apply migrations and seed an admin
alembic upgrade head
python -m scripts.seed            # admin@fleetflow.local / admin123

# 4. Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Frontend — quick start

```bash
cd frontend
npm install
npm run dev            # binds 0.0.0.0 — reachable from the LAN
```

- Desktop admin dashboard: http://localhost:5173 (log in as admin / fleet manager)
- The dev server proxies `/api` to the backend on port 8000, so start the backend first.

### Driver app on the phone (same Wi-Fi)

1. Find this PC's IP: `ipconfig` → e.g. `192.168.1.20`.
2. Allow the port once (admin PowerShell):
   `New-NetFirewallRule -DisplayName "FleetFlow dev" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow`
3. On the phone open `http://192.168.1.20:5173`, log in with a driver account.
4. Browser menu → **Add to Home Screen** — it installs as the FleetFlow PWA
   (manifest + service worker via vite-plugin-pwa).

Two experiences from one codebase: `admin`/`fleet_manager` logins land on the
desktop dashboard (`/admin`), `driver` logins land on the mobile UI (`/driver`).

## Tests

```bash
cd backend
pytest                # auth + RBAC tests run on in-memory SQLite (no DB needed)
```

## Project layout

```
backend/
  app/
    core/       config, database, security, dependencies (RBAC)
    models/     SQLAlchemy models
    schemas/    Pydantic request/response DTOs
    api/routes/ routers per module
    services/   business rules (allocation, alerts, imports, reports)
    jobs/       APScheduler tasks
  alembic/      migrations
  scripts/      seed.py
  tests/
frontend/
  src/
    api/        fetch client + TS mirrors of the backend schemas
    auth/       JWT session context + role route guards
    components/ shared UI primitives (table, modal, badges, bell)
    pages/admin/   desktop dashboard (vehicles, allocations, fuel, reports…)
    pages/driver/  mobile-first driver UI (trips, handover) — installable PWA
docker-compose.yml
```

