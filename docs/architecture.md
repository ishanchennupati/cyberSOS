# CyberSOS — Architecture (Phase 0)

## Overview

```text
┌────────────────┐        HTTPS/JSON        ┌──────────────────┐        SQL        ┌──────────────┐
│  Next.js (FE)  │ ───────────────────────▶ │  FastAPI (BE)     │ ────────────────▶ │  PostgreSQL   │
│  App Router    │ ◀─────────────────────── │  /api/v1/*        │ ◀──────────────── │  (Supabase or │
└────────────────┘                          └──────────────────┘                    │   local)      │
                                                                                       └──────────────┘
```

Frontend and backend are independently runnable and communicate only over
HTTP, using `NEXT_PUBLIC_API_URL` on the frontend side.

## Frontend

- **Next.js 14, App Router, TypeScript, Tailwind CSS**
- `app/` — routes: `/` (landing) and `/incident/start` (first flow step)
- `components/` — shared UI: `ui/button.tsx` (shadcn-style primitive),
  `progress-steps.tsx`, `error-state.tsx`, `loading-state.tsx`,
  `site-footer.tsx`, `case-ticket.tsx`
- `lib/api.ts` — single place that talks to the backend; every request goes
  through `request()`, which normalizes network failures, timeouts, and
  non-2xx responses into a typed `ApiError` so the UI never renders a raw
  stack trace
- `types/incident.ts` — TypeScript types mirroring the backend's Pydantic
  schemas, so payload shapes can't silently drift apart

No business logic lives inside components beyond simple UI state
(selected option, request status). Data fetching and error normalization
live in `lib/api.ts`.

## Backend

- **FastAPI, Pydantic, SQLAlchemy, PostgreSQL, Uvicorn**
- `app/main.py` — app wiring only: middleware, router mounting, startup
  hook. No business logic.
- `app/core/config.py` — environment-driven settings (`DATABASE_URL`,
  `CORS_ORIGINS`), read once via `pydantic-settings`
- `app/db/` — SQLAlchemy engine/session (`session.py`) and declarative
  base (`base.py`)
- `app/models/` — ORM models (`Incident`, plus its enum columns)
- `app/schemas/` — Pydantic request/response schemas (`IncidentCreate`,
  `IncidentRead`)
- `app/services/` — business logic, e.g. `incident_service.py` (creation,
  a placeholder urgency rule). Routes call services; they don't contain
  logic themselves.
- `app/api/routes/` — thin route handlers (`health.py`, `incidents.py`)
- `app/api/v1.py` — aggregates route modules under `/api/v1`

## Database

- PostgreSQL, reachable via `DATABASE_URL` (works the same for a local
  Postgres instance or a hosted Supabase Postgres instance)
- Phase 0 creates tables directly from the SQLAlchemy models on startup
  (`Base.metadata.create_all`). `alembic` is already in
  `requirements.txt` so real migrations can be introduced without a
  dependency change once the schema needs to evolve.
- Single table so far: `incidents` (see `docs/product.md` for the field
  list and enum values).

## API communication

- All endpoints are versioned under `/api/v1`, except the top-level
  `/health` liveness check.
- `GET /health` — API liveness
- `GET /api/v1/health/database` — confirms the API can reach Postgres,
  without ever returning connection details or credentials
- `POST /api/v1/incidents` — create an incident (financial fraud only,
  for now)
- `GET /api/v1/incidents/{incident_id}` — fetch one incident
- CORS is restricted to the origins listed in `CORS_ORIGINS`
  (defaults to `http://localhost:3000`)

## Future layers (not built yet)

- **AI layer** — real triage/urgency classification, guided Q&A, drafting
  help for the complaint narrative. Will sit behind `app/services/`, called
  from new route(s), so today's routes and models don't need to change
  shape to accommodate it.
- **Evidence-processing layer** — file upload, OCR, image/screenshot
  parsing, structured extraction of transaction details. Will introduce a
  new `evidence` table linked to `incidents.id`, plus storage (e.g. object
  storage bucket referenced by URL, not stored in Postgres directly).
- **Government-service links** — deeper, still non-authoritative,
  integration such as pre-filling the citizen's own submission to
  cybercrime.gov.in, or checking 1930 callback status if such an API
  becomes available. CyberSOS will not submit anything on the citizen's
  behalf without their explicit action, and will keep saying so.
