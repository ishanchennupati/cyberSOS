# Phase 3R payment conversation repair — 2026-10-02

The narrow payment-method repair is implemented and verified. Phase 4 has not
started. This supplements the earlier A/B/C/D acceptance, which did not reveal
the longer-session payment verification loop.

1. **Citizen experience:** Natural payment names become canonical values. Citizens
   can confirm a pending method naturally without repeating its name. Accepted AI
   questions and optional Yes/No replies remain visible; free text remains available.
2. **Previously working:** Two-stage Gemini, canonical persistence, reviewed action
   policy, current backend projections, one conversational interaction and composer.
3. **Actual gap:** Saved session candidates repeatedly contained `net banking`
   instead of `net_banking`; uncertain candidates lacked a safe semantic confirmation
   path. Terminal logs separately reported `QUESTION_FIELD_MISMATCH` and
   `UNSUPPORTED_QUICK_REPLY`. Rejected raw wording was not retained, so the exact
   text behind those historical rejections cannot be reconstructed.
4. **Decision:** Reuse existing extraction, validation, fact merge and next-move
   pipeline. Normalize supported rail names and bind AI-understood confirmation to
   one active supported candidate. Preserve validation rather than accepting arbitrary
   provider output or matching citizen replies to a fixed list of sentences.
5. **Frontend:** No production UI changes required. Added a six-turn live mobile
   browser regression for wording, composer, corrected amount and reload.
6. **Backend/domain/AI:** Canonical rail enum in provider grammar; natural aliases
   normalized before candidate review; optional AI semantic confirmation/rejection
   marker; active candidate and displayed-question matching; source/confidence checks;
   verification provenance; declined reviews cleared from current projection.
   All payment verification questions must name exactly their target rail, including
   aliases, even without quick replies. Extraction rechecks historical questions too.
7. **Database/storage:** No migrations or new tables. Existing JSON turn metadata
   stores the optional marker and resolved reviews. Historical messages and snapshots
   remain unchanged; legacy candidate aliases normalize only in active projection.
8. **API/contracts:** Routes and citizen request payloads unchanged. Internal typed
   extraction Candidate adds nullable strict `confirms_pending`, payment-method only.
   Existing responses may include this additional candidate metadata.
9. **Security/privacy:** Confirmation cannot invent a method, verify a different
   target, or promote uncertainty. GPay and generic card do not establish a rail.
   Exact current-source quotes and confidence checks still apply. Case authorization,
   deterministic actions and private diagnostics remain intact. Tests use synthetic
   cases and isolated migrated SQLite; no user case edits or secret output.
10. **Tests:** 19 new regressions cover aliases, natural affirmation, rejection,
    uncertainty, replay, later turns, wrong/absent targets, vague/multiple-rail
    verification and provider grammar. Existing numeric, corrections, languages,
    unauthorized/ambiguous/scam payment, device, timeout, malformed-output and
    provider failure regressions remain in the full suite.
11. **Verification:** Exact commands and results below. Read-only reviewer reproduced
    the missing question-target guard; it was repaired and rechecked with no remaining
    material findings.
12. **Live provider:** Gemini `gemini-3.5-flash-lite`; both extraction and reasoning
    passed on all six final browser turns, including validation and actual rendering.
    A separate three-turn live confirmation test passed after an explicitly synthetic
    seed. One initial browser run hit HTTP 429 on turn six; the final sequential run
    passed. The quota failure is provider availability, not validator rejection.
13. **Manual journey:** With the updated backend running, open localhost:3000,
    click Tell us what happened and send “Someone deceived me. I sent ₹5,000 using
    net banking.” Answer naturally. If asked to verify net banking, say “That is right,
    that was how I paid.” Then say “Sorry, the amount was ₹4,500.” Reload: the current
    case should retain the method and corrected amount; historical wording remains.
    Also rerun fresh cases for “₹5,000 is gone from my account. I just got a message.”
    and “₹5,000 left my account without my approval.” Established facts must not be
    requested again; currently justified actions appear with one useful next move.
14. **Limitations:** Provider quota/timeouts can still trigger safe fallback. These
    tests establish specific journeys, not universal conversational correctness.
    Semantic pending confirmation is currently scoped to payment method. The live
    confirmation seed uses a fake provider to establish reproducible uncertainty;
    its subsequent extraction/reasoning calls use live Gemini. No complete Phase 4
    prompt text was supplied for line-by-line confirmation.
15. **Roadmap:** NO CHANGE. Phase 4 should reuse canonical backend facts and current
    projections, preserving natural text and server-validated AI investigation.
    Use the updated Phase 4 prompt in a fresh conversation. No future feature was built.
16. **Core product:** Preserved chat-first intake, no form-first flow, AI conversational
    investigation, deterministic critical actions, self-building case, truthful external
    status and official-handoff compatibility. No commit, push or deployment.

Exact commands, from `backend` unless indicated:

```powershell
$env:DIAGNOSTICS_LOG_DIR=''
..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short --show-capture=no
# 380 passed in 43.12s.

..\.venv\Scripts\python.exe -m tests.live_payment_confirmation
# LIVE PAYMENT CONFIRMATION PASS; three live extraction/reasoning turns after fake seed.

$env:CYBERSOS_BUILD_DIR='.next-check'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
$env:SMOKE_LIVE_AI='1'
$env:SMOKE_JOURNEY='__tests__/payment-live-journey.cjs'
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
..\.venv\Scripts\python.exe -m tests.smoke_local
# Initial run: turn six provider 429. Final run: LIVE GEMINI six-turn payment browser PASS.

# From frontend:
node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs
# Initial sandbox subprocess EPERM; rerun with escalation: 13 passed.
```

The existing `.next-check` production build was reused because production frontend
source did not change in this narrow repair. Smoke servers were isolated on
3001/8001 and cleaned up; the user's 3000/8000 servers were not terminated.
