export type IncidentType =
  | "financial_fraud"
  | "phishing"
  | "identity_theft"
  | "social_media"
  | "job_scam"
  | "other";

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
  incident_type: IncidentType;
  payment_method: PaymentMethod;
  amount?: number | null;
  incident_time?: string | null;
}

export interface TriagePayload {
  incident_type: IncidentType;
  occurred_at: string;
  amount: number;
  payment_method: PaymentMethod;
  transaction_id?: string | null;
}

export interface Incident {
  id: string;
  incident_type: IncidentType;
  payment_method: PaymentMethod;
  amount: number | null;
  incident_time: string | null;
  occurred_at: string | null;
  transaction_id: string | null;
  urgency: Urgency;
  urgency_computed_at: string | null;
  status: IncidentStatus;
  created_at: string;
  updated_at: string;
}

export interface ActionItem {
  id: string;
  title: string;
  why: string;
  phone: string | null;
  url: string | null;
  url_label: string | null;
}

export interface ActionPlan {
  urgency: Urgency;
  urgency_label: string;
  core_message: string;
  large_amount: boolean;
  actions: ActionItem[];
  complaint_draft: {
    body: string;
  };
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
    enabled: false,
  },
  {
    id: "identity_theft",
    label: "Identity theft",
    description: "Someone used your KYC, Aadhaar, or PAN without you.",
    enabled: false,
  },
  {
    id: "social_media",
    label: "Social media / impersonation",
    description: "A hacked or fake profile used to cheat you or others.",
    enabled: false,
  },
  {
    id: "job_scam",
    label: "Job or investment scam",
    description: "A fake job, trading tip, or 'guaranteed return'.",
    enabled: false,
  },
  {
    id: "other",
    label: "Something else",
    description: "Another kind of cyber incident.",
    enabled: false,
  },
];

export const PAYMENT_METHOD_OPTIONS: {
  id: Exclude<PaymentMethod, "unknown" | "bank_transfer" | "card">;
  label: string;
  description: string;
}[] = [
  { id: "upi", label: "UPI app", description: "GPay, PhonePe, Paytm, BHIM, or similar" },
  { id: "debit_card", label: "Debit card", description: "ATM / debit card payment or swipe" },
  { id: "credit_card", label: "Credit card", description: "Credit card payment or swipe" },
  { id: "net_banking", label: "Net banking", description: "Bank website or app transfer" },
  { id: "wallet", label: "Wallet", description: "Paytm wallet, Amazon Pay, or similar" },
];
