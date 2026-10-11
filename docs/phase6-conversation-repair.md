# Phase 6 conversation repair checkpoint

**Historical checkpoint, superseded by [final acceptance](phase6-final-acceptance.md).**
The repair gate passed on 2026-10-11: 23 live understanding turns, 15 validated
follow-ups, eight application-control responses and zero fallbacks. Core reporting
is implemented and separately verified. The open-gate and core-not-started wording
below describes the earlier checkpoint, not the current status.

Work started 2026-10-09 and resumed 2026-10-10 after a Codex usage-limit interruption.

## Second resumed repair checkpoint — 2026-10-10

The resumed work repaired shared contracts rather than switching the configured model: each native generation branch now matches the server's move shape; device control is distinct from account compromise; supported service names tolerate the descriptive `account` suffix; and optional imperative buttons cannot discard an independently grounded answer. Only those imperative buttons are omitted, with `omitted_quick_replies` diagnostics; fabricated destinations, secrets, outcomes and unsafe main text still reject the full proposal.

An unanswered question is now deferred when relevant context is unchanged, including after an unrelated correction. Changed context still permits a consequential reask. Two older tests assumed automatic open-story restarting or counted a repeated fake device question as success; those expectations now assert unknown rail preservation and rejection of repetition. An observed false claim that unknown loss meant no loss has a new grounding regression and prompt/validation repair. Canonical unknowns remain unknown.

Fresh verification: **518 backend tests passed in 51.84s**, including 48 repair tests; targeted repair plus the two affected historical tests passed 50/50; frontend contracts passed 13/13. Configured PostgreSQL control/reload/replay/correction/cross-case denial passed with fake AI (`tmp/phase6-configured-contract-final.log`). Exact backend command: `../.venv/Scripts/python.exe -m pytest -q --tb=line --show-capture=no`, output `tmp/phase6-backend-contract-final.log`. Frontend command: `node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs`. No frontend product code changed in this resumed pass; the previously passing `.next-phase6-final` production build was used. A read-only reviewer found no important issue in the generation-schema/device/button changes; later deferral and unknown-loss changes are verified by tests rather than a second review.

Fresh final browser regressions also passed with fake AI: `__tests__/phase6-repair.cjs` (three routes, help/conclusion, mobile drafts and reload), and `__tests__/phase5-journey.cjs` (hybrid entry, upload, partial/conflicting/natural evidence review, canonical memory, plan, mobile resume/deletion). Both use `../.venv/Scripts/python.exe -m tests.smoke_local` with the environment below, `SMOKE_LIVE_AI=0`, and `SMOKE_ASGI_APP=tests.phase5_smoke_app:app`; logs are `tmp/phase6-fake-contract-final.log` and `tmp/phase6-phase5-contract-final.log`. Final `git diff --check` passed. Test permissions were escalated only after Windows sandbox temporary-SQLite access failed; no approval rejection or usage exhaustion occurred in this resumed pass.

The two resumed live browser runs used the exact environment/command documented below, with `SMOKE_LIVE_AI=1` and `SMOKE_ASGI_APP=tests.phase6_live_app:app`. The first exposed the service-name mismatch and unsafe optional buttons. The second (`tmp/phase6-live-contract-final.log`, saved snapshot `backend/tmp/phase6-repair-live-1791646455941.json`) completed **23 synthetic turns** across three routes and witness isolation. Understanding succeeded on every turn; **three follow-up responses were rejected**, with no schema-malformed failure. Two capability descriptions were rejected as instructions (`so you can report it properly` and the CyberSOS-subject clause `guides you ... and report it officially`). The financial response actually instructed bank contact in explanation prose; its first rejection code was `FAKE_EXTERNAL_STATUS` because the broad bank/status pattern also matched citizen payment approval. Codes alone therefore still do not describe the full defect. Mean browser turn latency was 5,250ms; maximum 8,645ms, excluding the harness's deliberate between-turn waits. Token/cost measurements remain unavailable; no quota failure, paid fallback or model switch occurred in these runs.

Human-style inspection also found the unknown-as-no-loss claim (now fixed locally, **not freshly live-verified**) and generic requests for more account-story detail despite an already adequate account-access story. The gate remains **OPEN**. The next repair should distinguish application capability/purpose clauses from citizen instructions without accumulating wording exceptions, keep actual procedural prose rejected, and eliminate redundant open-story requests after adequate understanding. Reporting work remains untouched. The original evidence below is historical where superseded by this section.

## Citizen behavior and decisions

Harassment fallback no longer starts financial intake. Typed help/plan/summary/conclusion requests display current canonical understanding, consequential unknowns and backend-approved actions inside chat, while leaving understanding/reporting review unconfirmed. Questions pause persistently; corrections still update the living case and help. The permanent composer, drafts, retries, replay keys and ownership remain in the same journey.

The diagnosed causes were an unconditional money fallback, provider-dependent citizen control, missing question disposition and disconnected action presentation. Repairs extend existing atomic turns and JSON metadata rather than creating another questionnaire, case store or reporting system. AI interprets facts and multilingual intent. The application handles clear citizen control and renders approved help without a redundant follow-up call; `agent.status=not_requested`, `reason=citizen_control` explicitly identifies this path and is never counted as live AI follow-up success.

Question disposition records answers, declines and repeated nonanswers. Suppression is scoped to relevant context; consequential changed context can permit a meaningful reask. Open-story labels cannot bypass financial question relevance. Evidence requests obey declines. A narrow direct-command fallback protects clear English control during understanding failure and never creates facts, verifies evidence or authorizes actions. This does not replace multilingual AI interpretation with phrase matching.

Witness/separate-incident requests stay outside the original canonical case until scope is clarified. One scope clarification and a separate-case link are available; pause and subsequent clarification do not repeat that question. No physical danger is inferred from harassment. Bystander-specific emergency handling remains **unproven**, and no new critical policy was authored.

## Layer and contract changes

- Frontend: current-help artifact follows the backend projection after corrections, including newly applicable and withdrawn actions; historical help requests do not mix old facts with current instructions. Existing action groups and composer remain. Approximate time and identifiers have readable presentation.
- Backend/domain/AI: `conversation_control.py`, intent/schema/prompt extensions, disposition-aware fallback, current-help projection, consent-versus-fact binding and calibrated semantic validation. Captured synthetic proposals distinguish genuinely repeated/unsafe output from false wording rejection. Critical playbooks are unchanged.
- Database/storage: no migration or new store. Control/dispositions persist in existing revision-bound conversation turn JSON; canonical facts and originals retain their existing storage/provenance. Configured PostgreSQL control/replay/correction and private evidence regression were exercised with fake AI; synthetic cases were retained, originals used by the evidence test were deleted by that test.
- API: existing owned turn/read endpoints; additive turn metadata and `projection.current_help`. `not_requested` is an explicit diagnostic state, not a fabricated provider success.
- Security/privacy: ownership, atomic revision/replay, unknowns, evidence review separation, private originals and deterministic action authority are preserved. Synthetic proposal capture exists only in opt-in test code under ignored `backend/tmp/phase6-proposals`; production does not log raw proposals. No model change, paid fallback, production access, commit, push or deployment.

## Verification evidence

Repository root: `C:/Users/Ishan Chennupati/Downloads/cybersos`. Backend commands run from `backend`; frontend commands from `frontend`. Normal configured frontend API is `http://localhost:8000`; disposable browser builds explicitly use `8001`, frontend `3001`. The stable backend dotenv resolves to `backend/.env`; inspected configured DB is PostgreSQL at the existing Supabase pooler, migration `20261007_evidence_intelligence`. Configured provider remains Gemini `gemini-3.5-flash-lite`, enabled with a configured key; no secret was printed.

| Command / verification | Evidence at checkpoint |
| --- | --- |
| `../.venv/Scripts/python.exe -m pytest -q --tb=line --show-capture=no` | Final current backend suite: **511 passed in 38.67s**, including 41 repair regressions. Log `tmp/phase6-backend-final.log`. Earlier failures were repaired; this result includes the newest control/consent changes. |
| `../.venv/Scripts/python.exe -m pytest tests/test_phase6_conversation_repair.py tests/test_phase4_responses.py -q --tb=line --show-capture=no` | Targeted run: 74 passed in 9.47s before the last three fixes; the final 511-test suite covers those newer fixes. |
| `node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs` | 13 passed on resume. |
| `$env:NEXT_PUBLIC_API_URL='http://localhost:8001'; $env:CYBERSOS_BUILD_DIR='.next-phase6-final'; npm run build` | Resumed production compilation, lint/types and page build PASS. Latest changes after this build are backend/test-only. |
| `../.venv/Scripts/python.exe -m tests.phase6_configured_runtime` | PASS configured PostgreSQL control/reload/replay/correction/current-help and cross-case denial, fake AI. Latest log `tmp/phase6-configured-runtime-resume.log`; this precedes the last case-review pause fix. |
| `../.venv/Scripts/python.exe -m tests.phase5_configured_runtime` | PASS configured private evidence upload/link/analysis/conflict/review/replay/deletion, fake AI. Log `tmp/phase6-evidence-configured-regression.log`. |
| Browser `__tests__/phase6-repair.cjs`, `tests.phase5_smoke_app:app` | PASS three routes, typed help/conclusion, current review not confirmed, mobile composer, artifact drafts and reload. Latest log `tmp/phase6-repair-fake-resume.log`; this precedes the last case-review pause fix. |
| Browser `__tests__/phase5-journey.cjs`, `tests.phase5_smoke_app:app` | PASS hybrid choices, partial/conflict/natural evidence review, current memory/plan, mobile resume/deletion. Log `tmp/phase6-phase5-regression.log`. |
| Browser `__tests__/phase4-journey.cjs`, `tests.case_agent_smoke_app:app` | PASS direct chat, interrupted creation/reload/retry, correction, owned attachment/replay/deletion and mobile artifacts. Log `tmp/phase6-phase4-regression.log`. |
| Browser `__tests__/phase4-scroll.cjs` | PASS desktop/mobile message/action scrolling, independent details and visible draft; mocked case, no AI. Log `tmp/phase6-scroll-regression.log`. |
| `git diff --check` | PASS at final checkpoint; only Git line-ending warnings. |

Browser environment (PowerShell, backend CWD):

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
$env:CYBERSOS_BUILD_DIR='.next-phase6-final'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
$env:SMOKE_ASGI_APP='tests.phase5_smoke_app:app'
$env:SMOKE_JOURNEY='__tests__/phase6-repair.cjs'
../.venv/Scripts/python.exe -m tests.smoke_local
# Live synthetic opt-in: SMOKE_LIVE_AI=1 and SMOKE_ASGI_APP=tests.phase6_live_app:app.
# Clear SMOKE_LIVE_AI for ordinary fake/mock regressions.
```

## Live acceptance and limitations

Live synthetic understanding/follow-up were actually invoked across the three routes, with correction, explanation, distress, uncertainty/skip, help/conclusion and mobile return. Saved snapshots/proposals and screenshots are under ignored `backend/tmp`; logs include `tmp/phase6-repair-live.log`, `phase6-repair-live-2.log`, `phase6-repair-live-final-2.log` and `phase6-repair-live-resume.log`. These runs are not a clean acceptance pass. Failures included genuine known-fact repetition, provider 503/timeouts and false rejections involving reporting-purpose clauses, honest capability limitations and consent questions tagged as fact inquiries. Fixes preserve negative tests for actual unsafe instructions, recovery promises and general-emergency misuse of 1930. A test-harness route-navigation race was corrected; a browser timeout without a started AI stage is not provider evidence.

The final live checkpoint (`tmp/phase6-repair-live-checkpoint.log`) completed the journey chain but failed strict stage acceptance on **six follow-up responses**: three `ACTION_IN_INVESTIGATION` rejections and three schema `MALFORMED_OUTPUT` rejections. Raw synthetic proposals show mixed causes: a financial capability answer introduced bank/1930 instructions without an approved action reference; an account capability explanation was rejected despite describing reporting preparation; and account access already described by the citizen was asked again using `remote_access`, sometimes under an incompatible move type. An action-purpose answer also attached an action ID to an incompatible answer type. These are not all provider outages or all unsafe wording. Further isolated validator fixes would not establish conversational quality.

Control responses rendered approved help and stopped routine questioning even when those ancillary model responses failed. No provider/model substitution or billing change was made. Live provider reliability, comprehensive meaningful conversational acceptance, human-operated manual acceptance, full three-route multilingual control quality and cost/token measurement remain unproven. Earlier two-turn language passes do not certify these new flows. **This repair session ends with the gate open, as required by Phase 6; reporting implementation remains untouched.**

Provider research used [Google's rate-limit documentation](https://ai.google.dev/gemini-api/docs/rate-limits) and [pricing](https://ai.google.dev/gemini-api/docs/pricing). Project/account limits were not enumerated in an authenticated console; a 503 is not proof of quota exhaustion. One build escalation was not executed because automatic approval review itself hit a Codex usage limit; this was not an unsafe-action determination. The user resumed, and the same build then passed.

## Resume and boundary

1. Start from the passing 518-test backend checkpoint. Reproduce the newest captured failures with fixed synthetic outputs: CyberSOS-subject capability/purpose versus citizen instructions; actual procedural model prose must remain rejected. Remove redundant requests for the already adequate account story. Keep the schema/device/service/button/deferral repairs and unknown-loss regression intact; avoid further isolated wording exceptions.
2. Obtain repeatable live three-route understanding/follow-up quality, including the exact harassment -> why money -> stop/help -> conclude chain, plus correction/unknown/distress/reload and supported witness isolation. Review actual usefulness and reduced repetition alongside assertions. Continue to disclose unsupported bystander guidance and any live failures.
3. Publish the final repair evidence and update `docs/phase-status.md`. Only when this mandatory gate passes, begin Phase 6 portal research/mappings, reviewed packet, packet-only narrative, review/export/copy/print and truthful handoff under the existing authorization. Do not begin Phase 7.

Next manual synthetic journey: homepage -> Tell us what happened -> optional Women/Children hint -> "Someone harassed me on Instagram." -> "Why are you asking about money?" -> "Enough questions. Tell me what to do now." -> "Summarize and conclude." Correct to Facebook, open case details with a draft, reload and verify current help reflects the correction while questions remain paused and review remains unconfirmed. Repeat with the documented UPI scam and account-takeover fixtures; never use real citizen data.

Roadmap: **NO CHANGE** to phase scope/order or core invariants. Later reporting must consume current canonical state and require its own revision-bound review; current help/understanding review is not reporting approval. Control and question-disposition metadata remain important context for later companion work. Core check: chat-first, no form-first intake, AI investigation, deterministic critical actions, self-building case, truthful external status and future official-handoff compatibility are preserved.
