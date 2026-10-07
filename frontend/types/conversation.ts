import type { ActionItem, PaymentMethod, Urgency } from './incident';

export type FactField = 'authorization' | 'ongoing_loss' | 'remote_access' | 'account_compromised' | 'credentials_exposed' | 'occurred_at' | 'payment_method' | 'transaction_status' | 'amount' | 'transaction_id' | 'evidence_available' | 'money_lost' | 'immediate_danger' | 'blackmail' | 'private_image_threat' | 'bank_involved';
export type ReplyValue = string | boolean | null;
export interface Question { field: FactField | null; priority: 'CRITICAL' | 'SUPPORTING' | 'REPORTING' | 'OPTIONAL'; question: string }
export interface NextMove {
  type: 'ASK_CLARIFICATION' | 'REQUEST_EVIDENCE' | 'VERIFY_INFORMATION' | 'RESOLVE_CONFLICT' | 'ACKNOWLEDGE_AND_WAIT' | 'EXPLAIN_APPROVED_ACTION' | 'CONTINUE_OPEN_CONVERSATION' | 'ANSWER_RELEVANT_QUESTION';
  purpose: 'containment' | 'understanding' | 'preservation' | 'reporting' | 'conflict' | 'support';
  message: string; related_field: string | null; quick_replies: string[];
  evidence_kind: 'transaction_message' | 'transaction_receipt' | 'non_explicit_conversation' | 'profile_identifier' | null;
  action_id: string | null; basis: string[];
  fact_refs?: { field: string; value: unknown }[];
  knowledge_refs?: { id: string; claim: string }[];
}
export interface TurnRequest {
  turn_id: string;
  expected_revision: number;
  type: 'shortcut' | 'answer' | 'correction' | 'completion' | 'message' | 'evidence_review' | 'route_hint' | 'case_review';
  field?: FactField | null;
  value?: ReplyValue;
  text?: string;
  timezone?: string;
  action_id?: string | null;
  attachment_ids?: string[];
  route_hint?: 'women_children' | 'financial' | 'other' | 'not_sure';
  review_context_id?: string;
  evidence_review?: {attempt_id:string; decisions:{candidate_id:string; decision:'accept'|'reject'|'correct'; value?:string; resolve_conflict?:boolean}[]};
}
export interface EvidenceAnalysis {
  id:string; evidence_id:string; status:'processing'|'review_needed'|'failed'; base_revision:number;
  provider:string; model:string; failure:string|null;
  candidates:{id:string; field:string; value:string; source_text:string; page:number|null;
    confidence:number; uncertainty:string|null; reviewed:boolean; current_value:unknown;
    conflict:boolean; changed_since_analysis:boolean}[];
}
interface FinancialBase {
  money_lost: boolean | null;
  detected_language: 'en' | 'te' | 'hi' | 'te-Latn' | 'hi-Latn' | 'mixed' | 'unknown';
  signals: string[]; currency: string | null; payment_app: string | null;
  claimed_organization: string | null; claimed_person: string | null;
  identifiers: { type: 'phone' | 'email' | 'upi' | 'url' | 'account'; value: string }[];
  evidence_mentioned: string[];
  time_window: { start: string; end: string; approximate: true; original: string; timezone: string } | null;
  fact_schema_version: '1.0'; occurred_at: string | null; amount: string | null;
  payment_method: PaymentMethod; transaction_id: string | null;
  transaction_status: 'pending' | 'completed' | 'unknown' | null;
  account_compromised: boolean | null; remote_access: boolean | null;
  credentials_exposed: boolean | null; ongoing_loss: boolean | null; evidence_available: boolean | null;
  platform:string|null; message_text:string|null; threat_text:string|null; timestamp_text:string|null; recipient:string|null;
  immediate_danger:boolean|null; blackmail:boolean|null; private_image_threat:boolean|null; bank_involved:boolean|null;
  provenance: { field: string; origin: 'user_statement' | 'user_verification' | 'evidence_extraction' | 'inference' | 'legacy' | 'ai_extraction'; evidence_id: string | null; confidence: number | null; verified: boolean; source_turn: string | null; source_text: string | null; uncertainty: string | null }[];
}
export type FinancialFacts = FinancialBase & (
  { kind: 'financial_scam_transfer'; authorization: 'authorized' } |
  { kind: 'unauthorized_financial_transaction'; authorization: 'unauthorized' } |
  { kind: 'financial_authorization_unknown'; authorization: 'unknown' } |
  { kind: 'incident_understanding'; authorization: 'unknown' }
);
export interface CandidateUnderstanding {
  status: 'understood' | 'fallback'; message: string; language?: string; conflicts: string[];
  candidates: { field: string; value: ReplyValue | string[] | { type: string; value: string }[];
    source_text: string; source_turn: string; confidence: number; uncertainty: string | null;
    status: 'accepted' | 'needs_review' | 'rejected' | 'conflict' }[];
}
export interface ConversationTurn {
  id: string; incident_id: string; role: 'user'; type: TurnRequest['type']; text: string;
  structured_reply: TurnRequest; fact_changes: { field?: FactField; before?: ReplyValue; after?: ReplyValue;
    knowledge_sources?: { id:string; title:string; url:string; reviewed_on:string; version:string }[];
    updates?: { field: string; before: unknown; after: unknown; correction: boolean }[];
    understanding?: CandidateUnderstanding; conflicts?: string[]; acknowledgement?: string;
    next_move?: NextMove | null; agent?: { status: 'decided' | 'fallback'; reason: string | null;
      category?: 'PROVIDER_UNAVAILABLE' | 'PROVIDER_5XX' | 'PROVIDER_QUOTA' | 'PROVIDER_AUTH' | 'PROVIDER_MODEL_UNAVAILABLE' | 'TIMEOUT' | 'MALFORMED_OUTPUT' | 'VALIDATION_REJECTED' | 'APPLICATION_ERROR' | null;
      invocation_succeeded?: boolean; parsing_succeeded?: boolean; validation_succeeded?: boolean;
      proposed_type?: string | null; rejection_reason?: string | null; http_status?: number | null } };
  pending_question: Question | null; revision: number; created_at: string;
  attachments: { id: string; original_filename: string; mime_type: string; file_size: number; deleted: boolean; preview_url: string | null; extraction_status?:string|null }[];
}
export interface Completion {
  id: string; incident_id: string; plan_id: string; action_id: string; completed: boolean;
  user_note: string | null; user_recorded_reference: string | null; updated_at: string; meaning: 'user_self_report';
}
export interface ConversationState {
  incident_id: string; revision: number; version: '1.0'; answered: FactField[];
  facts: FinancialFacts; pending_question: Question | null; next_move: NextMove | null; turns: ConversationTurn[];
  plan: { id: string; incident_id: string; revision: number; plan: {
    playbook_id: string; playbook_version: string; fact_schema_version: string; evaluated_at: string;
    facts: FinancialFacts; urgency: Urgency; reasons: string[]; actions: ActionItem[];
    sources: { id: string; authority: string; display_name: string; official_url: string; purpose: string; supported_guidance: string[]; reviewed_on: string; notes: string }[];
  } };
  completions: Completion[];
  projection: { reference: string; revision: number; plan_revision: number; status: string;
    working_understanding: string[]; known_facts: Record<string, {value: unknown; source_turn: string | null; origin: string; verified: boolean; evidence_id?:string|null; source_deleted?:boolean}>;
    evidence_count: number; completed_actions: number; completion_meaning: string };
  memory: { revision: number; [key: string]: unknown };
  evidence_reviews?: EvidenceAnalysis[];
  route_hint?: string|null;
  understanding_review?: {available:boolean; reviewed:boolean; has_reviewed?:boolean; summary:Record<string,{value:unknown}>};
}
