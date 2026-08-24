# CyberSOS

CyberSOS is an independent prototype that helps people in India respond to a
cyber or financial fraud incident. It guides a person through the facts of an
incident, highlights urgency, suggests immediate actions, preserves evidence
metadata, and prepares a complaint draft for the official reporting channels.

CyberSOS does **not** replace the Government of India's Cyber Crime Reporting
Portal or the 1930 helpline. It does not submit a complaint on the user's
behalf and it is not affiliated with either service.

## What the application does

The current guided flow supports three top-level categories:

- **UPI / financial fraud**: situation, incident type, time, amount, payment
  method, UTR/transaction ID, and optional evidence
- **Other cyber crime**: social media crime, ransomware, hacking,
  cryptocurrency crime, online trafficking, online gambling, and other crime
- **Women/children related cyber crime**: safety, threats or blackmail,
  affected person, platform, account access, online content, and evidence

When the flow is submitted, the backend:

1. Creates an incident record.
2. Validates category-specific fields.
3. Computes an urgency level and score during triage.
4. Builds an ordered action plan, including 1930 and cybercrime.gov.in where
   appropriate.
5. Generates a complaint draft from the structured incident data.
6. Stores uploaded evidence files locally and records their metadata.

The urgency engine is deterministic. For financial fraud it considers how long
ago the incident occurred and whether the amount is at least INR 100,000. The
other categories use explicit safety, exposure, threat, and attacker-activity
signals. This is product logic, not legal or financial advice.

## Architecture

```text
┌─────────────────────┐     HTTP/JSON      ┌─────────────────────┐     SQL      ┌──────────────┐
│ Next.js frontend    │ ─────────────────▶ │ FastAPI backend     │ ──────────▶ │ PostgreSQL   │
│ App Router          │ ◀───────────────── │ /api/v1             │ ◀────────── │ local/Supabase│
└─────────────────────┘                   └─────────────────────┘              └──────────────┘
                                                  │
                                                  └── local evidence files
```

The frontend and backend are separate applications. The frontend only talks
to the backend over HTTP using `NEXT_PUBLIC_API_URL`; it does not access the
database directly.

### Frontend

The frontend is Next.js 14 with the App Router, React, TypeScript, Tailwind
CSS, and Lucide icons.

- `frontend/app/page.tsx` is the landing page.
- `frontend/app/incident/start/page.tsx` owns the guided incident flow and
  its local form state.
- `frontend/app/incident/[id]/result/page.tsx` loads and displays the action
  plan.
- `frontend/components/` contains reusable flow, status, result, and UI
  components.
- `frontend/components/steps/` contains the category-specific questions.
- `frontend/lib/api.ts` is the only API client. It normalizes network,
  timeout, and non-2xx failures into `ApiError` objects.
- `frontend/types/incident.ts` contains TypeScript request and response types
  corresponding to the backend schemas.

Components handle presentation and simple interaction state. Persistence,
validation, triage, urgency, action selection, and complaint generation live
in the backend.

### Backend

The backend is FastAPI with Pydantic, SQLAlchemy, Alembic, Uvicorn, and the
PostgreSQL driver.

- `backend/app/main.py` creates the FastAPI app, configures CORS, mounts the
  API router, and runs the startup schema compatibility check.
- `backend/app/core/config.py` loads environment-based settings.
- `backend/app/api/` contains versioned routers and thin route handlers.
- `backend/app/schemas/` defines request validation and response models.
- `backend/app/services/incident_service.py` contains incident creation,
  triage, urgency scoring, action-plan construction, complaint drafting, and
  evidence storage.
- `backend/app/models/incident.py` defines the `Incident` and `Evidence` ORM
  models and their enums.
- `backend/app/db/` contains the SQLAlchemy base, engine/session setup, and
  additive schema compatibility logic.

Routes call services rather than implementing business rules themselves. This
makes the deterministic rules replaceable later without changing the API
shape or the frontend flow.

### Database and files

The database contains:

- `incidents`: category, payment, amount, timestamps, transaction ID, guided
  details, urgency, score, status, and audit timestamps
- `evidence`: incident relationship, original filename, stored filename,
  content type, size, and creation time

The tracked Alembic revision is in
`backend/alembic/versions/20260824_phase2.py`. On startup, `ensure_schema()`
also creates a fresh schema and applies additive compatibility changes for
older local databases. Evidence file bytes are stored below
`EVIDENCE_STORAGE_DIR` (default `./evidence`) and are limited to 10 MiB per
upload. Production deployments should use durable object storage instead.

For a separate product description and architecture notes, see
[`docs/product.md`](docs/product.md) and
[`docs/architecture.md`](docs/architecture.md).

## Repository layout

```text
cybersos/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routers
│   │   ├── core/            # configuration
│   │   ├── db/              # engine, sessions, schema compatibility
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic contracts
│   │   └── services/        # business logic
│   ├── alembic/             # database migrations
│   ├── tests/               # backend tests
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js routes and pages
│   ├── components/          # reusable UI and flow steps
│   ├── lib/                 # API client and frontend utilities
│   ├── types/               # TypeScript domain types
│   └── .env.example
├── docs/
└── README.md
```

## Setup on a new computer

### Prerequisites

- Git
- Node.js 18.18 or newer and npm
- Python 3.11 or newer
- PostgreSQL 14 or newer, either installed locally or provided by a
  [Supabase](https://supabase.com) project

You need a database before starting the backend. Create a local database and
user, or create a Supabase project and copy its PostgreSQL connection string.
The connection string must be usable by `psycopg2`, for example:

```text
postgresql://cybersos:cybersos@localhost:5432/cybersos
```

### Windows PowerShell

From the repository root:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and set `DATABASE_URL` to your database. The default
`CORS_ORIGINS` already allows the local frontend. Then, still inside
`backend`, apply the migration and start the API:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

In a second PowerShell terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm install
npm run dev
```

If PowerShell blocks activation, run this once in the current terminal and
repeat the activation command:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### macOS or Linux

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `DATABASE_URL` in `backend/.env`, then start the backend:

```bash
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

### Local URLs

- Frontend: <http://localhost:3000>
- API liveness: <http://localhost:8000/health>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

The backend database check is available at
<http://localhost:8000/api/v1/health/database>.

## Configuration

### Backend: `backend/.env`

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | Yes | None | PostgreSQL connection string |
| `CORS_ORIGINS` | No | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated allowed frontend origins |
| `SERVICE_NAME` | No | `cybersos-api` | Service name returned by `/health` |
| `API_V1_PREFIX` | No | `/api/v1` | API version prefix |
| `EVIDENCE_STORAGE_DIR` | No | `./evidence` | Directory for uploaded evidence files |

### Frontend: `frontend/.env.local`

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Base URL of the FastAPI API |

Never commit `.env`, `.env.local`, database credentials, or uploaded evidence.
The example files are safe templates and are committed for setup guidance.

## API reference

All application routes are under `/api/v1`, except `/health`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | API liveness |
| GET | `/api/v1/health/database` | Check database reachability |
| POST | `/api/v1/incidents` | Create a draft incident |
| GET | `/api/v1/incidents/{incident_id}` | Read an incident |
| POST | `/api/v1/incidents/{incident_id}/triage` | Validate details and compute urgency |
| PATCH | `/api/v1/incidents/{incident_id}/details` | Update validated other-crime details |
| POST | `/api/v1/incidents/{incident_id}/evidence` | Upload one evidence file as multipart form data |
| GET | `/api/v1/incidents/{incident_id}/action-plan` | Return urgency, ordered actions, and complaint draft |

FastAPI's interactive documentation at `/docs` is the authoritative view of
request and response fields. Financial triage requires a positive amount and a
known payment method. Other-crime payloads have additional conditional
validation rules defined in `backend/app/schemas/incident.py`.

## Development and verification

Run backend tests from `backend` with the virtual environment activated:

```bash
pytest
```

The test fixture uses SQLite and a temporary schema, so PostgreSQL is not
required to run the backend test suite. It covers incident CRUD, validation,
triage, urgency decisions, action plans, complaint drafts, and evidence
metadata/file persistence.

For the frontend:

```bash
npm run lint
npm run build
```

Run those commands from `frontend`. `npm run dev` starts the development
server; `npm run start` serves a previously built production bundle.

## Current boundaries and future work

Implemented today:

- Guided financial-fraud, other-cyber-crime, and women/children flows
- Deterministic urgency scoring and action plans
- Complaint draft generation
- PostgreSQL persistence and Alembic migration support
- Local evidence uploads and metadata persistence
- Health checks, API documentation, and backend tests

Not implemented yet:

- Authentication, accounts, and incident history for returning users
- AI-generated questions or complaint text
- OCR or evidence-content analysis
- Direct integrations with banks, UPI providers, 1930, or
  `cybercrime.gov.in`
- Automatic government complaint submission
- Notifications and status callbacks
- Multilingual support
- Production object storage, retention policy, and deployment configuration

The project is intended as a citizen-support layer. Official reporting and
emergency decisions remain the user's responsibility, with the official
channels taking precedence over any CyberSOS output.
