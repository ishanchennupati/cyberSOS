# CYBERSOS — PHASE 4
# Conversational foundation, direct chat, memory, curated RAG and current artifacts

Read root AGENTS.md and [shared execution contract](README.md) completely first.
Inspect repaired Phase 3R. Do NOT begin Phase 5. This phase includes backend/AI
foundation and citizen UI, not a frontend-only redesign.

## End-user result

Homepage Tell us what happened opens the chatbot directly with a centered welcome
and bottom composer. The citizen sends their story once. CyberSOS answers naturally,
retains case context, explains questions/actions, asks only useful missing details,
and builds truthful current artifacts underneath.

## Inspect before implementing

Trace homepage, `/incident/start`, conversation routing and first-message handoff.
Reproduce the reported draft requiring another Send; do not assume its exact cause.
Inspect `frontend/components/conversation.tsx`, existing action panel and API/types;
backend conversation service, understanding, case_agent, ai_provider, next_move
schema, facts, policy, evidence/storage and persisted turns. Investigate narrow
question/acknowledgement grammars, replaced explanations and last-four-turn context.
Reuse secure uploads, private case access, revisions, retries, corrections and plans.

## Checkpoint A — conversational/context foundation

1. Evolve the bounded response contract to allow acknowledgement, relevant answer,
   grounded explanation and an optional single follow-up together. User intent can
   combine correction, answer, new facts and a question. No mandatory question or
   field-filling loop; unrelated text does not become case truth.
2. Replace wording allowlists with typed semantic/reference and safety validation.
   Preserve exact grounding for facts/identifiers, unsupported-claim rejection,
   prohibited-secret boundaries and applicable action references. Do not simply
   remove validation or let a second model authorize critical actions.
3. Render accepted AI wording. Explain approved actions naturally while keeping
   reviewed instructions visible; explanations cannot add procedures, guarantees
   or fake external status. Scripted copy is fallback only.
4. Add case memory: saved messages from both sides, current facts, source-linked
   derived summary/open issues and relevant older recall. Refresh against case
   revision after corrections; summaries never verify candidates or compete with
   facts. Track answered unknowns, declined questions and already-given explanations.
5. Introduce a small genuinely retrieved curated knowledge collection and adapter.
   Capture supporting source IDs, versions, jurisdiction and review dates. Use
   existing official-source registry where sound. Query only when external knowledge
   is useful, distinguish case facts from knowledge, and test source support.
   No hardcoded FAQ-response matching disguised as RAG, paid search, arbitrary
   browsing, large vector service or automatic ingestion of citizen evidence.
6. Isolate private recall by case ownership. Treat retrieved text as hostile data.
   Missing retrieval support yields an honest limitation, not invented knowledge.
7. Evaluate free-tier model availability and synthetic conversation quality before
   changing configured models. Gemini 3.8 Flash is a candidate, not a fixed winner.
   Keep extraction/reasoning stages independently diagnosable and quota-bounded.

## Checkpoint B — one chat and durable composer/attachments

- Remove the intermediate story form/Continue step. First Send must durably create
  or use the authorized case and save/process one message, with retry/idempotency
  across partial case-creation failures. No second send or duplicate case/turn.
  Old start links may enter this same experience; no second intake system.
- Initial centered Tell us what happened and concise explanation; no empty plan,
  category choice, wizard or money-only shortcut dominating intake.
- Bottom multiline composer grows roughly 1–6 lines, then scrolls internally.
  Desktop/mobile, keyboard, disabled-empty-send, send/loading/retry and draft retention.
- Single + attachment control for approved JPG/JPEG, PNG and PDF. No technical
  classification menu. Show removable previews and progress before Send.
- Establish durable case-authorized turn ↔ existing evidence linkage. Support text
  with attachments and attachment-only messages without inventing a narrative.
  Define staged upload, cancel/remove, partial failure, orphan cleanup and deletion;
  replay/refresh cannot duplicate uploads or claim a failed attachment was sent.
- Historical turns show secure attachment previews/downloads on resume. Never expose
  public storage URLs; hostile filenames are escaped. Distinguish upload from analysis.
- Voice is Phase 9. Do not show a working-looking microphone or promise recording
  before implemented support; keep the composer extensible without a parallel shell.

## Checkpoint C — current artifacts and shared UI

- Readable messages and optional inline replies; no duplicated question card.
  Compact synthetic-only notice, subtle statuses, accessible feedback for
  misunderstanding/repetition and jump-to-latest without stealing scroll position.
- Show justified urgent actions immediately, independent of intake completion.
  Current plan comes from canonical backend state, not historical assistant text.
  ACT NOW/PRESERVE/REPORT/FOLLOW THROUGH contain only applicable actions; completion
  is citizen self-report. AI cannot hide a valid urgent policy action.
- Build a lightweight backend case projection from current facts, plan revision,
  completions and evidence. Known/useful fields only; uncertain understanding labeled.
  No invented readiness score or Phase 6 reporting semantics.
- Compact plan/case artifacts open intentional desktop detail panel/mobile sheet
  where useful; preserve draft/focus. Modest View case only, not Phase 7 companion.
- Establish shared UI components/tokens for later evidence/report/case/voice views.
  Verify contrast, mobile keyboard, focus and composer access in every state.

## Verification and acceptance

Test browser CTA → direct chat → first Send saved exactly once → grounded reply.
Then: why are you asking, relevant knowledge question with supporting source,
natural confirmation, mixed question/correction, unknown, pause/skip, distress,
off-topic, known numeric references, unauthorized versus scam-authorized payment,
financial+device signals and older recall beyond four exchanges. Correct a fact,
reload and prove summaries/current artifacts use the correction while history stays.

Test attachment-only/text+file sends, invalid/oversized file, cross-case linkage,
cancel, interrupted upload/send, identical replay, stale revision, refresh/resume
and deletion behavior. Test retrieval poisoning/missing support, provider 503,
quota, timeout, malformed output and validator rejection separately. Test English,
Roman Telugu and Hinglish understanding without claiming Phase 9 localization.

Verify both live AI stages and retrieval/reference validation through the actual
browser using synthetic data; mocks alone do not pass. Grade natural usefulness
as well as correctness. Report exact commands, model/quota outcomes and measured
limitations. Phase 4 passes only when all three checkpoints deliver one usable
conversation. Do not implement evidence AI extraction/review, reporting, long-term
recovery, broad new playbooks or voice here. Stop; do NOT begin Phase 5.
