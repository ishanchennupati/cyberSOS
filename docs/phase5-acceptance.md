# Phase 5 implementation and acceptance

Date: 2026-10-07. Scope: hybrid conversation, initial three-route coverage and evidence intelligence. No Phase 6, commit, push, deployment, billing or model change.

**Subsequent quality audit:** local infrastructure/regression passes did not establish the full conversational contract. Offline probes reproduced repeated irrelevant fallback questions and ignored plan/stop requests. Remaining work includes application behavior, not only provider reliability; see [conversation-quality audit](phase5-conversation-quality-audit.md).

## Result and engineering decisions

Citizens can speak immediately, optionally choose/change a route hint, attach records in the same composer, review useful extracted details individually or in natural conversation, resolve conflicts and resume the same growing case. Justified urgent help appears early; initial fuller-plan presentation follows a concise understanding review. Later corrections refresh the living plan without demanding review on every turn.

The gaps were financial assumptions in shared facts/actions, legacy evidence verification that did not update canonical conversation truth, and missing attachment-analysis/review lifecycle in the chat. The implementation extends existing ownership, storage, fact validation and atomic revision/idempotency machinery rather than adding per-category systems.

- Frontend: shared branding, optional hints, pending citizen/assistant states, persistent composer/drafts, inline source preview/review, partial/conflict controls, explicit natural-review focus, analysis polling/retry, mobile reload and honest deleted-source copy. Existing scroll repair is preserved.
- Backend/domain/AI: additive nullable facts, playbook 1.2.0, current-plan refresh preserving historical snapshots, exact candidate/quote/reference validation, partial natural review, per-identifier provenance and canonical memory refresh. Active evidence review has a bounded 30-second model timeout; ordinary text remains 20 seconds. Native schema limits quick replies to four.
- Database/storage: additive `20261007_evidence_intelligence` creates immutable attempts and review records with one active processing attempt per original. Configured PostgreSQL migration preserved existing row counts. Originals remain in existing private storage; deletion clears derivatives and tombstones retained reviewed fact sources.
- API/contracts: owned `POST /evidence/{id}/analyze`; extended conversation turns for evidence review, route hint and understanding review; read projection includes review/analysis states. Existing turn revision and replay keys control merges. Legacy mutation routes cannot bypass chat canonical truth.
- Security/privacy: case capabilities on all reads/mutations; stale/replayed/late-deleted results cannot overwrite current truth; broad Yes cannot confirm unrelated documents; embedded evidence instructions cannot authorize actions or external access. No raw real citizen records were used. This is functional/security regression verification, not an independent exhaustive security audit.
- Tests: added Phase 5 policy, evidence and hybrid suites; updated historical expectations for narrower banking/urgency applicability; added fake and live browser journeys, interrupted-analysis and delayed-first-attachment checks. Independent read-only review findings were addressed and rereviewed.

## Verification ledger

Repository root: `C:\Users\Ishan Chennupati\Downloads\cybersos`. Commands below run from `backend` unless specified. Tests require Windows temporary-file/browser/worker permissions. Disposable browser harnesses own their test processes, SQLite database and synthetic evidence directory.

| Command / environment | Result |
| --- | --- |
| `../.venv/Scripts/python.exe -m pytest -q --tb=line` | Final: 470 passed in 25.92s. Initial baseline: 422 passed in 28.58s. Final regression initially found six failures; premise validation preserves candidate verification/evidence requests while rejecting unsupported transaction questions, the payment fixture now states UPI, and the new timeout was added to the environment example. New helpline and move-label guard tests also passed after correcting exact synthetic source quotes/schema labels. |
| Frontend: `node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs` | 13 passed. Urgent-style expectation updated to backend critical AND high/critical priority; neutral containment remains available in the fuller plan. |
| Frontend: `$env:NEXT_PUBLIC_API_URL='http://localhost:8001'`, `$env:CYBERSOS_BUILD_DIR='.next-phase5'`, `npm run build` | Passed compilation, lint, type check and production page build. |
| `../.venv/Scripts/python.exe -m tests.smoke_local`, `SMOKE_ASGI_APP=tests.phase5_smoke_app:app`, `SMOKE_JOURNEY=__tests__/phase5-journey.cjs` | Passed three-route synthetic browser journey, optional/mistaken hints, pending, first-message delayed analysis, partial/conflict/natural review, canonical memory, fuller plan, mobile resume and deletion. AI is fake. |
| `$env:PHASE5_APPLY_DEV_MIGRATION='1'`, `../.venv/Scripts/python.exe -m tests.phase5_configured_migration` | Passed guarded configured PostgreSQL additive upgrade, unchanged existing row counts. |
| `../.venv/Scripts/python.exe -m tests.phase5_configured_runtime` | Passed configured PostgreSQL/private-storage upload, conflict/review, replay, reload, cross-case denial and original deletion. AI explicitly fake; synthetic case retained. |
| `../.venv/Scripts/python.exe -m tests.phase5_provider_probe` | Live synthetic PNG extraction passed, 9348 ms. |

Browser harness common PowerShell environment (exact):

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
$env:CYBERSOS_BUILD_DIR='.next-phase5'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
# Set SMOKE_ASGI_APP and SMOKE_JOURNEY to the pair in the ledger.
../.venv/Scripts/python.exe -m tests.smoke_local
```

**Implementation/local acceptance PASS; comprehensive live acceptance NOT PASS.** Opt-in live environment additionally uses `$env:SMOKE_LIVE_AI='1'`, `$env:SMOKE_ASGI_APP='tests.phase5_live_app:app'`, `$env:SMOKE_JOURNEY='__tests__/phase5-live.cjs'`. Existing configured model is `gemini-3.5-flash-lite`, retained. One earlier whole live run passed all routes and formats, but human review identified an assumed payment in the ambiguous opening; that run was not treated as final acceptance. Final scoped guard regressions cover clarification, open-conversation and relevant-answer labels. Subsequent attempts exposed bounded timeouts and oversized reply output, now schema-bounded. Provider failures preserve saved conversation and safe canonical facts; they do not establish stable live reliability.

The final comprehensive attempt passed live ambiguous-loss clarification, clear financial facts/actions, PNG/JPEG/PDF native extraction, amount conflict resolution and all-remaining-details natural review (both AI stages, canonical transaction ID). It also extracted safe Instagram threat details. A financial process answer timed out and a threat response was rejected for adding instructions; an automated reload then failed with `ERR_NETWORK_IO_SUSPENDED`. Strict acceptance remained failed. The separate account-only run reached owned account screenshot extraction and mobile reload: opening understood/decided in 6375 ms, account story understood but question-field mismatch rejected in 5909 ms, process answer understood/decided in 7261 ms, PNG review-needed in 6755 ms. Strict stage checks failed because of that mismatch. No clean overall live pass is claimed. Synthetic diagnostics are in ignored `tmp/phase5-live-acceptance.log`, `tmp/phase5-live-account.log` and `backend/tmp/phase5-live-results-*.json`.

Live measured browser durations in the comprehensive attempt: ambiguous opening 6760 ms; financial story 7252 ms; natural document review 9025 ms; financial PNG 6632 ms, JPEG 7714 ms, PDF 7160 ms; threat PNG 9012 ms. These include client/API work and are observations, not performance guarantees or time-to-first-action measurements. The timed-out financial answer took 22729 ms. No paid fallback or model comparison was performed in this phase.

Additional browser regression: same common environment, `SMOKE_ASGI_APP=tests.case_agent_smoke_app:app`, `SMOKE_JOURNEY=__tests__/phase4-journey.cjs`: PASS fake AI, direct chat, interrupted creation, retry once, correction/resume, attachment-only/replay/deletion and mobile artifacts. With `SMOKE_ASGI_APP=tests.phase5_smoke_app:app`, `SMOKE_JOURNEY=__tests__/phase4-scroll.cjs`: PASS mocked case, desktop/mobile wheel scrolling, independent details scrolling and composer draft visibility. An earlier standalone scroll attempt hit connection refused after the live harness had stopped; the self-contained rerun passed.

Live language regression: common environment plus `SMOKE_LIVE_AI=1`, `SMOKE_ASGI_APP=tests.phase5_live_app:app`, `SMOKE_JOURNEY=__tests__/phase4-languages.cjs`, `../.venv/Scripts/python.exe -m tests.smoke_local`: PASS Roman Telugu and Hinglish, two turns each, both AI stages, validated facts/rendering/reload. This does not certify all three incident domains in those languages or voice. Final `git diff --check`: PASS (line-ending normalization warnings only).

## Manual journey and limits

Open the homepage → Tell us what happened → type “I lost 5000” without choosing a hint. Confirm no bank/1930 action. Start a synthetic case with Financial Fraud and “Someone pretending to be my bank made me send INR 35000 via UPI ten minutes ago.” Attach `backend/tests/fixtures/phase5/financial.png`. Compare screenshot INR 3500 with story INR 35000, select Use attachment value, then say “All remaining details in this attachment are correct.” Review the case, open the fuller plan, reload on a narrow viewport, and delete the attachment; confirmed details remain honestly labeled. Repeat with non-explicit threat and Google-account synthetic stories/fixtures. Do not use real citizen files.

Human-operated manual browser acceptance was not run; automated browser journeys plus human inspection of synthetic output are distinguished. Declared limits, supported scenarios, languages and lifecycle are in [the support matrix](phase5-support-matrix.md). Provider latency/timeouts remain a limitation; no launch reliability target, universal-language/image accuracy or recovery promise is claimed.

## Roadmap and core check

**NO CHANGE** to phase scope/order or core invariants. Later phases must consume current canonical facts plus source-linked immutable attempts/reviews, not legacy `Evidence.extracted_data`. Phase 6 requires its own fresh revision-bound reporting approval; prior understanding review is not approval to submit a complaint. Phase 7 must define full-case lifecycle and return semantics; Phase 8 expands proven coverage; Phase 9 adds voice. No later-phase capability was implemented.

Core check: chat-first, no form-first intake, AI-led investigation, deterministic critical actions, self-building canonical case, truthful external status and future official-handoff compatibility are preserved.

## Timing evidence

Historical local root-session task intervals for this repository (excluding idle gaps and subagent sessions) show Phase 2 about 90 active minutes, initial Phase 3 about 47 minutes, and Phase 4 about 210 minutes including follow-ups (main implementation about 180). Repairs varied substantially. Phase 5 began at 13:37:46 UTC today. The initial generic 6–10 hour estimate was corrected to roughly 2.5–4 hours after examining those records. Remaining-time estimates are ranges because provider failures and regressions cannot be predicted precisely.
