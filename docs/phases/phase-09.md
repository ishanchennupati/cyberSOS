# CYBERSOS — PHASE 9
# Multilingual voice input and reviewed language experience

Read root AGENTS.md and [shared contract](README.md) completely. Inspect actual
Phase 8 composer, stored language/context and provider support. Do NOT begin Phase 10.

## End-user result

Citizens type or speak within the same CyberSOS conversation. Reviewed targets are
English, Telugu and Hindi, with Roman Telugu, Telugu+English and Hinglish tests.
Canonical facts and action policy remain language-independent.

Deliver voice across supported scenarios in all three entry points, preserving
the hybrid flow: citizens can tap an entry/recommended answer, type, attach evidence
or speak. Do not build separate voice journeys per route or require classification
before recording. Earlier phases must not display a fake working microphone.

## Required implementation

1. Audit separately language understanding, generation, UI localization, deterministic
   action translations and stored language preferences. A understood sentence is not
   proof of full multilingual support. Publish only tested language/browser support.
2. Extend the Phase 4 composer with one microphone entry point and a replaceable
   speech-input adapter. Research actual free-tier access, browser capture formats,
   provider privacy and limits; never silently use a paid speech service.
3. Explicit permission/start → visible recording → stop/cancel → editable transcript
   → citizen Send → same existing message/validation/case pipeline. No silent
   transcription-to-fact promotion, background listening or separate voice assistant.
   Cancellation and retry must not duplicate recordings/messages or mutate facts.
4. Preserve amounts, dates, identifiers, negatives and authorization meaning through
   transcription. Uncertain terms receive review; do not translate away ambiguity.
5. Adapt natural replies and curated retrieval to declared language needs. Source
   support remains required; same case memory across language changes. User language
   preference is not an incident fact and must not imply a person's identity/location.
6. Review translations of authoritative actions to preserve policy meaning; free-form
   explanation cannot introduce new safety procedures. Localize UI/status/error and
   review surfaces consistently, not only assistant text.
7. Minimize raw audio retention and document actual upload/storage/provider behavior.
   Deleted audio/transcripts and derived private references follow lifecycle policy.
   Spoken AI replies/TTS are optional and excluded unless separately authorized.

## UI requirements

- Accessible microphone with recording indicator, stop/cancel, transcript edit and
  clear review-before-send. Typing and attachment controls remain usable.
- Useful language control/preferences without mandatory language selection before
  the first story. Correct script rendering, wrapping and mobile keyboard behavior.
- Mic denied/unavailable, unsupported recording, transcription/quota/network failure
  leave typing functional and preserve safe drafts; no fake working voice control.

## Verification and acceptance

Verify live synthetic voice journeys for each supported entry point, including
Not sure/direct-story entry, recommended replies, corrections, plan review and
reporting. Reuse the shared route-by-scenario acceptance matrix.

Test synthetic speech with accents, background noise, code-mixing, names, ₹ amounts,
dates and identifiers. Correct a transcript before Send and prove only corrected
text reaches canonical facts. Test denial, cancel, failure, duplicate send, expiry
and deletion on supported browsers/devices where available; record unavailable
device testing explicitly.

Verify speech provider live separately, then live understanding/reasoning, same
case memory/actions, evidence/report interaction and secure resume. Structured
language review must assess meaning, not only matching translated strings. No
universal language claim or new voice case subsystem. Stop; no Phase 10.
