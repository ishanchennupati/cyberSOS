# Phase 4 implementation

Scope: the three checkpoints in `docs/phases/phase-04.md`, preserving the existing
canonical mutation, private case capabilities and deterministic policy. Synthetic
India journeys, existing incident playbooks, English presentation with English,
Roman Telugu and Hinglish interpretation are the evaluation scope. Existing case
capability expiry limits access; it is not automatic data deletion. No new launch
retention period is invented here. Long-term recovery/deletion remains Phase 7;
unsent staged attachment cleanup is case-scoped after 24 hours on the next upload.

## Decisions

Extend existing JSON turn snapshots for source-linked memory and assistant replies
rather than introducing another transcript system. Use a bounded lexical retrieval
adapter over reviewed official-source claims, with immutable source snapshots.
Preserve exact structured fact/action/source references and reject unauthorized
instructions; replace sentence grammars with a semantic response contract.

Use a client-generated case creation key plus a separate private creation secret
for recoverable first-send creation. Stage existing private evidence with upload
idempotency keys; atomically link owned evidence to the durable turn. Original
storage and validation remain shared with existing uploads. Never extract files.

Replace the conversation shell with shared message/composer/artifact primitives.
Current projection comes from the backend; urgent actions remain visible without
opening details. Keep this workspace and preserve the user's runtime and changes.

## Ordered tasks

1. Baseline runtime/browser reproduction and existing tests.
2. Test and implement budgeted context, derived memory and reviewed retrieval.
3. Test and implement flexible bounded replies, grounding and source validation.
4. Test and implement creation replay, owned evidence linkage and projection.
5. Test and implement direct chat, staged attachment composer, history and artifacts.
6. Full backend/frontend/browser acceptance, then live synthetic provider journeys.
7. Record exact commands, live quota/model outcomes, limitations and roadmap impact.

## Review focus

Never trust old summaries after corrections. Never make historical actions current.
Reject cross-case attachments and duplicate replay. Distinguish upload from analysis.
Retain drafts and creation/turn keys after partial failure. Test missing and poisoned
knowledge, unsafe claims, unknowns/skips, provider failures, older recall and mobile
composer access with artifacts open. Do not mark the phase passed on mocks alone.
