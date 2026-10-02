# Current architecture after Phase 3R

The primary Next.js intake accepts an arbitrary story: “Tell us what happened in
your own words.” Money is gone remains an optional shortcut. New story-first cases
use GeneralIncidentFacts (`incident_understanding`) and have no financial actions
or initial questionnaire. Existing financial cases retain their Phase 2 behavior.
The homepage and response-plan layout are preserved; voice and Phase 4 are excluded.

Text -> AI candidate understanding -> application validation -> canonical facts
-> conversation controller -> deterministic playbooks -> approved actions ->
case-aware AI next move -> move validation. The provider receives the current
bounded message, server timestamp/timezone, current facts, unresolved candidates,
bounded recent conversation, evidence metadata and approved actions; no tools or
evidence bytes. Gemini uses google-genai 2.26.0, compact JSON Schema transport,
strict application contracts, a configurable model (default gemini-3.8-flash), per-stage timeout and
bounded retries. Missing key, disabled provider, exceptions, timeout, oversized or
malformed output save the story with an honest fallback and targeted clarification.
FakeProvider is an explicit test double, never an environment-selectable provider.

Candidates retain exact source quotes/spans, source turn, extraction type,
confidence, uncertainty and acceptance/review/conflict state in immutable turns.
Accepted explicit candidates retain unverified AI provenance in current facts;
inferences and uncertain candidates cannot select critical actions. Language
detection is provisional and source-linked. Lists preserve multiple signals and
identifiers. Literal identifiers/amounts/rails/currency receive additional grounding
checks. Claimed organizations never populate the victim bank; GPay alone is never
UPI. Installing a remote tool alone does not establish current access.

Relative time resolves supported English and common Telugu/Hindi/transliterated
phrases against the server timestamp/timezone into approximate intervals. Unknown
phrases remain candidates for review. Exact occurred_at stays null. Financial
playbook 1.1.0 uses the earliest interval endpoint conservatively; 1.0.0 remains
available unchanged for prior inputs. Generic 1.1.0 reuses approved preservation,
official portal and citizen follow-up actions, never bank/1930 guidance without
reported financial loss. Detailed new nonfinancial safety playbooks are deferred.
Canonical generic cases use IncidentType.other so legacy metadata/summary consumers
do not claim financial fraud. Reporting notes remain drafts requiring user review.

Conversation controller -> validated IncidentFacts -> Phase 1 playbook -> approved
actions + one validated AI next move (or no question). The controller owns case
state, correction history, explicitly answered unknowns and concurrency, never
safety action rules. Only provider fallback uses Phase 1 question priorities.
AI chooses investigation, verification, conflict resolution, evidence intent,
approved action explanation, open conversation or waiting. The application
renders safe wording; there is no fixed AI interview order. Actions exist from financial
case creation, before amount, reference or upload. An answered unknown remains
null/unknown and is skipped until the user explicitly corrects it.

GET /api/v1/incidents/{incident_id}/conversation restores facts, history, pending
question, current immutable plan and all self-reported completions. It initializes
state for an existing typed financial case when needed, suppressing established
facts. POST .../conversation/turns accepts a strict TurnRequest: turn_id (also the
idempotency key), expected_revision, type, field, value and optional action_id.
Supported types are shortcut, answer, correction, completion and message. Message
turns have text (1–8000 characters) and an IANA timezone, without field/value/action.
`conversation_first: true` on incident creation opts into the general story-first
state. Existing create requests remain compatible. New model defaults normalize
old persisted requests before idempotency comparison, preserving Phase 2 retries.

conversation_states stores schema version, revision, answered fields and pending
question. conversation_turns stores immutable user turns with role/type, server
text, original structured request, timestamp, before/after fact change and next
question. Assistant acknowledgements, next moves, unresolved candidates and safe
provider status are snapshotted in turn JSON. Reads/idempotent retries never invoke
the provider. Explicit corrections and plain answers to active conflict moves
preserve before/after history; differing statements
without a correction cue leave the existing fact intact and request clarification.
Turn UUID is the persisted request/idempotency key. Existing plan
snapshots retain the full prior facts/provenance and actions across corrections.

An atomic UPDATE WHERE revision=expected_revision claims each mutation. The turn,
new plan/facts or completion and updated state commit in one transaction. Stale
requests return 409. Same-ID identical retries return the latest durable state;
same ID with a different payload is rejected. No duplicate mutation or completion.
Completions remain plan-scoped in storage; the conversation carries forward the
latest self-report for each stable action ID, displaying only applicable actions.
Legacy fact/triage/completion writes reject conversation cases to prevent bypassing
revision checks. All operations reuse Phase 1 case authority and private no-store.

The browser uses a canonical /incident/{id}/conversation URL for reopen/bookmark,
cookie authority, a 65-second turn request timeout covering two bounded provider
stages, synchronous double-send guard and
visible retryable unsaved replies. Retry retains the exact request ID and payload.
409 reloads the current state and requires review before a new reply; it does not
replay stale facts. Unsaved drafts live in component memory and are lost on refresh;
saved history and completions restore from the database. Native controls, focus on
the next question/error, live save status and narrow layout support accessibility.

Phase 2 UX repair restores a dedicated numbered response plan. The backend's
CONTAIN phase maps to ACT NOW; REPORT joins ACT NOW only when the backend marks
that action critical. The remaining groups are PRESERVE, REPORT and FOLLOW THROUGH;
action.order controls numbering and ordering. The renderer does not inspect facts,
predict urgency or add safety instructions. Non-immediate actions remain under
their existing phases (PRESERVE, REPORT, FOLLOW THROUGH), with recorded
priority, approved explanation and official source accessible in disclosures.
No API, domain rule or schema migration was needed; TypeScript ActionItem now
includes the critical property already present in the backend ResponseAction.

Desktop places visible conversation history and a persistent composer beside the
existing sticky response plan. Mobile shows ACT NOW first with sticky actions/
conversation shortcuts. Guided question controls appear only for fallback or
optional corrections. AI quick replies are natural message turns. Green completion
styling belongs to completed actions. Empty groups
are omitted and UNDERSTAND stays in the conversation. Only returned applicable
actions are rendered, including completed actions. The current financial playbook
returns all four groups from its initial plan; the UI does not hide approved steps
to simulate later applicability. New immediate action IDs are announced in a polite live region.
Mark done is an accessible pressed button that saves the existing completion turn,
keeps keyboard focus and still means only user self-report. Input text resets when
the active field changes, including stale-state reloads, to prevent carrying a
previous question's answer into the next one. Phase 3 extends this controller.

Validated IncidentFacts (Pydantic discriminated union) -> version-keyed
ResponsePlaybook -> immutable ResponsePlan -> ordered ResponseActions.
GeneralIncidentFacts, FinancialScamTransferFacts, UnauthorizedFinancialTransactionFacts and explicit
unknown authorization keep missing amount/time/booleans null. Unverified critical
inferences require review. Typed provenance can reference only evidence in the
owning case. Critical decisions live in app/domain/playbooks.py with no AI/network
imports. The conversation controller consumes the playbook's question priorities.

Incident remains the canonical ORM; additive columns retain current playbook ID,
version, fact schema, facts and revision. response_plans stores immutable full
fact/action/source snapshots; reads never recalculate history with current rules.
action_completions refers to a plan/action and contains only user self-report,
notes and user-recorded references. It cannot represent official progress.

One OfficialSource registry in app/domain/sources.py owns financial official URLs,
review dates and narrow supported claims. Plans snapshot the sources they use.
Legacy nonfinancial rules remain limited existing behavior, now protected by case
access. Deprecated financial wrappers delegate to the canonical engine.

Private router dependencies resolve ownership before every operation. Creation
issues a 256-bit random capability; only SHA-256 and server expiry are stored.
Constant-time verification accepts a per-case HttpOnly/SameSite Strict cookie or
X-Case-Secret header; no URL token. Secure defaults on. Private writes reject
unapproved Origin values. Missing/wrong/expired/absent resources share 404. Original
files pass through the authenticated backend even with optional cloud storage;
private responses use no-store. UUID knowledge alone conveys no access.

Alembic head 20261001_understanding expands turn text to TEXT and preserves Phase 2
rows; bounded input is enforced at the API. Candidate/current-fact data uses existing
JSON snapshots, so no extra tables are needed. Downgrade deliberately retains TEXT
to avoid truncating saved stories. 20261001_conversation added state/turn tables.
Old cases have no fabricated facts/history and no assigned ownership capability;
legacy_unversioned cases remain locked pending owner-verified administrative
recovery, which is deferred. No startup DDL or destructive legacy rewrite.

Evidence policy maps playbook IDs to declared content restrictions: credentials,
explicit intimate media, CSAM and unnecessary identity documents are prohibited.
Recognizable labelled credentials are rejected before text/metadata persistence.
Semantic image moderation and complete sensitive-data detection are NOT implemented.
Existing heuristic/optional extraction and manual correction remain; no Phase 5.

Tests use migrated temporary SQLite and temporary evidence. Full golden scenario,
OpenAPI/frontend contract, migration, private-resource and browser checks are in
verification.md. PostgreSQL, live storage and human manual verification remain
unrun. Gemini live extraction succeeded, but full live next-move acceptance remains
blocked by provider high-demand errors. Voice and broader playbooks remain deferred.
Retention/account recovery readiness for real citizen data is not established.
Existing retention/account recovery limitations still restrict use to
synthetic data; capability expiry is an access limit, not automatic data deletion.

## Structure cleanup

incident_service.py now orchestrates persistence/triage and current financial
plans. Complaint formatting is in incident_presentation.py; old nonfinancial
responses are in legacy_incident_service.py. Summary/evidence consumers import
formatting directly; existing service helper import contracts remain available.
components/conversation.tsx renders the new primary interface, with shared typed
contracts in types/conversation.ts. The earlier wizard components/controller remain
unused compatibility source; there is no mandatory wizard on the primary path.


## Phase 3R repair (2026-10-02)

The existing next-move contract/controller remains canonical. Investigative
questions retain validated provider wording; validation checks actual requested
unknowns, grounded amounts/currency/identifiers and retrospective intent rather
than rejecting every digit. Natural authorization quick replies are supported.
Waiting/evidence prose has bounded sentence validation to prevent safe prefixes
from smuggling advice, identity-document requests or fabricated official status.
Approved-action explanations always use exact deterministic policy text.

One latest assistant interaction contains fallback question and optional controls;
there is no duplicate question card. The composer remains permanent. Canonical
acknowledgements keep the amount even when currency is unknown and do not assert
an account source. Accepted AI canonical acknowledgements are retained once.

Diagnostics distinguish provider unavailable/5xx, timeout, malformed output,
validation rejection and application errors. Next-move diagnostics identify
invocation, parsing, validation, proposed type and bounded rejection code. Raw
provider output, exception text, credentials and private reasoning are not logged.
Settings anchor backend/.env; OS overrides retain precedence. The local launcher
backs up and migrates explicit local SQLite and uses local evidence storage.
Live acceptance remains pending; see phase3-understanding.md and verification.md.
