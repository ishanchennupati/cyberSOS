import type { ActionItem, PaymentMethod, Urgency } from './incident';

export type FactField = 'authorization' | 'ongoing_loss' | 'remote_access' | 'account_compromised' | 'credentials_exposed' | 'occurred_at' | 'payment_method' | 'transaction_status' | 'amount' | 'transaction_id' | 'evidence_available';
export type ReplyValue = string | boolean | null;
export interface Question { field: FactField; priority: 'CRITICAL' | 'SUPPORTING' | 'REPORTING' | 'OPTIONAL'; question: string }
export interface TurnRequest {
  turn_id: string;
  expected_revision: number;
  type: 'shortcut' | 'answer' | 'correction' | 'completion';
  field: FactField | null;
  value: ReplyValue;
  action_id?: string | null;
}
interface FinancialBase {
  fact_schema_version: '1.0'; occurred_at: string | null; amount: string | null;
  payment_method: PaymentMethod; transaction_id: string | null;
  transaction_status: 'pending' | 'completed' | 'unknown' | null;
  account_compromised: boolean | null; remote_access: boolean | null;
  credentials_exposed: boolean | null; ongoing_loss: boolean | null; evidence_available: boolean | null;
  provenance: { field: FactField; origin: 'user_statement' | 'user_verification' | 'evidence_extraction' | 'inference' | 'legacy'; evidence_id: string | null; confidence: number | null; verified: boolean }[];
}
export type FinancialFacts = FinancialBase & (
  { kind: 'financial_scam_transfer'; authorization: 'authorized' } |
  { kind: 'unauthorized_financial_transaction'; authorization: 'unauthorized' } |
  { kind: 'financial_authorization_unknown'; authorization: 'unknown' }
);
export interface ConversationTurn {
  id: string; incident_id: string; role: 'user'; type: TurnRequest['type']; text: string;
  structured_reply: TurnRequest; fact_changes: { field?: FactField; before?: ReplyValue; after?: ReplyValue };
  pending_question: Question | null; revision: number; created_at: string;
}
export interface Completion {
  id: string; incident_id: string; plan_id: string; action_id: string; completed: boolean;
  user_note: string | null; user_recorded_reference: string | null; updated_at: string; meaning: 'user_self_report';
}
export interface ConversationState {
  incident_id: string; revision: number; version: '1.0'; answered: FactField[];
  facts: FinancialFacts; pending_question: Question | null; turns: ConversationTurn[];
  plan: { id: string; incident_id: string; revision: number; plan: {
    playbook_id: string; playbook_version: string; fact_schema_version: string; evaluated_at: string;
    facts: FinancialFacts; urgency: Urgency; reasons: string[]; actions: ActionItem[];
    sources: { id: string; authority: string; display_name: string; official_url: string; purpose: string; supported_guidance: string[]; reviewed_on: string; notes: string }[];
  } };
  completions: Completion[];
}
