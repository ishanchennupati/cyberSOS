# CyberSOS

CyberSOS is an independent cyber-incident support prototype for India. It prepares
information and points users to external reporting channels. It is not a bank,
police service, government service, legal-advice service or fund-recovery service.
It cannot predict recovery, refunds, FIR eligibility or official response times.

Use synthetic data for local development. Private cases now require a case capability; UUID URLs alone do not authorize
access. Retention policy, returning-user authentication and account recovery are
not implemented. Continue using synthetic data; this is not ready for real data.

## CURRENTLY WORKING

- Existing structured guided intake: financial fraud, other cyber crime and
  women/children categories. These are limited existing flows, not comprehensive
  response playbooks or conversational intake.
- Incident create/read and typed, versioned financial response playbooks for
  approved scam payments, unauthorized transactions and unknown authorization.
  Immutable plan revisions, source snapshots and user-owned action completion.
  Existing category validation, complaint drafts, description and template summary.
- Evidence upload/reject/list/view/update/delete, original filename/private path,
  MIME/type, size, SHA-256, description, extraction/verification and timestamps.
- Local text heuristic extraction where supported; explicit extraction failure
  and manual correction for unsupported content/provider failure. No local OCR.
- Suspect identifiers, timeline events and evidence-readiness display.
- Single Evidence ORM and mounted frontend API contracts; HTTP 204 delete and
  backend-origin preview handling.
- Tracked Alembic fresh/legacy schema migrations, isolated SQLite tests and
  synthetic browser smoke. PostgreSQL is supported in configuration/DDL but
  PostgreSQL execution has not been verified in this environment.

Urgency is a product heuristic based on recency and ongoing-risk facts. Reporting amount, transaction ID and uploads do not gate protective actions.
Financial action selection is centralized in app/domain/playbooks.py. Recovery
fields are absent from active HTTP contracts; old database columns remain only
to preserve historical data.

## OPTIONAL PROVIDER-DEPENDENT

Supabase private storage and existing Anthropic extraction/summary adapters are
opt-in. Their SDKs are not included in baseline requirements; configuration alone
does not establish provider availability. Live providers are not verified. Missing
credentials permit local storage, heuristic extraction/manual correction and
template summary fallback. Gemini is intended for future explicitly scoped work;
it is not integrated. AI does not control current deterministic action selection.
See [backend/.env.example](backend/.env.example) for every available setting.

## PLANNED / NOT YET IMPLEMENTED

Conversational/voice intake, conversation-state controller, broader cybercrime
playbooks, Gemini, multilingual support, retention policy, account authentication
and returning-user recovery are not implemented. Phase 1 provides the financial
domain foundation; Phase 2 has not started. See [roadmap](docs/roadmap.md).

## NO REAL GOVERNMENT INTEGRATION

CyberSOS does not submit complaints, call government APIs, receive official
confirmations or track live police/bank/government progress. The user must review
and submit reporting information independently. Keep any actual reference received
from the official service; local records and synthetic demo tickets do not prove
receipt. External links are handoffs. No recovery or response-time promise.

## Stack and local setup

Next.js 14/React/TypeScript/Tailwind frontend; FastAPI/Pydantic/SQLAlchemy/Alembic
backend. Python 3.11+ and Node 18.18+ match the repository's existing baseline.
Run the following from the repository root in PowerShell for a new environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Frontend setup, CWD frontend:

```powershell
npm ci
```

Keep credentials in ignored local environment files. Copy the example only if
no local file exists. DATABASE_URL is required; temporary SQLite works locally,
so PostgreSQL/cloud credentials are not required for development verification.
All settings are documented in backend/.env.example and frontend/.env.example.

Backend start, CWD backend (set a synthetic local DB/storage directory):

```powershell
$env:DATABASE_URL='sqlite:///./local.sqlite'
$env:LOCAL_STORAGE_ROOT='./evidence'
$env:CASE_COOKIE_SECURE='false' # HTTP localhost with synthetic data only
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Frontend start in a second terminal, CWD frontend:

```powershell
npm run dev
```

Default frontend http://localhost:3000; backend http://localhost:8000/health.
Swagger http://localhost:8000/docs is authoritative for all mounted API methods,
parameters and responses. NEXT_PUBLIC_API_URL defaults to http://localhost:8000;
CORS_ORIGINS must allow the frontend origin. PostgreSQL connection strings may be
used instead of SQLite; do not apply unverified upgrades to real data casually.

## Migrations and verification

Startup performs no DDL. Head is 20261001_response_foundation; the first baseline
uses explicit historical DDL rather than create_all. Before an existing-schema
upgrade, back up database and original evidence, set LOCAL_STORAGE_ROOT to the
previous EVIDENCE_STORAGE_DIR and run alembic upgrade head from backend. Supports
the audited legacy schema unversioned or stamped at either previous revision.
Existing incident/evidence values, private paths and timestamps survive tested
SQLite upgrades. Legacy hashes are backfilled only from available original bytes;
missing MIME/hash remains null. Files are not moved. Consolidation is forward-only;
rollback requires backup restore. No existing database was migrated during cleanup.

Backend tests, CWD root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -c backend/pytest.ini -q -p no:cacheprovider
```

Tests create a session-private migrated SQLite DB, per-test temporary evidence,
reset rows between tests and clean up. They never use shared ./test.db. Full suite
includes fresh schema parity, all supported legacy upgrade cases, OpenAPI/API
contracts, evidence/suspect/timeline CRUD and wording regressions.

Frontend verification, CWD frontend:

```powershell
node --test __tests__/api-contract.test.cjs
npm run lint
npm run build
```

Synthetic real-browser smoke requires the production build plus an existing
Playwright driver/cached Chromium. Exact environment-specific tested invocation
and manual smoke steps are in [verification.md](docs/verification.md).
No live-provider/manual success is implied by local automation.

## Canonical documentation

- [Current product](docs/product.md), [architecture](docs/architecture.md)
- [Action rules](docs/action-engine.md), [official sources](docs/official-sources.md)
- [Roadmap/status](docs/roadmap.md), [phase evidence](docs/phase-status.md)
- [Verification commands/results](docs/verification.md)
- [Historical docs](docs/legacy/README.md): obsolete phase numbering/proposals
- [Audit](docs/audit.md): historical findings plus resolution appendices

## Private cases and Phase 1

Case creation sets a per-case HttpOnly, SameSite Strict cookie; production Secure
cookies default on. Use localhost for BOTH frontend and backend during development
and set CASE_COOKIE_SECURE=false only for local HTTP. Requests include cookies;
never copy a case secret into a URL, query, localStorage or a log. API clients may
use X-Case-Secret in a header. Capabilities expire after seven days by default.
Missing, expired and cross-case credentials receive 404 on every private resource,
including original evidence. Clearing cookies loses local access.

The additive Phase 1 migration preserves old incidents/evidence, marks historical
cases legacy_unversioned and leaves their capability unset. Those cases stay locked;
there is no public claim/reset endpoint. Owner-verified administrative recovery is
not implemented. Back up existing data; a UUID is never accepted as ownership.

Evidence policy rejects declared prohibited content and recognizable labelled
credentials in text/metadata. It is a policy foundation, not image moderation or a
guarantee that all sensitive content is detected. AI output cannot select critical
actions. Completion means only the user says they acted, not official confirmation.
See [architecture](docs/architecture.md), [sources](docs/official-sources.md) and
[verification](docs/verification.md) for contracts, review limits and exact checks.

## Code organization

| Location | Responsibility |
| --- | --- |
| backend/app/domain | Typed facts, deterministic playbooks, sources and evidence policy |
| backend/app/api/routes | HTTP validation, authorization and service calls |
| backend/app/services/incident_service.py | Incident persistence, triage and versioned financial plan integration |
| backend/app/services/incident_presentation.py | Complaint formatting and display labels |
| backend/app/services/legacy_incident_service.py | Existing nonfinancial category responses |
| backend/app/services | Case access, response snapshots, evidence/storage, summary, suspect and timeline operations |
| backend/app/models / schemas | Database mappings / validated API contracts |
| backend/alembic / tests | Tracked migrations / synthetic regression fixtures and tests |
| frontend/app | Next.js routes and page rendering |
| frontend/features/incident-intake | Existing guided intake state, validation and API orchestration |
| frontend/components / lib / types | Reusable UI / API and utilities / TypeScript contracts |
| docs | Current decisions, verification, phase evidence and labelled historical documents |

This organization preserves the existing guided flow; it does not implement
Phase 2 conversation features. Test matrices retain financial/access/migration
coverage; duplicate legacy matrix assertions are combined rather than repeated.
Default frontend builds still use .next. CYBERSOS_BUILD_DIR=.next-check permits
isolated verification alongside a running development server; the check directory
is ignored. Alternate smoke ports must match NEXT_PUBLIC_API_URL at build time.
See the latest cleanup verification record for the exact commands.
