# Repository cleanup and structure plan

User scope: delete unnecessary files, simplify the existing codebase, and prepare
reviewable local changes for the user to push. No commit/push, new features or
Phase 2. Preserve existing private cases, evidence, backups and local environment.

- R1 hygiene: remove confirmed unreferenced StepCrimeCategory/StepWomenChildrenRedirect,
  obsolete test.db files, regenerable caches/metadata and empty docs/docs. Keep
  migrations, synthetic fixtures, locks, historical evidence and active data.
- R2 backend separation: move complaint formatting/labels into incident_presentation.py
  and legacy nonfinancial responses into legacy_incident_service.py. Keep
  incident_service.py focused on persistence/triage orchestration and current
  versioned financial plan integration. Preserve existing import contracts.
- R3 frontend separation: move guided intake state, persistence, validation and
  API orchestration into features/incident-intake/use-incident-flow.ts. Leave
  app/incident/start/page.tsx responsible for rendering. Consolidate identical
  time-change callbacks. No conversation controller or UI redesign.
- R4 verification/documentation: targeted checks during the moves, then one final
  backend suite, frontend lint/types/build and synthetic financial browser. Use
  a separate build directory if the user's development server is running.
  Check secret/generated-file eligibility, existing imports and final diff.

Risks: circular imports around complaint/summary/evidence services; hidden callers
of old service helpers; moving React state may alter closure behavior. Use direct
imports at real consumers, retain public helper exports and exercise existing
golden/complaint/API/browser regressions. Avoid rebuilding the live .next directory.
