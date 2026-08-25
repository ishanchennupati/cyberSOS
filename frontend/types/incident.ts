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
    id: "other",
    label: "Something else",
    description: "Another kind of cyber incident.",
    enabled: true,
  },
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
