# Phase 7 implementation and acceptance

Implemented and verified 2026-10-16 against all sections of `phases/phase-07.md`.
Scope is local synthetic testing. Live Resend delivery remains unverified pending
private local credentials. Strict live resumed-conversation acceptance is partial
because Gemini returned repeated HTTP 503; this is not full production acceptance.

## Citizen experience and architecture

Guest chat starts immediately. A validated AI readiness proposal presents the
personalized deterministic plan and draft case sheet inline without asking the
citizen to conclude or approve it. Fact review and Phase 6 packet approval remain
separate. New information refreshes the existing canonical projection. Routine
post-outcome questions require a material reason and a brief purpose explanation.

Evidence-offer consent is durable interaction state, not evidence existence.
An active Yes opens the practical attachment/description affordance once. Completion
updates do not replay previous questions. Notes/references use revision-controlled
conversation turns; explicit completion mentions offer citizen confirmation rather
than setting externally verified completion.

View case expands the same projection: relevant source-linked facts/uncertainty,
safe evidence metadata, citizen records, timeline and existing reviewed reporting
packet. The persistent composer and draft remain accessible beside/on return from
the companion. Homepage and chat expose an intentional secure-return surface.

## Secure return

Optional safe-email identity uses a replaceable Resend adapter. Only a citizen
with existing case authority AND a freshly verified account can link a guest case.
Signing in never automatically claims cases. Saved-case history is account scoped.
No new identity provider framework or parallel case system was introduced.

Email challenges last 15 minutes, are browser-bound and consumed only on explicit
POST confirmation. Links carry the secret in a fragment; the return page removes
it from browser history before confirmation. Email requests use generic responses,
database-backed IP/address/global limits and no paid fallback. Failed delivery
does not establish a session. Sessions expire after seven days by default.

Case recovery codes are high-entropy capabilities, hashed in the database and
shown once. Recovery rotates the code and guest credential atomically. A code
opens only its case, not the account's other cases, and cannot change email.
Cross-device return supports fresh email verification on the destination browser
or case-reference-plus-code recovery. An email link must be confirmed in its
requesting browser. Lost sessions plus lost recovery methods cannot be bypassed
using a UUID or bookmark. Citizens must save each replacement recovery code.

Resend is not configured in the local environment yet. Real delivery requires:

```dotenv
EMAIL_PROVIDER=resend
RESEND_API_KEY=<set privately in backend/.env>
RESEND_TEST_RECIPIENT=<your Resend account email>
RESEND_FROM_EMAIL=CyberSOS <onboarding@resend.dev>
RESEND_VERIFIED_DOMAIN=false
PUBLIC_APP_URL=http://localhost:3000
```

No domain purchase is required for that self-inbox test. Other recipient delivery
requires a verified sending domain; do not enable it by setting a flag alone.
Configure tracking off for authentication email before using a verified domain.
Provider dashboards/billing/account availability have not been inspected.

Sources checked: [Resend pricing](https://resend.com/pricing),
[testing sender restrictions](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain),
[OWASP recovery](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html).
Email contains only authentication information, never incident/evidence contents.

## Persistence, contracts and deletion

Migration `20261015_companion` adds optional accounts, hashed sessions/challenges,
case ownership, hashed recovery, shared throttles, deletion jobs and case lifecycle
columns. Existing cases receive 90 days from migration; existing valid authority,
facts, evidence, memory and reporting records are preserved. Configured PostgreSQL
has been migrated through `20261016_file_cleanup`, which adds independent
retryable orphan-file cleanup after failed upload/metadata persistence.

The existing `ConversationRead.projection` now includes companion presentation,
records, evidence metadata, timeline and expiry. `NextMove` adds bounded readiness,
evidence-offer and material-follow-up metadata. `TurnRequest` adds `case_update`
for notes/references; AI record candidates require a current-message source quote.
Existing reporting approval/digest and deterministic action contracts are reused.
The Gemini-native transport separates common response fields from a small typed
interaction union, avoiding schema-complexity errors observed in real provider
calls. The adapter validates and flattens this envelope into the unchanged public
NextMove contract; provider success never bypasses application safety checks.
Auth routes cover email request/confirmation, session, saved cases, logout,
session revocation and case-code recovery. Owned incident routes add save,
recovery-code generation, explicit resume and deletion. Reads and explicit resume
do not invoke any AI provider. Signed-in citizens can reverify without signing
out or losing guest authority; verification freshness is visible in the UI.

Synthetic retention: 90 days of inactivity, extended by conversation updates,
uploads, explicit resume, linking and reporting mutations. Ordinary GET reads,
listing and background analysis do not extend expiry. Expired/deleting cases are
denied before cleanup runs. The running application performs cleanup hourly.
When the app is offline, physical cleanup waits until it runs again. For manual
cleanup and before serving a restored backup:

```powershell
# Run from backend for manual/restore cleanup.
../.venv/Scripts/python.exe -m app.services.lifecycle
```

Deletion first persists revocation and a private original-file manifest, then
removes storage and cascades through transcript, plans/completions, candidates,
reviews, evidence, identifiers, timeline and reporting snapshots. Storage failure
returns access-revoked/cleanup-pending and retains a retry job. No persistent
private search index/cache exists. Derived memory is case-only and rebuilt from
remaining canonical state. Deleting the last owned case keeps an active account
session usable for another case. After its sessions expire, cleanup removes an
identity with no remaining owned cases. Client case drafts are cleared after
deletion. Browser drafts are session storage, not cross-device canonical memory.

`CASE_DELETION_JOURNAL` is a separate private append-only list of deleted UUIDs.
Keep it durable and outside DB restore replacement. Availability checks consult it;
a recorded deleted case is denied even if its old database row reappears. A missing
journal is valid only for a fresh installation; operators must restore it for a
recovered installation. A corrupt/unreadable journal fails closed.

Before serving a restored backup: preserve/reconcile the journal, rotate
`AUTH_EPOCH` outside the database, run the lifecycle command to remove restored
deleted cases, and verify denial with old credentials. Old sessions/challenges/
codes/guest secrets become invalid after epoch rotation; linked owners require
fresh email verification. Guest-only access cannot be recovered using revoked codes.
This is an operator restore procedure, not a managed backup service.

Application deletion cannot erase downloaded packets, independently retained
database/storage backups, or provider/email logs. No production retention policy,
backup deletion automation or public-data handling approval is implied.

## Verification record

- Initial runtime audit: configured PostgreSQL at `20261010_reporting`, stable
  backend `.env` loading, Gemini `gemini-3.5-flash-lite`; no model/billing changes.
- Targeted migrated SQLite suites: owner-gate coverage, new API mounting,
  schema compatibility, readiness, evidence consent, notes, expiry, isolation,
  revocation, concurrent code redemption, deletion during provider execution,
  storage failure/retry and journal restore denial.
- PostgreSQL round trip passed using fake AI/captured test email: autonomous
  presentation, separate fact/packet review, PDF, explicit email link, expiry,
  cross-browser code recovery, identical facts/history/memory, reference update,
  deletion and denied packet access. Script deletes its synthetic case.
- Browser mobile/desktop passed across all three hints: consent, readiness,
  separate approval, preserved composer draft, reference, test email verification,
  explicit linking, expiry, cross-device recovery, rotated code and deletion.
- Production build and all 13 frontend contract tests passed. Full backend:
  619 passed. The new suites cover readiness without classification/approval gates,
  consent, source-grounded record organizations, explicit resume, re-verification,
  periodic cleanup, orphan-file retry and account continuity after last-case deletion.
- Existing Phase 5 mobile evidence/conflict/natural-review journey and Phase 6
  three-route reporting/copy/PDF/correction/stale-export/isolation browser journeys
  pass against the production build with explicitly fake AI.
- Live Gemini `gemini-3.5-flash-lite`: all three synthetic routes reached autonomous
  companion presentation without citizen approval, then expired/recovered with
  identical canonical facts, transcript and derived memory. Known details were not
  requested again after presentation. The stricter fresh-reply-after-recovery run
  passed for Women/Children (a useful validated answer in 18.7 seconds), then failed
  Financial Fraud acceptance because both provider attempts returned high-demand
  HTTP 503. State remained intact and the safe fallback appeared. The script
  stopped at that assertion, so Other fresh resumed reply was not run. These are
  explicit live acceptance limits, not three-route live quality passes.
  The earlier three-route run accepted 6 of 9 follow-ups; 3 proposals were rejected
  (repeated recap, unsupported account ownership, ungrounded identifier) and safely
  replaced. These fallbacks limit conversational polish; HTTP 200 is not counted
  as validated AI. Provider 503 retries also occurred. No latency/cost target or
  universal language/model suitability claim is made.
- Partial independent review raised stale-verification UX and orphan-file cleanup;
  both were reproduced and fixed. The reviewer hit its usage limit before completing
  the full review. Additional self-review checked authorizers, cookie/challenge
  handling, recovery/deletion lock order and restore boundaries; this is not an
  independent security audit. `git diff --check` passes (Windows line-ending
  conversion warnings only).

Commands, from backend unless otherwise stated:

```powershell
../.venv/Scripts/python.exe -m tests.runtime_audit
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe -m tests.phase7_configured
../.venv/Scripts/python.exe -m pytest -q --tb=short --show-capture=no
$env:PHASE7_LIVE='1'
../.venv/Scripts/python.exe -m tests.phase7_live
```

Artifacts are local ignored `tmp/phase7-{backend-final,build-final,browser-final,
configured-final,frontend-contracts,reporting-regression,evidence-regression}.log`,
plus `tmp/phase7-live-final.log` (completed three-route presentation/recovery),
`tmp/phase7-live-resumed.log` (strict resumed-turn failure) and the synthetic
`tmp/phase7-live.json` (completed routes from the latest run only). Only the opt-in live script calls Gemini; browser/configured
DB tests use fake AI and captured mail. No live Resend delivery was run.

Browser environment: `CYBERSOS_BUILD_DIR=.next-phase7`, backend port 8001,
frontend port 3001, `SMOKE_ASGI_APP=tests.phase7_smoke_app:app`,
`SMOKE_JOURNEY=__tests__/phase7-companion.cjs`, and the existing local
`PLAYWRIGHT_PACKAGE` driver. Run `python -m tests.smoke_local` using the venv.
From frontend: `node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs`
and `npm run build` with `NEXT_PUBLIC_API_URL=http://localhost:8001`.
Existing browser regressions ran from backend with the same driver/ports/build:

```powershell
$env:SMOKE_ASGI_APP='tests.phase5_smoke_app:app'
$env:SMOKE_JOURNEY='__tests__/phase5-journey.cjs'
../.venv/Scripts/python.exe -m tests.smoke_local
$env:SMOKE_ASGI_APP='tests.phase6_reporting_smoke_app:app'
$env:SMOKE_JOURNEY='__tests__/phase6-reporting.cjs'
../.venv/Scripts/python.exe -m tests.smoke_local
```

## Manual journey, boundaries and roadmap

With synthetic data: Tell us what happened → choose an optional hint or type →
describe the incident → useful questions/early urgent help → automatic inline
plan and draft case sheet → correct a fact or add a record → View case → save a
recovery code or verify a safe email and explicitly save the case → return via
Your cases or the recovery page → continue the same chat → delete the case.

India and the initial Phase 5 incident matrix remain the support boundary.
English is the main Phase 7 acceptance language; existing bounded Telugu/Hinglish
regressions are retained, not universal language certification. Voice is Phase 9.
No Phase 8 coverage expansion, deployment, commit, push or paid service provisioning.

Roadmap: REQUIRED CHANGE for later operational prompts to preserve lifecycle
cleanup and preserve the deletion journal/rotate AUTH_EPOCH on restore. Later
phases must reuse account/case ownership and the same reviewed reporting packet.
No core invariant changes: chat-first, no form-first intake, AI investigation,
deterministic critical actions, self-building case, truthful external status and
future authorized official-handoff compatibility all remain required.


## Phase contract coverage

| Phase 7 section | Implemented path and evidence |
| --- | --- |
| October 11 conversation-to-companion enhancement | Validated readiness ? inline deterministic plan and draft case sheet; automatic presentation remains separate from fact/packet approval; three-hint mobile/desktop and live tests. |
| October 12 conversation repairs | Early justified urgent help preserved; material-only post-outcome questions; durable evidence offer/Yes/decline state; completion no longer replays a question. |
| Required implementation | Existing projection expanded with records, metadata, timeline and packet; optional owned secure return; persisted facts/history/memory; existing separate-incident controls; retention/deletion/restore procedure. |
| UI requirements | Intentional View case, inline living artifacts, persistent composer/draft, re-verification and replacement-code recovery, neutral expiration/deletion states; viewport checks on mobile/desktop. |
| Verification and acceptance | Owned API/unit/migration/race/failure tests, actual PostgreSQL round trip, six browser companion journeys, earlier evidence/reporting regressions and live synthetic conversation/return. Resend delivery remains pending. |

Root gaps were the old review-before-plan presentation gate, replayed interaction
state after completion, and absence of durable identity/recovery/lifecycle. The
solution extends existing typed contracts and canonical state rather than adding a
second case system. UI changes are the inline CaseSheet/companion and SecureReturn;
backend changes are readiness/consent validation, record provenance, shared ownership
and lifecycle services. The two migrations and API additions are described above.
Security boundaries remain case-scoped: no UUID authority, cross-case retrieval,
unchecked model instructions or invented official status. Critical actions and
Phase 6 review/export rules remain authoritative.


Remaining acceptance work: once local Resend credentials are available, enable the
configured adapter and verify one real self-inbox sign-in/reverification round
trip. When Gemini demand permits, rerun the strict live resumed-conversation script
through all three routes; its current failure is preserved rather than counted as
a success. No silent paid fallback or model change was introduced. The locally
implemented scope is complete; these external-provider checks remain outstanding.
