# Phase 6 core reporting implementation

**Historical delivery report, superseded by [final acceptance](phase6-final-acceptance.md).**
The repair gate now passes and six independently live narrative drafts succeed
without quota fallback. The earlier open repair and five-of-six live results below
are preserved as historical evidence, not the current completion status.

Implemented 2026-10-10; final verification resumed 2026-10-11. The user explicitly
authorized core implementation after the open conversation repair checkpoint was
reported. **Core reporting is implemented; three previously documented live
conversation failures remain open.** This report does not relabel that repair as
accepted. See [repair checkpoint](phase6-conversation-repair.md).

## Citizen experience

From the existing conversation, **Prepare report** opens an intentional reporting
artifact. The citizen reviews existing facts, corrects them through the permanent
composer, prepares a narrative, then separately approves the complete packet.
Reviewed fields/individual identifiers and narrative can be copied; reviewed PDF,
JSON and an inert print view are available. The verified official destination
opens externally. CyberSOS does not submit, collect portal OTPs, or claim an
official acknowledgement. Chat drafts, mobile composer access and reload persist.

## Gap, decision and boundaries

The previous summary generator read legacy incident columns and a description;
populated values did not establish review or canonical provenance. It could not
safely become the Phase 6 complaint packet. Reporting now consumes suitable
canonical facts after existing case review, with a separate reporting approval.
Conversation cases cannot bypass this boundary through `generate-summary`; old
non-conversation summaries remain legacy functionality and are not packet inputs.

| Input | Reporting treatment |
| --- | --- |
| Current explicit conversation/correction facts | Eligible after citizen fact review; latest provenance retained |
| Citizen-verified evidence facts | Eligible canonical values; source references retained |
| Inferred facts | Eligible only when verified |
| Legacy columns/provenance, raw description/summary | Excluded; never silently promoted |
| OCR/extraction candidates, unresolved conflicts | Candidates excluded; conflicts block preparation |
| Case memory/RAG/source guidance | Never narrative incident facts; official guidance is separate |
| Evidence originals | Private inventory only; listing does not verify contents |
| Citizen action completions/references | Latest state per action, explicitly self-reported; no external status |

Identifiers are filtered per value rather than by one field-level provenance entry.
Original identifiers retain underscores and other supported meaning. Portal
restricted symbols are named explicitly in a separate transfer copy; the original
narrative and facts remain available. Short narratives are never padded with
invented details to meet the portal's published minimum.

## Layer changes

- Frontend: reporting panel inside the existing chat artifact hierarchy; separate
  fact/packet review, exact identifier copy, server-validated copy/download,
  accessible feedback and recovery. Another-tab correction prevents stale copy.
  Changed revision resets stale fact-review retry keys; recoverable retries keep
  the same key. Composer/drafts remain usable with the artifact open.
- Backend/domain/AI: typed `ReviewedCasePacket`, explicit reporting predicates,
  versioned portal mapping, `HandoffProvider` boundary and packet-only narrative
  drafting. AI chooses coherent order and supported fact-linked sentence wording;
  validation requires each eligible fact exactly once. This intentionally bounds
  wording rather than accepting unrestricted prose. Timeout/quota/malformed or
  unsupported output produces a truthful local draft from the same facts.
- Database/storage: additive `reporting_snapshots` table, migration
  `20261010_reporting`; immutable packet/narrative snapshots with separate review
  timestamp. Canonical state remains authoritative. Snapshots are case-owned and
  cascade with case deletion; no new public file store. Existing retention and
  secure-return limitations remain, so synthetic data only.
- API: owned `GET /incidents/{id}/reporting`, `POST /reporting/drafts`,
  `POST /reporting/drafts/{draft_id}/review`, and
  `GET /reporting/drafts/{draft_id}/export?format=json|pdf|html`, under `/api/v1`.
  Retry UUID, case revision and source digest bind preparation/review/export.
  Corrections, evidence inventory or recorded-action changes invalidate old packets.
- Security/privacy: ownership applies to previews and all exports; approved
  freshness is checked by the backend before copy/download. Exports exclude private
  storage paths, raw candidates, model metadata and internal failure diagnostics.
  HTML/PDF render untrusted text as data, without fetching URLs or embedding active
  links. Private exports use no-store/nosniff and restrictive print-view CSP.

## Sources and declared coverage

Jurisdiction: India. Reporting interface/narrative templates: English. Declared
initial fixtures cover financial scam payments, harassment/private-image threats,
and account takeover through all three optional entry hints, plus overlap and a
wrong hint. Hints do not establish facts or special portal eligibility.

Mapping `ncrp-2026-10-10.1` cites the verified public
[official login/checklist](https://cybercrime.gov.in/Webform/Crime_AuthoLogin.aspx)
and [official 2019 manual](https://cybercrime.gov.in/UploadMedia/MHA-CitizenManualReportOtherCyberCrime-v10.pdf).
The public checklist supplies the narrative minimum, symbol restriction and general
evidence limit. Authenticated route-specific fields, maximum narrative lengths and
women/children special-content eligibility remain unverified. The older manual's
attachment limit differs from the public checklist; the applicable live form must
be checked. Unknown maximum lengths/types remain unknown in the mapping.

Identity, registration and OTP stay on the official portal. Bank/wallet/merchant
names not supported in the current canonical packet must also be entered there;
a caller's claimed bank never establishes the citizen's bank. General harassment
does not prove eligibility for the special women/children content branch. A reviewed
packet means prepared information is ready to transfer, not a complete or accepted
official complaint. Uploading CyberSOS PDF does not fill or replace the portal form.

## Verification

Backend CWD: `backend`; frontend CWD: `frontend`. Stable runtime dotenv:
`backend/.env`. Configured development DB: PostgreSQL, existing Supabase pooler
`aws-0-ap-northeast-2.pooler.supabase.com:5432/postgres`; no credentials printed.
Migration applied to that DB. Normal frontend API target remains localhost:8000;
disposable acceptance build uses backend 8001/frontend 3001. Normal backend 8000
was not running during inspection; running user services were not replaced.

| Exact command / check | Result and evidence |
| --- | --- |
| `../.venv/Scripts/python.exe -m pytest -q --tb=line --show-capture=no` | **543 passed in 73.12s**; `tmp/phase6-core-backend-final.log` |
| `../.venv/Scripts/python.exe -m pytest tests/test_phase6_reporting.py -q --tb=line --show-capture=no` | 17 passed: review separation, stale/owned export, actual PDF contents, packet-only failures, provenance, current action state, wrong hint/overlap/conflict and legacy summary bypass |
| `node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs` | 13 passed |
| `NEXT_PUBLIC_API_URL=http://localhost:8001`, `CYBERSOS_BUILD_DIR=.next-phase6-final`, `npm run build` | Production compilation, lint/types and static pages passed; `tmp/phase6-core-build-final.log` |
| `../.venv/Scripts/python.exe -m alembic upgrade head` | Configured PostgreSQL upgraded from evidence intelligence to `20261010_reporting`; fresh/legacy migration preservation and metadata tests also passed |
| `../.venv/Scripts/python.exe -m tests.phase6_reporting_configured` | Configured PostgreSQL packet approval, replay/readback/PDF, correction/stale export and cross-case denial passed with fake AI; `tmp/phase6-reporting-configured.log` |
| `../.venv/Scripts/python.exe -m tests.smoke_local`, reporting browser journey | Three-route desktop/mobile, exact clipboard/PDF, revision recovery, remote stale copy, reload, composer and ownership; final logs `tmp/phase6-reporting-mobile-final.log`, `tmp/phase6-reporting-desktop-final.log` |
| Same harness, `__tests__/phase5-journey.cjs` | Hybrid/evidence partial/conflict/natural review, canonical memory/plan, mobile resume/deletion passed with fake AI; `tmp/phase6-core-phase5-final.log` |
| Same harness, `__tests__/phase4-journey.cjs` | Direct chat/retry/correction, private attachments and mobile artifacts passed with fake AI; `tmp/phase6-core-phase4-final.log` |
| Actual exported live PDFs parsed with `pypdf.PdfReader` | Three PDFs valid; citizen account/transfer copy, independent draft label and private-path exclusion confirmed; no active PDF annotations |
| `git diff --check` | Passed; only Git line-ending warnings |

Browser harness environment:

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
$env:CYBERSOS_BUILD_DIR='.next-phase6-final'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
$env:SMOKE_JOURNEY='__tests__/phase6-reporting.cjs'
$env:SMOKE_ASGI_APP='tests.phase6_reporting_smoke_app:app'
$env:SMOKE_LIVE_AI='0'
# SMOKE_REPORT_DESKTOP=1 selects desktop; default is mobile.
../.venv/Scripts/python.exe -m tests.smoke_local
```

One initial browser navigation failed with Chromium `ERR_NETWORK_CHANGED` before
the citizen journey; the identical retry passed. Windows sandbox temporary SQLite
and Next workers required approved test escalation. No approval rejection occurred.
`reportlab==5.0.1` renders PDFs; `pypdf==6.19.0` is a dev-only inspection dependency
in `requirements-dev.txt`. PDF needs a supported system font; unsupported glyphs
return a clear error with Unicode JSON/browser-print alternatives, never silent loss.
The individual-identifier clipboard test initially read before the asynchronous
write completed; it now waits for the actual copy-success feedback. Final mobile
and desktop runs passed. Backend route/table inventories and the historical summary
test were updated to cover the new owned routes, snapshot table and review boundary.

## Provider evidence and limitations

Configured provider stayed Gemini `gemini-3.5-flash-lite`. Synthetic live reporting
used the same browser journey with `SMOKE_LIVE_AI=1` and
`SMOKE_ASGI_APP=tests.phase6_live_app:app`. The complete three-route journey passed
its reporting/review/correction/export assertions. **Five draft calls were validated
live Gemini output; the sixth received quota 429 and safely produced a local
fallback.** Successful drafting durations were 1,857 / 2,175 / 2,199 / 1,744 / 1,499ms;
these are drafting-stage measurements, not time-to-first-action. Log:
`tmp/phase6-reporting-live.log`. No further live calls or paid/model fallback followed
the quota event. Mock and configured-PG tests are distinct from that live evidence.

Account limits/billing console were not enumerated; no cost/token measurement or
universal model/language claim. Narrative wording is bounded by supported claims.
Human-style inspection covered the browser artifact and parsed PDF output; this is
not a human-operated citizen beta. Three conversation repair failures remain open.
Authenticated portal field coverage and unrestricted multilingual PDF rendering
are not certified. No real citizen data, commit, push, deployment or Phase 7 work.

## Manual journey and roadmap

Install backend/dev requirements as needed, run `alembic upgrade head` from backend,
then start the backend/frontend with the existing README commands. Use synthetic
data: Tell us what happened -> optional hint -> report a supported incident ->
Prepare report -> review facts -> inspect citizen account/unknowns/evidence ->
approve packet -> copy a field/narrative -> download PDF/JSON or print -> open the
official destination. Correct the platform/amount in chat and verify old copy/export
is refused until a new packet is prepared and reviewed. Do not enter a real OTP or
identity document in CyberSOS. Live AI availability depends on the configured quota.

Roadmap: **NO CHANGE required**. Later phases must reuse the reviewed packet and
its revision/digest approval rather than legacy summaries or understanding review.
**OPTIONAL IMPROVEMENT:** expand verified authenticated route fields, supported bank
identity representation and calibrated narrative wording after obtaining evidence;
the provider/mapping boundaries remain replaceable. These recommendations do not
change a core invariant.

Core check: chat-first, no form-first intake, AI-led investigation, deterministic
critical actions, self-building canonical case, truthful external status and future
authorized official-handoff compatibility are preserved.
