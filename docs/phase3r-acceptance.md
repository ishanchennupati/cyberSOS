# Phase 3R final repair and acceptance — 2026-10-02

Update: the later longer-session payment review loop was repaired and verified;
see [phase3r-payment-repair.md](phase3r-payment-repair.md) for current results,
including 380 backend tests and the final six-turn live browser pass.

The initial A/B/C/D acceptance below passed. Phase 4 was not started. This report supersedes older
live-failure checkpoints; historical tests and messages remain history.

1. **Citizen experience:** The four requested synthetic stories pass live extraction,
   canonical merge, deterministic actions, live next-move reasoning, validation and
   mobile browser rendering. The question appears once and natural input remains
   available. A establishes loss=true, amount=5000, INR and unauthorized approval;
   the next move does not repeat those established facts. B retains unknown approval;
   C retains the scam-induced citizen payment, claimed SBI and GPay without inventing
   a victim bank or payment rail. D retains financial and device-compromise signals.
2. **Existing implementation:** Both provider stages, bounded moves, grounding,
   policy evaluation, durable conversation, diagnostics, accepted AI wording and
   single-question rendering already existed in the uncommitted working tree.
3. **Actual remaining gaps:** A previous live correction omitted correction_source
   and remained a conflict. Today's live C altered the rupee character in exact
   source quotes, causing safe rejection of otherwise useful facts. The old browser
   acceptance failed to assert C's payment facts. A subsequent check exposed an
   unsupported signal label and omission of the explicit scam-payment authorization.
4. **Chosen approach:** Reuse the existing grammar, candidate validator and canonical
   merge. For messages up to 512 characters, source_text generation selects exact
   current-message sentence spans through one shared SourceQuote schema definition.
   Longer messages retain arbitrary short exact quotes checked by the application,
   avoiding repeated whole-story output. Signal values use the existing domain
   vocabulary. The prompt clarifies sending after deception and correction intent.
   A narrowly anchored complete amount correction can supply missing correction
   intent only after confidence, source and amount grounding pass. An unrelated
   apology does not authorize an overwrite. No generated critical action authority.
5. **Frontend:** No new production UI changes were necessary this turn. Existing
   accepted AI wording, inline quick replies, composer and current backend-derived
   action plan were verified. C's live browser acceptance now asserts actual payment
   facts as well as absence of invented bank/rail. Next's generated verification-build
   include was removed from tsconfig after building.
6. **Backend/domain/AI:** Exact short-story source grammar, domain signal grammar,
   explicit scam/correction prompt guidance and grounded missing-marker amount
   correction handling. Added a read-only, credential-redacted runtime audit script.
7. **Database/storage:** No new schema/migration. Configured PostgreSQL is already
   at 20261001_understanding, with conversation_states, conversation_turns and all
   required incident columns. It was inspected read-only. Tests used disposable
   migrated SQLite. The development launcher backed up local.sqlite and confirmed
   head before starting; synthetic final browser cases remain in that local store.
8. **API/contracts:** No public API changes. Provider JSON grammar is stricter while
   existing application validation remains authoritative. Existing immutable turn
   JSON retains correction history and provenance; current facts/plans remain backend truth.
9. **Security/privacy:** No secrets printed, hosted case mutations, external messages,
   paid infrastructure, public evidence access or tool authority added. Tests use
   synthetic stories. Source mismatch, unsupported facts, actions, secrets, URLs,
   outcomes and repeated established questions remain rejected. The full suite
   includes cross-case authorization, replay/revision and diagnostic privacy checks.
10. **Tests:** Six new backend cases cover missing correction metadata (two phrases),
    unrelated apology, actual SDK source-grammar transport, valid signal vocabulary,
    and long-story output limits. Existing multilingual doubles cover Telugu,
    Roman Telugu, Hindi and Hinglish; failure regressions distinguish unavailable,
    503, timeout, malformed output, validator rejection and application error.
11. **Verification:** Exact commands and results appear below. Initial correction
    tests failed twice before repair; source grammar and signal tests also failed
    before their repairs. Full final suite: 361 passed. Review found and fixed the
    long-story source-enum output regression before final acceptance.
12. **Live provider:** Real configured Gemini, gemini-3.5-flash-lite, 20-second stage
    deadline, one bounded transient retry. Live four-case browser check passed on
    disposable API 8001/frontend 3001. Final required B/A browser check also passed
    through the actual development API 8000/frontend 3000. Live extraction/next move
    and 5000→4500 correction passed separately through the actual application API
    using TestClient and disposable storage. Scripted browser verification uses a
    fake provider and is reported separately.
13. **Manual test:** Open http://localhost:3000, click Tell us what happened and start
    B: “₹5,000 is gone from my account. I just got a message.” In a new case start A:
    “₹5,000 left my account without my approval.” Confirm grounded acknowledgement,
    applicable actions, one useful move and natural composer. Reply naturally, then
    send “Sorry, the amount was ₹4,500.” Check the current amount, preserved original
    message, reevaluated actions and refresh/resume. Servers were left running.
14. **Limitations:** These are bounded live passes, not a guarantee of provider
    availability or semantic accuracy. Live multilingual quality, long-story live
    quality, sustained load and human screen-reader testing were not evaluated.
    Natural correction forms outside the narrow fallback still depend on provider
    metadata or conflict clarification. Evidence extraction, voice, localization,
    redesigned chat UI and official submission remain outside Phase 3R.
15. **Roadmap impact — NO CHANGE:** Later phases remain compatible. Reuse current
    backend projections and both AI stages; preserve provider grammar/application
    validation separation and existing reporting adapter direction. This repair
    requires no future prompt rewrite and changes no core invariant.
16. **Core product check:** Preserved chat-first/story-first intake, no form-first
    requirement, AI conversational investigation, deterministic critical actions,
    self-building canonical case, truthful external status and future verified
    official-handoff compatibility. No commit, push or deployment.

## Exact verification commands

PowerShell; backend commands run from backend unless noted. Test commands using
Windows temporary SQLite or child processes were rerun with approved escalation
after sandbox failures. Sandbox failures were environmental, not passing results.

```powershell
$env:DIAGNOSTICS_LOG_DIR=''
..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short
```

Final: **361 passed in 35.75s**, exit 0. Baseline before this turn's changes:
355 passed in 32.41s. The initial sandbox full run encountered SQLite temp-directory
permission errors and was interrupted; `pytest -x -q --tb=short` confirmed the cause.

```powershell
..\.venv\Scripts\python.exe -m pytest tests/test_phase3r_case_agent.py tests/test_phase3_understanding.py -q -p no:cacheprovider --tb=short
..\.venv\Scripts\python.exe -m tests.runtime_audit
..\.venv\Scripts\python.exe -m tests.live_case_agent
```

Targeted suite: 94 passed before the final long-story test; final full suite includes
it. Runtime audit: exit 0, configured dotenv/backend directory, redacted PostgreSQL
destination and current revision/tables verified. Live API: **LIVE GEMINI PASS /
LIVE CORRECTION PASS**, exit 0. Earlier Unicode-escaping experiment failed live
grounding and was removed; source validation was never weakened.

Frontend directory:

```powershell
node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs
npm run lint
$env:CYBERSOS_BUILD_DIR='.next-check'
$env:NEXT_PUBLIC_API_URL='http://localhost:8001'
npm run build
```

13 frontend tests passed, lint had no warnings/errors, fresh production compilation,
types and build passed. Node test/build initial sandbox attempts failed spawn EPERM;
approved retries passed. Build directory is separate from the running dev server.

Backend directory, live four-case browser acceptance:

```powershell
$env:CYBERSOS_BUILD_DIR='.next-check'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
$env:SMOKE_LIVE_AI='1'
$env:SMOKE_JOURNEY='__tests__/live-case-agent-journey.cjs'
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
..\.venv\Scripts\python.exe -m tests.smoke_local
```

Final strengthened run: **LIVE GEMINI browser B,A,C,D PASS**, exit 0. Earlier run
passed the old weak C test despite rejected quotes; strengthened acceptance then
failed on missing authorization, which prompted the grounded prompt clarification.

Backend directory, fake-provider browser acceptance against fresh build (separate
shell; SMOKE_LIVE_AI unset):

```powershell
$env:CYBERSOS_BUILD_DIR='.next-check'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
$env:SMOKE_ASGI_APP='tests.case_agent_smoke_app:app'
$env:SMOKE_JOURNEY='__tests__/case-agent-journey.cjs'
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
..\.venv\Scripts\python.exe -m tests.smoke_local
```

**PASS FAKE PROVIDER browser**, exit 0: numeric AI wording, natural quick reply,
correction, device signals, optional evidence, fallback, resume and 320px layout.

Started actual development servers:

```powershell
# Repository root:
.\.venv\Scripts\python.exe backend/run_local.py
# Frontend, separate shell:
npm run dev
```

Launcher confirms absolute backend/local.sqlite, backend/.env, current model,
key-present boolean and successful API startup. Frontend ready at localhost:3000.
No production database writes were used for citizen acceptance.

Frontend directory, final actual-development browser acceptance:

```powershell
$env:SMOKE_FRONTEND_URL='http://localhost:3000'
$env:SMOKE_API_URL='http://localhost:8000'
$env:SMOKE_LIVE_AI='1'
$env:SMOKE_LIVE_CASES='B,A'
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
node __tests__/live-case-agent-journey.cjs
```

**LIVE GEMINI browser B,A PASS**, exit 0. B requested optional transaction evidence;
A asked about ongoing loss. Neither fell back. Screenshots and synthetic diagnostics
are ignored under backend/tmp; screenshot A was visually inspected.

Repository root: `git diff --check` passed (line-ending advisories only). Existing
user changes and earlier phase work remain uncommitted.
