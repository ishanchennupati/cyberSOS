# Phase 5 implementation plan

**Spec:** `docs/phases/phase-05.md` and `docs/phases/README.md`.
**Goal:** Shared hybrid conversation and reviewed evidence intelligence across initial Indian financial fraud, online harassment/threat/private-image blackmail, and account takeover/impersonation scenarios.
**Architecture:** Extend the current facts, deterministic policy, conversation compare-and-swap, private evidence storage, memory and projection. Immutable extraction attempts supply bounded candidates; partial citizen reviews use the existing turn transaction. No parallel case store, reporting packet, voice, paid fallback or deployment.

## Constraints and rulings

- Execute in the authorized workspace; preserve the existing `.gitignore`, action-panel scroll repair and its test/report. No commits or branch integration.
- AGENTS.md authorizes routine reversible implementation without repeated approvals; this supersedes skill design/worktree/commit approval rituals. Execute inline; no delegation requested.
- Initial jurisdiction IN. Text evaluation: existing English, Roman Telugu and Hinglish. File support: JPG/JPEG, PNG, PDF <=10 MB. Only synthetic, non-explicit records. No launch retention decision.
- Current configured database is PostgreSQL at `20261003_chat_attachments`; local acceptance uses disposable migrated SQLite. Provider configured `gemini-3.5-flash-lite`; retain model. Test free availability independently for extraction.
- Original extraction/review is legacy financial metadata and never reaches canonical state. Reuse storage and routes, but version chat review through conversation turns. Do not silently convert legacy evidence into verified facts.

## Tasks

- [x] 1. Generalize shared facts and source-backed versioned policy. Test ambiguous loss, unknown timing/authorization, harassment without bank actions, physical danger, takeover, overlaps and correction.
  Files: `domain/facts.py`, `domain/playbooks.py`, `domain/sources.py`, `schemas/understanding.py`, `services/understanding.py`, `services/ai_provider.py`, `services/case_agent.py`, `tests/test_phase5_policy.py`.
- [x] 2. Add immutable extraction attempts and partial review contracts. Migrate a disposable DB; test private access, replay, malformed/unreadable output, failures, stale completion/deletion. Gemini inline bytes, no URL fetching or shared RAG indexing.
  Files: evidence models/schema/services/routes; new `services/evidence_intelligence.py`; additive Alembic migration; `tests/test_phase5_evidence.py`.
- [x] 3. Merge structured and natural evidence review through `conversation_service.submit`'s existing revision claim. Keep candidates separate; surface conflicts; stale reviews cannot overwrite corrections; refresh memory/plan/identifiers/timeline atomically. Test partial review, broad Yes, multiple files, correction, concurrency, replay and deletion.
- [x] 4. Persist optional routing hints and revision-bound understanding review. Contextual validated replies, no fixed intake. Add shared branding, pending citizen message/assistant indicator, citizen recovery copy and keyboard focus; compact early actions and intentional fuller plan.
  Files: conversation contracts, service, composer/conversation, new compact review component, shared brand, frontend types/API.
- [ ] 5. Verify full backend regressions, frontend checks/build and browser route/evidence/review/resume/mobile journeys; live synthetic JPG/PNG/PDF extraction and route follow-up. Record actual failures, latency, quota and explicit unsupported cases. Write support matrix and acceptance report with exact commands and roadmap/core checks.

## Review focus

- Broad affirmation with multiple documents never verifies arbitrary candidates.
- Extraction completed after deletion never resurrects originals or candidates.
- Correction after extraction cannot be overwritten by stale evidence review.
- Choice hints, amount alone and unknown timing never authorize bank/emergency actions.
- Pending/retry/reload preserves one turn, attachments, new drafts and composer access.

## Progress ledger

Baseline: `../.venv/Scripts/python.exe -m pytest -q` from backend: 422 passed in 28.58s. Runtime read-only audit confirmed configured model/key presence and Phase 4 tables. Source research: NCRP FAQ/manual and platform Google account recovery, Gemini image/PDF/pricing primary documentation; evidence limitations and support policy to be documented with source links.

Implementation and local/browser verification complete; task 5 remains open for a clean comprehensive live conversational-quality pass. Real native file extraction and downstream natural review were exercised, but provider timeouts/rejected prose prevented repeatable full acceptance. See [acceptance](../phase5-acceptance.md) and [declared coverage](../phase5-support-matrix.md). No Phase 6 started.
