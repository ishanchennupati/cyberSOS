# CYBERSOS — PHASE 6
# Reviewed reporting packet, narrative review and official handoff foundation

Read root AGENTS.md and [shared contract](README.md) completely. Inspect Phase 5
canonical facts/provenance, memory and current projection plus existing summaries,
exports and official sources. Do NOT begin Phase 7.

## Mandatory prerequisite — repair conversation behavior before reporting implementation

Agreed on 2026-10-07. A Phase 6 execution request includes an ordered prerequisite
checkpoint repairing the existing Phase 5 conversation. Read
[quality audit](../phase5-conversation-quality-audit.md),
[Phase 5 acceptance](../phase5-acceptance.md) and current phase status first.
Do not treat passing infrastructure/unit tests as completed conversational acceptance.
Do not start portal mappings, reporting packet code, narrative drafting, exports or
handoff UI until the repair checkpoint below passes. These are repairs to the shared
conversation foundation, not deferred Phase 8 enhancements or a replacement chatbot.

### Repair requirements

1. Reproduce the observed money-loss fallback loop in harassment cases and the
   ignored stop/plan/conclusion requests. Trace composer -> turn contract -> intent
   interpretation -> response selection -> canonical memory -> rendered response.
   Add behavioral regressions before repairing application code. Inspect actual
   rejected synthetic proposals to distinguish unsafe output from false rejection;
   rejection codes alone do not establish which wording was wrong.
2. Prioritize the citizen's current request: answer a relevant question, show useful
   current help, summarize/conclude, pause, or investigate. Persist control state
   across reload through the existing turn/revision path. Clear stop/pause requests
   must remain effective during understanding or follow-up failure. Do not replace
   multilingual AI interpretation with an exhaustive phrase list; a bounded safe
   control fallback must not create incident facts or actions.
3. Ask only consequential relevant missing questions. Track question disposition,
   answers, declines and repeated nonanswers; do not repeat merely because a field
   remains unknown. A meaningful reask requires changed context or explicit citizen
   permission. General/nonfinancial cases must not automatically receive financial
   intake. Do not impose a fixed questionnaire, universal field checklist or turn cap.
4. Connect natural help/plan requests to current backend-approved actions and concise
   known-fact review in the chat. Reviewed policy owns critical instructions; the
   application can render them and AI can explain grounded purpose. Preserve prompt
   early urgent help, unknowns and citizen corrections. Do not require a particular
   button before responding to a typed help request, silently mark facts reviewed,
   or treat understanding review as later reporting/submission approval.
5. Recognize sufficient understanding and citizen-requested conclusion: summarize
   known facts, disclose consequential uncertainty, present applicable next steps,
   and stop routine investigation while keeping the case open. Corrections/new
   information may refresh facts and actions without automatically restarting intake.
6. Replace the failure-driven question loop with an intent-aware safe fallback:
   respect pause; provide applicable approved help or an honest limitation; ask only
   a necessary relevant clarification. Keep drafts, replay keys, ownership and
   canonical provenance. Retain grounding/safety checks while repairing semantic
   field/wording mismatches; do not accept unchecked authoritative prose.
7. Evaluate the witness request "Someone just got harassed in front of me; what
   should I do?" Establish only consequential physical/online/safety context, who
   is affected and whether this is a separate incident. Do not assume immediate
   danger, silently mix third-party facts into an existing case, or invent bystander
   instructions. Existing justified urgent policy must surface before routine intake.
   Any needed critical guidance requires current reviewed source/policy support;
   declare unproven coverage rather than claim universal emergency handling.

### Repair acceptance gate

Use synthetic data only and the existing free-tier/provider boundaries. Verify:

- Live multi-turn journeys across the three initial routes: an adequate story,
  useful follow-up/answer, correction, unknown/skip, distress, plan request,
  summary/conclusion and reload. Human-review usefulness, reduced repetition and
  effort alongside deterministic assertions; JSON/HTTP success alone is insufficient.
- Exact regression: Instagram harassment -> "Why are you asking about money?" ->
  "Enough questions. Tell me what to do now." -> "Summarize and conclude."
  No repeated irrelevant money question; show applicable help and honor control.
- Clear stop/pause and help requests during simulated understanding timeout,
  follow-up timeout, malformed/rejected output and quota failure. No question loop,
  invented facts/actions, duplicate turns or loss of saved control on reload.
- Witness/physical-versus-online clarification and new-incident isolation; supported
  urgent actions appear promptly without unsupported danger or banking inference.
- Existing evidence partial/conflict review, memory freshness, action applicability,
  ownership/replay, mobile composer and Phase 4/5 regression journeys remain correct.
- Repeatable live understanding/follow-up quality for the declared scenarios. Record
  actual failures, latency and provider status; mocks cannot establish live success.

Publish a repair completion report and update phase status with exact evidence and
limitations. If the gate remains unmet, finish the repair session with the gate
explicitly open; do not proceed to reporting implementation or declare Phase 6
complete. Once it passes, proceed to the Phase 6 scope below under the existing
Phase 6 authorization without an additional routine approval. No automatic paid
fallback, model switch, production access, commit, push or deployment.

## End-user result

CyberSOS prepares a complaint-ready packet from reviewed case information. The
citizen reviews what already exists rather than telling the story or filling fields again.

## Portal-aligned complaint preparation across all three entry points

1. Inspect the current official reporting routes and field requirements at execution
   time. Build a versioned, source-linked mapping from canonical reviewed information
   to applicable portal sections/labels, requiredness, formats and character limits.
   Match the relevant fields, not every category's form at once; the initial route
   hint alone cannot determine the final reporting route. Support declared scenarios
   in Women/Children Related Crime, Financial Fraud and Other Cyber Crime.
2. Build quietly from conversation and evidence, then offer understanding review and
   a portal-ready draft without a second intake form. Populate only supported reviewed
   facts; disclose unknowns/conflicts. Ask only useful missing reporting questions,
   explain why, and accept corrections through the existing canonical mutation path.
   Do not require sensitive identity documents or credentials in CyberSOS merely
   because the official portal requests them; explain what must be entered there.
3. Separate the citizen complaint fields/narrative from CyberSOS's response checklist.
   Provide Copy field, Copy narrative, secure PDF/download and print with accessible
   feedback. Preserve supported meaning and portal character limits without losing
   original facts. Export only the revision-bound reviewed packet.
4. Link to verified official destinations. Registration, verification and submission
   occur on the official portal until a genuine authorized integration exists; never
   request its OTP. Evidence-upload support is not complete-form import support.
   Verify route-specific attachment types/limits; do not promise that uploading our
   PDF fills or replaces the official form. Clearly label the draft as prepared by
   CyberSOS, not an official receipt or accepted complaint.

## Required implementation

1. Map each summary/export/narrative input to reviewed canonical, unreviewed candidate,
   legacy field, derived data or citizen-recorded assertion. Populated is not reviewed.
2. Build a typed ReviewedCasePacket from suitable reviewed summary, timeline,
   financial details where relevant, identifiers, evidence inventory, citizen actions
   and explicit unknowns/conflicts. No database dump or silent legacy promotion.
   Declare review semantics for explicit conversation facts and targeted missing review.
3. AI narrative drafting consumes that packet only, with traceable claim/fact
   references and no invented dates, identities, amounts, legal conclusions or status.
   RAG can explain reporting requirements but cannot become incident narrative facts.
   Keep reviewed official guidance separate from the citizen's account of events.
4. Natural review corrections use canonical mutation/provenance semantics, refresh
   memory/plan/projection and invalidate older packet drafts/approval. Persist a
   revision-bound reviewed snapshot for export; do not create competing report truth.
5. Add backend reporting states with explicit predicates: gathering, ready to review,
   ready for handoff. No invented percentages; unknowns may be disclosed without
   blocking all help. Unresolved consequential conflicts require targeted review.
6. Reuse/create a HandoffProvider boundary consuming ReviewedCasePacket. Implement
   review, copy, secure export/PDF/print and verified official destination only.
   Opening a URL is not submission or acknowledgement. No fabricated official API.
7. Ownership-gate packets, previews and exports; exclude secrets, storage URLs,
   internal diagnostics/model metadata and hidden/unreviewed candidates. Safe export
   rendering and access to originals must not expose private files publicly.

## UI requirements

- Reporting preview is an intentional artifact in the existing chat/case surface,
  with readable sections, review/correct controls and natural composer access.
- Clearly separate citizen account, recorded actions, unknowns and source guidance.
  No second intake form. Show what changed after corrections and require fresh review.
- Accessible copy/export feedback and honest official-destination explanation.
  Mobile sheets preserve focus/draft. Never show Submitted/Police accepted without
  real verified integration; citizen-entered references remain Recorded by you.

## Verification and acceptance

Verify portal-field mapping, relevant/irrelevant sections, unknown required fields,
per-field copy, narrative limits and actual PDF/export output for supported scenarios
in all three entry points. Test wrong initial choice and overlap without duplicate
intake. Record source/version and any current-portal verification limitations; do
not claim upload-based import without official evidence.

Test canonical reviewed state → packet → live grounded draft → natural correction
→ new case revision → fresh review/export → official handoff link. Populated legacy
fields cannot silently become official facts. Test stale export/review, uncertainty,
conflicts, malicious identifiers/report text, wrong-case access, safe PDF/print/copy,
source resolution, provider failure and no fake acknowledgement.

Verify live drafting separately from understanding, reasoning and evidence stages;
inspect actual browser/export output with synthetic fixtures. Re-run current-plan,
memory and attachment journeys. Citizen tells the story once and reviews truthful
prepared material. No full long-term companion/recovery. Stop; no Phase 7.
