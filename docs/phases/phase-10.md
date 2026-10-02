# CYBERSOS — PHASE 10
# Comprehensive security, privacy and adversarial acceptance

Read root AGENTS.md and [shared contract](README.md) completely. Do NOT publicly
launch or begin Phase 11. Earlier phases must already enforce relevant security;
this is system acceptance, not deferred basic protection.

## Required audit and repair

1. Map actual routes/resources, trust boundaries and provider payloads: chat,
   attachments, evidence/parsing/review/merge, memory/summaries/private recall,
   shared RAG ingestion/retrieval, actions, case projection, packet/export/handoff,
   voice, sessions/recovery, storage, caches and deletion.
2. Produce/test a route and resource authorization matrix. Case A cannot read,
   link, review, search, export or delete Case B. Enforce ownership before retrieval
   and signed/file access, not by asking the LLM to filter unauthorized results.
3. Attack uploads, signatures/MIME/size, filenames/paths, parsing limits, malicious
   PDF/OCR, review replay and canonical promotion. No evidence prompt can change
   policy, access secrets or automatically become reviewed facts/shared knowledge.
4. Attack RAG corpus poisoning, unsupported citations, stale/withdrawn sources,
   private/public mixing, unauthorized chunk retrieval and tool/URL injection.
   No automatic arbitrary outbound fetch of citizen-supplied URLs; assess SSRF if
   any permitted fetch feature exists.
5. Attack memory poisoning, summary promotion, stale facts, cross-case leaks,
   indirect instruction carryover and deleted material reappearing from caches.
6. Attack responses: secrets, invented actions, suppression of valid urgent actions,
   fabricated recovery/status, harmful cyber requests and nonexistent capabilities.
   Verify semantic validation allows legitimate natural replies while rejecting risk.
7. Attack reporting: unreviewed/legacy promotion, stale review/export, hidden
   metadata/credentials, malicious content and fabricated acknowledgement.
8. Attack long-term return: enumeration, expiry, replay, stolen references,
   rate limiting, revocation and supported device/session behavior.
9. Verify XSS/untrusted rendering in messages, AI, filenames, OCR, notes, citations,
   reports and transcripts; origins/CORS/CSRF protections and accessible error UI.
10. Exercise simultaneous messages, attachment linking, review, correction,
    completion, deletion and extraction; atomic revisions and idempotency must hold.
11. Inspect actual privacy-safe diagnostics and provider/storage behavior; no keys
    or unnecessary raw citizen-equivalent content. Test audio and lifecycle cleanup,
    including indexes/caches and documented backup/log limitations.

## UI acceptance during security work

Fix actionable error/retry, expired access and deletion states without leaking case
existence. Security must not reintroduce forms or remove natural input unnecessarily.
Keep composer, focus, language meaning and current artifacts consistent.

## Decision and evidence

Use synthetic cases and approved testing environments. Research current primary
security guidance and preserve reproduced findings, severity, remediation and
verification evidence. Critical/high-risk blockers must be fixed or the capability
excluded from the explicitly defined test/pilot scope. Lower risks require recorded
limits, ownership and follow-up rather than a blanket secure claim.

Re-run realistic live synthetic journeys and release-critical regressions after
repairs. Output an evidence-backed acceptance decision and supported scope matrix.
This does not authorize real data, deployment, spend or public beta. Stop; no Phase 11.
