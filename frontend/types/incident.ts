export type IncidentType = "financial_fraud";

export type PaymentMethod = "upi" | "bank_transfer" | "card" | "wallet" | "unknown";

export type Urgency = "critical" | "high" | "medium" | "low";

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

export interface Incident {
  id: string;
  incident_type: IncidentType;
  payment_method: PaymentMethod;
  amount: number | null;
  incident_time: string | null;
  urgency: Urgency;
  status: IncidentStatus;
  created_at: string;
  updated_at: string;
}
