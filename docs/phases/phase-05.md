# CYBERSOS — PHASE 5
# Evidence intelligence inside the conversation and canonical case

Read root AGENTS.md and [shared contract](README.md) completely. Inspect Phase 4
attachments, response/memory/RAG contracts, existing extraction, review, identifiers,
timeline and canonical mutation paths. Do NOT begin Phase 6.

## End-user result

A citizen attaches a synthetic screenshot/PDF. CyberSOS extracts useful candidate
details, asks for review only where useful, understands natural corrections and
updates the same case/actions. Evidence reduces typing rather than adding a workflow.

## Required implementation

1. Reuse Phase 4 turn/evidence relationship, storage, file validation and ownership.
   Connect sound existing extraction/review services; do not build another vault,
   upload model or isolated evidence fact store.
2. Support useful grounded candidates: amount/currency, timestamp, transaction
   reference/status, recipient, UPI/contact/profile identifiers, message text and
   claimed organization. Declare supported formats/providers; PDF/text/OCR and image
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

## Verification and acceptance

Run real chat attachment → extraction → partial/full natural review → canonical
merge → action/memory/projection update → reload. Test correct/incorrect affirmation,
conflicting amounts, multiple files, uncertain time, failure, malformed output,
quota/503/timeout, malicious document instructions, cross-case access, replay,
concurrent correction/review, deletion and extraction-after-deletion.

Use live extraction on synthetic supported JPG/PNG/PDF fixtures, independently of
mock tests; verify downstream reasoning and browser review. Document unsupported
formats and unreadable/scanned cases truthfully. Re-run Phase 4 conversational
quality and financial regressions. Evidence must reduce citizen effort and update
the same canonical case. No reporting packet or Phase 6 work. Stop after report.
