# Step 0A — Repository audit

Audit date: 2026-09-30. Branch: `phase-0`. Audited HEAD: `cadb2d7986b9c053a1262742a650544c283daa7c`.
Scope: documentation only; current source and executed checks establish behavior. No application fixes, refactors, migrations, dependency installations, provider calls, commits, pushes, deployments, or spending.
The pre-existing uncommitted change to `AGENTS.md` is the Phase protocol requested earlier and was preserved.

## Requirement evidence

| Requirement | Result | Evidence |
| --- | --- | --- |
| R1 | done | [verification.md](verification.md): complete backend suite, lint, production build, fresh temporary SQLite Alembic upgrade; actual failures and environment restrictions recorded. |
| R2 | done | Suspected-issue register below, including explicit UNCLEAR for the missing roadmap comparison. |
| R3 | done | Runtime OpenAPI inventory and all 25 frontend calls/URLs below; 19 missing operations and one upload contract mismatch. |
| R4 | done | Claim inventory below includes reachable and legacy claims, thresholds, and explicit negative findings. |
| R5 | done | Proposed 0B/0C order and decisions below. No next step started. |

## What works today, and what is only present in source

The frontend is Next.js 14.2.35 / React 18 / TypeScript / Tailwind; backend is FastAPI / Pydantic / SQLAlchemy with PostgreSQL as intended deployment database and SQLite used in tests. Evidence: `frontend/package.json:7`, `frontend/package.json:13`, `backend/requirements.txt:1`, `backend/app/db/session.py:19`.

The landing entry is “I've Been Scammed” (`frontend/app/page.tsx:60`). The primary journey uses a five-step form, creates the incident at step 1, validates further steps, triages, and navigates to the result page (`frontend/app/incident/start/page.tsx:80`, `:259`, `:266`, `:273`, `:289`, `:305`, `:319`, `:465`). It is not the AGENTS.md conversation-first experience. Financial triage requires positive amount and a known payment method (`backend/app/schemas/incident.py:188`); it does not require a transaction ID (`:177`). Useful actions appear after triage, rather than before unnecessary reporting fields. Women/children and other cybercrime routing and actions exist (`backend/app/services/incident_service.py:564`, `:658`, `:851`).

Current mounted API supports incident creation/read/triage/details, legacy file upload, action plans, and two health checks. Complete backend tests exercised those journeys: 161 passed and two failed. A frontend build is evidence of compilation, not successful evidence-vault integration. Evidence/suspect/timeline implementations exist but are unmounted and cannot simply be mounted because their model import collides.

Action selection is deterministic in `backend/app/rules/action_rules.py:10`; wording comes from service constants (`backend/app/services/incident_service.py:378`, `:586`). Financial action-plan generation recomputes time-dependent rules when read (`:566`), so stored triage priority and later action-plan priority can differ. Legacy urgency and action builders remain alongside the mounted rule path (`:443`, `:457`); their tests passing does not establish correctness of current API behavior.

## R2 — Suspected-issue register

| Suspected issue | Status | Evidence and consequence |
| --- | --- | --- |
| a. Duplicate Evidence models on one table | CONFIRMED | `backend/app/models/incident.py:167` and `backend/app/models/evidence.py:81` both subclass the same Base and declare `__tablename__ = "evidence"` at lines 168/82. Legacy model has stored_filename/content_type/size_bytes; newer model has storage_path/mime_type/file_size/hash/extraction fields (`incident.py:177`, `evidence.py:98`). Importing app.main then app.models.evidence reproduces SQLAlchemy InvalidRequestError: table evidence already defined. See verification probe. |
| b. Evidence/suspects/timeline routers unmounted while frontend calls them | CONFIRMED | `backend/app/api/v1.py:3` imports only health/incidents; lines 6–7 include only those routers; `backend/app/main.py:40` mounts that aggregate. Route modules exist at `backend/app/api/routes/evidence.py:19`, `suspects.py:14`, `timeline.py:10`. Frontend calls at `frontend/lib/api.ts:116`, `:169`, `:197`. Exception: POST incident evidence is mounted through the legacy incidents router (`incidents.py:59`), not the new evidence router. |
| c. Frontend calls without backend handlers | CONFIRMED | Evidence-readiness, description and generate-summary calls at `frontend/lib/api.ts:222`, `:226`, `:233` have no route decorator anywhere in backend/app/api/routes. Services exist (`backend/app/services/evidence_service.py:266`, `incident_summary.py:128`) but are not routes. Consumers at `frontend/app/incident/[id]/evidence/page.tsx:52`, `:139`, `:146`. Other missing operations have unmounted handlers, detailed in R3. |
| d. Startup ensure_schema/create_all instead of migration-only lifecycle; first migration calls create_all | CONFIRMED | Startup invokes ensure_schema (`backend/app/main.py:29`–32). It calls create_all (`backend/app/db/schema.py:96`–97), adds enum values and missing columns (`:117`, `:128`, `:133`). Tracked migrations do exist; first revision uses live Base.metadata.create_all and returns for a fresh DB (`backend/alembic/versions/20260824_phase2.py:18`–22). env.py imports only incident metadata (`backend/alembic/env.py:8`). Fresh SQLite upgrade reaches head but creates no suspect/timeline tables. This is mutable model-based initialization plus migrations, not absence of Alembic. |
| e. Tracked test.db and tsconfig.tsbuildinfo; shared ./test.db | CONFIRMED | `git ls-files test.db backend/test.db frontend/tsconfig.tsbuildinfo` returns root test.db and frontend/tsconfig.tsbuildinfo; backend/test.db is not tracked. Shared relative DB set at `backend/tests/conftest.py:3`; each test drops all tables at lines 27/30 and attempts deletion at lines 31–35. `.gitignore:20` ignores only backend/test.db, not root test.db. Tests were run with a temporary process CWD to preserve existing files. No database contents inspected. |
| f1. docs/docs duplicates and legacy “Phase 3 evidence vault” | CONFIRMED | Both `docs/product.md:1` / `docs/docs/product.md:1` and `docs/architecture.md:1` / `docs/docs/architecture.md:1` exist. Scope differs at product lines 34–38; nested architecture describes startup table creation at line 56 while canonical architecture describes migrations at line 56. Legacy report title is `docs/docs/phase3-evidence-vault.md:1`; line 78 claims all three new tables are created and lines 104–107 claim local fallback works. Runtime evidence contradicts these completion claims. |
| f2. Legacy naming conflicts with docs/roadmap.md | UNCLEAR | `Test-Path docs/roadmap.md` returned False, and `git ls-files docs/roadmap.md` returned no file. The roadmap comparison cannot be made; no roadmap or replacement phase numbering invented. |
| g. Referenced storage/AI/Supabase settings absent | CONFIRMED | Settings fields at `backend/app/core/config.py:17`–24 are DATABASE_URL, CORS_ORIGINS, SERVICE_NAME, API_V1_PREFIX, EVIDENCE_STORAGE_DIR. Missing references listed below. backend/.env.example contains only DATABASE_URL/CORS_ORIGINS (`:4`, `:7`). Missing optional settings break advertised fallback rather than merely disable cloud providers. |

### Settings and related drift

All references below are absent from Settings and backend/.env.example:

| Setting / property | Reference |
| --- | --- |
| supabase_configured | `backend/app/services/storage_service.py:63`, `:165` |
| SUPABASE_URL | `backend/app/services/storage_service.py:65` |
| SUPABASE_EVIDENCE_BUCKET | `backend/app/services/storage_service.py:66` |
| SUPABASE_SERVICE_ROLE_KEY | `backend/app/services/storage_service.py:68`–69 |
| LOCAL_STORAGE_ROOT | `backend/app/services/storage_service.py:135` |
| max_evidence_file_size_bytes | `backend/app/services/file_validation.py:74` |
| EXTRACTION_PROVIDER | `backend/app/services/evidence_extraction.py:250` |
| SUMMARY_PROVIDER | `backend/app/services/incident_summary.py:124` |
| ANTHROPIC_API_KEY | `backend/app/services/evidence_extraction.py:195`, `incident_summary.py:76` |
| ANTHROPIC_MODEL | `backend/app/services/evidence_extraction.py:212`, `incident_summary.py:105` |

EVIDENCE_STORAGE_DIR is present in Settings (`config.py:24`) but absent from .env.example and used by the mounted legacy upload (`api/routes/incidents.py:69`).
MAX_EVIDENCE_FILE_SIZE_MB, MAX_ID_DOCUMENT_SIZE_MB and DEMO_MODE appear only in the legacy documentation's claimed configuration (`docs/docs/phase3-evidence-vault.md:121`–130), not implemented Settings; do not confuse those with actual settings references.
The legacy report claims pypdf/anthropic dependencies (`:65`); requirements does not declare either. Lazy imports exist at `evidence_extraction.py:85`, `:203`, `incident_summary.py:79`. Gemini is intended by AGENTS.md but has no implementation here; no provider/model changes or model-availability checks were made in this documentation-only audit.
New services also expect Incident.bank/wallet/merchant/description (`incident_summary.py:62`–67; `evidence_service.py:164`, `:266`), absent from the mapped Incident (`models/incident.py:68`–164). Fixing configuration alone cannot make those paths work.

## R3 — Every frontend API call versus mounted OpenAPI

Runtime inventory came from app.openapi() with DATABASE_URL=sqlite:///:memory: and CORS_ORIGINS=http://testserver, without startup, local .env secret output, or a live provider. The corrected automated comparison exited 0: **25 calls/URLs, 6 operation matches, 19 missing**. Initial parser attempt mishandled quote delimiters and is excluded as invalid evidence (recorded in verification.md).

Mounted operations (8 total):

| Method | OpenAPI path | Mount/handler evidence |
| --- | --- | --- |
| GET | /health | `backend/app/main.py:35` |
| GET | /api/v1/health/database | `backend/app/api/routes/health.py:13` |
| POST | /api/v1/incidents | `backend/app/api/routes/incidents.py:21` |
| GET | /api/v1/incidents/{incident_id} | `backend/app/api/routes/incidents.py:27` |
| POST | /api/v1/incidents/{incident_id}/triage | `backend/app/api/routes/incidents.py:35` |
| PATCH | /api/v1/incidents/{incident_id}/details | `backend/app/api/routes/incidents.py:47` |
| POST | /api/v1/incidents/{incident_id}/evidence | `backend/app/api/routes/incidents.py:59` |
| GET | /api/v1/incidents/{incident_id}/action-plan | `backend/app/api/routes/incidents.py:74` |

Frontend calls are centralized in frontend/lib/api.ts; the only fetch is line 37. The file URL helper is included because previews issue browser requests outside request(). Below, {id}, {incident_id}, {evidence_id}, {suspect_id}, {event_id} normalize parameter names, not route behavior.

| Frontend function (file:line in frontend/lib/api.ts) | Method | Path | Result / existing unmounted handler |
| --- | --- | --- | --- |
| getApiHealth :74 | GET | /health | MATCH |
| createIncident :78 | POST | /api/v1/incidents | MATCH |
| getIncident :85 | GET | /api/v1/incidents/{id} | MATCH |
| triageIncident :89 | POST | /api/v1/incidents/{id}/triage | MATCH |
| uploadEvidence :105 | POST | /api/v1/incidents/{incident_id}/evidence | MATCH PATH; incompatible response and ignored extra form fields |
| getActionPlan :112 | GET | /api/v1/incidents/{id}/action-plan | MATCH |
| listEvidence :116 | GET | /api/v1/incidents/{incident_id}/evidence | MISSING; evidence.py:84 |
| getEvidence :120 | GET | /api/v1/evidence/{evidence_id} | MISSING; evidence.py:91 |
| updateEvidence :132 | PATCH | /api/v1/evidence/{evidence_id} | MISSING; evidence.py:116 |
| deleteEvidence :139 | DELETE | /api/v1/evidence/{evidence_id} | MISSING; evidence.py:125 |
| extractEvidence :143 | POST | /api/v1/evidence/{evidence_id}/extract | MISSING; evidence.py:131 |
| verifyEvidence :151 | POST | /api/v1/evidence/{evidence_id}/verify | MISSING; evidence.py:138 |
| compareEvidence :158 | GET | /api/v1/evidence/{evidence_id}/compare | MISSING; evidence.py:167 |
| evidenceFileUrl :162 | GET | /api/v1/evidence/{evidence_id}/file | MISSING; evidence.py:97 |
| createSuspect :169 | POST | /api/v1/incidents/{incident_id}/suspects | MISSING; suspects.py:17 |
| listSuspects :176 | GET | /api/v1/incidents/{incident_id}/suspects | MISSING; suspects.py:31 |
| updateSuspect :183 | PATCH | /api/v1/suspects/{suspect_id} | MISSING; suspects.py:39 |
| deleteSuspect :190 | DELETE | /api/v1/suspects/{suspect_id} | MISSING; suspects.py:49 |
| createTimelineEvent :197 | POST | /api/v1/incidents/{incident_id}/timeline | MISSING; timeline.py:13 |
| listTimelineEvents :204 | GET | /api/v1/incidents/{incident_id}/timeline | MISSING; timeline.py:27 |
| updateTimelineEvent :211 | PATCH | /api/v1/timeline/{event_id} | MISSING; timeline.py:35 |
| deleteTimelineEvent :218 | DELETE | /api/v1/timeline/{event_id} | MISSING; timeline.py:45 |
| getEvidenceReadiness :222 | GET | /api/v1/incidents/{incident_id}/evidence-readiness | MISSING; no handler |
| updateIncidentDescription :226 | PATCH | /api/v1/incidents/{incident_id}/description | MISSING; no handler |
| generateIncidentSummary :233 | POST | /api/v1/incidents/{incident_id}/generate-summary | MISSING; no handler |

Unmounted handler references above use prefix `backend/app/api/routes/`.
No frontend wrapper calls the mounted database-health or PATCH details operations. External official anchors are handoff links, not backend API calls.
Mounted upload accepts only file and returns six legacy metadata fields (`incidents.py:59`–69; `schemas/incident.py:210`–218); frontend sends evidence_type/description (`api.ts:103`–104) and expects mime_type/file_size/sha256/extraction/verification/preview fields (`frontend/types/evidence.ts:56`–71). Extra fields are not consumed by that handler. Mounting the new evidence router would duplicate POST at the same path (`evidence.py:44`–54), requiring a canonical upload decision.
The common frontend request() always parses JSON (`api.ts:70`), while unmounted evidence/suspect/timeline DELETE handlers return 204 (`evidence.py:125`, `suspects.py:49`, `timeline.py:45`). Even after mounting, those calls need a compatible empty-response contract.

## R4 — Claims prohibited by AGENTS.md

This inventory identifies claims in repository source, not verified official advice. No claim is endorsed and no source review date is fabricated. Reachability distinctions matter: current financial API uses CORE_MESSAGES and _RULE_ACTIONS; legacy builders remain callable but are not used by mounted build_action_plan (`incident_service.py:586`, `:601`). All backend service references below mean `backend/app/services/incident_service.py` unless a full path is supplied.

| Claim / rule | File:line evidence | Reachability / concern |
| --- | --- | --- |
| “Best chance of reversal” | service:96 | Current critical core message predicts probability. |
| “strong reversal window” | service:99 | Current high core message predicts window. |
| “Reversal less likely but still possible” | service:100 | Current medium core message predicts probability. |
| “Focus shifts to ... FIR over reversal” | service:101 | Legacy medium_low message asserts age-dependent recovery focus. |
| “Reversal unlikely ... often required for insurance/dispute claims” | service:103–108 | Current low and legacy standard messages predict recovery and third-party requirements. |
| 1930 alerts bank while debit “still reversible” | service:169–170 | Current _CALL_1930_NOW assumes reversible payment and helpline/bank behavior. |
| Reporting today “keeps you inside a usable reversal window” | service:177–178 | Current _CALL_1930_TODAY promises a fixed usable window; 24×7 availability is an additional unreviewed official claim. |
| Reporting creates an official trail recognized by banks, insurers and portal | service:185–186 | Legacy action asserts official recognition/outcome. |
| Bank can freeze debit, block beneficiary, start chargeback; “first hour ... best chance” | service:193–195 | Current _BANK_NOW generalizes bank powers/payment remedies and predicts a recovery window/probability. |
| Banks reverse “many” debits within 24 hours | service:201–202 | Current _BANK_TODAY makes frequency/window claims. |
| Written bank reference “will” be needed for portal/insurance | service:208–209 | Current _BANK_DISPUTE claims fixed third-party requirements. |
| Portal “slower than a phone alert” | service:215–216 | Legacy action asserts comparative response timing without measurement. |
| Same-day complaint gives coordinator something to act on | service:224–225 | Current _FILE_PORTAL_TODAY asserts official handling rationale without source registry. |
| Reversal less likely after a few days; complaint now “main path” | service:233–234 | Legacy action predicts probability/window. |
| Banks rarely reverse after weeks; FIR if amount large; insurer/dispute requirements | service:242–244 | Legacy action predicts probability and monetary filing threshold/third-party behavior. |
| Old debit reversal unlikely; complaint required before bank/wallet/insurer even looks | service:252–253 | Legacy action predicts recovery and guaranteed gatekeeping. |
| “NPCI can still attempt a UPI reversal when the report is fast” | service:320–321 | Legacy payment action implies NPCI recovery behavior tied to speed. No numeric NPCI filing threshold found. |
| Blocking card “stops follow-on debits” while chargeback filed | service:327–328 | Legacy action implies guaranteed containment and remedy processing. |
| Credit-card chargebacks “clearer consumer path than UPI” | service:334–335 | Legacy action makes unsupported comparative financial-remedy claim. |
| ₹1,00,000+ banks “often escalate faster” | service:373–375 | Legacy LARGE_VALUE_ACTION invents amount-dependent bank behavior/timing. |
| ₹1,00,000+ FIR “can support escalation” | service:393–394 | Current consider_fir text ties FIR advice to amount; ID also misleadingly bank_fraud_desk at line 392. |
| FIR action only when amount >=100000 | `backend/app/rules/constants.py:15`; `backend/app/rules/action_rules.py:246`–247 | Current rule encodes prohibited monetary FIR threshold. |
| Legacy amount threshold bumps urgency; adds fraud-desk advice | service:51, :440, :452–453, :465–466 | Legacy rule embeds ₹100,000 special handling; no evidence for faster bank response. Severity bands alone are not a legal filing threshold. |
| Recovery “open” <24h, “uncertain” <7d, “likely_expired” >=7d; pending opens window | `backend/app/rules/action_rules.py:214`–221 | Current deterministic recovery prediction, persisted at service:849 and returned at :607. |
| “Recovery window: ...”; disclaimer does not remove predicted label | `frontend/components/result-screen.tsx:173`–175 | User-facing display of current predicted window. |
| Recency “single biggest factor” in whether money can be reversed | `frontend/components/steps/step-when.tsx:26`–27 | User-facing ranking/recovery assertion. |
| Amount/payment method change “who you call” and reversal request | `frontend/components/steps/step-amount.tsx:24` | Implies amount-dependent response; broader than current mounted action rules. |
| Transaction ID makes 1930/bank find debit “much faster” | `frontend/components/steps/step-transaction-id.tsx:18` | User-facing unmeasured timing claim. |
| Reporting “creates a record” / “formal record” | service:669, :683 | Current category actions imply official outcome without distinguishing user submission from confirmed receipt. |
| Open/pending recovery window and expiry policy described as time sensitivity | `docs/action-engine.md:8`, `:11`, `:23` | Documentation propagates the current prohibited inference despite disclaimer. |
| ₹100,000 as urgency factor | `README.md:33`–35 | Describes legacy amount behavior, inconsistent with current rule's severity/threshold separation. |

Tests entrench these rules rather than validate official truth: `backend/tests/test_action_rules.py:51`–60 (FIR threshold), `:63`–69 (open window), `:106` (likely_expired); `backend/tests/test_triage.py:51`–67 (legacy amount bump); `backend/tests/test_action_plan.py:24`–31 (large-value action). These must be deliberately updated when behavior is authorized to change.

Negative findings: no numeric recovery percentage, fixed refund eligibility, explicit “police will recover/refund,” numeric NPCI/FIR threshold beyond the ₹100,000 FIR rule, or under-30-second service promise was found in app/rule source. “Call now/today” is an action instruction, not itself a recovery promise; transaction-time choices and internal timeouts are not service-performance claims. Sample ticket is clearly labelled “Sample only — not a real case” (`frontend/components/case-ticket.tsx:50`); independence/demo banners are present (`frontend/app/page.tsx:70`–72; `frontend/components/evidence/demo-banner.tsx:8`, `:20`). No fabricated live government status was observed in those screens.

## Other material audit limits and risks

Incident lookup checks existence, not an authenticated owner (`backend/app/api/routes/incidents.py:28`–32, `:63`–69). New evidence routes depend only on DB, not incident-scoped user authorization (`evidence.py:54`, `:92`); mounting them alone would not permit real-data use under AGENTS.md.
Mounted upload writes local files and metadata but has no SHA-256 or new validation pipeline (`backend/app/services/incident_service.py:751`–787); the newer validator/hash pipeline is unmounted (`evidence_service.py:41`–48). This audit does not inspect real database/evidence contents, perform a security scan, or authorize real citizen data.
The scenario fixture `backend/tests/fixtures/scenarios.yaml` is absent. No behavior was added, so no fixture was invented in 0A.
No browser journey, live provider, PostgreSQL migration/upgrade from a prior schema, or official-guidance review was run. A fresh SQLite head upgrade is narrower evidence than production migration readiness.

## R5 — Proposed fix order (proposal only)

### 0B: establish a coherent, reproducible foundation

1. Make baseline tests deterministic: inject/freeze time in API tests; use per-test temporary DB/storage, no shared ./test.db; document supported runtime/dependency commands. The two observed failures come from fixed August dates assessed with September's real clock (`tests/test_incidents_api.py:9`, `:24`, `:57`, `:89`; service:832).
2. Choose one Evidence ORM/schema/service/upload implementation; map additive preservation of existing incident/evidence metadata and stored files. Consolidate model imports before changing router mounts. Resolve missing Incident fields and configuration together; ensure missing optional provider credentials cannot prevent local startup.
3. Replace startup DDL with tracked immutable Alembic operations. Define supported prior schema before implementing transitions; verify fresh PostgreSQL and SQLite schemas and upgrades from synthetic prior-schema fixtures. A passing SQLite create_all-based migration does not close this work.
4. Reconcile mounted API with the agreed frontend contract: preserve working incident routes, avoid duplicate POST evidence, resolve missing handlers and 204 JSON parsing; verify mounted OpenAPI and synthetic smoke journeys.
5. Remove generated files from tracking without deleting legitimate user data; update ignore rules. Consolidate canonical docs and mark legacy reports accurately. Add the agreed roadmap/phase definitions and scenarios fixture; avoid inventing intended next-phase scope.

### 0C: correct response truth and product safety after foundation checks

1. Replace recovery predictions, FIR/amount gates, and unsupported bank/NPCI/police/insurance/timing claims with reviewed primary-source-backed action text. Create the official-source registry and truthful review records. Update tests that currently enforce prohibited rules.
2. Explicitly distinguish scam-induced authorized transfers from unauthorized debits before choosing applicable guidance; preserve non-financial incident paths. Audit unknown/contradictory facts and prevent reporting fields/transaction IDs/uploads from delaying established protective actions.
3. Make action IDs/order/provenance/versioning and user-completion semantics match the agreed contracts, and encode expected scenarios. Address actual mounted legacy/new rule divergence.
4. Make consent, incident ownership/access denial, safe evidence restrictions, credential redaction, deletion and retention verifiable before any real-data use. Exact implementation boundary should be named in the 0C prompt; do not silently broaden 0B into a production launch or 0C into the whole roadmap.
5. Verify automated local contracts/journeys separately from manual review and explicitly authorized live-provider tests; time-to-useful-action remains a measured target, not a displayed promise.

If 0B exposes more current functionality, remove misleading claims and restrict to synthetic data before anyone uses that functionality with real incidents; foundation work is not approval to expose unsafe advice.

### Decisions needed before implementation steps

- Supply or approve the actual 0B/0C requirement boundaries and roadmap: docs/roadmap.md does not exist. The sequence above is a proposal, not an accepted phase definition.
- Confirm supported migration starting points and whether existing local incident/evidence data must be preserved. Recommended default: preserve; do not treat root test.db as disposable without authorization.
- Choose the canonical evidence contract (recommend the richer hash/provenance contract through an additive migration) and whether 0B should restore the existing vault calls or deliberately hide unsupported UI until a later named step.
- Confirm provider scope: AGENTS.md intends Gemini; current unused provider source is Anthropic. Recommend local provider doubles/manual fallback first, Gemini integration only in an explicit later requirement; live-provider verification requires separately authorized credentials/cost.
- Decide the prerequisite gate for 0B: **0A audit requirements are complete, but baseline is not fully passing**. The Phase protocol requires recorded passing predecessor evidence. This record separates audit completion from application-baseline failure; the 0B prompt should say whether passing audit-document checks suffice or explicitly authorize the baseline-repair step despite these known failures.

No decision is needed to complete this audit. No fixes were made.

## Step 0B resolution appendix — 2026-09-30

0A findings/line numbers above are a historical snapshot. Prohibited claims
remain deferred to 0C.

| Requirement | Status | Resolution and evidence |
| --- | --- | --- |
| R1 | done | models/evidence.py is sole Evidence ORM; duplicate in incident.py and duplicate upload removed. tests/test_evidence_contract.py:32, :71 cover registration and rich metadata/hash/file CRUD. |
| R2 | done | api/v1.py mounts evidence/suspects/timeline. tests/test_evidence_contract.py:41 checks all 25 frontend method/path pairs mounted once: zero missing. Frontend API contract tests verify response handling. |
| R3 | done | Frozen explicit 20260824_phase2 baseline plus additive 20260930_evidence_contract. Startup ensure_schema/helper removed. test_evidence_contract.py:60 rejects startup DDL; test_migrations.py:43 checks data survival. |
| R4 | done | test_migrations.py:27, :43, :87: five fresh/current-schema upgrade cases, original bytes and unknown hashes. SQLite passed; PostgreSQL NOT RUN. |
| R5 | done | tests/conftest.py session-private migrated DB, temporary storage, row resets/disposal; test_config.py:33 rejects repository test.db. Tracked database unchanged. |
| R6 | done | core/config.py/.env.example cover code reads; test_config.py:7 covers settings/example/no-credential local storage; absent key/model fails extraction honestly. |
| R7 | done | evidence_service.py owns upload/validation/storage/preview/verification/extraction side effects; incidents delegate readiness/description/template summary services. Suspect/timeline services validate source ownership; CRUD tests pass. |

Evidence paths above are under backend/app or backend/tests as appropriate.

Scope decisions:
- Retain every frontend consumer. Missing readiness GET uses existing
  compute_readiness; description PATCH persists; generate-summary uses existing
  deterministic template provider. No new AI/fake saving/extraction.
- Preview URLs remain backend API-relative; frontend resolves against API_URL.
  Empty HTTP 204 deletion does not attempt JSON parsing.
- Preserve original private file locations and timestamps; rename legacy columns
  via migration. Legacy MIME and unavailable SHA-256 remain null; actual available
  bytes establish hash, every new upload calculates it.
- Retain previous revision IDs, add consolidation revision; adopt audited
  unversioned/current stamped schema. No existing database altered. Back up and
  configure prior storage root before migration (README/verification instructions).
  Consolidation downgrade blocked to prevent metadata loss; restore backup.
- Optional provider settings permit local storage/deterministic providers.
  Existing Anthropic adapters remain opt-in; no assumed model or new integration.
- Re-extraction of verified evidence returns 409, preserving manual corrections.
  Independent reviewer reproduced overwrite; two red/green regression cases cover
  successful and failed candidate extraction.
- Source-evidence must belong to the same incident for suspect/timeline creation;
  this is relational consistency, not full citizen authorization.
- Test clock fixed to existing fixture dates; production action rules unchanged.

0B user decisions needed: none. 0C prohibited claims, duplicate legacy docs/naming
and tracked generated-artifact cleanup remain open. No 0C started. Restored vault
remains a synthetic prototype pending real-data authorization/retention readiness.

## Phase 0C resolution — 2026-09-30

The claim inventory above is historical evidence, not current guidance. Phase 0C
removed/reworded current and callable legacy financial messages: recovery windows/
probability, bank reversal/freeze/chargeback guarantees, first-hour/24-hour claims,
NPCI reversal assumptions, faster bank/transaction-ID handling, insurance gates,
and amount-conditioned FIR/fraud-desk escalation. Active action text now emphasizes
prompt reporting, preserving records, asking applicable bank options and external
handoff without predicting outcomes.

Rules no longer infer recovery from age/pending status; deprecated HTTP
recovery_window is null even for stale stored predictions. Original database
values are preserved. Amount bands remain impact metadata only, not FIR/reporting
eligibility. Existing urgency ordering/ongoing-risk elevations remain.

Generated test.db and frontend/tsconfig.tsbuildinfo removed from Git index only;
local files preserved. Ignore patterns cover runtime DB/build/evidence/env output.
No tracked uploads/secrets found. Migrations, fixtures and lockfiles retained.
docs/docs snapshots moved under explicitly marked docs/legacy; current README,
product/architecture/action-engine/roadmap supersede obsolete Phase 3 numbering.
Optional providers and incomplete conversation/playbook/government capabilities
are explicitly distinguished. Official-source review limits recorded in
official-sources.md; no new recovery/timing/official-outcome claims adopted.

Evidence: backend/tests/test_phase0c_truth.py (17 cases), updated previous rule/
action/triage/complaint/API tests, scenario fixture and browser assertions.
205 backend + four frontend contracts, lint/build, fresh/legacy SQLite migrations
and synthetic browser pass; exact commands/failures in verification.md.
PostgreSQL/live-provider/manual NOT RUN. Real-data prerequisites remain outside
this cleanup. No Phase 1 begun or next-step decision invented.
