# CyberSOS revised Phase 4–12 execution prompts

Agreed requirements consolidated on 2026-10-02 and updated on 2026-10-04 after the Phase 4 review. These are future execution
contracts, not evidence that their features exist. Read the root AGENTS.md,
this shared contract and the selected phase completely in a fresh phase conversation.
Execute one phase only. No automatic commit, push, deployment, billing or release.

## Phase ownership and dependencies

| Phase | Required deliverable | Reused by |
| --- | --- | --- |
| [4](phase-04.md) | Direct chat, flexible grounded responses, case memory, curated RAG, attachment linkage, current plan/projection, shared UI | All later phases |
| [5](phase-05.md) | Hybrid conversation, initial three-route coverage, personalized action applicability, UI refinements and evidence intelligence | 6–12 |
| [6](phase-06.md) | Portal-field mapping, ReviewedCasePacket, narrative review, copy/export and honest handoff across three routes | 7–12 |
| [7](phase-07.md) | Full case companion, secure long-term return and lifecycle/deletion | 8–12 |
| [8](phase-08.md) | Expand and deepen initial Phase 5 coverage through the same contracts | 9–12 |
| [9](phase-09.md) | Multilingual voice input and reviewed language presentation in the same composer | 10–12 |
| [10](phase-10.md) | Comprehensive security/privacy/adversarial acceptance | 11–12 |
| [11](phase-11.md) | Authorized deployment rehearsal and supervised synthetic beta | 12 |
| [12](phase-12.md) | Final demonstrated support, operations and explicitly gated release decision | Future operations |

Phase 4 has three ordered checkpoints within one phase: conversational/context
foundation; unified chat/composer/attachments; current artifacts and full acceptance.
Do not mark Phase 4 complete after only a visual redesign or only backend tests.
Voice is required in Phase 9, not an early placeholder claim in Phase 4.

## Agreed hybrid journey and delivery across entry points

From Phase 5, Tell us what happened opens the same conversation with three optional
starting choices matching the official portal: Women/Children Related Crime,
Financial Fraud and Other Cyber Crime. Also offer Not sure and immediate free-text
input/attachments. Voice joins in Phase 9. These are routing hints, not verified
facts, mandatory classification or three separate bots. Allow changes and overlapping
signals; typing a sufficient story bypasses selection without another Continue step.

Hybrid means recommended answer buttons throughout an adaptive conversation,
not three entrance buttons followed by an empty chat box. The LLM writes grounded
normal replies and contextual optional choices, asks at most one useful follow-up,
skips known information and accepts natural answers, uncertainty, pause and correction.
Stable UI labels, honest failure messages and reviewed critical-action content remain
application-controlled; the LLM does not need to generate every interface control.

Build each Phase 5–9 capability across declared supported scenarios in all three
entry points before accepting that phase. Use one shared case agent, mutation,
memory, evidence, plan and reporting architecture. Declare supported scenarios,
jurisdiction and restrictions before implementation; an entry-point label is not
a claim of universal incident coverage. Initial nonfinancial support moves into
Phase 5; Phase 8 expands it instead of introducing it for the first time.

The case builds quietly during conversation. Once enough relevant information exists,
offer concise understanding review, then a tailored fuller response plan and,
from Phase 6, the portal-ready complaint draft. Conversation remains open afterward.
Do not impose an intake-completion gate: individually justified urgent actions appear
earlier, compactly. AI interprets and explains; reviewed source-backed deterministic
policy authorizes critical actions. Unknown timing is not proof of urgency, and
unknown authorization is not a citizen statement of uncertainty.

Reviewed official retrieval supports guidance, never establishes case facts or
authorizes critical actions. Research source freshness and applicability; preserve
citations and safe missing-source behavior. Arbitrary search results must not become
instructions or trigger citizen-URL fetching. Unrestricted live browsing remains
outside agreed scope; use replaceable reviewed retrieval within free-tier limits.

This approved optional-choice entrance supersedes earlier future-phase wording that
prohibits all category choices. Story-first opportunity, no mandatory classification,
no fixed questionnaire and deterministic critical actions remain preserved. Phase 4
is a historical implementation contract, not an instruction to redo it now.

Official-source starting points: [portal entry routes](https://cybercrime.gov.in/Webform/Index.aspx),
[reporting FAQ](https://www.cybercrime.gov.in/webform/FAQ.aspx) and
[citizen manuals](https://cybercrime.gov.in/webform/Citizen_Manual.aspx).
Reverify current routes, fields and upload limits during implementation; older manuals
alone do not establish the current form or complete-complaint import capability.

## Requirement coverage

| Agreed requirement | First complete delivery | Later extensions/acceptance |
| --- | --- | --- |
| Direct-to-chat CTA, centered welcome, one first Send | 4 | Regression in every phase |
| Permanent multiline composer, inline replies, mobile/accessibility, retry/drafts | 4 | 5 review, 6 report, 7 companion, 9 voice |
| Natural NLP, relevant answers, purpose explanations, uncertainty/skip/pause, scope redirection | 4 | Hybrid/domain foundation 5, expansion 8, language 9, final quality 12 |
| Per-case transcript/summary/older recall and correction freshness | 4 | Evidence 5, reporting 6, long-term return 7 |
| Curated RAG, supported citations, source lifecycle and private isolation | 4 | Evidence 5, domain 8, language 9, security 10 |
| Synthetic free-tier model evaluation, bounded quotas and replaceable providers | 4 | Extraction 5, drafting 6, speech 9, deployment 11 |
| JPG/JPEG, PNG, PDF and durable authorized message attachments | 4 | Actual extraction/review 5, secure lifecycle 7 |
| Deterministic early actions and current backend case projection | Existing foundation + 4 UX | Applicability and initial coverage 5, expansion 8; regression throughout |
| Evidence candidates/review/conflicts reaching canonical facts | 5 | Reporting 6 and later |
| Reviewed case packet, secure export and honest official handoff | 6 | Companion 7, broader coverage 8 |
| Full case companion, recorded references, recovery and deletion | 7 | System security 10 and operations 12 |
| Hybrid entrance and initial reviewed incident support across three routes | 5 | Expansion 8, multilingual 9, support freeze 12 |
| Multilingual microphone, editable transcript, same pipeline | 9 | Security 10, supported-device acceptance 11–12 |
| Privacy/safety, meaningful human-reviewed quality and UI consistency | Every phase | Comprehensive 10, synthetic beta 11, final 12 |

Optional enhancements are not silently required: spoken replies, unrestricted
browsing, custom model training, large vector infrastructure, dark mode and
decorative animation. Prioritize demonstrated citizen benefit over these additions.

## Engineering method required in every phase

1. Inspect the actual repository and prior reports; identify working, partial,
   missing, broken, duplicated and legacy paths. Treat prior findings as hypotheses.
2. Reproduce the relevant citizen journey and trace UI → API → domain/AI →
   database/storage → UI. Check runtime directory, env overrides, redacted DB
   target, migrations, frontend API target and provider configuration first.
3. Research changing provider/model/SDK, official-source and security facts using
   current primary documentation. Cite evidence and distinguish assumptions.
4. Compare reasonable approaches; choose the smallest robust one preserving the
   product. Modify earlier-phase code when required, without speculative features.
5. Implement authorized scope, run targeted checks, then verify complete journeys,
   persistence, authorization and meaningful failures. Preserve unrelated user work.
6. Report AGENTS.md's completion items, exact commands/results, live versus fake
   provider status, manual journey, limitations and roadmap impact. Stop at boundary.

## Shared contracts, not parallel subsystems

Names below are conceptual; retain good current naming and document actual typed
interfaces when implemented. Reuse existing storage, conversation revision/replay,
case authorization and deterministic playbooks.

| Contract | Owner | Required boundary |
| --- | --- | --- |
| Canonical case mutation | Existing domain/controller | Validated updates, provenance, conflict/correction semantics, atomic revision and idempotency |
| Conversational response | 4 | Grounded natural text, checkable fact/source/action references, optional one follow-up; no arbitrary tool/action authority |
| Case memory/context | 4 | Saved transcript, canonical facts, derived source-linked summary, relevant older recall; stale summaries never override current facts |
| Knowledge retrieval | 4 | Reviewed source/version/jurisdiction metadata; relevance and claim support; public knowledge separate from private case material |
| Turn ↔ evidence linkage | 4 | Ownership, persisted metadata, retry/replay and deletion semantics; reuse existing evidence records |
| Current case projection | 4 | Backend-derived current facts, actions/completions and evidence; no frontend case truth |
| Evidence review/merge | 5 | Original, candidate, reviewed and canonical layers; one existing revision-controlled mutation path |
| ReviewedCasePacket/handoff | 6 | Appropriate reviewed inputs, revision-bound review/export, truthful external status and provider boundary |
| Secure return/lifecycle | 7 | Expired authority handling, no UUID access, memory/index/cache deletion |
| Speech input adapter | 9 | Reviewable transcript through the same message path, bounded audio processing/retention |

Long-running extraction/drafting must not commit against stale revisions. Retries
must not duplicate turns, evidence, reviews or action completion. Reads/resume must
not accidentally rerun paid or rate-limited model stages.

## UI contract across phases

- Homepage CTA opens chat directly. No separate story form/Continue step and no
  second submission of the first message.
- Initial centered welcome; one readable conversation column, compact header and
  permanent bottom composer. Welcome yields to history after the first send.
- Reuse shared composer, message rendering, inline replies, attachment previews,
  artifact presentation, status/errors and accessible styling across all phases.
- Useful artifacts appear intentionally. Prefer expanded desktop panel/mobile
  sheet where practical; opening them must preserve draft and conversation access.
- Three optional portal entry choices appear inside chat from Phase 5; the composer
  remains available without a mandatory category screen.
- Urgent justified actions appear promptly and compactly; no empty dashboard/sidebar,
  form-first intake, readiness percentage or giant repeated question. Fuller plan
  presentation follows useful understanding review, not an arbitrary turn count.
- Neutral investigation styling; urgent styling only for applicable urgent actions,
  completed styling for recorded completion. Include textual meaning, not color alone.
- Keyboard navigation, focus restoration, accessible status announcements, mobile
  keyboard/viewport handling and jump-to-latest without forced scrolling.
- Preserve drafts on recoverable failures; transient status must not dominate chat.
  Optional streaming cannot display unvalidated authoritative instructions.

## Scope, budget and acceptance

Current authorization is synthetic testing only: fake stories, photos, PDFs and
recordings. No real citizen data, billing, paid fallback or public access. Model
selection remains provisional; evaluate available free-tier candidates fairly with
the same memory, retrieval and synthetic journeys, including quotas. No vendor
benchmark proves Telugu/Hinglish conversation quality. Prefer local retrieval and
existing database memory; vectors and multiple agents are not prerequisites.

Declare support per incident, jurisdiction, language, browser and file type, with
evidence. Initial work preserves existing reviewed jurisdiction/playbooks; research
and declare any extension instead of assuming global coverage. Launch retention,
identity/recovery, spoken replies and live browsing are not silently decided here.

Every phase extends a shared evaluation set: useful answers, why-question
explanations, corrections, uncertainty, skip/pause, mixed intent, distress,
off-topic redirection, older recall and unsupported claims. Later phases add their
evidence/report/return/voice journeys. Combine hard assertions and structured human
review; model grading is supplementary. Record failures as well as passes.

From Phase 5, maintain a route-by-scenario acceptance matrix for all three entry
points, including Not sure/direct-story bypass, mistaken initial choice and overlaps.
Phases 10–12 verify security, operational and final acceptance across that same matrix.

Relevant research is linked in AGENTS.md §25. These prompts replace the supplied
Phase 4–12 versions; they do not replace historical implementation reports.
