# Phase 6 manual-test repair — 2026-10-11

Scope: repair the reported repeated conversation, irrelevant questions and sent
text remaining in the composer. The requested inline response plan followed by
a populated draft case sheet is recorded in [Phase 7](phases/phase-07.md), for
implementation in that phase.

The reported repairs are implemented and verified within the English synthetic
scope below. This supplements the earlier Phase 6 acceptance.

## Evidence and root causes

The latest development logs and stored conversation showed separate assistant
turns repeating the same recap after No/Yes; React was not duplicating one turn.
The unknown-field context omitted empty identifiers but offered claimed identity
fields for ordinary harassment. A declined profile question could return after
new threat signals. The composer cleared only after the complete server response.
The existing fact review remained collapsed when the agent finished investigating.

The original Hi failure had a bounded ValueError diagnostic without retained raw
output; its exact cause cannot be proved retrospectively. Synthetic live replay
exposed additional concrete failures: unsupported coercive blackmail from an
unconditional leak threat, a payment-only confirmation flag on an ordinary answer,
a legitimate username question rejected by topic validation, inverted danger
question wording, and a greeting rejected for its optional open question.

## Changes and boundaries

- Citizen experience/frontend: submitted text clears immediately; pending text
  remains visible in the transcript. Failures restore an untouched draft, retries
  reuse the turn key, and newer typing survives success/failure. Identical newer
  text and a deliberately cleared draft survive, including reload recovery.
  Existing understanding review opens when investigation yields an acknowledgement;
  explicit review confirmation still opens the existing response plan.
- Backend/domain/AI: offer identifier targets and filter unrelated identity/payment
  recipient targets; preserve declined identifiers after new threats and combined
  text/identifier requests. Reject repeated unchanged case recaps and offer the
  existing review instead. Bind short-message intent quotes and nonpayment
  confirmation flags in the native schema. Unsupported English coercion stays an
  uncertain candidate. Reject inverted danger questions. Preserve a safe grounded
  greeting body while omitting its unnecessary question, after validating the
  entire proposal for safety and grounding, then validating the retained body.
- Storage: existing owned turns retain review/disposition metadata. No new tables,
  migrations or historical fact rewrites. No API routes or request types changed;
  turn metadata includes an optional review prompt and additional declined-topic
  context. Frontend typing reflects the optional review prompt.
- Security/privacy: ownership, private evidence, idempotency, revision checks,
  source grounding and deterministic action policy remain enforced. Bare Yes/No
  and greetings never approve the understanding or reporting packet. Diagnostic
  codes remain bounded; no raw citizen/provider output is added to production logs.

## Verification

New repair regressions were observed failing before their fixes. The repair suite
now contains 78 tests, including question relevance, deferral, repeated recap,
native schema, intent diagnostics, unsupported coercion and safe greeting retention.
Browser regressions cover immediate clearing, interrupted sends, same-key retry,
desktop/mobile, concurrent drafts and deliberately empty draft persistence.

From `backend`:

```powershell
../.venv/Scripts/python.exe -m pytest -q
../.venv/Scripts/python.exe -m pytest tests/test_phase6_conversation_repair.py -q
../.venv/Scripts/python.exe -m tests.smoke_local
```

From `frontend`:

```powershell
node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs
$env:CYBERSOS_BUILD_DIR='.next-phase6-manual'
$env:NEXT_PUBLIC_API_URL='http://localhost:8001'
node node_modules/next/dist/bin/next build
```

Full backend: **574 passed in 66.94s**,
`tmp/phase6-manual-repair-backend-final.log`.
Frontend contracts: **13 passed**, `tmp/phase6-manual-repair-frontend-final.log`.
Production compilation, lint/types and
page generation passed, `tmp/phase6-manual-repair-build.log`. The build used the
previous verified unchanged font cache after a clean-cache Next font-fetch failure;
clean-cache remote font loading is an existing unresolved build limitation.

The smoke command used the installed Python Playwright driver package,
`CYBERSOS_BUILD_DIR=.next-phase6-manual`, backend port 8001 and frontend port 3001.
Each run migrated a disposable SQLite database and used its own temporary servers;
the normal development servers were preserved.

| Journey | App / live flag | Evidence under `tmp/` |
| --- | --- | --- |
| Immediate clearing, failure recovery and retry | `tests.case_agent_smoke_app:app` / 0 | `phase6-send-repair-final.log` |
| Identical and deliberately cleared newer drafts | `tests.case_agent_smoke_app:app`, controlled turn responses / 0 | `phase6-send-races-final.log` |
| Reporting through all three routes, copy/PDF, stale approval and mobile | `tests.phase6_reporting_smoke_app:app` / 0 | `phase6-manual-reporting-regression.log` |
| Evidence, conflict review, memory, resume and deletion | `tests.phase5_smoke_app:app` / 0 | `phase6-manual-phase5-regression.log` |
| Chat, interrupted creation/retry, private attachments and mobile | `tests.case_agent_smoke_app:app` / 0 | `phase6-manual-phase4-regression.log` |
| Exact synthetic manual-test sequence through Hi and review | `tests.phase6_live_app:app` / 1 | `phase6-manual-repair-live-acceptance.log` |

Select `SMOKE_ASGI_APP`, `SMOKE_JOURNEY` and `SMOKE_LIVE_AI` before the smoke
command. Corresponding journeys are `phase6-send-repair.cjs`,
`phase6-send-races.cjs`, `phase6-reporting.cjs`, `phase5-journey.cjs`,
`phase4-journey.cjs` and `phase6-manual-repair.cjs` under `frontend/__tests__/`.
The draft race test mocks delayed POST responses; it is not live AI evidence.
`git diff --check` passed; CRLF conversion warnings are not whitespace failures.

The complete live browser replay passed with the configured Gemini
`gemini-3.5-flash-lite`: ten successful understanding calls, nine accepted model
replies and one application review response after recap validation, followed by
explicit review/plan confirmation. No quota/timeout/malformed-output fallback
occurred in that run. Inspection then found that the recap guard had also rejected
a legitimate platform-referencing greeting. The guard was narrowed and that exact
captured live greeting was reproduced RED→GREEN through the owned durable API,
alongside the full backend suite; no additional live call was required for that
validation-only refinement. The live browser run predates this final narrowing.
Provider, timeout/retry settings and free-tier configuration remain unchanged.
Earlier failed replays remain failed evidence under
`phase6-manual-repair-live*.log`; they are not counted as successful runs.

## Manual journey, limits and roadmap

Create a fresh synthetic women/children-hint case; describe Instagram harassment,
decline profile details, add a leak threat without a demand, answer useful questions,
then send Hi. Check that text clears while pending and declined details are not
asked again. Review the current understanding explicitly to open the existing plan.
Type another draft during a delayed send and check that it survives. Continue with
the existing separate reporting packet review/copy/export flow.

This repair does not silently correct historical reviewed facts. Correct an old
case in chat and review its current facts. The coercion safeguard and additional
question-topic recognition are bounded English repairs, not new multilingual
coverage. Model replies remain nondeterministic and provider failures retain safe
recovery. No live reporting-draft rerun was needed for unchanged reporting code;
its prior live evidence remains in [Phase 6 acceptance](phase6-final-acceptance.md).

Roadmap: **OPTIONAL IMPROVEMENT**, now explicitly assigned to Phase 7: a current
review leading to an inline personalized plan and filled draft case sheet. The
existing canonical projection and Phase 6 packet boundaries remain compatible;
no core invariant changes are needed. No Phase 7 implementation, model switch,
billing, commit, push or deployment occurred.

Core check: chat-first, no form-first intake, AI investigation, deterministic
critical actions, a self-building case, truthful external status and official
handoff compatibility are preserved.
