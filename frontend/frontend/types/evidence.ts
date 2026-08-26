export type EvidenceType =
  | "bank_statement"
  | "transaction_receipt"
  | "payment_screenshot"
  | "sms_message"
  | "email"
  | "chat_conversation"
  | "website_url"
  | "suspect_information"
  | "photo_video"
  | "other_document";

export type ExtractionStatus = "pending" | "processing" | "completed" | "failed";

export type VerificationStatus = "unverified" | "verified" | "needs_review";

export type SuspectIdentifierType =
  | "phone"
  | "email"
  | "upi_id"
  | "bank_account"
  | "website"
  | "social_media"
  | "other";

export interface ExtractedFinancialData {
  amount: number | null;
  transaction_id: string | null;
  payment_method: string | null;
  date: string | null;
  time: string | null;
  bank: string | null;
  wallet: string | null;
  merchant: string | null;
  upi_id: string | null;
  phone_number: string | null;
  email: string | null;
  website_url: string | null;
}

export const EMPTY_EXTRACTED_DATA: ExtractedFinancialData = {
  amount: null,
  transaction_id: null,
  payment_method: null,
  date: null,
  time: null,
  bank: null,
  wallet: null,
  merchant: null,
  upi_id: null,
  phone_number: null,
  email: null,
  website_url: null,
};

export interface Evidence {
  id: string;
  incident_id: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  sha256_hash: string;
  evidence_type: EvidenceType;
  description: string | null;
  extraction_status: ExtractionStatus;
  extracted_data: ExtractedFinancialData | null;
  verification_status: VerificationStatus;
  uploaded_at: string;
  created_at: string;
  updated_at: string;
  preview_url: string | null;
}

export interface FieldComparison {
  field: string;
  label: string;
  incident_value: string | null;
  evidence_value: string | null;
  matches: boolean;
}

export interface ComparisonResult {
  has_incident_data: boolean;
  all_match: boolean;
  comparisons: FieldComparison[];
}

export interface VerifyResponse {
  evidence: Evidence;
  comparison: ComparisonResult;
}

export interface SuspectIdentifier {
  id: string;
  incident_id: string;
  type: SuspectIdentifierType;
  value: string;
  source_evidence_id: string | null;
  verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  id: string;
  incident_id: string;
  event_time: string;
  event_type: string;
  description: string;
  source_evidence_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReadinessItem {
  id: string;
  label: string;
  met: boolean;
}

export interface EvidenceReadiness {
  percent: number;
  items: ReadinessItem[];
  missing_summary: string | null;
}

export interface GenerateSummaryResponse {
  draft: string;
  provider: string;
  disclaimer: string;
}

export const EVIDENCE_TYPE_OPTIONS: { id: EvidenceType; label: string }[] = [
  { id: "bank_statement", label: "Bank / transaction document" },
  { id: "payment_screenshot", label: "Payment screenshot" },
  { id: "sms_message", label: "SMS / message" },
  { id: "email", label: "Email" },
  { id: "chat_conversation", label: "Chat / conversation" },
  { id: "website_url", label: "Website / URL" },
  { id: "suspect_information", label: "Suspect information" },
  { id: "photo_video", label: "Photo / video" },
  { id: "other_document", label: "Other document" },
];

export const SUSPECT_TYPE_OPTIONS: { id: SuspectIdentifierType; label: string }[] = [
  { id: "phone", label: "Phone number" },
  { id: "email", label: "Email address" },
  { id: "upi_id", label: "UPI ID" },
  { id: "bank_account", label: "Bank account" },
  { id: "website", label: "Website / URL" },
  { id: "social_media", label: "Social media profile" },
  { id: "other", label: "Other" },
];

export const EXTRACTED_FIELD_LABELS: Record<keyof ExtractedFinancialData, string> = {
  amount: "Amount",
  transaction_id: "Transaction ID",
  payment_method: "Payment method",
  date: "Date",
  time: "Time",
  bank: "Bank",
  wallet: "Wallet",
  merchant: "Merchant",
  upi_id: "UPI ID",
  phone_number: "Phone number",
  email: "Email",
  website_url: "Website URL",
};
