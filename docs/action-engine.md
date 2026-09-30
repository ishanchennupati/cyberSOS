# Phase 1 deterministic financial response engine

app/domain/playbooks.py is the single critical-action implementation. Registry
keys are (playbook_id, version); current version is 1.0.0, fact schema 1.0.
Approved scam transfers, unauthorized transactions and unknown authorization
select distinct bank action IDs. Approved scam transfers never receive RBI
unauthorized-transaction guidance. No AI or frontend rule selects critical actions.

Known ongoing access/loss adds report_ongoing_access first. Then the appropriate
bank action, call_1930, preserve_evidence, file_cybercrime and record_follow_up.
Urgent reporting may precede preservation. Actions have stable IDs, lifecycle
phase, priority/order, instruction/reason, minimum facts, applicability, source
reference and user completion permission. Reporting fields never gate actions.

Timing bands remain product urgency heuristics: under 24 hours critical, under
72 hours high, under seven days medium, older low; unknown timing high. Known
ongoing loss/remote access or pending payment raises urgency; account/credential
exposure raises at least high. These do not predict recovery or official timing.
Actions remain available for old incidents and missing amount/reference/evidence.

Fact priorities are CRITICAL, SUPPORTING, REPORTING and OPTIONAL. Explicit unknown
and null remain unknown; false is an established answer. next_unanswered_fact is
only a foundation for future question selection. No conversation controller/UI.

Persisted plans retain exact validated facts, versions, actions and source
snapshots. Corrections create revisions. Reads do not reevaluate old snapshots.
Completion is user_self_report for that plan/action, never bank/government status.
No recovery score/window/probability field exists in active contracts. Legacy
storage columns remain without exposure. Deprecated helper tests use wrappers
that delegate to this engine; nonfinancial rules are unchanged legacy behavior.

Golden scenarios live in backend/tests/fixtures/scenarios.yaml. Tests protect
stable IDs/order, reporting independence, unknown semantics, source integrity,
AI exclusion, corrections, completion and case isolation. See verification.md.
