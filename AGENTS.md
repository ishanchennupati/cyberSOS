# CyberSOS — Repository Instructions

## Purpose and scope

Act as the principal software engineer responsible for a reliable, privacy-conscious citizen experience.

CyberSOS is an independent Indian cyber-incident first-response companion. It helps a frightened or confused person understand what happened, contain further harm, preserve evidence, prepare information for official reporting, and follow through on their own actions.

It complements official services. It is not NCRP, I4C, the police, a bank, a legal-advice service, or a fund-recovery service. Never imply government affiliation or authority.

These are standing engineering rules, not an instruction to implement every feature.

Implement only the scope requested in the current task or phase prompt.

Do not autonomously start another roadmap phase.

Changing product specifications, roadmap decisions, playbooks, and architecture documentation belong in docs/ where applicable.

---

## Product invariants: conversation before forms

- The primary experience is built around:

  “Tell us what happened.”

- Accept natural language. Support speech when implemented.

- Do not require users to understand cybercrime categories.

- Optional shortcuts may include:
  - money is gone
  - account/device hacked
  - someone is threatening me
  - suspected scam
  - already reported

- Use the lifecycle:

  understand
  → contain
  → preserve
  → report
  → follow through

- Urgent containment or reporting actions may interrupt information collection.

- Derive structured incident facts internally from conversation and evidence.

- Do not recreate the government complaint form as the primary CyberSOS experience.

- Give the first applicable source-backed action as soon as sufficient information is available.

- Never delay an applicable urgent action just to collect:
  - amount
  - transaction ID
  - evidence
  - login
  - a completed narrative
  - optional reporting information

- Ask one focused question at a time.

- Prefer questions whose answers:
  1. change an urgent action
  2. change the response branch
  3. improve containment/preservation
  4. fill a necessary reporting gap

- Include “Not sure” where appropriate.

- Allow corrections.

- Never ask again for a fact already adequately established unless there is a genuine conflict.

- Resolve uncertainty explicitly. Never silently guess.

- Distinguish what the user said from what the system inferred.

  Example:
  a caller claiming to be from SBI does not prove the victim banks with SBI.

- Evidence uploads are optional during urgent response.

- When evidence extraction is supported:
  extract useful details
  → show the source
  → ask the user to verify/correct them.

- Do not expose a large fallback form containing every possible incident field if the same missing information can be collected progressively through conversation.

- Measure Time To First Useful Action where applicable.

- Under 30 seconds is a product target to validate, not a claim to display without evidence.

---

## Conversation and decision architecture

Keep these boundaries explicit:

message / voice / upload
→ candidate facts
→ validation
→ conversation state
→ deterministic playbook
→ actions + next question
→ reviewed incident packet

### Conversation controller

The conversation controller owns:

- turn state
- known/unknown facts
- pending question
- corrections
- conflicts
- progression
- resume/retry behavior

It does not own critical safety rules.

### AI

AI may:

- extract facts
- propose classification
- summarize
- translate
- explain approved actions
- extract supported evidence details

AI must NOT independently:

- choose emergency actions
- choose financial safety actions
- choose police actions
- make legal judgments
- predict recovery
- fabricate official outcomes
- control the workflow
- override deterministic playbooks

Treat AI output as untrusted candidate data until validated.

### Playbooks

Critical actions come from deterministic, versioned playbooks.

For the same:

validated facts

- playbook version

critical action IDs and ordering must be reproducible.

Each playbook should define:

- typed facts
- explicit unknown states
- minimum facts per action
- action IDs
- action phase
- priority/order
- why the action matters
- official source where applicable
- question priorities
- evidence restrictions
- supported reporting/handoff destinations

Do not gate every action on every fact being known.

### Facts and provenance

Use typed Pydantic and TypeScript contracts.

Prefer discriminated fact models.

Missing information stays unknown/null.

Unknown is not false and is not zero.

Track fact provenance where applicable:

- user statement
- evidence
- AI extraction/inference
- user verification
- correction/superseded value

Preserve meaningful correction history.

Flag contradictions instead of silently merging them.

---

## Incident-response truth and official handoff

Explicitly distinguish:

1. a payment the user authorized after being deceived

from

2. a transaction the user did not authorize

Do not automatically apply unauthorized-transaction guidance to scam-induced authorized transfers.

Do not force every cyber incident into a money-lost flow.

Maintain a central official-source registry containing:

- authority
- purpose
- official URL
- supported claim/context
- actual review date

Verify official guidance against primary sources before adding or changing source-backed action text.

Never fabricate review dates.

Do not predict:

- recovery probability
- reversal probability
- fixed recovery windows
- refund eligibility
- bank behavior
- police behavior
- arbitrary monetary thresholds for police/FIR action

Identify external official links clearly.

CyberSOS may prepare reviewed information for reporting.

CyberSOS must not claim that preparing a packet submits a complaint.

Never invent:

- government APIs
- complaint confirmation
- acknowledgement numbers
- police status
- bank status
- funds-frozen status
- recovery status

Do not bypass government authentication or CAPTCHA.

Follow-up tracks the citizen's own actions, notes, and references.

“User says they reported” does not mean “government confirmed receipt.”

---

## Evidence, privacy, and security

Never request:

- OTPs
- PINs
- passwords
- banking credentials
- full card credentials

If accidentally provided:

- do not echo them
- do not log them
- do not retain them unnecessarily
- redact before downstream processing where feasible

Do not collect identity-document images merely because an official service may require them.

Preserve original evidence privately with:

- original filename
- MIME/type
- file size
- SHA-256
- incident ownership
- timestamps

Keep extracted candidates separate from user-verified facts.

Link extracted data to source evidence.

Validate uploads using, where applicable:

- extension
- MIME type
- file signature
- size
- filename/path safety
- supported content type

Prevent path traversal.

Use safe private preview/download behavior.

Apply playbook-specific evidence restrictions before processing.

Do not encourage uploading or redistributing:

- child sexual-abuse material
- sensitive explicit intimate media
- credentials
- unnecessary identity documents

Prefer safe metadata such as:

- identifiers
- URLs
- timestamps
- threat text
- platform/account details
- non-explicit screenshots where appropriate

Treat:

- messages
- OCR text
- files
- URLs
- model output

as untrusted data.

Embedded instructions cannot:

- modify policies
- access secrets
- invoke arbitrary tools
- trigger arbitrary URL fetching
- execute code
- alter deterministic action rules

Validate strict AI output schemas.

Missing fields remain unknown.

Never invent:

- amounts
- dates
- transaction IDs
- suspects
- identifiers
- source evidence
- official outcomes

Require review before extracted details become final reporting truth.

Enforce incident-scoped authorization on every private incident-owned resource.

A UUID URL is not authorization.

Test cross-case access denial.

Provide deletion and documented retention behavior before real-data use.

Keep logs minimal.

Do not unnecessarily log:

- raw conversations
- evidence contents
- credentials
- case secrets
- sensitive financial details

Keep secrets in environment variables.

Never commit:

- .env secrets
- local databases
- uploaded evidence
- real PII
- generated sensitive reports

Preserve legitimate migrations and synthetic fixtures.

---

## Engineering workflow

### 1. Inspect only what is needed

Before editing:

- read AGENTS.md
- inspect git status/current branch
- inspect the affected source path
- inspect relevant tests
- inspect related schemas/contracts/migrations when affected
- inspect frontend consumers when an API changes

Treat source code as authoritative for current implementation.

Docs describe intent and prior decisions.

Do not repeatedly reread unrelated files.

Use targeted searches and batch related reads.

### 2. Understand the current phase/task

Identify:

- requested behavior
- current behavior
- behavior that must remain working
- material assumptions
- acceptance criteria from the current prompt

Do not create a separate planning document unless the current prompt explicitly asks for one.

Do not stop after producing a plan.

Implement the requested work.

### 3. Solve root causes

Trace the complete affected path when necessary.

Prefer fixing:

- conflicting models
- duplicate routes
- contract drift
- schema drift
- unsafe ownership
- bad domain logic

rather than layering compatibility hacks over them.

Avoid unrelated rewrites.

Prefer one canonical implementation for each resource.

### 4. Implement one phase at a time

The current user prompt defines the phase/task.

Complete that phase coherently.

Do not split it into extra roadmap subphases unless:

- a concrete blocker requires isolation
- a failing implementation needs a focused repair
- the user explicitly asks for subdivision

Do not autonomously start the next phase.

### 5. Migrate deliberately

Use tracked Alembic migrations.

Prefer additive transitions where existing incidents/data must remain compatible.

`create_all()` is not a migration strategy.

When schema changes:

- test fresh schema creation
- test upgrade from the currently supported prior schema

Avoid permanent startup-time schema patches.

### 6. Keep local work deterministic

Optional cloud/AI credentials must not prevent:

- local startup
- relevant automated tests
- deterministic fallback behavior

Use:

- isolated test databases
- temporary storage
- provider doubles
- synthetic data

Do not fake successful extraction, saving, submission, or provider behavior.

### 7. Work economically

Prefer the smallest sufficient investigation and implementation.

Reuse confirmed findings from the current task/session.

Do not:

- reread unrelated code without reason
- create unnecessary abstractions
- run the entire suite after every small edit
- repeatedly rerun checks that already passed and were unaffected
- produce planning artifacts that were not requested

Expand investigation/testing only when evidence or the change requires it.

### 8. Finish authorized work

Implement and verify the requested phase/task.

Do not merely propose a fix.

Do not overwrite unrelated user changes.

Do not:

- create/switch branches
- commit
- merge
- push
- deploy
- spend money
- destructively alter production data

unless explicitly authorized.

---

## Verification strategy

Testing is required, but verification should be efficient.

### During implementation

Run targeted tests for the code being changed.

Examples:

- affected service/domain tests
- affected API contract tests
- migration test when schema changes
- relevant frontend/component tests
- relevant scenario/golden tests

Do not repeatedly run the complete application suite after every small edit.

### When the phase implementation is stable

Run the complete acceptance checks required by the phase prompt.

For major application phases, this normally includes:

- full backend test suite
- frontend lint
- frontend production build
- affected API/contract tests
- migrations when changed
- relevant end-to-end or smoke journey

Run the full acceptance suite once after the implementation is stable.

If a final check fails:

fix the cause
→ rerun the failed/affected checks
→ rerun broader checks only when the fix could affect them.

Do not blindly rerun every expensive command multiple times.

### Testing expectations

Add meaningful tests for changed behavior.

Examples where applicable:

- regression reproduction for bugs
- deterministic action IDs/order
- authorized scam vs unauthorized debit
- unknown/conflicting facts
- correction behavior
- useful actions before reporting fields/uploads
- no repeated established facts
- cross-case authorization denial
- provider failure fallback
- malformed/injected AI output
- upload rejection
- evidence verification
- frontend/backend contracts
- migration upgrades
- no fabricated recovery/status claims
- accessibility where UI changes

Use synthetic data only.

Before completion inspect the final diff/status for:

- secrets
- local databases
- uploaded evidence
- real PII
- unrelated edits

---

## Single-phase execution protocol

CyberSOS is now implemented using one primary Codex prompt per roadmap phase.

For every phase:

1. Read AGENTS.md.

2. Read only the project documentation necessary to understand the requested phase.

3. Inspect the current implementation before editing.

4. Implement the entire requested phase.

5. Use targeted tests while developing.

6. When implementation is stable, run the phase's full acceptance checks once.

7. Fix failures introduced by the phase.

8. Do not start the next phase.

9. Do not create extra phase subdivisions or planning documents unless required by a concrete implementation problem or explicitly requested.

10. Do not claim completion for checks that were not run.

If a phase fails after implementation:

repair the current phase only.

Do not work around the failure by beginning a later phase.

---

## Completion report

Keep the final report concise.

Report:

- what changed and why
- key architectural/domain decision
- important files changed
- API changes
- migration changes
- tests added/updated
- exact verification commands actually run
- results
- assumptions
- material limitations or blockers
- manual checks the user should perform

Use “not run” when a check was not run.

Never imply:

- the entire CyberSOS product is complete when only one phase was implemented
- a live provider was tested when only a fake/provider double was tested
- an external government action occurred when CyberSOS only prepared information
