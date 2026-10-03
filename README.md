# CyberSOS

CyberSOS is an independent cyber-incident support prototype for India. It prepares
information and points users to external reporting channels. It is not a bank,
police service, government service, legal-advice service or fund-recovery service.
It cannot predict recovery, refunds, FIR eligibility or official response times.

Use synthetic data for local development. Private cases now require a case capability; UUID URLs alone do not authorize
access. Retention policy, returning-user authentication and account recovery are
not implemented. Continue using synthetic data; this is not ready for real data.

## Product journey and approved enhancements

CyberSOS is an AI-first companion: explain an incident once, receive useful help,
review the developing case and prepare information for official reporting.

The approved Phase 5 hybrid experience opens inside chat with three optional portal
entry choices: **Women/Children Related Crime**, **Financial Fraud** and **Other
Cyber Crime**, plus **Not sure** and immediate natural input. These are changeable
routing hints, not confirmed facts or mandatory classification. The LLM offers
contextual recommended answer buttons throughout the conversation; citizens may
tap, type or attach evidence. Voice joins in Phase 9. No fixed questionnaire,
required long narrative or repeated known information.

The case builds quietly. With enough relevant understanding, the citizen reviews
it and receives a personalized fuller response plan. Individually justified urgent
actions appear earlier and compactly. AI understands and explains; backend policy
validates critical actions against reviewed official guidance. "I lost 5000" alone
must not establish a bank payment or trigger a generic financial checklist. Internet
retrieval supplies supporting reviewed knowledge, not unrestricted action authority.

From Phase 6, reviewed information maps to applicable official portal fields, with
field-by-field copy, narrative copy and secure PDF/export. The citizen reviews and
submits on the official destination. Uploading our PDF is not assumed to populate
or replace its form. The continuing case remains open to corrections and new evidence.

## Currently implemented foundations

- Phase 4 direct conversation, natural text, optional quick replies, relevant
  questions, corrections, skip/pause, persisted exchanges and source-linked case
  memory/older recall. Reviewed local retrieval supplies supporting knowledge.
- Persistent multiline composer, JPG/JPEG/PNG/PDF chat attachments, upload progress,
  cancellation, private previews, durable turn links, retry/replay and session drafts.
- Current backend-derived plan and lightweight View case. Typed financial playbooks
  distinguish scam-authorized payments, unauthorized transactions and unknown
  authorization; action completion records what the citizen says they did.
- Case-scoped authorization and incident/evidence/identifier/timeline contracts.
  Existing extraction, verification, draft and summary adapters are foundations,
  not proof of the Phase 5 intelligence or Phase 6 reviewed reporting experience.
- Local text heuristics where supported; no local OCR or demonstrated chat image
  analysis. Unsupported content needs honest failure/correction handling.
- Tracked migrations and synthetic tests. The configured development PostgreSQL
  database was migrated to `20261003_chat_attachments` during the Phase 4 runtime
  repair; actual chat, attachment and reload requests were verified there.

Evidence and limitations are in [Phase 4 acceptance](docs/phase4-acceptance.md).
The approved three-choice hybrid entrance, improved plan applicability/presentation,
consistent branding and assistant pending-message UI are planned Phase 5 changes,
not capabilities already demonstrated by the current app. Existing nonfinancial
signals do not establish comprehensive nonfinancial safety coverage.

## Provider-dependent capability and evidence

Gemini understanding and follow-up use the configured provider/model and bounded
case context; use synthetic data only. Phase 4 recorded live English/Roman Telugu/
Hinglish journeys, and the configured-runtime repair verified both live AI stages
and browser rendering. Quota, timeout and validation failures still require honest
fallback; successful tests do not guarantee availability or universal language support.
See [Phase 4 acceptance](docs/phase4-acceptance.md) and historical
[Phase 3/3R notes](docs/phase3-understanding.md) for the respective results.

Supabase private storage and existing Anthropic extraction/summary adapters remain
optional. Do not infer hosted storage or live evidence extraction/drafting readiness
from configuration or text-conversation tests. Missing credentials permit local
storage and supported heuristic/template fallbacks. AI does not independently
authorize critical actions. [Settings reference](backend/.env.example).

## Revised roadmap — planned, not implemented

Each capability is delivered and verified across declared supported scenarios in
all three entry points using one shared conversation/case system. The three labels
do not imply support for every cybercrime. Initial reviewed nonfinancial coverage
moves into Phase 5; Phase 8 expands it.

| Phase | Planned delivery |
| --- | --- |
| [5](docs/phases/phase-05.md) | Hybrid entrance and recommended answers throughout chat, initial three-route coverage, evidence intelligence, personalized action applicability and UI refinements |
| [6](docs/phases/phase-06.md) | Reviewed portal-aligned complaint fields/narrative, copy/export and truthful official handoff |
| [7](docs/phases/phase-07.md) | Full continuing case companion, timeline, secure return and lifecycle/deletion |
| [8](docs/phases/phase-08.md) | Expand scenarios and deepen reviewed guidance across the existing routes |
| [9](docs/phases/phase-09.md) | Multilingual voice input, editable transcript and reviewed language experience |
| [10–12](docs/phases/README.md) | Security/privacy acceptance, authorized deployment rehearsal, synthetic beta and gated final acceptance |

Voice, full localization, reviewed portal-field reporting, comprehensive incident
coverage, long-term recovery and production retention are not yet implemented.
The [shared phase contracts](docs/phases/README.md) govern future execution;
[AGENTS.md](AGENTS.md) defines permanent product/engineering rules. Older
[roadmap records](docs/roadmap.md) are historical where they conflict with these
approved updates. Future requirements do not authorize building later phases early.

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

Backend start, CWD repository root (explicit synthetic local database/storage;
Gemini configuration still comes from `backend/.env`):

```powershell
.\.venv\Scripts\python.exe backend/run_local.py
```

Stop an existing backend on port 8000 before using the launcher. It selects
`backend/local.sqlite` explicitly, backs up existing local data to ignored
`backend/tmp`, applies tracked migrations, uses local evidence storage and HTTP
development cookies. It never migrates the remote database from `.env`. Settings
load `backend/.env` independently of the launch directory; shell environment
variables still take precedence and require a process restart when changed.

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

### AI diagnostics and free-tier development

Phase 3R uses two provider stages: candidate fact extraction, then a case-aware
conversational proposal after validation and deterministic playbook evaluation.
HTTP 200 means the turn was saved; it does not prove either AI stage succeeded.
Fallback preserves the case but is not the intended normal AI conversation.

The current development default is `gemini-3.5-flash-lite`. Its stable endpoint,
structured output support and free-tier availability were checked against
[Google's model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
and [pricing](https://ai.google.dev/gemini-api/docs/pricing) on 2026-10-02.
It passed all four synthetic live browser scenarios and a correction/history check
with the configured project. This is a development choice for low latency and free-tier
extraction; it is not a claim of superior reasoning or guaranteed availability.
Actual [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) are project-specific;
each message normally needs two calls. Changing keys within the same project does
not increase quota. Keep testing synthetic: Google's free tier may use submitted
content to improve its products. No billing, paid tier or alternate provider is enabled.

Backend diagnostics appear in the terminal and, by default, ignored
`backend/tmp/logs/cybersos-<process-id>.jsonl`. Each process has its own file to
avoid Windows rotation conflicts; files rotate at 1 MB with two backups per process.
Set `DIAGNOSTICS_LOG_DIR` to a private directory, or blank to disable file logs.
Delete local diagnostic files when no longer useful; no case content is retained
in them. Browser DevTools Console shows `[CyberSOS diagnostic]` events for HTTP,
network, timeout, malformed responses, AI fallback, rendering and runtime errors.
Browser logs are local console diagnostics, not uploaded telemetry.

Use the `X-Request-ID` response header to correlate a browser event with backend
`http_request`, `ai_stage` and `request_error` events. AI stages are `extraction`
and `follow_up`; errors distinguish quota, authentication, missing model, provider
5xx, timeout, malformed output, validation rejection and application errors.
The default single retry applies to transient provider/network failures only and
remains within each stage's existing deadline; `ai_retry` records attempts. Quota,
authentication, missing-model and invalid-output failures go directly to honest fallback.
Safe stack locations identify code failures without logging exception messages,
locals, SQL parameters, stories, evidence, cookies, keys or raw provider responses.
Raw Uvicorn access logs are suppressed in favor of sanitized route templates.

After changing `.env`, restart the backend; a running process caches settings.
For the configured hosted development database, apply the tracked migrations from
`backend` before starting the updated application (no migrations at startup):

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --no-access-log
```

The local SQLite launcher above is still available when explicitly choosing local
development storage. Existing hosted cases remain on the hosted database.

Startup performs no DDL. Head is 20261003_chat_attachments; the first baseline
uses explicit historical DDL rather than create_all. Before an existing-schema
upgrade, back up database and original evidence, set LOCAL_STORAGE_ROOT to the
previous EVIDENCE_STORAGE_DIR and run alembic upgrade head from backend. Supports
the audited legacy schema unversioned or stamped at either previous revision.
Existing incident/evidence values, private paths and timestamps survive tested
SQLite upgrades. Legacy hashes are backfilled only from available original bytes;
missing MIME/hash remains null. Files are not moved. Consolidation is forward-only;
rollback requires backup restore. The historical cleanup did not migrate existing databases; the later Phase 4
runtime repair applied the additive chat-attachment migration to the configured
development PostgreSQL database. See its acceptance record for exact evidence.

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
- [Approved phase roadmap/contracts](docs/phases/README.md), [Phase 4 evidence](docs/phase4-acceptance.md)
- [Earlier roadmap/status](docs/roadmap.md), [earlier phase evidence](docs/phase-status.md): historical where superseded
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
| backend/app/services/conversation_service.py | Durable progression, corrections, idempotency and optimistic concurrency |
| frontend/components/conversation.tsx | Primary conversation, actions, retry and accessible structured replies |
| frontend/types/conversation.ts | Typed conversation requests, state, facts and history |
| frontend/features/incident-intake | Retained legacy wizard source, unused by primary intake |
| frontend/components / lib / types | Reusable UI / API and utilities / TypeScript contracts |
| docs | Current decisions, verification, phase evidence and labelled historical documents |

Phase 2 replaces primary wizard intake; existing drafts and evidence remain
reachable. Test matrices retain financial/access/migration
coverage; duplicate legacy matrix assertions are combined rather than repeated.
Default frontend builds still use .next. CYBERSOS_BUILD_DIR=.next-check permits
isolated verification alongside a running development server; the check directory
is ignored. Alternate smoke ports must match NEXT_PUBLIC_API_URL at build time.
See the latest cleanup verification record for the exact commands.
