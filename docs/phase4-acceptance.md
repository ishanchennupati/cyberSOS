# Phase 4 acceptance record

Synthetic development scope: existing India playbooks, English presentation,
English/Roman Telugu/Hinglish interpretation. No production access or billing
change. Implementation and acceptance evidence are recorded below.

## Citizen experience and gap

The homepage opens one minimal conversation directly. The citizen can explain
the incident once, keep typing naturally, ask relevant questions, correct facts,
skip or pause investigation, attach JPG/PNG/PDF files, return to saved messages,
and intentionally open current plan/case details. Urgent backend policy actions
remain visible while intake continues.

The previous conversation shell emphasized structured intake and narrow approved
wording; context retained only a few user messages. Files were separate from
durable conversation turns. Investigation now uses both sides of saved exchanges,
current canonical facts, corrected source-linked memory and relevant older recall.

## Implementation

Frontend: shared growing keyboard-accessible composer, upload progress/cancel,
private previews, optional quick replies, retry after reload, session drafts,
jump-to-latest and modest intentional artifacts. Mobile artifacts occupy layout
space instead of covering the composer. Typing during a send and quick replies
preserve unrelated drafts and files.

Backend/domain/AI: bounded flexible response contract, exact fact/action/source
references, semantic grounding and safety checks, saved control intents, source-
linked derived memory, bounded recall and lexical retrieval over the existing
reviewed official-source registry. Provider stages remain independently diagnosed.
Fallback preserves unknowns/declines/pauses and the deterministic current plan.
This reuses existing turn JSON, storage and policy boundaries rather than adding
a second case system, another model stage or a hosted vector service.

Database/storage: migration `20261003_chat_attachments` adds owned turn/evidence
links and a staged flag. Creation and upload keys make interrupted requests
replayable; originals use separate random attempt storage keys. Existing private
storage validation is reused. Old unlinked staged files expire lazily after 24
hours on the next case upload. Linked attachments survive that cleanup; deletion
leaves an honest historical tombstone. Only the local database was migrated.

API/contracts: conversation responses include current projection, derived memory,
historical attachments and actual reviewed citations. Message requests support
attachment-only/text-plus-file sends. Creation ID plus a separate private secret
supports replay without treating a UUID as authority. Case cookies remain required.

## Security and privacy

Canonical facts, approved actions and private case ownership remain backend
authority. Retrieved knowledge cannot establish citizen facts or authorize actions.
Citizen uploads never enter shared knowledge. No model tools, arbitrary browsing,
unchecked instruction streaming or file extraction were added. Private filenames
render as React text; previews use authorized file endpoints. Provider errors log
bounded diagnostics instead of raw sensitive inputs. Tests use synthetic data.

Generated `.next*/static/media` files are fonts/build assets. Evidence originals
are runtime data under ignored local `backend/evidence` or the existing private
storage adapter, not version-controlled source files.

## Verification commands and evidence

Commands run from `backend` unless specified; browser harnesses migrate disposable
SQLite databases and clean up only their own servers.

| Command | Result |
| --- | --- |
| `../.venv/Scripts/python.exe -m pytest -q` | 422 passed in the final full regression run (21.58 seconds). |
| `node --test __tests__/*.test.cjs` (frontend) | 13 passed. |
| `npx tsc --noEmit` (frontend) | Passed after final frontend changes; builds also check types. |
| `$env:NEXT_PUBLIC_API_URL='http://localhost:8001'; $env:CYBERSOS_BUILD_DIR='.next-phase4'; npm run build` (frontend) | Passed; isolated production build. |
| `node __tests__/phase4-composer.cjs` with `PLAYWRIGHT_PACKAGE` | Desktop/mobile empty-send, first-send interaction, failed-send draft retention passed. |
| `../.venv/Scripts/python.exe -m tests.phase4_provider_probe` | Live configured-model response schema probe passed after repair. |
| `$env:PHASE4_LIVE='1'; ../.venv/Scripts/python.exe -m tests.phase4_model_evaluation` | Both candidate models listed; candidate 3.8 had timeout/quota failures. |
| `$env:PHASE4_LIVE='1'; $env:PHASE4_MODELS='gemini-3.5-flash-lite'; ../.venv/Scripts/python.exe -m tests.phase4_model_evaluation` | Repaired-schema extraction and reasoning passed all three languages, with identical canonical/RAG reasoning context. Six calls; no model configuration change. |
| `git diff --check` (root) | Passed; Windows line-ending notices only. |

Browser harness environment:

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
$env:CYBERSOS_BUILD_DIR='.next-phase4'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
$env:SMOKE_JOURNEY='__tests__/phase4-journey.cjs'
$env:SMOKE_ASGI_APP='tests.case_agent_smoke_app:app'
../.venv/Scripts/python.exe -m tests.smoke_local
```

Fake-provider browser acceptance proved direct CTA, one saved first send, current
urgent actions, correction/reload, current memory, mobile composer with details
open (390×844 and 390×420), attachment-only/private resume/replay/deletion.
The extended interrupted-create/reload/retry regression also passed, preserving
the original case and one saved turn. Text-plus-file send, quick-reply preservation
of unsent files/draft, and typing a new draft while saving passed in the browser.
Keyboard controls and focus restoration were checked through browser interactions.
Calculated shared-token contrast ratios are 14.53:1 for ink/paper, 6.67:1 for
muted ink/paper and 15.97:1 for white/ink. The short mobile viewport simulates
keyboard space; no physical-device keyboard test was performed.

Live run replaces `SMOKE_JOURNEY` with `__tests__/phase4-live.cjs`, sets
`SMOKE_LIVE_AI='1'` and `LIVE_DELAY_MS='10000'`, and uses `app.main:app`.
An earlier run passed eight exchanges through both real stages, then reached
429 on older recall. A paced final nine-turn run passed both live stages on every
exchange, with real source validation/citation, corrected amount and older blue
profile-picture recall. Browser/API round trips measured 6.816–11.705 seconds in
that run; these are full response times, not time-to-first-action measurements.
The diagnostic ASGI entry point `tests.phase4_live_app:app` captured synthetic
proposals privately for validation diagnosis and delegates to the real provider.
It is test-only and is never imported by the application. Failed runs also exposed
provider JSON grammar, overly broad validation and mobile/reload defects; those
were corrected and retained as regression coverage.

For the final live language command, set `SMOKE_JOURNEY` to
`__tests__/phase4-languages.cjs`, `SMOKE_LIVE_AI='1'` and
`SMOKE_ASGI_APP='tests.phase4_live_app:app'`, then run the same
`../.venv/Scripts/python.exe -m tests.smoke_local` harness. Both two-turn
Roman Telugu and Hinglish browser journeys passed extraction, canonical grounding,
reasoning, safety validation and rendering. They confirmed ₹5,000/INR/UPI,
scam-authorized payment and financial+device signals, followed by a useful answer
to why the access question matters. Final measured round trips were 9.114/5.855
seconds for Roman Telugu and 6.548/5.893 seconds for Hinglish. An earlier language
attempt encountered 503 (one bounded retry); another exposed the retrospective
“had you send … and install …” false positive, now covered by a regression test.

Runtime reconciliation: the initial `backend/.env` target was remote Supabase
PostgreSQL at migration `20261001_understanding`. It was inspected read-only and
not migrated. `backend/run_local.py` deliberately overrides that target with
`backend/local.sqlite`, `backend/evidence`, local cookie settings and no hosted
storage credentials. It snapshots/migrates the local DB on startup. Normal
frontend development targets port 8000; the isolated build/harness targets 8001.
All browser acceptance used disposable locally migrated SQLite/private storage.
No key or private database hostname is included in this report.

Added tests cover correction freshness, older recall, source poisoning/withdrawal,
semantic claims and unsafe instructions, multilingual context budgets, natural
skip, persistent pause, creation/upload/turn replay, cross-case linkage, stale
revisions, cancellation and lazy cleanup. Existing timeout, malformed output,
quota, 503 and authorization tests remain in the full suite. Reviewer findings
were reproduced and addressed with targeted regression tests.
Final control coverage also suppresses both exact/approximate time after a time
question is skipped, and rejects procedures disguised as open-conversation questions.

## Provider decision and limitations

Configured `gemini-3.5-flash-lite` is retained. Gemini 3.8 Flash was evaluated as
a candidate, not selected: observed timeout/quota failures prevent a defensible
quality comparison. No silent fallback or billing change occurred. Model-list
availability does not establish account quota or production suitability.
Current primary documentation reviewed: [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing),
[quota limits](https://ai.google.dev/gemini-api/docs/rate-limits). Official reporting
claims reuse reviewed [MHA/PIB information](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1814120&lang=2&reg=48).

Small reviewed RAG coverage intentionally limits external answers. Lexical recall
is replaceable and may miss semantic paraphrases. Model latency and free-tier
availability vary. Safety validation is conservative and unsupported output uses
fallback; test results do not establish production security readiness.

No OCR/evidence analysis, reporting packet, voice, broader incident playbooks or
long-term account recovery were implemented. Case cookie expiry is an access
limit, not automatic deletion. Existing development data persists until deleted;
production retention/deletion remains an explicit later-phase decision. Drafts
are session-scoped. Cancelled uploads whose response was lost can remain staged
until lazy cleanup. Remote PostgreSQL and hosted storage were not migrated/tested
during the original acceptance run; see the runtime repair below for later evidence.

## Manual next journey

Open the homepage → Tell us what happened → send a synthetic incident. Ask why a
question matters and what the reporting portal is. Correct the amount, skip a
question, pause, reload, then explicitly resume. Attach a synthetic PNG/PDF with
and without text; retry after an interrupted request; open and delete it after
reload. On mobile, open View case/Response plan while keeping a multiline draft.
Use only synthetic data and expect explicit fallback when free-tier quota is hit.

## Roadmap and core product check

NO CHANGE: Phases 5–7 already anticipate the composer attachments, memory and
current projection. They remain compatible. Later evidence phases should extend
the existing staged upload and turn linkage; case/report views should consume
current backend projections rather than historical assistant claims.

OPTIONAL IMPROVEMENT: retrieval/recall can gain better semantic matching when
evaluation demonstrates a need; keep boundaries replaceable and private.

The planned phase order remains compatible. These decisions do not change a core
invariant. Chat-first experience, no form-first intake, AI conversational
investigation, deterministic critical actions, self-building case, truthful
external status and future official-handoff compatibility are preserved.

## Configured-runtime repair, 2026-10-04

Citizen experience: the running development app can load conversations, reply and
upload/read/link attachments again. Root cause: configured PostgreSQL remained at
`20261001_understanding`, without `evidence.staged_for_chat` or
`conversation_attachments`. Evidence ORM reads failed before AI processing. Original
isolated SQLite verification did not prove this configured runtime was ready.

Decision/database: applied only the existing additive Phase 4 migration
`20261003_chat_attachments`, using a guarded transaction against the configured
database. Checked the starting revision and preserved existing incident, evidence
and conversation row counts. No database switch, case reset or original-file move.

Frontend, backend/domain/AI and API contracts: no implementation changes for this
repair. Startup instructions now explicitly migrate the configured development
database before launching updated code. Startup still does not automatically alter
a remote schema. Security/privacy: existing private case-cookie authorization,
storage and validation boundaries retained; unauthenticated case/evidence reads
returned 404. Diagnostic upload files were deleted; synthetic test cases remain.

Tests: reused the existing migration suite; no new application tests. Ran these
commands from the repository root, except pytest from `backend`:

- `.venv/Scripts/python.exe tmp/diagnose_phase4_schema.py`: confirmed the old schema,
  then confirmed the new revision, Evidence column and attachment table after repair.
- `.venv/Scripts/python.exe tmp/repair_phase4_schema.py`: migration committed;
  existing row counts unchanged.
- `.venv/Scripts/python.exe tmp/verify_phase4_runtime.py`: actual localhost:8000
  case creation 201; conversation/message/replay/evidence/file/attachment/reload
  requests passed; replay deduplicated, unauthorized reads denied, test file deleted.
- `.venv/Scripts/python.exe tmp/phase4_runtime_diagnostics.py`: persisted diagnostic
  results confirmed live Gemini extraction `understood` and follow-up `decided`,
  including successful provider invocation, parsing and follow-up validation;
  removed the diagnostic file left by an earlier verifier parsing error.
- `../.venv/Scripts/python.exe -m pytest tests/test_migrations.py -q`: 5 passed.
- `node tmp/verify_phase4_browser.cjs`: actual localhost:3000 browser send returned
  200; assistant response rendered and survived reload; retry error absent.
  Browser launch required sandbox escalation after subprocess EPERM.

Live provider: actual configured `gemini-3.5-flash-lite`, both critical AI stages
passed on short synthetic messages, including the browser journey. This repair
does not re-establish all original multi-turn quality scenarios or production readiness.

Manual next journey: reload the affected conversation, use Retry message once if
the interrupted-message banner remains, send a short synthetic story and attach a
synthetic PNG/PDF. Confirm the reply appears and survives reload. Do not use real
citizen data. Free-tier quota and provider latency remain limitations; the green
focus outline, branding differences and loading copy are unchanged for now.

Roadmap impact: REQUIRED CHANGE to Phase 5 acceptance scope: shared branding,
accessible focus styling, pending-message presentation, clearer recovery wording
and low-effort distressed-user journeys are now recorded in `phases/phase-05.md`.
Evidence architecture remains compatible: reuse the migrated Phase 4 linkage.
No core invariant changes: chat-first experience, no form-first intake, AI
conversational investigation, deterministic critical actions, self-building case,
truthful external status and future official-handoff compatibility are preserved.
