# FleetFlow

Fleet management system (Holisun internship project). Vehicles, drivers,
allocations, legal documents, service history, fuel imports, predictive
maintenance alerts, and cost-per-km (TCO) reports.

One codebase, two experiences: a desktop admin dashboard and a mobile-first
driver PWA on the same API. See [`PLAN.md`](PLAN.md) for the full design.

## Stack

- **Backend:** Python 3.12+ · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL 16
- **Auth:** JWT (PyJWT) + bcrypt (pwdlib), role-based access control
- **Frontend:** React 18 · Vite · TypeScript · Tailwind (added in a later milestone)
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
frontend/       React PWA (added in the Dual-UI milestone)
docker-compose.yml
```

## Build order (milestones)

1. **Scaffold** — repo, Docker Postgres, FastAPI skeleton, JWT auth + RBAC ← _done_
2. **Vehicles + drivers CRUD** (plate/VIN validation, CNP masking, audit log) ← _done_
3. Allocations (no-overlap exclusion constraints) + handover reports (immutability)
4. **Documents + service records + maintenance rules** ← _done_
5. Trip sheets + fuel import parser
6. Alert engine (APScheduler) + notification center
7. TCO + utilization reports (xlsx/PDF export)
8. Dual UI + PWA (driver mobile pages, admin dashboard, LAN access)
```
