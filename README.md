# CyberSOS — Phase 0

Foundation for CyberSOS, a citizen-support layer that helps someone in
India respond to a cyber/financial fraud incident: understand what
happened, know what to do immediately, organize evidence, and reach the
official channels (1930, cybercrime.gov.in).

This phase ships only the base project: a working Next.js frontend, a
working FastAPI backend, Postgres connectivity, the landing page, and the
first step of the incident flow. See `docs/product.md` and
`docs/architecture.md` for the full picture, including what's
intentionally not built yet.

> CyberSOS is an independent prototype. It is not affiliated with, and
> does not replace, the Government of India Cyber Crime Reporting Portal
> or the 1930 helpline.

## Project structure

```text
cybersos/
├── frontend/     # Next.js (App Router, TypeScript, Tailwind)
├── backend/      # FastAPI (Pydantic, SQLAlchemy, PostgreSQL)
├── docs/         # product.md, architecture.md
└── README.md
```

Frontend and backend are independently runnable and only talk to each
other over HTTP.

## Prerequisites

- Node.js 18.18+ and npm
- Python 3.11+
- A PostgreSQL database — either:
  - a local Postgres instance, or
  - a [Supabase](https://supabase.com) Postgres project

## 1. Database setup

1. Create a Postgres database (locally, or a new Supabase project).
2. Copy its connection string — you'll need it for `DATABASE_URL`.
3. No manual schema setup is required: on startup, the backend creates
   the `incidents` table automatically from its models.

## 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set DATABASE_URL to your Postgres connection string

uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`.

- `GET http://localhost:8000/health` → `{"status": "ok", "service": "cybersos-api"}`
- `GET http://localhost:8000/api/v1/health/database` → confirms DB connectivity
- Interactive API docs: `http://localhost:8000/docs`

## 3. Frontend setup

```bash
cd frontend
npm install

cp .env.example .env.local
# defaults to NEXT_PUBLIC_API_URL=http://localhost:8000, which matches the backend above

npm run dev
```

The app is now running at `http://localhost:3000`.

## Environment variables

**Backend (`backend/.env`)**

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string (local or Supabase) |
| `CORS_ORIGINS` | No (defaults to `http://localhost:3000`) | Comma-separated origins allowed to call the API |

**Frontend (`frontend/.env.local`)**

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | Base URL of the FastAPI backend |

Neither `.env` file is committed — only the `.env.example` templates are.

## API endpoints (Phase 0)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | API liveness |
| GET | `/api/v1/health/database` | Database connectivity check |
| POST | `/api/v1/incidents` | Create an incident |
| GET | `/api/v1/incidents/{incident_id}` | Fetch one incident |

## What was completed

- Next.js frontend: landing page, `/incident/start` first-step flow,
  reusable progress/error/loading components, mobile-first responsive
  layout, keyboard-accessible controls
- FastAPI backend: modular structure (routes → services → models),
  health + database-health endpoints, incident create/read
- PostgreSQL: `incidents` table via SQLAlchemy models, created
  automatically on backend startup
- Frontend ↔ backend communication via `lib/api.ts`, wired end-to-end on
  the incident-start page (selecting an option and continuing creates a
  real draft incident)
- `docs/product.md` and `docs/architecture.md`
- `.env.example` for both apps, `.gitignore` covering secrets and build
  output

## What remains for Phase 1

- The rest of the incident flow (steps 2–5: incident details, immediate
  actions, evidence collection, report preparation)
- Real triage/urgency logic (Phase 0 uses a simple placeholder rule based
  on amount only — see `backend/app/services/incident_service.py`)
- Evidence upload and processing
- Authentication
- Alembic migrations in place of `create_all` (dependency is already
  installed, migration scripts aren't written yet)

## Assumptions made

- Phase 0's incident-start page submits a draft incident immediately on
  "Continue" (with `payment_method: unknown`) to prove out the frontend
  ↔ backend ↔ database path end-to-end, since deeper UI to capture
  amount/payment method wasn't in scope for this phase.
- The placeholder urgency rule in `incident_service.py` is a stand-in
  only, not the real triage logic mentioned in the product goals.
- No test suite was requested for Phase 0, so none is included yet.
