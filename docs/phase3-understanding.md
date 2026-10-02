# Phase 3 / 3R operating notes

## Final acceptance — 2026-10-02

The latest repair and real development-server acceptance pass. See
[phase3r-acceptance.md](phase3r-acceptance.md) for the complete current report,
exact commands, actual runtime, separate live/fake results and limitations.
Both live stages passed for B/A/C/D, and required B/A also passed through ports
3000/8000. New repair preserves exact short-message source spelling, domain signal
vocabulary and grounded amount-correction intent. Longer messages retain bounded
application-validated substring selection. Historical checkpoints below remain
history; they do not override this current acceptance. No Phase 4 started.

## AI availability and diagnostic repair - 2026-10-02

This update supersedes the runtime/model state in the earlier checkpoint below.
The user authorized upgrading hosted PostgreSQL: four pending tracked migrations
were committed atomically, from `20260824_urgency_metadata` to
`20261001_understanding`. Both pre-upgrade incident/evidence tables were empty.
All current model tables/columns were verified, and the running API created/read
a synthetic case and denied access without its case credentials. The smoke case
was removed. No new migration or startup DDL was introduced by this repair.

The user's subsequent screenshots were checked against saved stage diagnostics:
the first story and unauthorized reply extracted successfully; one follow-up
returned 503; the later evidence request was a successful AI decision; correction
extraction returned 503 and follow-up was correctly skipped. The connection/key
was present. These were intermittent provider failures, not missing AI wiring.

`gemini-3.5-flash-lite` is now the configurable development default and was set in
the ignored local `.env` while preserving credentials. Official model/pricing
documentation was checked on 2026-10-02. A synthetic live unauthorized case passed
both extraction and validated next-move reasoning. The final four-case live browser
acceptance passed, as did a live 5,000-to-4,500 correction with original history
preserved. Results and exact commands are recorded in verification.md. These bounded
passes do not guarantee ongoing provider capacity or multilingual quality.

Provider output grammar now binds candidate fields to their correct value types,
using the same field groups as application validation. Instructions clarify literal
currency normalization, exact source quotes, mixed device/financial signals, allowed
quick replies and current access versus merely installed software. Safety validators
and deterministic playbook authority remain intact. One configured retry handles
transient network/500/502/503/504 failures inside the original 20-second stage deadline;
quota, authentication, unknown models and invalid output are not blindly retried.

Privacy-safe diagnostic logs correlate HTTP and AI stage results with a request
ID. Backend JSON events go to terminal and rotating ignored file logs; frontend
HTTP/AI/runtime/rendering errors go to the browser console. Raw request targets,
exception messages, SQL parameters, stories, evidence and provider output are
excluded. Known schema validation locations/types and safe stack frames remain
available. API responses expose `X-Request-ID`; controlled 500 responses include
the same request ID. No new reporting/voice/evidence-extraction phase was started.

## Answered-candidate verification repair - 2026-10-02

The subsequent user session had two `ALREADY_ANSWERED` next-move rejections, not
provider outages. Read-only saved turn metadata established the cause: a Not-sure
answer about ongoing loss remained a `needs_review` candidate and was offered for
verification on two later turns. Active unresolved candidates now exclude answered
uncertainty, including the current Not-sure reply. Historical candidates remain;
actual conflicts are retained for conflict resolution. Unknown remains unknown.

Gemini's per-case response grammar now limits clarification to eligible unknown
fields, verification to eligible unanswered candidates, and conflict resolution
to actual conflicts. No fixed question sequence or relaxation of safety validation
was added. The provider receives the case as structured JSON rather than a JSON string.
Both exact regressions and two real Gemini follow-ups on a seeded declined-answer
fixture passed. Full backend acceptance: 355 tests. A separate fully live correction
check asked for conflict review instead of immediately applying the corrected amount;
it did not meet automatic-correction acceptance. See verification.md for details.

## Earlier checkpoint - 2026-10-02

The user authorized the additional Phase 3R repair. Code repair and deterministic
acceptance are verified; **full live Gemini acceptance remains incomplete**.
No Phase 4 or Phase 5 was started. Preserve uncommitted work and user AGENTS.md edits.

The exact screenshot turn ("5000 gone", 2026-10-01 19:31:53) is in
`backend/local.sqlite`: extraction accepted money_lost=true and amount=5000;
next-move invocation returned ServerError HTTP 503 before parsing/validation.
Other validator/wording/UI defects were independently reproduced and repaired.

The backend the user restarted on 8000 instead used the configured PostgreSQL
database at revision `20260824_urgency_metadata`, without conversation tables;
creating a case returned HTTP 500 before AI. The old local SQLite store is at
`20261001_conversation`. Dotenv was CWD-relative, shell overrides take precedence,
and settings are cached. Settings now anchor `backend/.env`; `backend/run_local.py`
explicitly selects local SQLite, snapshots it, applies tracked migrations, disables
remote evidence storage and starts the API. Stop the existing backend first:

```powershell
# Repository root; frontend can remain running on 3000.
.\.venv\Scripts\python.exe backend/run_local.py
```

No remote database migration or API-key change was made. The original database and
credentials remain in ignored `.env`. The launcher is synthetic development only.

Final live browser/API/Gemini check on isolated ports 8001/3001, configured
`gemini-3.8-flash`, 20-second stage timeout and zero retries:

| Case | Extraction | Next-move reasoning | UI fallback |
| --- | --- | --- | --- |
| B: amount + transaction message | HTTP 503 | skipped | once, composer enabled |
| A: explicit unauthorized debit | HTTP 503 | skipped | once, composer enabled |
| C: SBI claim + GPay transfer | strict parsing rejected output | skipped | once, composer enabled |
| D: AnyDesk + money disappeared | HTTP 429 quota | skipped | once, composer enabled |

Raw model output was not saved. The exact malformed field in C was not captured;
future failures now record bounded Pydantic error locations/types without raw
input or messages. No successful live next move was observed. Do not claim a live
pass or repeat calls while quota is exhausted. A new API key alone is not a fix:
Gemini limits apply per project; 503 and malformed output are separate failures.

When the user indicates quota is available or has configured another authorized
project, rerun explicit live browser acceptance from `backend`:

First build from `frontend` with `CYBERSOS_BUILD_DIR=.next-check` and
`NEXT_PUBLIC_API_URL=http://localhost:8001`; the API URL is compiled into browser code.

```powershell
$env:CYBERSOS_BUILD_DIR='.next-check'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
$env:SMOKE_LIVE_AI='1'
$env:SMOKE_JOURNEY='__tests__/live-case-agent-journey.cjs'
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
..\.venv\Scripts\python.exe -m tests.smoke_local
```

This preserves the user's servers and uses disposable migrated SQLite/evidence.
It uses the real provider; synthetic candidate/canonical/agent/rendering diagnostics
and screenshots are saved only in ignored `backend/tmp`. Normal smoke/pytest
runs never use a real key. Live tests respect configured bounded retries. Build
`.next-check` first if the frontend source or compiled API URL has changed.

Phase 3 adds interpretation to the existing conversation controller. It does not
add Phase 4 design, voice, evidence AI, government submission or full localization.

## Configuration

Install backend/requirements.txt and run `alembic upgrade head` from backend using
the project environment before starting the upgraded server. The migration only
widens saved turn text; it preserves prior turns and state. Downgrade deliberately
retains TEXT so saved stories are not truncated.

`GEMINI_API_KEY` is optional. Without it, the API saves stories and honestly uses
one focused clarification. `UNDERSTANDING_ENABLED=false` or provider `disabled`
also enables this path. Never use actual citizen data during prototype testing.

The intended primary provider is Gemini, using google-genai 2.26.0. Its dependency
requirements raised Pydantic to 2.13.5 and httpx to 0.28.1. Provider calls use
strict JSON Schema output and register no tools. Model defaults to
`gemini-3.8-flash`; override `UNDERSTANDING_MODEL` when your project requires it.
The default deadline is 20 seconds per stage (configurable up to 30), including
bounded retries. Local `.env` retains zero retries for free-tier testing. Gemini's
HTTP deadline is never below its observed 10-second minimum. SDK retries are
disabled; low thinking is used for configured Gemini 3 models. Input is bounded at 8000 characters; provider output is
bounded by token and character limits. All settings are in backend/.env.example.

SDK/model references checked 2026-10-01:

- [Google Gen AI Python SDK](https://github.com/googleapis/python-genai)
- [Official model list](https://ai.google.dev/gemini-api/docs/models)
- [Structured output documentation](https://ai.google.dev/gemini-api/docs/structured-output)

Live synthetic Gemini calls were made in Phase 3R. Initialization, extraction,
strict parsing and canonical merge succeeded for the unauthorized ₹5,000 example.
Full live case-agent acceptance did **not** pass: next-move calls timed out or
received HTTP 503 high-demand responses, and later extraction calls also returned
503. Multilingual live quality still needs evaluation. No API key is printed.

## Phase 3R conversation architecture

The root defects were a fixed question selector after extraction and provider
failure hidden by generic fallback. Live debugging found an invalid 8-second SDK
deadline and a rejected complex extraction grammar. Provider schemas now compact
duplicate union branches and omit transport-only limits; strict Pydantic limits,
types, extra-field rejection and grounding remain authoritative in the app.

Each turn now follows:

message → candidate extraction → validation/merge → deterministic playbook →
case-aware AI next move → move validation → atomic case/turn/plan update.

`NextMove` supports ASK_CLARIFICATION, REQUEST_EVIDENCE, VERIFY_INFORMATION,
RESOLVE_CONFLICT, ACKNOWLEDGE_AND_WAIT, EXPLAIN_APPROVED_ACTION and
CONTINUE_OPEN_CONVERSATION. It carries purpose, proposed message, related fact,
optional safe quick replies/evidence intent/action reference and bounded basis
labels. It has no authoritative action-plan field or chain-of-thought.

AI owns move choice and timing; there is no ordered interview on successful AI
turns. The app rejects established/declined facts, missing conflicts/candidates,
unsupported action references and unsafe proposals. Valid grounded AI investigative wording is retained, including known amounts and
natural authorization quick replies. Waiting acknowledgements and evidence
invitations use bounded validated sentence shapes; canonical financial
acknowledgements are grounded in typed facts. Exact approved action explanations
still come from policy. Arbitrary generated instructions
are never authoritative user-facing content. Acknowledgements use current facts.

Decision context includes current canonical facts and verification metadata,
accepted/unresolved candidates, conflicts, recent bounded messages, known unknowns,
approved actions, case state and case-scoped evidence type/verification metadata.
It excludes evidence bytes, filenames and storage secrets. Context has a 24,000
character bound. Unresolved candidates and user-declared uncertainty survive turns.
Plain answers to an active conflict can resolve it without a magic correction word.

Moves and acknowledgements persist in existing immutable turn JSON; GET/retry do
not call AI again. No Phase 3R database migration is needed. ConversationRead adds
nullable `next_move`; `pending_question` is used for guided fallback. The existing
Phase 3 text-widening migration is still required when upgrading from Phase 2.

The workspace shows visible history, a persistent composer, optional quick replies,
approved actions and lightweight working understanding. Every typed follow-up and
AI quick reply enters the same understanding pipeline. Evidence requests link to
existing safe storage; AI screenshot extraction remains Phase 5 and is not claimed.
Homepage and Phase 4 work remain untouched. Provider failure preserves the message
and case, discloses unavailable understanding/follow-up and uses guided clarification.

## API and facts

Create with `POST /api/v1/incidents`, `{ "conversation_first": true }`. This creates
a general case without financial advice or a pending question before expression.
Older create requests retain their Phase 1/2 behavior. The optional financial
shortcut remains supported.

Send `POST /api/v1/incidents/{id}/conversation/turns` with a unique `turn_id`,
`expected_revision`, `type: "message"`, `text` and optional IANA `timezone`
(default Asia/Kolkata). Message turns cannot include field/value/action_id.
The server provides the timestamp. Retrying must reuse the exact ID and payload.
Authority, optimistic revision checks and atomic writes are unchanged.

Existing conversation responses now support generic canonical facts and message
turns. Candidate understanding/status/history lives in turn.fact_changes;
accepted explicit facts retain unverified AI provenance in current facts.
`pending_question.field` may be null for a rich-fact conflict that needs a text
clarification in fallback; there is at most one active conversational move. Structured financial replies
and corrections remain available. Preparing notes does not submit a complaint.

Accepted amounts/identifiers/organization claims/rails/currency get lexical
grounding checks. Semantic interpretation still depends on provider quality;
source grounding is not independent factual verification. Unsupported uncertain
facts remain candidates. Review/correct before relying on reporting drafts.

Common relative-time phrases resolve to approximate intervals with original
text and timezone. Unsupported phrases remain for clarification. Exact time is
not fabricated. Financial playbook 1.1.0 uses the earliest supported endpoint;
1.0.0 remains reproducible for old inputs. Generic actions reuse existing approved
preservation/official-reporting/follow-up text. No bank or 1930 action without an
established financial branch. This is not a comprehensive nonfinancial safety
playbook release.

## Manual synthetic scenarios

1. With configured Gemini, explain: “Someone claimed SBI, made me install
   AnyDesk, and I sent ₹35,000 through GPay about twenty minutes ago.” Review
   source quotes, provisional financial/device/impersonation signals, amount and
   approximate interval. Victim bank and payment rail should remain unknown;
   current remote access should be clarified. Approval should not be asked again
   when the sending statement was extracted explicitly.
2. Repeat in Telugu, Hindi, Romanized Telugu, Hinglish and mixed language. Compare
   canonical understanding and confirm detected language. Provider doubles tested
   normalization; these live-language evaluations are still outstanding.
3. Say “Sorry, ₹3,500.” Confirm current amount changes and the earlier story remains.
   Without a correction cue, a differing amount should prompt clarification.
4. Describe an account takeover/no-money scam. Confirm no financial helpline/bank
   actions appear. General preservation/reporting handoffs remain limited.
5. Remove the key or disable understanding. Confirm the story saves, the app says
   understanding is unavailable, asks one focused question and never invents an
   amount. Answer Yes to money lost to reach the existing financial fallback.
6. Refresh/retry, use a 320px viewport and keyboard, and deny cross-case access.
   Never enter actual credentials, identity documents or private citizen evidence.


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


### Actual development-runtime repair

The user's terminal confirmed psycopg2 UndefinedColumn for incidents.bank on case
creation. Configured PostgreSQL at the old urgency migration lacks 11 current
incident columns and both conversation tables. Browser fetch showed an unreachable
message because the unhandled 500 lacked CORS headers. This happens before Gemini.

Restarted the development backend with run_local.py after stopping the old Uvicorn
process and its remaining Python child (which retained the old listening socket).
The launcher backed up local.sqlite and upgraded 20261001_conversation to
20261001_understanding. Backend 8000 now uses explicit local SQLite and local
storage, retaining the configured Gemini key. Remote database untouched. Restarted
frontend 3000 after it stopped during diagnosis. Direct case creation 201 and
private conversation read 200 passed; the created case was found in local SQLite.
No Gemini calls were made during this runtime repair. Use the launcher for future
local starts; plain uvicorn without DATABASE_URL override still selects the old
configured PostgreSQL database.

The subsequent unresponsive-button report was a separate frontend bootstrap
failure: main-app.js and app-pages-internals.js returned 404, so the displayed
page never hydrated. Two Next development processes used the same .next cache
on ports 3000 and 3001. Stopped both, preserved the broken generated cache in
ignored backend/tmp, and restarted a single cold-cache server. npm run dev now
specifies port 3000 explicitly, preventing Next's automatic alternate-port start.
The real development-browser test __tests__/dev-start-interaction.cjs passed:
typing enables story submission, both buttons create a case and reach the
conversation-turn endpoint, and no JavaScript requests fail. Turns are intercepted
before AI invocation; this is a UI/runtime pass, not a live Gemini acceptance pass.
