import type {
  ActionPlan,
  Incident,
  IncidentCreatePayload,
  TriagePayload,
} from "@/types/incident";
import type {
  ComparisonResult,
  Evidence,
  EvidenceReadiness,
  EvidenceType,
  ExtractedFinancialData,
  GenerateSummaryResponse,
  SuspectIdentifier,
  SuspectIdentifierType,
  TimelineEvent,
  VerificationStatus,
  VerifyResponse,
} from "@/types/evidence";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  const isMultipart = typeof FormData !== "undefined" && init?.body instanceof FormData;

  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        ...(isMultipart ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
      },
    });
  } catch {
    // Network failure — backend unreachable, timeout, DNS, etc.
    throw new ApiError("We couldn't reach CyberSOS. Check your connection and try again.");
  }

  if (!response.ok) {
    let detail = "Something went wrong. Please try again.";
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (Array.isArray(body?.detail)) {
        const firstError = body.detail.find(
          (item: unknown): item is { msg: string } =>
            typeof item === "object" &&
            item !== null &&
            "msg" in item &&
            typeof item.msg === "string"
        );
        if (firstError) detail = firstError.msg;
      }
    } catch {
      // response wasn't JSON — keep the default message, never surface raw text
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

export function getApiHealth() {
  return request<{ status: string; service: string }>("/health");
}

export function createIncident(payload: IncidentCreatePayload) {
  return request<Incident>("/api/v1/incidents", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getIncident(id: string) {
  return request<Incident>(`/api/v1/incidents/${id}`);
}

export function triageIncident(id: string, payload: TriagePayload) {
  return request<Incident>(`/api/v1/incidents/${id}/triage`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function uploadEvidence(
  incidentId: string,
  file: File,
  evidenceType: EvidenceType = "other_document",
  description?: string
) {
  const form = new FormData();
  form.append("file", file);
  form.append("evidence_type", evidenceType);
  if (description) form.append("description", description);
  return request<Evidence>(`/api/v1/incidents/${incidentId}/evidence`, {
    method: "POST",
    body: form,
  });
}

export function getActionPlan(id: string) {
  return request<ActionPlan>(`/api/v1/incidents/${id}/action-plan`);
}

export function listEvidence(incidentId: string) {
  return request<Evidence[]>(`/api/v1/incidents/${incidentId}/evidence`);
}

export function getEvidence(evidenceId: string) {
  return request<Evidence>(`/api/v1/evidence/${evidenceId}`);
}

export function updateEvidence(
  evidenceId: string,
  payload: Partial<{
    evidence_type: EvidenceType;
    description: string;
    extracted_data: ExtractedFinancialData;
    verification_status: VerificationStatus;
  }>
) {
  return request<Evidence>(`/api/v1/evidence/${evidenceId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteEvidence(evidenceId: string) {
  return request<void>(`/api/v1/evidence/${evidenceId}`, { method: "DELETE" });
}

export function extractEvidence(evidenceId: string) {
  return request<Evidence>(`/api/v1/evidence/${evidenceId}/extract`, { method: "POST" });
}

export function verifyEvidence(
  evidenceId: string,
  extractedData: ExtractedFinancialData,
  verificationStatus: VerificationStatus = "verified"
) {
  return request<VerifyResponse>(`/api/v1/evidence/${evidenceId}/verify`, {
    method: "POST",
    body: JSON.stringify({ extracted_data: extractedData, verification_status: verificationStatus }),
  });
}

export function compareEvidence(evidenceId: string) {
  return request<ComparisonResult>(`/api/v1/evidence/${evidenceId}/compare`);
}

export function evidenceFileUrl(evidenceId: string) {
  return `${API_URL}/api/v1/evidence/${evidenceId}/file`;
}

export function createSuspect(
  incidentId: string,
  payload: { type: SuspectIdentifierType; value: string; source_evidence_id?: string | null }
) {
  return request<SuspectIdentifier>(`/api/v1/incidents/${incidentId}/suspects`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listSuspects(incidentId: string) {
  return request<SuspectIdentifier[]>(`/api/v1/incidents/${incidentId}/suspects`);
}

export function updateSuspect(
  suspectId: string,
  payload: Partial<{ type: SuspectIdentifierType; value: string; verified: boolean }>
) {
  return request<SuspectIdentifier>(`/api/v1/suspects/${suspectId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteSuspect(suspectId: string) {
  return request<void>(`/api/v1/suspects/${suspectId}`, { method: "DELETE" });
}

export function createTimelineEvent(
  incidentId: string,
  payload: { event_time: string; event_type?: string; description: string; source_evidence_id?: string | null }
) {
  return request<TimelineEvent>(`/api/v1/incidents/${incidentId}/timeline`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listTimelineEvents(incidentId: string) {
  return request<TimelineEvent[]>(`/api/v1/incidents/${incidentId}/timeline`);
}

export function updateTimelineEvent(
  eventId: string,
  payload: Partial<{ event_time: string; event_type: string; description: string }>
) {
  return request<TimelineEvent>(`/api/v1/timeline/${eventId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteTimelineEvent(eventId: string) {
  return request<void>(`/api/v1/timeline/${eventId}`, { method: "DELETE" });
}

export function getEvidenceReadiness(incidentId: string) {
  return request<EvidenceReadiness>(`/api/v1/incidents/${incidentId}/evidence-readiness`);
}

export function updateIncidentDescription(incidentId: string, description: string) {
  return request<Incident>(`/api/v1/incidents/${incidentId}/description`, {
    method: "PATCH",
    body: JSON.stringify({ description }),
  });
}

export function generateIncidentSummary(incidentId: string) {
  return request<GenerateSummaryResponse>(`/api/v1/incidents/${incidentId}/generate-summary`, {
    method: "POST",
  });
}
