export type IncidentType =
  | "women_children"
  | "financial_fraud"
  | "other_cyber_crime"
  | "phishing"
  | "identity_theft"
  | "social_media"
  | "job_scam"
  | "other"
  | "other_cyber_crime";

export type TopLevelCrimeCategory =
  | "women_children"
  | "financial_fraud"
  | "other_cyber_crime";

export type OtherCrimeSubCategory =
  | "online_social_media"
  | "ransomware"
  | "hacking"
  | "cryptocurrency"
  | "online_trafficking"
  | "online_gambling"
  | "any_other";

export type PaymentMethod =
  | "upi"
  | "debit_card"
  | "credit_card"
  | "net_banking"
  | "wallet"
  | "unknown"
  | "bank_transfer"
  | "card";

export type Urgency = "critical" | "high" | "medium" | "medium_low" | "standard" | "low";

export type IncidentStatus =
  | "draft"
  | "triage_started"
  | "action_required"
  | "report_prepared"
  | "submitted"
  | "closed";

export interface IncidentCreatePayload {
  conversation_first?: boolean;
  incident_type: IncidentType;
  incident_subtype?: string | null;
  affected_person_type?: string | null;
  platform?: string | null;
  account_type?: string | null;
  immediate_danger?: boolean | null;
  threat_or_blackmail?: boolean | null;
  content_still_online?: boolean | null;
  account_access?: string | null;
  attacker_active?: boolean | null;
  sensitive_information_exposed?: boolean | null;
  evidence_types?: string[] | null;
  other_crime_sub_category?: OtherCrimeSubCategory | null;
  payment_method: PaymentMethod;
  amount?: number | null;
  incident_time?: string | null;
  details?: Record<string, unknown> | null;
}

export interface TriagePayload {
  authorization?: "authorized" | "unauthorized" | "unknown";
  incident_type: IncidentType;
  incident_subtype?: string | null;
  affected_person_type?: string | null;
  platform?: string | null;
  account_type?: string | null;
  immediate_danger?: boolean | null;
  threat_or_blackmail?: boolean | null;
  content_still_online?: boolean | null;
  account_access?: string | null;
  attacker_active?: boolean | null;
  sensitive_information_exposed?: boolean | null;
  evidence_types?: string[] | null;
  other_crime_sub_category?: OtherCrimeSubCategory | null;
  occurred_at: string;
  amount?: number | null;
  payment_method: PaymentMethod;
  transaction_id?: string | null;
  transaction_status?: "pending" | "completed" | "unknown" | null;
  is_account_compromised?: boolean;
  is_credentials_exposed?: boolean;
  is_otp_shared?: boolean;
  is_pin_shared?: boolean;
  is_password_shared?: boolean;
  is_remote_access_granted?: boolean;
  unauthorized_activity_continuing?: boolean | null;
  potential_additional_loss?: boolean | null;
  account_secured?: boolean;
  evidence_available?: boolean | null;
  details?: Record<string, unknown> | null;
}

export interface Incident {
  authorization: "authorized" | "unauthorized" | "unknown";
  playbook_id?: string | null;
  playbook_version?: string | null;
  fact_schema_version?: string | null;
  plan_revision?: number;
  id: string;
  incident_type: IncidentType;
  payment_method: PaymentMethod;
  amount: number | null;
  incident_time: string | null;
  occurred_at: string | null;
  transaction_id: string | null;
  transaction_status: string | null;
  description: string | null;
  is_account_compromised: boolean | null;
  is_credentials_exposed: boolean | null;
  is_otp_shared: boolean | null;
  is_pin_shared: boolean | null;
  is_password_shared: boolean | null;
  is_remote_access_granted: boolean | null;
  unauthorized_activity_continuing: boolean | null;
  potential_additional_loss: boolean | null;
  account_secured: boolean | null;
  evidence_available: boolean | null;
  incident_subtype: string | null;
  affected_person_type: string | null;
  platform: string | null;
  account_type: string | null;
  immediate_danger: boolean | null;
  threat_or_blackmail: boolean | null;
  content_still_online: boolean | null;
  account_access: string | null;
  attacker_active: boolean | null;
  sensitive_information_exposed: boolean | null;
  evidence_types: string[] | null;
  urgency_score: number | null;
  other_crime_sub_category: OtherCrimeSubCategory | null;
  details: Record<string, unknown> | null;
  urgency: Urgency;
  urgency_computed_at: string | null;
  severity: Urgency | null;
  ongoing_risk: Urgency | null;
  urgency_reasons: UrgencyReason[] | null;
  status: IncidentStatus;
  created_at: string;
  updated_at: string;
}

export interface ActionItem {
  critical: boolean;
  instruction: string;
  phase: "CONTAIN" | "PRESERVE" | "REPORT" | "FOLLOW_UP";
  priority: Urgency;
  order: number;
  minimum_facts: string[];
  applicability: string;
  official_source_id: string | null;
  can_mark_complete: boolean;
  id: string;
  title: string;
  why: string;
  phone: string | null;
  url: string | null;
  url_label: string | null;
}

export interface ActionPlan {
  playbook_id?: string | null;
  playbook_version?: string | null;
  fact_schema_version?: string | null;
  plan_revision?: number;
  urgency: Urgency;
  urgency_label: string;
  core_message: string;
  large_amount: boolean;
  actions: ActionItem[];
  complaint_draft: {
    body: string;
  };
  severity?: Urgency | null;
  ongoing_risk?: Urgency | null;
  urgency_reasons?: UrgencyReason[];
}

export interface UrgencyReason {
  factor: string;
  rule_id: string;
  human_readable_reason: string;
  severity_contribution: Urgency;
}

export const INCIDENT_TYPE_OPTIONS: {
  id: IncidentType;
  label: string;
  description: string;
  enabled: boolean;
}[] = [
  {
    id: "financial_fraud",
    label: "UPI / financial fraud",
    description: "Money sent or taken through UPI, a card, net banking, or a wallet.",
    enabled: true,
  },
  {
    id: "phishing",
    label: "Phishing / fake website",
    description: "A fake link, OTP trap, or lookalike site.",
    enabled: true,
  },
  {
    id: "identity_theft",
    label: "Identity theft",
    description: "Someone used your KYC, Aadhaar, or PAN without you.",
    enabled: true,
  },
  {
    id: "social_media",
    label: "Social media / impersonation",
    description: "A hacked or fake profile used to cheat you or others.",
    enabled: true,
  },
  {
    id: "job_scam",
    label: "Job or investment scam",
    description: "A fake job, trading tip, or 'guaranteed return'.",
    enabled: true,
  },
  {
    id: "other_cyber_crime",
    label: "Other cyber crime",
    description: "Another kind of cyber incident.",
    enabled: true,
  },
];

export const TOP_LEVEL_CRIME_OPTIONS: {
  id: TopLevelCrimeCategory;
  label: string;
  description: string;
}[] = [
  {
    id: "women_children",
    label: "Women/Children Related Crime",
    description: "Sensitive reports should go directly to the official government portal.",
  },
  {
    id: "financial_fraud",
    label: "Financial Fraud",
    description: "Money sent or taken through UPI, card, net banking, wallet, or similar.",
  },
  {
    id: "other_cyber_crime",
    label: "Other Cyber Crime",
    description: "Social media crime, ransomware, hacking, cryptocurrency, trafficking, gambling, or another cyber crime.",
  },
];

export const OTHER_CRIME_OPTIONS: {
  id: OtherCrimeSubCategory;
  label: string;
  description: string;
}[] = [
  {
    id: "online_social_media",
    label: "Online and Social Media Related Crime",
    description: "Bullying, stalking, phishing email, hacked or fake profiles, job/matrimonial fraud, or threats.",
  },
  { id: "ransomware", label: "Ransomware", description: "Device or data locked for payment or extortion." },
  { id: "hacking", label: "Hacking", description: "Unauthorized access, data breach, website defacement, or account/server compromise." },
  { id: "cryptocurrency", label: "Cryptocurrency Related Crime", description: "Fraud, extortion, or suspicious transfer involving cryptocurrency." },
  { id: "online_trafficking", label: "Online Trafficking", description: "Online sale or movement of trafficked goods or people." },
  { id: "online_gambling", label: "Online Gambling", description: "Poker, betting, casino, or related gambling activity online." },
  { id: "any_other", label: "Any Other Cyber Crime", description: "A cyber crime that does not fit the listed categories." },
];

export const PAYMENT_METHOD_OPTIONS: {
  id: PaymentMethod;
  label: string;
  description: string;
}[] = [
  { id: "upi", label: "UPI", description: "GPay, PhonePe, Paytm, BHIM" },
  { id: "net_banking", label: "Bank transfer / Net banking", description: "Bank website or mobile app" },
  { id: "card", label: "Debit / Credit card", description: "Online, ATM, or card transaction" },
  { id: "wallet", label: "Wallet", description: "Paytm Wallet, Amazon Pay, etc." },
  { id: "unknown", label: "Other / Not sure", description: "" },
];
