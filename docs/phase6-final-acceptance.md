# Phase 6 final acceptance — 2026-10-11

The subsequent [manual-test repair](phase6-manual-repair.md) records the reported
recap/question/composer defects, their fixes and newer verification. Counts and
live results in this report describe the earlier core acceptance checkpoint.

**Complete for the declared initial scenarios. The conversation repair gate now
passes, and core reporting is implemented and verified.** This supersedes the open
acceptance status in the historical [repair checkpoint](phase6-conversation-repair.md)
and the earlier [core delivery report](phase6-core-reporting.md). Historical failed
runs remain evidence; they have not been relabeled as successes.

## Citizen experience and scope

The citizen can describe an incident in chat, receive applicable reviewed help,
skip questions, request a summary or pause, correct facts and reload the case.
Prepared reporting material uses reviewed canonical information, with a separate
packet approval before field/identifier/narrative copy, private PDF/JSON or print.
Corrections invalidate earlier reporting approval and exports. The composer and
its draft remain available while reporting is open on mobile and desktop.

Declared acceptance covers English text in India, with synthetic Instagram/Facebook
harassment or private-image threats, deceptive UPI payments and Google/Microsoft
account-access/impersonation stories across all three optional entry hints. These
hints are nonexclusive and do not prove official category eligibility. This is not
universal crime, language, emergency or authenticated-form coverage. No Phase 7
implementation, commit, push, deployment, model switch or paid fallback occurred.

## Gap, decision and implementation

The repair gap was semantic: capability/purpose statements and citizen payment
permission were confused with instructions or external approval; generic story and
timing aliases could evade question deferral; the response controller overwrote
equivalent-topic suppression assembled by the agent context. Flat outcome matching
also rejected an explicit denial of guarantees. Live inspection exposed these
problems even when infrastructure and schema tests passed.

The fixes retain the existing AI investigation, canonical mutation and deterministic
action boundaries. Native generation branches target applicable unknowns. Exact,
approximate and textual incident timing share question suppression; the controller
preserves it. An adequate story cannot restart through another move type. A safe
answer can retain its grounded body while an unnecessary follow-up and its buttons
are omitted, after the entire proposal passes safety/grounding checks. Positive
outcome predictions, actual procedural instructions, secrets and fabricated status
remain rejected. Unreported financial loss stays unknown.

Frontend changes reuse the intentional chat reporting artifact, with accessible
copy feedback and current-export checks before clipboard writes. The requirements
panel now distinguishes the public anonymous form from registered routes and links
the checklist, FAQ, anonymous form and historical manual accurately. Expanded
requirements preserve composer access. Initial and corrected PDFs were downloaded
and inspected; another-tab corrections cannot copy or export a stale packet.

Backend/domain/AI changes include the typed `ReviewedCasePacket`, packet-only
grounded narrative provider, reporting predicates, revision/digest validation and
`HandoffProvider`. The immutable, owned `reporting_snapshots` table is provided by
migration `20261010_reporting`. No extra database columns were needed for the final
conversation repair: control/disposition information remains in existing turns.
Configured development PostgreSQL is at that migration head; persistence, replay,
review, PDF, correction invalidation and ownership passed with synthetic fake AI.

The owned incident API has reporting preview, draft preparation, separate draft
review and reviewed JSON/PDF/HTML export under `/api/v1/incidents/{id}/reporting`.
The API, provider boundary and review semantics are documented in the core report.
No official submission API exists. Opening the verified destination is a handoff,
not submission, receipt, police acceptance or a recovery result.

Security/privacy remain incident-scoped: exports omit private storage paths, raw
OCR, unreviewed candidates, secrets and internal model diagnostics. HTML is escaped
and constrained; PDFs contain no active annotations. Explicit legacy values are
not silently promoted. Identity documents, registration and OTP stay on the official
portal. All development stories, files and retained diagnostic artifacts are synthetic.

## Official requirements and external verification limits

Mapping `ncrp-2026-10-11.2` records the source and review date. The public
[official checklist](https://cybercrime.gov.in/Webform/Crime_AuthoLogin.aspx) supplies
the incident-information minimum, relevant financial labels, 10 MB evidence
checklist limit and JPEG/JPG/PNG identity images up to 5 MB on the portal.
The [official FAQ](https://cybercrime.gov.in/Webform/FAQ.aspx) establishes that the
special women/children content branch is narrower than ordinary harassment and
distinguishes anonymous reporting eligibility. The public
[anonymous form](https://cybercrime.gov.in/Webform/Crime_ReportAnonymously.aspx)
specifies a 200–1,500 character incident description and its separate required
location/platform/category fields. That maximum is never applied to registered
financial or other-crime packets.

Some public pages intermittently timed out; official indexed public content and
the reachable FAQ were inspected. Authenticated per-category maxima and evidence
file types/limits remain unobservable without official registration/OTP and are
explicitly unknown. The 2019 manual remains labeled historical, including its
different evidence-size limit. The Phase 6 contract explicitly requires recording
current-portal verification limitations; completeness does not require inventing
them or using real citizen credentials. The supported cases use registered handoff;
the anonymous form is source-linked guidance, not an automatically selected route.

## Tests and exact verification

The repair suite now covers 65 cases and reporting covers 18, including the new
false rejection, unknown-loss, story escape, timing alias and public-route mapping
regressions. Reviewer findings were reproduced RED→GREEN, followed by the green
full suite. The independent reviewer did not run providers or edit files.

Commands ran from `backend`, except the frontend commands stated below:

```powershell
../.venv/Scripts/python.exe -m pytest -q --tb=line --show-capture=no
../.venv/Scripts/python.exe -m tests.phase6_reporting_configured
../.venv/Scripts/python.exe -m tests.smoke_local
```

From `frontend`:

```powershell
node --test __tests__/api-contract.test.cjs __tests__/action-panel.test.cjs
$env:CYBERSOS_BUILD_DIR='.next-phase6-finish'
$env:NEXT_PUBLIC_API_URL='http://localhost:8001'
node node_modules/next/dist/bin/next build
```

Full backend: **561 passed in 45.10s**, log `tmp/phase6-finish-backend-final.log`.
Frontend contracts: **13 passed**, log `tmp/phase6-finish-frontend.log`. Production
build passed compilation, lint/types and page generation, log
`tmp/phase6-finish-build.log`. Next reported its existing font-override warning;
the build exited successfully. Configured-PG check passed, log
`tmp/phase6-finish-configured.log`. `git diff --check` passed; line-ending warnings
do not indicate whitespace failures.

Browser runs use this common environment, temporary servers and disposable SQLite:

```powershell
$env:PLAYWRIGHT_PACKAGE='C:/Users/Ishan Chennupati/AppData/Local/Programs/Python/Python313/Lib/site-packages/playwright/driver/package'
$env:CYBERSOS_BUILD_DIR='.next-phase6-finish'
$env:SMOKE_BACKEND_PORT='8001'
$env:SMOKE_FRONTEND_PORT='3001'
# Select the app, journey, live flag and desktop flag from the table below.
../.venv/Scripts/python.exe -m tests.smoke_local
```

| Result | SMOKE_ASGI_APP | SMOKE_JOURNEY | SMOKE_LIVE_AI | SMOKE_REPORT_DESKTOP | Log under tmp/ |
| --- | --- | --- | --- | --- | --- |
| PASS repair, mobile/reload | tests.phase6_live_app:app | __tests__/phase6-repair.cjs | 1 | 0 | phase6-finish-repair-complete.log |
| PASS independently live drafting | tests.phase6_reporting_live_app:app | __tests__/phase6-reporting.cjs | 1 | 0 | phase6-finish-drafting-live.log |
| PASS reporting/mobile | tests.phase6_reporting_smoke_app:app | __tests__/phase6-reporting.cjs | 0 | 0 | phase6-finish-reporting-mobile.log |
| PASS reporting/desktop | tests.phase6_reporting_smoke_app:app | __tests__/phase6-reporting.cjs | 0 | 1 | phase6-finish-reporting-desktop.log |
| PASS evidence/memory/plan | tests.phase5_smoke_app:app | __tests__/phase5-journey.cjs | 0 | 0 | phase6-finish-phase5.log |
| PASS chat/retry/private attachments | tests.case_agent_smoke_app:app | __tests__/phase4-journey.cjs | 0 | 0 | phase6-finish-phase4.log |

The reporting journeys verify actual clipboard contents, separate approvals,
initial/corrected PDFs, stale and foreign exports, reload, another-tab correction,
relevant/irrelevant financial sections and composer visibility with requirements
expanded. Mobile and desktop screenshots were visually inspected. Six independently
live draft proposals were revalidated against their stored synthetic packets and
six actual PDFs were parsed with `pypdf.PdfReader`, including corrected Facebook
and INR 3500 information. No active annotations, storage paths or internal provider
diagnostics appeared. Log: `tmp/phase6-finish-pdf-inspection.log`.

Windows test workers and temporary databases required approved execution outside
the filesystem sandbox. No approval rejection occurred. Tests used only their own
servers; existing user services were not terminated or repurposed.

## Provider and conversational acceptance

The configured provider remained Gemini `gemini-3.5-flash-lite`, enabled with a
configured key and a 20-second deadline/one bounded retry. No billing changes,
automatic paid fallback or model switch were made. Billing-console limits and
token/cost measurements were not available and are not claimed.

The accepted full live repair run contains **23/23 successful understanding turns,
15 validated follow-ups, eight explicit application-control responses and zero
fallbacks**. Saved artifact: `backend/tmp/phase6-repair-live-1791704668376.json`.
Mean measured browser turn was **4,835ms**, maximum **7,927ms**, excluding the
harness's deliberate eight-second between-turn waits. This is not a
time-to-first-action measurement. Earlier runs exposed genuine instructions,
false rejections and unsupported no-loss prose; they remain in the historical
logs and led to the documented regressions.

Human inspection of the final replies confirmed: no harassment money intake or
unsupported no-loss claim; useful purpose/capability answers; no known account
access reasked as device access; no generic story restart; corrections refresh
canonical facts; skipped topics stay deferred; current approved help and summaries
pause routine questions; reload retains control. Witness information is isolated
and does not invent danger. New consequential questions may still be asked after
a skip; a skip is not a request to close the case.

The independent narrative-stage browser run produced **six of six validated live
Gemini drafts**, covering initial and corrected packets in all three entry routes,
with **no quota event or local fallback**. Stage durations were 2,454.1 / 1,522.9 /
2,856.5 / 3,812.4 / 1,537.6 / 1,906.3ms. Intake in that run is explicitly fake;
understanding and follow-up live evidence is the separate run above. This verifies
drafting independently rather than presenting fake intake as live AI. The earlier
combined live reporting run had five successful drafts and one safe quota fallback;
the fresh six-success result supersedes that drafting gap without erasing it.

## Next manual journey, limitations and roadmap

Use the README backend/frontend startup commands after installing requirements and
running `alembic upgrade head`. With synthetic data: Tell us what happened → choose
an optional hint or type directly → explain a supported incident → ask why/help,
skip or correct a detail → Prepare report → review existing facts → inspect account,
unknowns and evidence → approve the packet → copy a field/narrative → download
PDF/JSON or print → open the verified portal. Correct the platform/amount in chat;
the previous packet must become unavailable until new preparation and review.

External limitations remain explicit: current authenticated-form requirements are
not certified; the packet is not a complete-form import or official receipt; bank/
wallet/merchant identity absent from canonical state remains unknown and is entered
on the official form; short narratives warn about the public minimum instead of
padding facts. Draft wording/order is bounded by fact-linked supported claims.
Non-English control coverage and unrestricted multilingual PDF glyph support are
not claimed by this acceptance. Unsupported PDF glyphs have an honest JSON/browser
print alternative. Bystander-specific emergency guidance is not universal. Secure
long-term return, recovery and production retention remain assigned to later phases.

Roadmap: **NO CHANGE required**. Later phases must use the reviewed packet and its
revision/digest approval rather than legacy summaries or understanding review.
**OPTIONAL IMPROVEMENT:** expand authenticated official-field evidence, canonical
bank identity and narrative/language coverage after targeted validation. These
recommendations do not change a core invariant.

Core check: chat-first; no form-first intake; AI investigation; deterministic
critical actions; a self-building canonical case; truthful external status;
compatible future authorized official handoff. All are preserved.
