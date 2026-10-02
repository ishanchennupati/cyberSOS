# CyberSOS revised Phase 4–12 execution prompts

Agreed requirements consolidated on 2026-10-02. These are future execution
contracts, not evidence that their features exist. Read the root AGENTS.md,
this shared contract and the selected phase completely in a fresh phase conversation.
Execute one phase only. No automatic commit, push, deployment, billing or release.

## Phase ownership and dependencies

| Phase | Required deliverable | Reused by |
| --- | --- | --- |
| [4](phase-04.md) | Direct chat, flexible grounded responses, case memory, curated RAG, attachment linkage, current plan/projection, shared UI | All later phases |
| [5](phase-05.md) | Evidence candidates, review/conflict resolution, canonical merge and memory/projection refresh | 6–12 |
| [6](phase-06.md) | Revision-bound ReviewedCasePacket, narrative review, export and honest handoff | 7–12 |
| [7](phase-07.md) | Full case companion, secure long-term return and lifecycle/deletion | 8–12 |
| [8](phase-08.md) | Reviewed broader incident coverage through the same contracts | 9–12 |
| [9](phase-09.md) | Multilingual voice input and reviewed language presentation in the same composer | 10–12 |
| [10](phase-10.md) | Comprehensive security/privacy/adversarial acceptance | 11–12 |
| [11](phase-11.md) | Authorized deployment rehearsal and supervised synthetic beta | 12 |
| [12](phase-12.md) | Final demonstrated support, operations and explicitly gated release decision | Future operations |

Phase 4 has three ordered checkpoints within one phase: conversational/context
foundation; unified chat/composer/attachments; current artifacts and full acceptance.
Do not mark Phase 4 complete after only a visual redesign or only backend tests.
Voice is required in Phase 9, not an early placeholder claim in Phase 4.

## Requirement coverage

| Agreed requirement | First complete delivery | Later extensions/acceptance |
| --- | --- | --- |
| Direct-to-chat CTA, centered welcome, one first Send | 4 | Regression in every phase |
| Permanent multiline composer, inline replies, mobile/accessibility, retry/drafts | 4 | 5 review, 6 report, 7 companion, 9 voice |
| Natural NLP, relevant answers, purpose explanations, uncertainty/skip/pause, scope redirection | 4 | Domain 8, language 9, final quality 12 |
| Per-case transcript/summary/older recall and correction freshness | 4 | Evidence 5, reporting 6, long-term return 7 |
| Curated RAG, supported citations, source lifecycle and private isolation | 4 | Evidence 5, domain 8, language 9, security 10 |
| Synthetic free-tier model evaluation, bounded quotas and replaceable providers | 4 | Extraction 5, drafting 6, speech 9, deployment 11 |
| JPG/JPEG, PNG, PDF and durable authorized message attachments | 4 | Actual extraction/review 5, secure lifecycle 7 |
| Deterministic early actions and current backend case projection | Existing foundation + 4 UX | Evidence 5, coverage 8; regression throughout |
| Evidence candidates/review/conflicts reaching canonical facts | 5 | Reporting 6 and later |
| Reviewed case packet, secure export and honest official handoff | 6 | Companion 7, broader coverage 8 |
| Full case companion, recorded references, recovery and deletion | 7 | System security 10 and operations 12 |
| Broader incident support without separate bots | 8 | Multilingual 9, support freeze 12 |
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
- Urgent justified actions appear promptly; no empty dashboard/sidebar, form-first
  intake, readiness percentage, giant repeated question or category picker.
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

Relevant research is linked in AGENTS.md §25. These prompts replace the supplied
Phase 4–12 versions; they do not replace historical implementation reports.
