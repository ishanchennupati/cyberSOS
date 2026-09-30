# Current architecture after Phase 1

The existing Next.js guided financial UI calls FastAPI through lib/api.ts with
credentials included. No conversational UI or new provider integration was added.

Validated IncidentFacts (Pydantic discriminated union) -> version-keyed
ResponsePlaybook -> immutable ResponsePlan -> ordered ResponseActions.
FinancialScamTransferFacts, UnauthorizedFinancialTransactionFacts and explicit
unknown authorization keep missing amount/time/booleans null. Unverified critical
inferences require review. Typed provenance can reference only evidence in the
owning case. Critical decisions live in app/domain/playbooks.py with no AI/network
imports. Fact priorities expose a future next-question seam, not a controller.

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

Alembic head 20261001_response_foundation is additive and preserves Phase 0 data.
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
Phase 2 conversation/AI/voice and broader playbooks have not begun.

## Structure cleanup

incident_service.py now orchestrates persistence/triage and current financial
plans. Complaint formatting is in incident_presentation.py; old nonfinancial
responses are in legacy_incident_service.py. Summary/evidence consumers import
formatting directly; existing service helper import contracts remain available.
The Next.js intake page renders UI; features/incident-intake/use-incident-flow.ts
owns existing guided state, validation, session persistence and API orchestration.
Identical date-change handlers are shared. No new conversation controller/UI.
