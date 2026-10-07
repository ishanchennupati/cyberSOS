# Phase status

## Phase 5 implementation — 2026-10-07

**Quality-audit correction:** subsequent offline reproductions confirmed repeated
fallback money questions in harassment cases, ignored plan/conclusion requests and
lost explicit pause on understanding failure. Remaining work includes application
conversation behavior, not solely live-provider reliability. See
[phase5-conversation-quality-audit.md](phase5-conversation-quality-audit.md).

User-approved execution order, 2026-10-07: the next Phase 6 implementation request
must first execute and verify the conversation repair checkpoint in
[phase-06.md](phases/phase-06.md). Reporting work cannot begin until that gate
passes. This update records future scope/order; repairs and Phase 6 reporting
have not been implemented by this documentation change.

**IMPLEMENTED; LOCAL ACCEPTANCE PASS; COMPREHENSIVE LIVE ACCEPTANCE OPEN.**
Hybrid entry hints, initial three-route policy and owned native-file candidate review
are implemented through the existing conversation/canonical-case architecture.
Final backend: 470 passed; frontend contracts: 13 passed; production build, Phase 5
fake-provider browser, Phase 4 regression and desktop/mobile scroll tests passed.
Configured PostgreSQL additive migration and private-storage integration passed
(fake AI). Real PNG/JPEG/PDF extraction, natural financial conflict review and safe
nonfinancial extraction were exercised; Roman Telugu/Hinglish two-turn live
regressions passed. Comprehensive live quality remains open due to provider timeout
and rejected follow-up wording; a scoped account run also failed question-field
validation. Do not claim a clean live acceptance pass or production readiness.
See [phase5-acceptance.md](phase5-acceptance.md) for exact commands/evidence and
[phase5-support-matrix.md](phase5-support-matrix.md) for limits. Roadmap NO CHANGE;
no Phase 6, model switch, billing, commit or deployment.

## Phase 3R longer-session payment repair — 2026-10-02

**PASS:** canonical payment names, bounded natural confirmation/rejection and
question-target binding. Backend 380 tests and frontend 13 tests pass. Final live
Gemini mobile browser passes six turns, both AI stages, amount correction and reload;
separate live pending confirmation passes. Initial provider 429 recorded distinctly.
See [phase3r-payment-repair.md](phase3r-payment-repair.md). Roadmap NO CHANGE;
Phase 4 not started. Earlier acceptance did not cover the later verification loop.

## Phase 3R final acceptance — 2026-10-02

**PASS:** live extraction, next-move reasoning, validation and actual browser
rendering for all four requested stories. Final B/A also passed on actual local
development servers 3000/8000. Backend 361 tests, frontend 13 tests, lint, fresh
build, fake-provider mobile/resume journey and live correction passed. See
[phase3r-acceptance.md](phase3r-acceptance.md) for current runtime, exact evidence,
remaining limitations and roadmap NO CHANGE. No Phase 4, commit or deployment.

## Step 0A — Repository audit

Date: 2026-09-30. Branch: `phase-0`. HEAD: `cadb2d7986b9c053a1262742a650544c283daa7c`.
Prerequisite: none (explicit prompt). No phase-status file existed before this step.
Scope: documentation only. **Audit deliverables complete; application baseline FAIL.** No fix or next step started.

### Requirements

| Requirement | Status | Evidence |
| --- | --- | --- |
| R1 | done | [verification.md](verification.md): exact baseline commands/CWD/prerequisites, actual results and failed sandbox attempts. Full suite 161 passed / 2 failed; lint/build passed; fresh temporary SQLite Alembic passed. |
| R2 | done | [audit.md](audit.md), suspected-issue register a–g: source file:line evidence plus duplicate-model reproduction. Roadmap comparison explicitly UNCLEAR because roadmap absent. |
| R3 | done | [audit.md](audit.md), complete 25-row frontend API matrix and eight mounted OpenAPI operations. Corrected runtime comparison confirms 19 missing operations. Mounted upload contract mismatch separately documented. |
| R4 | done | [audit.md](audit.md), claim inventory: recovery predictions, FIR/₹100,000 gate, NPCI/bank/timing assertions, current versus legacy reachability, tests enforcing them and negative findings. |
| R5 | done | [audit.md](audit.md), proposed ordered 0B/0C work and decisions required before implementation. |

### Separate verification outcomes

| Result class | Actual result |
| --- | --- |
| Local automated application baseline | **FAIL** — 2 backend tests fail; lint and build pass; fresh SQLite Alembic reaches head. Not an overall automated pass. |
| Local automated audit checks | **PASS** — corrected OpenAPI comparison executed and identifies mismatches; document consistency/scope checks and git diff --check passed. Audit checks do not convert missing routes into working ones. |
| Live-provider pass | **NOT RUN** — no live AI/storage/PostgreSQL provider verification. |
| Manual application pass | **NOT RUN** — no browser/keyboard/mobile/speech journey. |
| Documentation consistency review | **PASS** — source citations, call count, requirement coverage, commands and failure status reviewed. This is not a manual application pass. |

### Executed commands, working directories and results

Repository root R = `C:\Users\Ishan Chennupati\Downloads\cybersos`. Commands below use PowerShell.

Backend suite, launcher CWD R; execution CWD changed to a fresh OS temporary directory, pytest root/config R/backend:

```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile,pytest; from pathlib import Path; root=Path.cwd(); tmp=tempfile.mkdtemp(prefix='cybersos-0A-tests-'); print('Temporary working directory:',tmp,flush=True); os.chdir(tmp); raise SystemExit(pytest.main(['-c',str(root/'backend/pytest.ini'),str(root/'backend/tests'),'-v','-p','no:cacheprovider']))"
```

Initial sandbox attempt: exit 1, WinError 5 before collection. Approved identical retry: exit 1, 163 collected, 161 passed, 2 failed in 4.29s. Failures at `backend/tests/test_incidents_api.py:57` and `:89`, low versus expected critical; fixed August fixture and September real clock. Actual temp paths/prerequisites in verification.md.

Frontend CWD R/frontend:

```powershell
npm run lint
npm run build
```

Independent commands, both exit 0. Lint: no warnings/errors. Build: compilation, lint/types, static pages and traces completed.

Fresh Alembic launcher CWD R, migration CWD R/backend:

```powershell
.\.venv\Scripts\python.exe -c "import os,tempfile; from pathlib import Path; from alembic.config import Config; from alembic import command; from sqlalchemy import create_engine,inspect,text; root=Path.cwd(); tmp=Path(tempfile.mkdtemp(prefix='cybersos-0A-alembic-')); url='sqlite:///'+(tmp/'fresh.db').as_posix(); os.environ['DATABASE_URL']=url; os.chdir(root/'backend'); print('Working directory:',Path.cwd(),flush=True); print('Fresh database:',url,flush=True); cfg=Config('alembic.ini'); command.upgrade(cfg,'head'); eng=create_engine(url); print('Tables:',inspect(eng).get_table_names()); print('Revision:',eng.connect().execute(text('select version_num from alembic_version')).all())"
```

Initial sandbox attempt exit 1 unable to open temporary SQLite file. Approved identical retry exit 0: version 20260824_urgency_metadata; tables alembic_version/evidence/incidents. PostgreSQL and prior-schema upgrades NOT RUN.

OpenAPI and intentional collision probe, CWD R/backend:

```powershell
$env:DATABASE_URL='sqlite:///:memory:'; $env:CORS_ORIGINS='http://testserver'; ..\.venv\Scripts\python.exe -c "from app.main import app; import json; schema=app.openapi(); print(json.dumps({p:{m:{'operationId':v.get('operationId'),'response':v.get('responses',{}).get('200',v.get('responses',{}).get('201',{}))} for m,v in ops.items()} for p,ops in schema['paths'].items()},indent=2)); import app.models.evidence"
```

Eight mounted operations generated; intentional second Evidence import exit 1 InvalidRequestError confirms duplicate table. This is a successful bug reproduction, not a passing baseline.

Corrected comparison, CWD R/backend: exact multiline command in [verification.md](verification.md), “Corrected automatic frontend/OpenAPI comparison”; exit 0, TOTAL 25 MISSING 19. Earlier delimiter-parser result was rejected and not used.

Documentation consistency script, CWD R: exact command in verification.md, “Documentation consistency check”; corrected standalone execution exit 0. Confirmed R1–R5 coverage, 25 API rows, 19 missing/6 matching, explicit unavailable result classes, balanced code fences and no application tracked diff. Initial checker asserted an overly specific uppercase phrase in the narrative audit and failed; that attempt is recorded and is not passing evidence.

Final checks, CWD R:

```powershell
git diff --check
git diff --name-only
git status --short
git branch --show-current
```

Exit 0. Branch phase-0. Existing tracked modification AGENTS.md was preserved. Only new files for this step: docs/audit.md, docs/verification.md, docs/phase-status.md. No tracked application/test/migration/schema/dependency/generated database/evidence file changes. Git warns about unreadable pytest caches and expected LF/CRLF normalization; no whitespace errors.

### Completion report

Changed files: [audit.md](audit.md), [verification.md](verification.md), this file. They establish actual behavior, failed baseline evidence, full API mismatches and proposed next-step order.
Root causes: two Evidence ORM definitions/contracts, unmounted/incomplete vault routes, mutable startup schema lifecycle, missing configuration/model attributes, time-dependent API fixtures, duplicate/stale documentation, prohibited recovery/threshold claims.
Architectural decision: none implemented; consolidation/migration/contracts proposed only.
Migration/API changes: none. Tests added/changed: none (documentation-only). Commits/push/deploy/spending: none.
Assumptions: current source is authoritative; existing data preserved; temporary synthetic SQLite baseline is narrower than PostgreSQL proof.
Remaining limitations: baseline remains failing; 19 API operations absent; no live-provider/manual application pass; roadmap and scenarios fixture absent; real-data privacy/authorization prerequisites remain unresolved.
Phase gate: audit requirements are satisfied, but **no fully passing application baseline is recorded**. Consult the next step's explicit prerequisite definition; do not silently label these failures passed or start 0B.

## Step 0B — Consolidate evidence, routes and migrations

Date: 2026-09-30. Branch phase-0. Prerequisite: recorded 0A audit and passing
documentation checks; failing application baseline explicitly accepted for repair
by 0B prompt. Read audit.md first. PLAN-FIRST: plans/0B.md written before edits.
Scope: existing contract consolidation only. **0B complete locally.**

| Requirement | Status | Evidence |
| --- | --- | --- |
| R1 | done | Sole Evidence/rich fields/upload; backend/tests/test_evidence_contract.py:32, :71, :218 |
| R2 | done | All 25 frontend method/path pairs mounted once, full CRUD/missing contracts; test_evidence_contract.py:41, :153, :199; frontend API contract tests |
| R3 | done | Explicit historical baseline + additive 20260930_evidence_contract, no startup DDL; test_evidence_contract.py:60, test_migrations.py:43 |
| R4 | done | Five fresh/legacy SQLite cases, unversioned and both old revision stamps; backend/tests/test_migrations.py:27, :43, :87 |
| R5 | done | Session-private migrated DB/temp storage/row resets/disposal in tests/conftest.py; test_config.py:33 |
| R6 | done | Settings/.env.example coverage and absent-cloud local operation; backend/tests/test_config.py:7 |
| R7 | done | Thin routes delegate evidence/incident/suspect/timeline services; regression CRUD and browser pass |

### Separate results

| Class | Actual result |
| --- | --- |
| Local automated | PASS: 188 backend, 4 frontend contract tests, lint/build, fresh/current-schema SQLite migrations, existing browser journey |
| Live-provider | NOT RUN: PostgreSQL, live storage/AI |
| Manual application | NOT RUN: browser journey automated |
| Documentation/final diff | PASS: consistency checker and git diff --check exit 0; artifact/scope scan passed, recorded in verification.md |

Exact commands, CWD, prerequisites and failures: verification.md Step 0B section.
Final backend exit 0 (188 passed in 3.84s); Node/lint/build exit 0; final browser
exit 0 after Windows DB cleanup correction. Independent review found verified
extraction overwrite; two red regressions pass after 409 protection.

### Completion report

Changed files: canonical models/contracts, mounted routers/thin handlers/services,
Settings/example, Alembic baseline/new migration, isolated tests/synthetic fixtures,
frontend API boundary, smoke helpers, README/architecture and audit/verification/
status/plan. Root cause: competing contracts, unmounted routes, settings drift,
mutable startup schema and shared/time-dependent fixtures.

Architecture: one Evidence model, service-owned logic and Alembic-owned DDL.
Missing endpoints use existing readiness/template services and real persistence.
API: restored frontend contracts, backend-origin previews/204 handling; verified
re-extraction returns 409. Migration: head 20260930_evidence_contract preserves
tested current-schema incidents/evidence/files; no existing database migrated.
Tests: contract/config/fresh-and-legacy migration coverage, upload rejection/
fallback/verification/suspect/timeline CRUD, frontend boundary and browser.

Assumptions: audited old schema, configured previous storage root, synthetic usage.
Limitations: PostgreSQL/live-provider/manual NOT RUN; absent legacy MIME/hash null;
real-data authorization/retention remains open. 0C findings retained unchanged.
No new AI/dependencies/chat/playbooks/redesign/wording, commit/push/deploy/spending.
No further 0B decision needed. Stop here.

## Step 0C — Final baseline cleanup

Date 2026-09-30; branch phase-0. Prerequisite 0B passing backend/lint/build/
migration/automated smoke read and confirmed before editing. Scope final Phase 0
cleanup only. **Phase 0 complete for the local synthetic baseline.**

Requirement labels follow the prompt's numbered sections:
| Requirement | Status | Evidence |
| --- | --- | --- |
| R1 claims | done | rules/action_rules.py/constants.py and services/incident_service.py; schemas suppress stale predictions; frontend claim text rewritten; test_phase0c_truth.py and official-sources.md |
| R2 hygiene | done | .gitignore; cached removal of test.db/tsconfig.tsbuildinfo with local files retained; tracked-artifact regression; final Git checks |
| R3 documentation | done | README current/optional/planned/no-government distinctions; canonical product/architecture/action-engine/roadmap; obsolete docs/docs archived in docs/legacy |
| R4 commands | done | README setup/start; verification.md Phase 0C actual CWD/commands/results/temp DB/storage/migration/smoke instructions |
| R5 final regression | done | 205 backend, four frontend contracts, lint/build, standalone fresh CLI migration, all supported legacy upgrade cases and browser smoke pass |
| R6 acceptance | done | Local 0B contracts preserved, prohibited active claims removed, wording/artifact guards and honest README; no Phase 1 |
| R7 report | done | Verification record and final response restricted to requested cleanup/results/manual steps/remaining limits |

Local automated PASS: final backend exit 0 (205 passed in 4.07s), frontend request
tests 4 passed, lint/build exit 0, fresh Alembic CLI exit 0, upgrade/OpenAPI/API cases
in full suite passed, real synthetic browser exit 0 with cleanup. Commands/CWD/
prerequisites and red/failed initial runs in verification.md Phase 0C section.
Manual NOT RUN; live-provider/PostgreSQL NOT RUN. Automated browser is not manual.

Claims removed/rewritten: recovery/reversal predictions, windows, NPCI reversal
assumptions, bank/police/timing/insurance guarantees and amount-gated FIR/escalation;
no government submission/status or always-AI summary implication.
Hygiene: untrack generated files without deleting local bytes; ignore runtime
output; preserve .env secrets, migrations, fixtures, lockfiles and prior user edits.
Docs: canonical capability/status/start/verify instructions; explicit legacy archive.
Tests: 17 new claim/stale-value/artifact cases, updated entrenched rules/draft/API
expectations, fixture expectations and browser truth assertions.

Remaining blockers: none for local Phase 0. Real-data authorization/retention and
PostgreSQL/live-provider execution remain separate limitations. No real database
migration, new Phase 1 architecture, commit/push/merge/deploy/spending.

## Step 1 / Phase 1 - Incident domain and deterministic response foundation

Date 2026-10-01; branch phase-0. Prerequisite: 0C local passing evidence read before
editing. Plan docs/plans/1.md written first. **Phase 1 local acceptance complete.**
Requirement labels follow that implementation plan and cover the full prompt:

| Requirement | Status | Evidence |
| --- | --- | --- |
| R1 typed domain/playbooks/sources | done | app/domain/facts.py,response.py,playbooks.py,sources.py,policy.py; strict approved/unauthorized/unknown, null semantics, stable IDs/phases/minimum facts/priority, version registry, future-question seam, no AI/provider selection/recovery contracts; scenarios.yaml and test_phase1_playbooks.py |
| R2 persistence/additive migrations | done | Incident versions/facts/revision; response_plans/action_completions; 20261001_response_foundation preserves Phase 0; immutable source/fact/action snapshots; test_migrations.py/test_phase1_migrations.py/test_phase1_response.py |
| R3 private access/completion/evidence foundation | done | case_access.py hashes 256-bit capability, constant-time check, expiry, HttpOnly/Secure/Strict cookie/header; all current private routes incl originals protected; 29-operation cross-case matrix; source evidence owner gate, completion self-report, prohibited content and credential checks |
| R4 preserve financial journey/thin adapters | done | incident_service.py delegates financial actions to engine, nullable reporting inputs, canonical ResponseAction; deprecated old financial wrappers; frontend cookies/instruction/authorization mapping/resume; successful real browser; triage persistence review regression |
| R5 tests/docs/acceptance | done | 288 backend tests, five frontend contracts, lint/build, fresh and Phase 0 upgrade, OpenAPI, financial smoke and auth matrix PASS; verification.md exact commands/results and failed runs; README/architecture/action-engine/product/roadmap/sources updated |

Final commands/CWD (full prerequisites and fresh wrapper in verification.md):
- R: .\.venv\Scripts\python.exe -m pytest backend/tests -c backend/pytest.ini -q -p no:cacheprovider --tb=short -> exit 0, 288 passed in 19.65s.
- R/frontend: node --test __tests__/api-contract.test.cjs -> exit 0, 5 passed;
  npm run lint -> exit 0, no warnings/errors; npm run build -> exit 0.
- R wrapper invokes python -m alembic upgrade head from backend on fresh temporary
  SQLite -> exit 0, head 20261001_response_foundation. Full-suite Phase 0 upgrade PASS.
- R: PLAYWRIGHT_PACKAGE and PYTHONPATH=backend; python backend/tests/smoke_local.py
  using root .venv -> exit 0, financial browser PASS, temporary data/servers removed.
- R: git diff --check / git diff --cached --check -> exit 0; tracked-artifact
  listing empty; 83 changed/new text secret/control-marker checks PASS.

Local automated PASS. Live-provider/PostgreSQL NOT RUN. Human manual NOT RUN;
checklist in verification.md. Focused independent review found refresh discarding
pending triage fields; reproduced and fixed with flush-before-refresh/status sync,
regression includes financial and category-change paths. No other material review
finding. Failed attempts/fixture corrections recorded honestly in verification.md.

Architecture/API: typed facts -> deterministic versioned playbook -> immutable
plan/actions; facts/response-plan/plans/completions and plan/action completion routes
are additive and private. Existing financial UI works; no chat. Recovery fields
removed from active responses; legacy DB values preserved. Official source review
2026-10-01 in central runtime registry/documented primary references; no liability,
refund/recovery or government outcome promises.

Material limits: legacy_unversioned cases locked with no inferred ownership/facts;
no account/capability recovery or retention readiness; seven-day default capability
expiry; evidence restrictions foundation lacks semantic image moderation; live
providers/PostgreSQL unverified. No blocker for requested local synthetic scope.
Phase 2 conversation/AI/voice/languages/broader playbooks/government tracking,
Phase 5 extraction and dashboards/notifications NOT STARTED. No commit/push/merge/
deploy/spending; Phase 0 and unrelated user edits preserved.

## Phase 1 live-development follow-up: missing playbook_id

2026-10-01: user reported live POST /api/v1/incidents -> 500, SQLite
OperationalError: incidents has no column named playbook_id. The terminal's
DATABASE_URL override used backend/local.sqlite at 20260930_evidence_contract;
a separate shell defaulted to PostgreSQL. Only read-only schema inspection was
performed on that PostgreSQL connection; it was not migrated or changed.

R1 diagnosis DONE: read traceback, checked running health and local SQLite schema.
R2 fix DONE: SQLite backup saved under ignored backend/tmp/migration-backups/
local-before-phase1-20261001-012002.sqlite; applied existing tracked revision to
20261001_response_foundation. Before/after comparison confirmed every pre-existing
incident field unchanged. No application code, new migration or data reset.

Execution CWD backend: root .venv interpreter invoked as
..\.venv\Scripts\python.exe - with a Python stdin wrapper that used sqlite3.backup,
set DATABASE_URL to the absolute backend/local.sqlite path, cleared Settings cache,
and called alembic.command.upgrade(Config('alembic.ini'), 'head'). Exit 0.
Equivalent developer migration command (use the same DATABASE_URL as the server):
```powershell
$env:DATABASE_URL='sqlite:///./local.sqlite'
..\.venv\Scripts\python.exe -m alembic upgrade head
```

R3 verification DONE: CWD root, .\.venv\Scripts\python.exe - with urllib live
synthetic probes: create 201, authorized financial triage 200, typed action plan
200 with financial_scam_transfer/contact_bank_scam, anonymous case GET 404. Exit 0.
Only the generated synthetic verification incident and its cascading plans were
removed afterwards; existing cases untouched. Live server stayed running; no
restart required. Existing legacy cases remain locked under the Phase 1 policy.

Local live automated PASS. Human manual NOT RUN. Live-provider/PostgreSQL migration
NOT RUN. This is a runtime database upgrade fix, not Phase 2. No commit/push/deploy.

## Repository cleanup and structure follow-up

2026-10-01, branch phase-0, plan docs/plans/repository-cleanup.md. User authorized
cleanup/reorganization and asked to avoid unnecessary tests; no commit or push.

| Requirement | Status | Evidence |
| --- | --- | --- |
| R1 hygiene | done | Two unreferenced category/redirect components removed; obsolete root/backend test.db, old build metadata, caches and empty docs/docs removed; .gitignore covers .swc/.next-check and SQLite sidecars. Active local.sqlite/evidence/backup/env/dependencies preserved |
| R2 backend structure | done | incident_service.py reduced 536 -> 259 lines; complaint labels/formatting in incident_presentation.py; legacy nonfinancial behavior in legacy_incident_service.py; direct formatting imports avoid summary/evidence coupling |
| R3 frontend structure | done | Intake page reduced 490 -> 148 lines; existing controller logic in features/incident-intake/use-incident-flow.ts; duplicate time callbacks consolidated; no behavior/UI/API or Phase 2 change |
| R4 tests/verification | done | Duplicate 48-case legacy matrix merged, retaining both sets of assertions: 288 -> 240 passing cases. Access, migration, golden rules and smoke coverage retained. Existing claim scan extended to feature modules; no extra test cases added |

Targeted intermediate checks passed: 17 hygiene tests, 67 complaint/compatibility/
versioned API tests; frontend lint and TypeScript checks. Final commands:

CWD repository root:
```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -c backend/pytest.ini -q -p no:cacheprovider --tb=short
```
Exit 0: **240 passed in 15.43s**, including migration/private-route matrices.

CWD frontend:
```powershell
npm run lint
node node_modules/typescript/bin/tsc --noEmit --incremental false
node --test __tests__/api-contract.test.cjs
```
All exit 0: no lint/type errors; five API contracts passed.

Isolated production build, CWD frontend, exact wrapper:
```powershell
$taskTsconfig = [IO.File]::ReadAllBytes((Join-Path (Get-Location).Path 'tsconfig.json')); $env:CYBERSOS_BUILD_DIR='.next-check'; $env:NEXT_PUBLIC_API_URL='http://localhost:8001'; try { npm run build; $taskBuildExit = $LASTEXITCODE } finally { [IO.File]::WriteAllBytes((Join-Path (Get-Location).Path 'tsconfig.json'), $taskTsconfig) }; exit $taskBuildExit
```
Exit 0, compiled/types/lint/static generation/traces completed. Initial isolated
build with default API port also passed (nonblocking existing Newsreader fallback
metrics warning); rebuilt for alternate smoke port. Next's generated tsconfig
include change was restored byte-for-byte. Live .next/development servers untouched.

Final synthetic browser, CWD root:
```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'; $env:PYTHONPATH='backend'; $env:CYBERSOS_BUILD_DIR='.next-check'; $env:SMOKE_BACKEND_PORT='8001'; .\.venv\Scripts\python.exe backend/tests/smoke_local.py
```
Exit 0, PASS create/triage/versioned actions/upload/list/preview/extraction fallback/
verify/description/suspect/timeline/summary/reload/delete/mobile. Fresh temporary
migrations pass; synthetic DB/evidence and owned alternate-port servers removed.
Runner ports configurable; refuses occupied ports and never stops/reuses user servers.

Final source eligibility scan: no generated/private files eligible for Git and no
common secret markers; public .env.example credentials are explicitly examples.
An initial scanner wrongly flagged legitimate frontend evidence components and
sample DSNs; corrected to runtime directory prefixes and actual token patterns.
Caches/build metadata may regenerate during tools; they remain ignored. Git diff
and staged diff checks pass. Source/docs links/fences reviewed. No unrelated source
or real data removed; legitimate migrations/fixtures/locks/history retained.

Local automated PASS. Manual/live providers NOT RUN. No Phase 2, commit or push.
Manual check: repeat the existing synthetic financial flow and evidence operations;
incognito private-case access must still be denied. No new product behavior to test.

## Phase 2 — Stateful conversation controller + text interface

Local acceptance complete on 2026-10-01. Primary intake is now “Tell us what
happened” with the supported financial shortcut and one structured question at a
time. No live AI understanding, Gemini, voice, new categories or Phase 3 work.

The controller consumes Phase 1 typed facts and playbook question priorities;
critical actions still come exclusively from the unchanged deterministic
playbook. Actions appear from financial case creation, before amount/reference/
uploads. Unknown answers are retained and suppressed; explicit corrections save
before/after history and regenerate applicable plans.

New case-authorized GET conversation and POST conversation/turns restore state
and submit strict typed requests. Turn UUIDs are idempotency keys. Atomic revision
checks protect all conversation mutations; turn/state/facts/plan/completion commit
together. Legacy facts/triage/completion writes reject conversation cases.
Migration 20261001_conversation adds state/turn tables and preserves Phase 1 rows.

Frontend includes quick replies, progressive structured text fields, correction,
15-second request timeout, visible unsaved retry, stale-state review, native
keyboard controls, live status/focus, mobile layout and canonical resume URLs.
Review caught and fixed draft edit links and startup retry navigation.

Final evidence: full backend **254 passed**, frontend lint/types/build passed,
**7 API contracts passed**, Phase 2 financial browser/API journey passed and
existing evidence/draft browser journey passed. Exact commands, intermediate
failures/corrections and manual steps are in verification.md. Fresh/prior-schema
SQLite migrations tested. PostgreSQL/live providers/human screen reader: not run.
Existing real-data retention/recovery limitations remain. No commit/push/deploy.

## Phase 2 UX repair — Action hierarchy

Restored prominent ACT NOW, server-numbered action rows and compact call/Mark done
controls inside the conversation architecture. Current question is visually
separate; saved history and later phases are expandable. Desktop response plan is
sticky; mobile shows urgent actions first and provides sticky actions/question
links. Completion keeps focus, and new immediate actions receive live announcements.

No API/domain/controller/migration changes. TypeScript now exposes the existing
ResponseAction.critical property. Two presentation tests use current golden
playbook outputs; expanded financial journey checks ordering, separation,
persistence, corrections, completion focus, action updates, 320px/desktop layouts
and stale text-field protection. Test-only Windows cleanup fixed after diagnosis.

Final results: **84 relevant backend tests**, **9 frontend presentation/API tests**,
lint/types/production build and extended browser/API journey all passed. Exact
commands and manual smoke steps are in verification.md. Visual screenshots were
reviewed; human screen-reader/user-panic testing not run. No LLM or Phase 3.
# Phase 3 — AI-first natural-language incident understanding

Implemented and locally verified on 2026-10-01. Phase 4 is not started. The
homepage and Phase 2 workspace hierarchy remain intact. Citizens can freely
describe incidents before questions; shortcuts remain optional. New general
cases avoid financial assumptions. Gemini interprets candidate facts only;
application validation and versioned deterministic playbooks own actions.

Official google-genai 2.26.0 is behind a small asynchronous provider interface,
with configurable enable/provider/model, total timeout, bounded retries and
input/output limits. The default model gemini-3.8-flash was checked against
Google's official model list on 2026-10-01. SDK request construction was tested
with an HTTP transport double, not a live provider. No tools or URL fetching.

Strict candidates preserve multiple signals, multilingual detection, source
turn/quote/span, extraction type, uncertainty and confidence. Explicit grounded
facts remain unverified interpretations; uncertain/inferred candidates require
clarification. SBI claims never establish victim bank; GPay does not establish
rail; installation does not establish current remote access. Relative times stay
approximate. Corrections preserve history; conflicting values remain separate.
One focused clarification follows understanding. Rich-fact conflicts use a
text clarification rather than introducing additional form fields.

Migration 20261001_understanding expands turn text to TEXT, preserving Phase 2
state/turn rows. Facts/candidates use existing JSON snapshots. Previous request
shapes remain idempotently replayable. Financial 1.0.0 remains supported;
1.1.0 handles conservative approximate intervals and the generic response branch.

Acceptance: full backend **296 passed**, including all **42 Phase 3 tests**, after
the final credential-filter repair. The affected conversation/playbook/API suite
also passed. Frontend **10 presentation/API tests**, lint, TypeScript,
production build, Phase 3 no-key browser journey and existing Phase 2 browser
journey passed. Actual saved Phase 2 rows survive migration. See verification.md
for exact commands and intermediate failures. Live Gemini, PostgreSQL execution,
human screen-reader review and real multilingual quality evaluation: **not run**.
Detailed new nonfinancial safety playbooks, voice and full localization remain
outside this phase. Existing synthetic-data-only and retention limitations remain.
# Phase 3R — AI case-agent conversation repair (2026-10-01)

Implemented locally: AI next-move reasoning after canonical merge and deterministic
playbook evaluation; seven bounded move types; case-aware recent history, unresolved
candidates/conflicts and private evidence metadata; known/declined fact validation;
safe application-rendered phrasing; persistent composer/visible history; natural
corrections and conflict answers; honest provider fallback. No Phase 4 or Phase 5.

The exact unauthorized ₹5,000 story passes fake-provider API and browser checks.
Live Gemini initialized and successfully extracted/parsed/merged money lost,
amount 5000 INR and unauthorized approval. Its full next-move acceptance remains
**blocked by live HTTP 503 high demand/timeouts**. Later extraction calls also
returned 503. This is not a LIVE GEMINI PASS or completed live acceptance.

Acceptance: backend full suite 322 passed, final affected conversation suite 80
passed (including 28 Phase 3R tests); frontend contract tests 10 passed; lint/types/
production build passed; Phase 3R scripted-provider, Phase 3 no-key and Phase 2
guided-fallback browser journeys passed. No additional Phase 3R migration; durable
assistant state reuses immutable turn JSON. See verification.md for exact commands.


## Phase 3R repair checkpoint (2026-10-02)

Repaired known-amount question validation, natural authorization quick replies,
retention of grounded AI wording, duplicate fallback rendering, canonical
acknowledgements and stage-specific diagnostics. Anchored dotenv loading and added
an explicit local launcher with backup, tracked migrations and isolated evidence.
The screenshot's saved next-call failure was 503; the restarted user's PostgreSQL
runtime is separately missing conversation tables. Remote DB remains unchanged.

Fake-provider API/browser, no-key fallback browser and Phase 2 browser checks pass.
Backend acceptance: 340 passed before final bounded follow-up changes; final
changed/related suite 91 passed. Frontend contracts 10 passed, lint/build/types
passed. Full live acceptance remains incomplete: latest actual browser Gemini
A/B extraction 503, C malformed structured output, D 429; next moves skipped.
No more live calls while quota is exhausted. Detailed commands and safe diagnostics
are in verification.md; resume instructions are in phase3-understanding.md.
Do not begin Phase 4 or claim a live pass until both AI stages, validation and
rendering succeed.


### Replacement-key verification (2026-10-02)

After the user changed GEMINI_API_KEY and explicitly requested another check, ran
real browser acceptance with `SMOKE_LIVE_CASES=B,A` and zero retries. Fresh test
processes loaded the changed backend/.env; the key was never printed.

- B: **LIVE FACT EXTRACTION PASS**. Provider invoked, strict parsing succeeded,
  candidates money_lost=true, amount=5000, currency=INR and evidence_mentioned=message
  accepted with source quotes. Authorization/rail/bank/transaction reference/exact
  time remained unknown. "just got" stayed an unverified time candidate, not a
  canonical timestamp. Deterministic IDs: contact_bank_unknown, call_1930,
  preserve_evidence, file_cybercrime, record_follow_up. **LIVE NEXT-MOVE FAIL: 503**
  before output/validation. Grounded amount acknowledgement and authorization
  fallback rendered once; composer enabled.
- A: **LIVE FACT EXTRACTION FAIL: 503**; next-move skipped. Honest fallback once,
  preserved message, enabled composer, no fabricated canonical facts/actions.

No 429 was observed with the replacement key during these two cases. The key is
usable for extraction, but does not resolve provider 503 availability. No full
LIVE GEMINI pass. No further live calls after this bounded attempt. Original
four-case results above remain the historical first attempt; ignored screenshots
and phase3r-live-result.json now contain the replacement-key B/A results.
Resume at live next-move acceptance when provider capacity is available. Do not
rerun unaffected local checks or start Phase 4.
