# Deterministic Action Engine

The Action Engine is deterministic. Form or extraction data may populate structured incident fields, but urgency is calculated only by `app.rules.action_rules.determine_action_plan`.

## Financial fraud factors

- **Time:** under 24 hours starts at `critical`; 24-72 hours starts at `high`; 72 hours-7 days starts at `medium`; 7 days or more starts at `low`.
- **Transaction status:** `pending` sets the recovery window to `open` and raises urgency to `critical`. Completed transactions retain the age-based priority.
- **Ongoing risk:** continuing unauthorized activity, remote access, or possible additional loss raises urgency to `critical`. Account compromise, exposed credentials, shared OTP/PIN/password raises it to at least `high`.
- **Financial severity:** configurable bands are `<₹10,000` low, `₹10,000-₹49,999` medium, `₹50,000-₹99,999` high, and `>=₹100,000` critical. Severity is separate from urgency; amount alone does not raise urgency.
- **Recovery window:** recent incidents are `open` or `uncertain`; incidents at least seven days old are `likely_expired`. This describes time sensitivity, not a recovery guarantee.

When rules conflict, the highest urgency wins: `critical > high > medium > medium_low > standard > low`. Every result includes machine-readable factor, rule ID, explanation, and contribution fields.

## Women and children crimes

Existing safety, subtype, affected-person, content, and threat answers are reused. Follow-up questions appear for blackmail/intimate-content and stalking reports. Immediate physical danger is `critical`; active violence threats, blackmail, stalking access, escalation, and active threats are elevated according to their combination. A minor involved in an active threat or exploitation condition is at least `high`. A baseline report without active risk remains `low`.

## Other cyber crimes

Existing subtype, account access, active-control, sensitive-information, phishing, malware, and ransomware answers are reused. Continuing unauthorized activity, active account takeover, or active remote access is `critical`; exposed credentials or sensitive data is at least `high`; ransomware is `high` or `critical` when activity is ongoing. A resolved compromise is not automatically `critical`.

All category evaluators return the same urgency, risk, recovery-window, and structured-reason format. Category action items continue to come from the existing service action builders.