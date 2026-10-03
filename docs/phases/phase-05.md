# CYBERSOS — PHASE 5
# Hybrid conversation, initial three-route coverage and evidence intelligence

Read root AGENTS.md and [shared contract](README.md) completely. Inspect Phase 4
attachments, response/memory/RAG contracts, existing extraction, review, identifiers,
timeline and canonical mutation paths. Do NOT begin Phase 6.

## End-user result

A citizen attaches a synthetic screenshot/PDF. CyberSOS extracts useful candidate
details, asks for review only where useful, understands natural corrections and
updates the same case/actions. Evidence reduces typing rather than adding a workflow.

All three entry points receive this capability in declared supported scenarios.
Citizens choose or describe their situation, then tap recommended answers or type
throughout the same adaptive conversation. The case builds quietly; review useful
understanding before the fuller plan, while justified urgent actions appear earlier.

## Hybrid conversation and initial reviewed coverage

1. Add optional Women/Children Related Crime, Financial Fraud and Other Cyber Crime
   choices inside existing chat, plus Not sure. Keep the composer and attachments
   immediately available; no required selection or extra Continue screen. Persist
   the choice as a routing hint, not confirmed classification. Accept mistaken
   selections, changes and overlapping incidents without restarting the case.
2. Recommended answer buttons continue throughout conversation. The LLM proposes
   grounded replies and useful contextual choices within validated contracts; no
   category-specific fixed questionnaire or exhaustive wording allowlist. Citizens
   may type instead of tapping. Skip known details; do not force every reply to end
   in a question or use leading options to invent facts. Stable labels and truthful
   failure copy do not depend on provider availability.
3. Inspect financial assumptions across facts, AI validation, actions, evidence,
   memory and projection. Generalize necessary boundaries once; preserve financial
   authorization semantics and provenance. No per-category bots or parallel stores.
4. Research current official/platform sources and declare an initial support matrix
   covering all three routes, including relevant harassment/threat/private-image
   blackmail and account takeover/impersonation scenarios. Specify exclusions and
   jurisdiction; labels alone cannot imply every crime is supported. Review and
   version critical-action policies and evidence restrictions. Never solicit explicit
   intimate media, CSAM, credentials or unnecessary identity documents; use safer
   text, identifiers and non-explicit records. Extend retrieval, facts, policy and
   evidence contracts together; do not defer all nonfinancial behavior to Phase 8.
5. Tighten plan applicability: "I lost 5000" alone does not establish a bank payment,
   fraud, currency, authorization or timing. Ask useful clarification with optional
   answers before banking/reporting actions. Missing authorization is different from
   the citizen saying they are unsure. Unknown timing alone must not create urgency.
   A detailed first message may justify urgent help without further intake.
6. Tailor the action set to canonical facts, ongoing risks and recorded completions.
   AI explains approved actions in context using supporting reviewed retrieval;
   critical-action creation remains deterministic and source-backed. Research and
   curate fresh official guidance without unrestricted per-case internet authority.
7. Offer concise understanding review when enough is known; avoid confirmation on
   every turn. Present the fuller plan intentionally after review, while justified
   urgent actions appear promptly and compactly. Avoid a large automatic ACT NOW
   panel dominating an ambiguous early exchange. Keep the case building quietly;
   corrections refresh it and its plan. No Phase 6 complaint/export implementation.

## Evidence intelligence implementation

1. Reuse Phase 4 turn/evidence relationship, storage, file validation and ownership.
   Connect sound existing extraction/review services; do not build another vault,
   upload model or isolated evidence fact store.
2. Support useful grounded candidates across declared three-route scenarios:
   amount/currency, timestamp, transaction reference/status, recipient,
   UPI/contact/profile identifiers, message text and
   claimed organization, platform/account/profile references and non-explicit threat
   text where relevant. Omit irrelevant financial fields in nonfinancial cases.
   Declare supported formats/providers; PDF/text/OCR and image
   understanding may need different adapters. Do not claim readable-image analysis
   from a heuristic extractor that cannot read the image.
3. Preserve original evidence, immutable extraction attempt/candidates, citizen
   reviewed/corrected values and canonical facts separately. Retain source evidence,
   page/span where feasible, extraction uncertainty and review provenance. Missing
   date/year/timezone and ambiguous identifiers remain uncertain, not guessed.
4. Precisely trace evidence verification → canonical merge. Route accepted review
   through the existing atomic revision/idempotency path, preserving correction and
   conflict semantics. Unreviewed extraction cannot independently drive critical actions.
   Natural confirm/reject/correct can reference one unambiguous active review;
   broad Yes cannot accidentally verify unrelated fields or documents.
5. For story ₹35,000 versus screenshot ₹3,500, surface a concise conflict and let
   the citizen resolve it; no silent overwrite. Explain what came from which source.
   Partial review must not promote the entire extraction.
6. Reevaluate deterministic actions and refresh derived memory, current projection,
   reviewed identifiers and timeline. Never turn an old summary into current truth.
   Stale extraction/review results cannot overwrite a newer conversation correction.
7. Private evidence recall is ownership-gated and separate from shared RAG. Evidence
   assertions are candidates, not knowledge policy. Test embedded hostile instructions.
8. Define deletion/replacement of linked evidence: originals and derived extraction,
   private retrieval/cache references removed or honestly tombstoned according to
   lifecycle policy; review resulting canonical provenance without silent corruption.
   Preserve honest history and show deleted/unavailable attachments appropriately.

## UI requirements

- Extend the same composer/history and artifact surface. Citizen uploads voluntarily
  or when a useful AI request is made; never classify evidence first.
- Show uploaded, analyzing, review-needed, verified, failed and deleted states honestly.
  No duplicate automatic extraction calls on render/reload.
- Compact review artifact pairs the source preview with useful candidate details.
  Natural text is first-class; optional confirm/edit controls do not create a mega form.
- Failed/unsupported extraction offers Retry, Skip or Continue talking; ask only a
  consequential missing detail. Keep composer/draft available and mobile accessible.
- Show changed current plan/case information without rewriting historical messages.

## Phase 5 refinements requested after Phase 4

- Use the same CyberSOS logo, typography and color tokens on the homepage and
  conversation page. Keep the conversation visually minimal.
- Remove the prominent green composer outline on pointer focus. Preserve a clear,
  accessible keyboard focus indicator and visible caret.
- Immediately show the submitted citizen message with an assistant pending
  indicator. Keep database saving details behind the scenes rather than displaying
  "Saving" on Send. Reconcile the pending message with the durable backend turn,
  retain the same retry key, prevent duplicates and preserve recoverable drafts.
  Display only validated assistant responses; do not stream unchecked instructions.
- Replace technical recovery wording, such as "saved message key", with concise
  citizen-facing explanations and clear retry controls. Make attachment progress
  and failures understandable without exposing backend implementation details.
- Review short, distressed-user journeys for effort and clarity: a brief natural
  story, useful optional quick replies, timely applicable actions and attachments
  that reduce typing. Do not require a long narrative or add form-first intake.

These enhancements belong to Phase 5; the Phase 4 runtime repair does not implement
them. Verify consistent branding, pending/retry behavior, keyboard access and mobile
composer usability alongside the evidence journey.

## Verification and acceptance

Verify each declared route through choice-first and direct-story entry,
recommended buttons and natural answers, Not sure, mistaken-choice correction,
overlapping signals, distress, skip/pause and reload. Human-review usefulness and
effort, not only valid JSON. Verify live understanding and follow-up per route.
Test ambiguous "I lost 5000" without banking assumptions; clear first-turn financial
fraud with prompt justified help; harassment without irrelevant financial actions;
and unknown timing/authorization without invented urgency or citizen uncertainty.
Check fuller-plan review/presentation and compact early actions independently.

Run real chat attachment → extraction → partial/full natural review → canonical
merge → action/memory/projection update → reload. Test correct/incorrect affirmation,
conflicting amounts, multiple files, uncertain time, failure, malformed output,
quota/503/timeout, malicious document instructions, cross-case access, replay,
concurrent correction/review, deletion and extraction-after-deletion.

Use live extraction on synthetic supported JPG/PNG/PDF fixtures, independently of
mock tests; verify downstream reasoning and browser review. Document unsupported
formats and unreadable/scanned cases truthfully. Re-run Phase 4 conversational
quality and financial regressions. Evidence must reduce citizen effort and update
the same canonical case across all three supported entry routes. No reporting packet
or Phase 6 work. Stop after report.
