# Current architecture after Phase 2

The primary Next.js intake is a structured text conversation: “Tell us what
happened.” The supported shortcut is “Money is gone”; other categories are clearly
unsupported. No arbitrary narrative interpretation, live AI, Gemini or voice was
added. The financial draft and optional evidence views remain reachable.

Conversation controller -> validated IncidentFacts -> Phase 1 playbook -> approved
actions + one next question. The controller owns progression, correction history,
explicitly answered unknowns and concurrency, never safety action rules. Question
order comes from the Phase 1 playbook requirements. Actions exist from financial
case creation, before amount, reference or upload. An answered unknown remains
null/unknown and is skipped until the user explicitly corrects it.

GET /api/v1/incidents/{incident_id}/conversation restores facts, history, pending
question, current immutable plan and all self-reported completions. It initializes
state for an existing typed financial case when needed, suppressing established
facts. POST .../conversation/turns accepts a strict TurnRequest: turn_id (also the
idempotency key), expected_revision, type, field, value and optional action_id.
Supported types are shortcut, answer, correction and completion. Text inputs are
limited to the current structured field; arbitrary narrative is not interpreted.

conversation_states stores schema version, revision, answered fields and pending
question. conversation_turns stores immutable user turns with role/type, server
text, original structured request, timestamp, before/after fact change and next
question. Assistant question text is snapshotted in each turn, rather than calling
a provider. Turn UUID is the persisted request/idempotency key. Existing plan
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
cookie authority, a 15-second request timeout, synchronous double-send guard and
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

Desktop places the current question beside a sticky, independently scrollable
response plan. Mobile shows ACT NOW first with sticky actions/question shortcuts;
lower phases and saved history are expandable. The active question is a distinct
neutral card; green completion styling belongs to completed actions. Empty groups
are omitted and UNDERSTAND stays in the conversation. Only returned applicable
actions are rendered, including completed actions. The current financial playbook
returns all four groups from its initial plan; the UI does not hide approved steps
to simulate later applicability. New immediate action IDs are announced in a polite live region.
Mark done is an accessible pressed button that saves the existing completion turn,
keeps keyboard focus and still means only user self-report. Input text resets when
the active field changes, including stale-state reloads, to prevent carrying a
previous question's answer into the next one. No controller rollback or AI added.

Validated IncidentFacts (Pydantic discriminated union) -> version-keyed
ResponsePlaybook -> immutable ResponsePlan -> ordered ResponseActions.
FinancialScamTransferFacts, UnauthorizedFinancialTransactionFacts and explicit
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

Alembic head 20261001_conversation adds two tables and preserves Phase 1 data.
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
verification.md. PostgreSQL, live providers and human manual verification remain
unrun. Retention/account recovery readiness for real citizen data is not established.
Live understanding, voice and broader playbooks remain deferred. Phase 3 has not
begun. Existing retention/account recovery limitations still restrict use to
synthetic data; capability expiry is an access limit, not automatic data deletion.

## Structure cleanup

incident_service.py now orchestrates persistence/triage and current financial
plans. Complaint formatting is in incident_presentation.py; old nonfinancial
responses are in legacy_incident_service.py. Summary/evidence consumers import
formatting directly; existing service helper import contracts remain available.
components/conversation.tsx renders the new primary interface, with shared typed
contracts in types/conversation.ts. The earlier wizard components/controller remain
unused compatibility source; there is no mandatory wizard on the primary path.
