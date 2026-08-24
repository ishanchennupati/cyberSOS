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
- Alembic migrations in `backend/alembic/` track schema changes. The Phase 2
  revision adds the Other Cyber Crime fields and evidence metadata table;
  `ensure_schema` remains as additive compatibility support for older local
  databases.
- Single table so far: `incidents` (see `docs/product.md` for the field
  list and enum values).

## API communication

- All endpoints are versioned under `/api/v1`, except the top-level
  `/health` liveness check.
- `GET /health` — API liveness
- `GET /api/v1/health/database` — confirms the API can reach Postgres,
  without ever returning connection details or credentials
- `POST /api/v1/incidents` — create an incident from any supported guided flow
- `GET /api/v1/incidents/{incident_id}` — fetch one incident
- CORS is restricted to the origins listed in `CORS_ORIGINS`
  (defaults to `http://localhost:3000`)

## Future layers (not built yet)

- **AI layer** — the frontend currently uses a deterministic guided-question
  provider. An LLM-backed provider can replace that question list later,
  returning the same structured `details` payload and leaving persistence and
  complaint drafting unchanged.
- **Evidence-processing layer** — OCR, image/screenshot parsing, and
  structured extraction of transaction details. Phase 2 stores uploaded files
  locally and records metadata in `evidence`; production should move file
  bytes to object storage.
- **Government-service links** — deeper, still non-authoritative,
  integration such as pre-filling the citizen's own submission to
  cybercrime.gov.in, or checking 1930 callback status if such an API
  becomes available. CyberSOS will not submit anything on the citizen's
  behalf without their explicit action, and will keep saying so.
