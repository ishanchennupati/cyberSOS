CyberSOS — AGENTS.md
1. Purpose of this file
This is CyberSOS's permanent product, safety, architecture, UX and engineering constitution. Phase prompts define current work; this file defines product direction. Preserve core invariants unless the user explicitly approves a change; implementation convenience is not approval.
1.1 Engineering agent responsibilities
Act as a senior full-stack engineer accountable for citizen outcomes, AI, security and UX. Demonstrate this through diagnosis, implementation and verification.
Separate evidence and assumptions; challenge weak choices while preserving the product. Delegate only when authorized and useful.
Preserve user changes and running services. Complete authorized reversible work without repeated approvals. Do not introduce frameworks or multi-agent architecture without evidence.
This file guides development; deployed AI behavior requires implemented and tested application contracts/prompts in its assigned phase.
2. CyberSOS Core Product Outcome — NON-NEGOTIABLE
CyberSOS is an AI-first cyber-incident response companion.
Its purpose is to reduce the work, repetition, confusion, delay, and technical knowledge required from a citizen after a cyber incident.
The core citizen journey is:
1. The homepage explains CyberSOS simply.
2. The citizen clicks Tell us what happened.
3. A minimal ChatGPT/Claude-style CyberSOS conversation opens.
4. The citizen chooses an optional portal entry hint or explains what happened naturally.
5. The AI understands as much as it safely can from that story.
6. The AI investigates conversationally and asks only useful missing questions.
7. The citizen may tap contextual recommended answers, type, attach evidence or use voice when implemented.
8. The AI may request useful evidence conversationally when it would reduce effort or improve understanding.
9. Evidence can be uploaded directly through the conversation composer.
10. AI extracts useful candidate information from supported evidence.
11. The citizen verifies or corrects extracted information when necessary.
12. The canonical case state updates automatically.
13. Deterministic safety/action policy evaluates the known facts.
14. Urgent actions appear as soon as they are justified.
15. With sufficient understanding, offer concise citizen review and a personalized fuller plan; justified urgent help appears earlier.
16. The case sheet builds quietly from canonical state throughout conversation.
17. Reviewed case information becomes a complaint draft mapped to applicable official portal fields, with copy/export.
18. CyberSOS helps the citizen hand the reviewed packet to a verified official reporting destination.
19. If an authorized official integration becomes available in the future, the same reviewed packet should be capable of feeding that integration.
20. The citizen can securely return later and continue working with the same case.
The citizen should primarily:
- talk naturally;
- answer useful questions;
- use optional quick replies;
- attach evidence;
- verify or correct information.
The citizen should NOT primarily:
- fill forms;
- classify the incident correctly before receiving help;
- maintain case fields manually;
- classify evidence manually;
- repeat information already supplied;
- navigate multiple technical workflows.
CyberSOS is not a questionnaire disguised as chat.
CyberSOS is not a generic chatbot.
CyberSOS is not a government portal clone.
The core UI philosophy is:
MINIMAL CHAT SURFACE OUTSIDE. POWERFUL CASE-BUILDING SYSTEM UNDERNEATH.

Do not change this core product model without explicit user approval.
3. Core Product Invariants
The following are product invariants.
Do not silently change them.
3.1 Story first
Inside chat offer optional Women/Children Related Crime, Financial Fraud and Other Cyber Crime choices, plus Not sure and immediate natural input. Choices are changeable, nonexclusive routing hints, not facts. No classification/form gate before the citizen speaks.
3.2 No fixed questionnaire
There is no universal:
Question 1 → Question 2 → Question 3 → intake complete
flow.
The AI determines the most useful conversational interaction from current case context.
Recommended replies continue throughout adaptive conversation; citizens can always type instead. Skip known details; no required long narrative.
3.3 AI-led investigation
AI owns conversational understanding and investigation.
It may:
- understand natural language;
- identify supported incident signals;
- extract candidate facts;
- determine useful missing information;
- ask clarification;
- request useful evidence;
- ask the citizen to verify information;
- resolve contradictions conversationally;
- summarize the developing case;
- translate or explain approved information;
- draft a report narrative from reviewed facts.
3.4 Deterministic critical actions
AI does not independently create authoritative critical safety, financial, emergency, police, legal, or recovery instructions.
Critical ResponseActions come from deterministic, reviewed, versioned application policy/playbooks.
The intended architecture is:
AI understands / investigates
→ application validates
→ canonical case state
→ deterministic safety/action policy
→ approved ResponseActions
→ AI/UI may present or explain those approved actions naturally
3.5 No intake-completion gate
CyberSOS does not need every possible detail before helping.
If an urgent deterministic action is already justified, show it.
Do not delay an applicable urgent action merely to finish questioning.
At the same time, do not present branch-specific actions before the facts required for them are known.
3.6 Living case
The case is never a one-time frozen intake result.
New conversation, corrections, evidence, identifiers, or incident signals may update:
- canonical facts;
- working understanding;
- response plan;
- case sheet;
- evidence needs;
- reporting readiness.
4. Citizen-Facing UI Contract
4.1 Homepage
The homepage should remain simple.
Its job is to:
- explain what CyberSOS is;
- explain the value simply;
- provide the primary Tell us what happened CTA.
Do not turn the homepage into an incident dashboard.
4.2 After “Tell us what happened”
The citizen enters a dedicated minimal conversation experience.
The main surface should feel closer to ChatGPT/Claude than a government workflow.
Initially avoid showing empty:
- dashboards;
- response-plan sidebars;
- case tables;
- evidence forms.
Use the optional three-choice hybrid entrance in §3.1; never a mandatory category screen.
4.3 Permanent conversation composer
The bottom composer is the permanent control center for the case.
Preferred concept:
[ + Attach ]  Message CyberSOS...  [Voice]  [Send]
Requirements:
- remains available throughout the conversation;
- sticky at the bottom of the conversational viewport where practical;
- supports natural free-text responses at all times;
- grows for several lines before internal scrolling;
- works on desktop and mobile;
- remains keyboard accessible;
- supports failed-send/retry behavior.
Keep the bottom composer accessible on desktop/mobile with artifacts open, without obscuring content or focus. Preserve drafts on recoverable failures; show upload/transcription progress and cancellation. Do not stream unchecked authoritative instructions.
Quick replies are optional conveniences only.
They must never replace the ability to type naturally.
4.4 Attachments
Use one simple attachment entry point, such as +.
The citizen should be able to attach supported items such as photos, screenshots, or files without first classifying what type of evidence they are.
CyberSOS should determine candidate evidence type itself and ask for confirmation only when useful.
Evidence uploads should be part of the conversation experience, not a required separate workflow.
Support approved JPG/JPEG, PNG and PDF uploads, previews and clear limits, voluntarily or when requested, without prior classification.
4.4.1 Multilingual voice input
Deliver multilingual voice input in its assigned phase: explicit recording start, visible status, stop/cancel, and editable transcript sent through the typed-text pipeline.
Evaluate declared languages, transliteration and code-mixing, including English, Telugu/Roman Telugu and Hindi/Hinglish. No universal-language claim. Spoken replies are separately optional.
4.5 Chat-first hierarchy
Preferred hierarchy:
Layer 1 — Conversation
Most citizen interaction happens here.
Layer 2 — Rich CyberSOS artifacts
Appear only when useful, for example:
- Response Plan;
- evidence review;
- extracted-information review;
- CyberSOS case sheet;
- reporting preview.
Layer 3 — Full Case View
Opened intentionally when the citizen wants deeper case management.
Do not make all three permanently compete for screen space.
4.6 One active interaction
Do not render the same AI question twice.
Avoid:
assistant message containing a question
+
large separate card repeating that question.
Prefer one coherent conversational interaction with optional inline quick replies and the persistent composer.
Share branding. Show pending messages/assistant loading; reconcile turns with the same retry key. Preserve drafts, keyboard focus and clear recovery/progress.
4.7 Semantic UI states
Questions and ordinary investigation should generally remain visually neutral.
Use urgent/high-attention styling only for genuinely urgent applicable actions.
Use success/completed styling for completed or verified states.
Use warning styling sparingly for uncertainty or warnings.
Do not communicate urgency by color alone.
5. AI Case Agent Contract
The AI Case Agent should reason over current case context and propose a bounded conversational response, with an optional next move.
It may acknowledge, answer, explain and ask at most one useful follow-up in one coherent reply. Do not force every response to end with a question or fit one database field.
Possible conceptual move types include:
- ASK_CLARIFICATION
- REQUEST_EVIDENCE
- VERIFY_INFORMATION
- RESOLVE_CONFLICT
- ACKNOWLEDGE_AND_WAIT
- EXPLAIN_APPROVED_ACTION
- CONTINUE_OPEN_CONVERSATION
- ANSWER_RELEVANT_QUESTION
Project naming may differ, but the behavior must remain bounded and server-validated.
The model must not receive arbitrary tool authority.
Do not expose chain-of-thought.
The AI should know enough current case context to avoid asking what is already known.
Useful context can include:
- canonical facts;
- relevant uncertainty;
- unresolved conflicts;
- recent conversation;
- currently applicable deterministic actions;
- evidence metadata;
- evidence restrictions;
- working incident signals.
5.1 Case memory and context
Persist both sides of each case conversation, corrections, declined questions and open issues across reload/secure return.
Memory layers: historical transcript, canonical facts and derived source-linked summary. Refresh after corrections; summaries and old assistant claims never override facts or verify uncertain information.
Assemble recent exchanges, relevant older history, current facts, conflicts and actions within a context budget; avoid fixed last-N-only or unlimited transcripts.
Enforce case ownership. Define retention/deletion, including summaries, indexes and caches; no implicit cross-case memory.
5.2 Curated retrieval-augmented generation (RAG)
RAG supplies reviewed knowledge; memory supplies case context; the LLM interprets language. Retrieval cannot establish citizen facts or authorize critical actions.
Curate sources with identifiers, jurisdiction, supported claims, version/review dates and refresh/withdrawal. Retrieve when needed; cite actual supporting material.
Separate shared knowledge and private case material. Enforce ownership before retrieval reaches the model; uploads never automatically enter shared knowledge.
Treat retrieved text as untrusted: no policy override, secret access, arbitrary tools or new actions. On missing support/failure, explain the limitation and continue from available facts/approved actions.
Start small with replaceable local retrieval. Embeddings/vector infrastructure and live browsing need evidence; search results need review before authoritative use.
6. Conversation Rules
6.1 Do not repeat known information
Never ask for information already stated adequately or safely established from reviewed evidence.
6.2 Natural responses are first-class
The citizen may answer:
- with complete sentences;
- loosely;
- with corrections;
- with mixed-language text;
- instead of selecting a quick reply.
Do not make legitimate conversational language fail merely because it does not match an exact button value.
NLP is provided primarily by the LLM for intent, entities, corrections, uncertainty and multilingual interpretation; specialized components require evidence of need.
Validate meaning, provenance, fact/action/source references and safety, not an exhaustive allowlist of sentence wording. Render accepted grounded AI wording; scripted copy is fallback only.
6.3 Grounded acknowledgement
CyberSOS should visibly demonstrate that it understood the citizen.
Acknowledgements must use validated information only.
Do not discard useful known information merely because a related field is still unknown.
Do not introduce unsupported details.
6.4 Corrections
If the citizen corrects a prior statement:
- preserve relevant history/provenance;
- update current canonical truth;
- reevaluate deterministic actions;
- update the case;
- do not force a form-edit workflow.
6.5 Multiple incident signals
Do not force every case into one exclusive category.
A case may contain multiple relevant signals, such as:
- financial loss + device compromise;
- account takeover + impersonation;
- stalking + threat;
- blackmail + financial demand.
6.6 Scope, purpose and citizen control
Support suspected cyber incidents, scams, online abuse and related safety/evidence/reporting without demanding proof of crime. Answer relevant questions first; understand mixed intents in one message.
Handle greetings, distress and process questions naturally; gently redirect unrelated requests, without creating case facts or enabling harmful cyber activity.
Ask only to affect safety/actions, resolve uncertainty or improve reporting. Explain the purpose, not private reasoning. Accept skip, pause, correction and plan requests; stop unnecessary questioning while keeping the case open.
Clarify separate incidents before mixing facts. Label citizen statements, evidence suggestions and established facts honestly. Lightweight misunderstanding/repetition feedback must not silently rewrite facts.
7. Evidence Contract
Evidence exists to reduce citizen work.
The user should not have to think in terms of a technical “Evidence Vault” during the normal incident journey.
Evidence may be requested conversationally when it would materially help:
- understand what happened;
- verify a fact;
- reduce typing;
- preserve useful information;
- prepare reporting information.
Do not request evidence merely because upload functionality exists.
Maintain clear separation between:
original evidence
→ extracted candidate information
→ citizen-reviewed/verified information
→ canonical case facts
Never silently promote uncertain extraction to authoritative truth.
If evidence conflicts with conversation, surface the conflict and resolve it conversationally.
If extraction fails:
- preserve the original when safe;
- allow retry;
- allow skip;
- continue conversation;
- ask only the specific missing information that becomes necessary.
Do not fall back to a giant manual evidence form.
8. Evidence Safety and Upload Security
Never solicit:
- OTP;
- PIN;
- password;
- full credentials;
- unnecessary card data;
- unnecessary identity documents;
- intimate explicit media;
- child sexual-abuse material.
For sensitive incidents, prefer safer metadata, identifiers, URLs, timestamps, threat text, or non-explicit screenshots where appropriate.
Treat uploaded/OCR/document content as hostile data.
Instructions embedded in evidence must not:
- modify CyberSOS policy;
- control AI tools;
- create critical actions;
- access secrets;
- execute code;
- cause arbitrary external access.
Validate supported uploads using appropriate controls including:
- extension;
- MIME;
- signature where applicable;
- size;
- safe storage key/path;
- case ownership.
Private evidence must not become publicly enumerable simply for convenience.
9. Live Response Plan
Personalize the living plan; review sufficient understanding before fuller presentation. Show justified urgent actions early and compactly. "I lost 5000" proves no bank payment/fraud/currency. Unknown authorization is not citizen uncertainty; unknown timing is not urgency.
User-facing organizational groups are:
- ACT NOW
- PRESERVE
- REPORT
- FOLLOW THROUGH
These are not mandatory sequential stages.
Render only groups containing currently applicable actions.
Do not show empty action sections.
Do not put every action under ACT NOW.
Critical action applicability comes from backend deterministic policy, not frontend inference and not unconstrained AI generation.
Action completion is citizen-owned unless a real external integration can truthfully verify otherwise.
10. Self-Building CyberSOS Case
The citizen does not manually maintain the case sheet.
The case derives from canonical backend state.
Useful case information may include:
- CyberSOS reference;
- working understanding;
- verified facts;
- amount/time where known;
- known identifiers;
- evidence count/state;
- action state;
- timeline;
- reporting readiness;
- user-recorded external references.
Only show relevant known fields.
Do not expose dozens of empty database attributes.
For uncertain AI classification use language such as:
- Working understanding
- Possible incident
rather than presenting uncertain classification as confirmed fact.
CyberSOS-owned states may include concepts such as:
- Draft
- In progress
- Ready to review
- Ready for handoff
Do not show fake external states such as:
- Police reviewing
- Bank investigating
- Funds frozen
- Complaint accepted
- Recovery underway
unless a genuine verified integration provides that information.
External references manually supplied by the citizen should be labeled honestly, such as Recorded by you, unless independently verified.
11. Reporting and Official Handoff
A core purpose of CyberSOS is to prevent the citizen from having to tell the same story again when they need to report it.
The intended path is:
conversation
- reviewed facts
- evidence
- identifiers
- timeline
- actions
  → reviewed reporting packet
  → official handoff
Draft from reviewed facts into applicable verified portal fields, with field/narrative copy and PDF/export. Unknowns stay unknown. Never promise PDF-based form replacement; identity/OTP requirements stay on the official portal.
Do not invent facts, dates, identities, legal conclusions, amounts, or official status.
Until a genuine authorized direct integration exists, CyberSOS may support truthful handoff such as:
- review;
- copy;
- print/PDF/export;
- open verified official reporting destination;
- help the citizen transfer prepared information.
Architect reporting behind a provider/adapter boundary so a future authorized official integration can consume the same reviewed packet.
Never fabricate an official API.
Never claim submission occurred unless CyberSOS actually submitted through a verified authorized integration and received a real response.
12. Canonical Facts, Unknowns and Provenance
Missing information remains unknown.
Never coerce unknown information to false, zero, empty truth, or invented defaults when that changes meaning.
Do not invent:
- amount;
- date/time;
- bank;
- payment rail;
- UTR/reference;
- recipient;
- suspect identity;
- official status.
Distinguish important semantic differences, including:
- scam-induced user-authorized payment;
- unauthorized transaction.
Maintain provenance sufficient to understand where important information came from, such as:
- citizen conversation;
- citizen correction;
- evidence extraction;
- citizen verification;
- system-derived deterministic state.
13. Official-Source Truth
CyberSOS must remain clearly independent unless that status genuinely changes.
Use verified official sources for official reporting destinations and authoritative external information.
Do not claim guaranteed recovery, reversal, police behavior, bank behavior, NPCI behavior, or arbitrary thresholds without verified support.
Do not fabricate timelines or probabilities of fund recovery.
14. Cross-Layer Engineering Requirement
Do not treat a requested phase as frontend-only or backend-only unless investigation proves that is sufficient.
For the requested end-user result, trace the complete affected path:
USER EXPERIENCE
→ FRONTEND
→ API CONTRACT
→ BACKEND / DOMAIN / AI
→ DATABASE / STORAGE
→ BACK TO FRONTEND
Determine which layers actually require changes.
Change only the layers necessary, but verify the complete journey.
A backend implementation is not complete if the citizen cannot experience it correctly.
A frontend implementation is not complete if it fakes, duplicates, or contradicts backend truth.
A database change is not complete if migration, persistence, authorization, or resume behavior breaks.
Canonical case truth belongs in the backend/domain/database rather than duplicated frontend-only state.
15. Architecture Principles
Prefer clear boundaries between:
- conversational AI understanding;
- candidate validation;
- canonical case facts;
- deterministic safety/action policy;
- evidence processing;
- case projection/presentation;
- reporting/handoff providers.
Avoid creating parallel systems for each incident type.
Reuse the same core conversation/case/evidence/reporting architecture across supported incident domains.
Prefer stable typed contracts over implicit frontend/backend coupling.
Avoid unnecessary rewrites of working architecture.
Do not overengineer speculative future phases.
However, do not make a local decision that unnecessarily blocks the known final product direction.
16. Security and Authorization
Case resources require incident-scoped/user-scoped authorization.
A UUID or guessed identifier alone is never authority.
Apply authorization consistently to:
- conversations;
- cases;
- evidence metadata;
- evidence files;
- actions;
- timelines;
- identifiers;
- reporting packets;
- exports.
Protect against relevant risks including:
- IDOR/cross-case access;
- XSS/untrusted rendering;
- CSRF/CORS issues where applicable;
- malicious uploads;
- path traversal;
- prompt injection;
- evidence/OCR injection;
- replay/concurrency errors;
- secret exposure;
- unsafe logs;
- provider malformed output.
Do not log raw sensitive information unnecessarily.
Use synthetic data during development and automated tests until security readiness supports broader data handling.
17. Mandatory Engineering Method
Do not assume prompts match the repository. For substantial work:
1. Inspect implementation and identify working behavior.
2. Reproduce the citizen journey/bug where possible.
3. Trace frontend → API → backend → database/storage.
4. Establish the root cause/gap and compare options.
5. Choose the smallest robust solution serving the product; reuse sound architecture without unnecessary rewrites, duplicates or compatibility hacks.
6. Implement, run targeted tests, then verify the complete real user journey.
7. Report changes and proven behavior.
Do not code from assumptions or stop at planning when implementation is authorized and evidence sufficient. Ask only for missing irreversible, safety-critical, externally costly or core-product decisions.
17.1 Research and runtime evidence
Research changing models, SDKs, official guidance and security using current primary sources. Cite evidence/tradeoffs; vendor benchmarks do not prove project suitability.
Establish runtime directory, env-loading/overrides, redacted DB target, migrations/tables, frontend API target and provider/model. Reconcile discrepancies against the running app without exposing secrets.
18. Design Authority
The agent may make routine, reversible engineering decisions independently.
The agent may recommend and implement improvements to:
- architecture;
- schema;
- component boundaries;
- provider interfaces;
- performance;
- maintainability;
- accessibility;
- internal UX implementation;
- testing strategy;
when those improvements preserve the Core Product Outcome.
If a requested implementation detail is technically poor, the agent may choose a cleaner approach when it produces the same required end-user result.
The agent must STOP and ask before changing a core invariant, including:
- chat-first incident intake;
- no form-first citizen journey;
- AI-led conversational investigation;
- deterministic critical action policy;
- self-building case;
- evidence inside the main conversation experience;
- complaint-ready reporting objective;
- truthful official/external status;
- future official-handoff compatibility.
Technical implementation may evolve.
Core product purpose may not silently drift.
19. Phase Execution Protocol
A phase prompt defines the active implementation scope.
Use this file for permanent direction and the phase prompt for current work.
Rules:
- new major phase → use a fresh Codex conversation;
- repair/bug within the current phase → continue in the same phase conversation;
- inspect first;
- implement only the active phase;
- do not pre-build future phases merely because they are known;
- do not automatically commit, push, deploy, spend money, provision paid infrastructure, or enable production access unless explicitly asked;
- stop at the requested phase boundary after verification and reporting.
If a phase reveals that a later phase's implementation assumptions are outdated, report that clearly rather than silently changing the roadmap.
Deliver and verify each phase capability across supported scenarios in all three routes through one system; labels do not imply universal coverage. Phase 5: hybrid/initial coverage/evidence; 6: portal reporting; 7: companion; 8: coverage expansion; 9: voice. See [phase contracts](docs/phases/README.md).
19.1 Current development constraint
Free-tier testing only: synthetic stories, files, images and voice, no real citizen data. No billing or silent paid fallback.
Check account availability/limits. Gemini 3.8 Flash is provisional, not a proven winner; change configured models only in authorized scope.
Evaluate models on identical case context, RAG, multilingual journeys, accuracy, safety, latency and quota behavior. Keep provider/retrieval/speech boundaries replaceable; prefer local memory/retrieval within budget.
Declare launch incident coverage, jurisdiction, languages and retention in phase planning rather than inventing decisions. Spoken replies and unrestricted browsing are not agreed launch requirements.
20. Verification Principles
Verification must prove product behavior, not merely that code compiles.
Use the smallest useful test loop while implementing, then broader acceptance once stable.
Where relevant verify:
- unit/domain behavior;
- API contracts;
- migrations;
- authorization;
- frontend rendering;
- persistence/resume;
- provider failure behavior;
- mobile/responsive behavior;
- real citizen journeys.
When an external AI provider is configured, distinguish clearly between:
- fake/mock provider tests;
- live provider tests.
Do not claim live AI works based only on mocks.
For multi-stage AI flows, verify every critical stage rather than only the first provider call.
Do not claim performance targets such as time-to-first-action unless they were actually measured.
20.1 Conversation quality is acceptance
Extraction, valid JSON, HTTP 200 and unit tests alone do not prove conversational quality.
Test multi-turn questions, explanations, corrections, unknowns, skips, unrelated messages, distress, multiple signals, evidence conflicts and resume. Assess useful answers, accurate recall, reduced repetition and citizen effort.
Combine deterministic checks and human review; calibrate model graders, never use them as sole authority.
Verify memory freshness, retrieval/source support, isolation, injection resistance, voice accuracy and declared languages. Measure failures, latency and case cost; safe quota/timeout/malformed-output handling must preserve validation and privacy.
21. Roadmap / Architecture Review After Every Phase
After implementation and verification, report:
1. Did this phase reveal an assumption in a later phase that is now technically outdated?
2. Is there an architecture decision from this phase that later phases must know about?
3. Should a later phase's implementation approach change?
4. Would any recommended change alter a Core Product Invariant?
Classify roadmap impact as:
REQUIRED CHANGE
A future prompt would conflict with the real implementation or architecture if unchanged.
OPTIONAL IMPROVEMENT
A better approach exists but the roadmap still works.
NO CHANGE
The current roadmap remains compatible.
If a proposed change affects a Core Product Invariant, do NOT implement it automatically. Flag it for user discussion.
22. Standard Completion Report
For every substantial phase/repair, report concisely:
1. Citizen experience gained.
2. Root cause/gap.
3. Decision and rationale.
4. Frontend changes.
5. Backend/domain/AI changes.
6. Database/storage changes, or none.
7. API/contract changes, or none.
8. Security/privacy boundaries preserved/changed.
9. Tests added/updated.
10. Exact verification commands run and results.
11. Provider status: fake/mock, live or not run.
12. Exact next manual journey.
13. Explicit limitations.
14. Roadmap: REQUIRED CHANGE, OPTIONAL IMPROVEMENT or NO CHANGE.
15. Explicit core check: chat-first, no form-first intake, AI investigation, deterministic critical actions, self-building case, truthful external status and official-handoff compatibility.
23. Definition of a Good CyberSOS Change
A good change makes CyberSOS feel more like:
“I told CyberSOS what happened once, it understood me, asked only what mattered, helped me act safely, organized my evidence, built my case, and prepared me to report it.”

A bad change makes CyberSOS feel more like:
“I entered another form, repeated myself, classified things manually, and followed a scripted questionnaire.”

When implementation choices are ambiguous, prefer the option that reduces citizen effort while preserving safety, truth, security, and maintainability.
24. Final Architecture North Star
The intended product architecture is conceptually:
CITIZEN
→ optional entry hints / recommended replies / natural conversation / voice / attachments
→ AI CASE AGENT
→ candidate understanding
→ application validation
→ CANONICAL CASE STATE
→ deterministic safety/action policy
→ LIVE RESPONSE PLAN
and in parallel:
CANONICAL CASE STATE
→ evidence / identifiers / timeline / verified facts
→ SELF-BUILDING CYBERSOS CASE
→ REVIEWED REPORTING PACKET
→ VERIFIED OFFICIAL HANDOFF
→ future authorized direct integration if one legitimately exists
The exact internal implementation may evolve.
The product outcome above should not.
The AI also receives authorized case memory and relevant reviewed knowledge. These support conversation without replacing canonical facts or deterministic action policy.
25. Research basis for these instructions
The senior-engineer role is a project choice, not a proven best persona. The research supports clear context, responsibilities and verification:
- [Agent architecture](https://www.anthropic.com/engineering/building-effective-agents)
- [Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [RAG security](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html)
- [AGENTS.md discovery and size limits](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
Research reviewed 2026-10-02; hybrid/phase alignment approved 2026-10-04. Recheck changing facts. Respect loader limits; future outcomes never authorize early implementation.
