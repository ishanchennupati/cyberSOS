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

import type { ConversationState, TurnRequest } from '@/types/conversation';

export function getConversation(id: string) {
  return request<ConversationState>(`/api/v1/incidents/${id}/conversation`, { signal: AbortSignal.timeout(15000), cache: 'no-store' });
}

export function sendConversationTurn(id: string, payload: TurnRequest) {
  return request<ConversationState>(`/api/v1/incidents/${id}/conversation/turns`, {
    method: 'POST', body: JSON.stringify(payload), signal: AbortSignal.timeout(65000),
  }, (state, requestId) => {
    const changes = state.turns?.at(-1)?.fact_changes;
    if (changes?.understanding?.status === 'fallback') {
      reportDiagnostic('AI_EXTRACTION_UNAVAILABLE', { requestId });
    } else if (changes?.agent?.status === 'fallback') {
      reportDiagnostic('AI_FOLLOW_UP_UNAVAILABLE', { requestId, status: changes.agent.http_status ?? undefined });
    }
  });
}

export class ApiError extends Error {
  status?: number;
  requestId?: string;
  category?: string;
  constructor(message: string, status?: number, requestId?: string, category?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
    this.category = category;
  }
}

export function reportDiagnostic(category: string, metadata: {
  requestId?: string; route?: string; method?: string; status?: number;
  durationMs?: number; location?: string; line?: number; column?: number;
} = {}) {
  // Only controlled metadata. Never log Error objects, bodies, facts, cookies,
  // URLs with case IDs/queries, server detail text or provider responses.
  console.error('[CyberSOS diagnostic]', { timestamp: new Date().toISOString(), category, ...metadata });
}

function diagnosticRoute(path: string) {
  const route = path.split('?')[0];
  return route.replace(/(\/api\/v1\/(?:incidents|evidence|suspects|timeline))\/[^/]+/, '$1/{incident_id}');
}

async function request<T>(path: string, init?: RequestInit, onSuccess?: (data: T, requestId: string) => void): Promise<T> {
  let response: Response;
  const requestId = crypto.randomUUID();
  const started = performance.now();
  const metadata = { requestId, route: diagnosticRoute(path), method: init?.method ?? 'GET' };
  const isMultipart = typeof FormData !== "undefined" && init?.body instanceof FormData;

  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(isMultipart ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
        'X-Request-ID': requestId,
      },
    });
  } catch (error) {
    // Network failure — backend unreachable, timeout, DNS, etc.
    const category = error instanceof Error && ['TimeoutError', 'AbortError'].includes(error.name) ? 'TIMEOUT' : 'NETWORK_ERROR';
    reportDiagnostic(category, { ...metadata, durationMs: Math.round(performance.now() - started) });
    throw new ApiError("We couldn't reach CyberSOS. Check your connection and try again.", undefined, requestId, category);
  }

  const responseId = response.headers.get('X-Request-ID');
  if (responseId && /^[a-f0-9-]{36}$/i.test(responseId)) metadata.requestId = responseId;

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
    reportDiagnostic('HTTP_ERROR', { ...metadata, status: response.status, durationMs: Math.round(performance.now() - started) });
    throw new ApiError(detail, response.status, metadata.requestId, 'HTTP_ERROR');
  }

  if (response.status === 204) return undefined as T;
  try {
    const data = (await response.json()) as T;
    onSuccess?.(data, metadata.requestId);
    return data;
  } catch {
    reportDiagnostic('RESPONSE_ERROR', { ...metadata, status: response.status, durationMs: Math.round(performance.now() - started) });
    throw new ApiError('CyberSOS returned an unreadable response. Please try again.', response.status, metadata.requestId, 'RESPONSE_ERROR');
  }
}

function resolveEvidencePreview(evidence: Evidence): Evidence {
  return {
    ...evidence,
    preview_url: evidence.preview_url
      ? new URL(evidence.preview_url, API_URL).toString()
      : null,
  };
}

async function evidenceRequest(path: string, init?: RequestInit): Promise<Evidence> {
  return resolveEvidencePreview(await request<Evidence>(path, init));
}

export function getApiHealth() {
  return request<{ status: string; service: string }>("/health");
}

export function createIncident(payload: IncidentCreatePayload) {
  return request<Incident>("/api/v1/incidents", {
    method: "POST",
    signal: AbortSignal.timeout(15000),
    body: JSON.stringify(payload),
  });
}

export function createConversationCase(creationId: string, creationSecret: string) {
  return request<Incident>('/api/v1/incidents', { method: 'POST', signal: AbortSignal.timeout(15000),
    body: JSON.stringify({conversation_first:true, creation_id:creationId, creation_secret:creationSecret}) });
}

export function stageChatAttachment(incidentId: string, file: File, uploadId: string,
  signal: AbortSignal, onProgress: (percent: number) => void): Promise<Evidence> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append('file', file); form.append('upload_id', uploadId); form.append('staged_for_chat', 'true');
    xhr.open('POST', `${API_URL}/api/v1/incidents/${incidentId}/evidence`);
    xhr.withCredentials = true; xhr.timeout = 60000;
    xhr.upload.onprogress = event => { if (event.lengthComputable) onProgress(Math.round(event.loaded / event.total * 100)); };
    const abort = () => xhr.abort();
    signal.addEventListener('abort', abort, {once:true});
    const finish = () => signal.removeEventListener('abort', abort);
    xhr.onload = () => {
      finish();
      try {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) resolve(resolveEvidencePreview(data));
        else reject(new ApiError(typeof data.detail === 'string' ? data.detail : 'Attachment could not be uploaded.', xhr.status));
      } catch { reject(new ApiError('Attachment response could not be read. Retry checks the same upload key.')); }
    };
    xhr.onerror = () => { finish(); reject(new ApiError('Attachment upload was interrupted. Retry to check whether it was saved.')); };
    xhr.ontimeout = xhr.onerror;
    xhr.onabort = () => { finish(); reject(new ApiError('Upload cancelled.')); };
    if (signal.aborted) { finish(); reject(new ApiError('Upload cancelled.')); return; }
    xhr.send(form);
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
  return evidenceRequest(`/api/v1/incidents/${incidentId}/evidence`, {
    method: "POST",
    body: form,
  });
}

export function getActionPlan(id: string) {
  return request<ActionPlan>(`/api/v1/incidents/${id}/action-plan`);
}

export function listEvidence(incidentId: string) {
  return request<Evidence[]>(`/api/v1/incidents/${incidentId}/evidence`).then(
    (items) => items.map(resolveEvidencePreview)
  );
}

export function getEvidence(evidenceId: string) {
  return evidenceRequest(`/api/v1/evidence/${evidenceId}`);
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
  return evidenceRequest(`/api/v1/evidence/${evidenceId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteEvidence(evidenceId: string) {
  return request<void>(`/api/v1/evidence/${evidenceId}`, { method: "DELETE" });
}

export function extractEvidence(evidenceId: string) {
  return evidenceRequest(`/api/v1/evidence/${evidenceId}/extract`, { method: "POST" });
}

export function verifyEvidence(
  evidenceId: string,
  extractedData: ExtractedFinancialData,
  verificationStatus: VerificationStatus = "verified"
) {
  return request<VerifyResponse>(`/api/v1/evidence/${evidenceId}/verify`, {
    method: "POST",
    body: JSON.stringify({ extracted_data: extractedData, verification_status: verificationStatus }),
  }).then((result) => ({ ...result, evidence: resolveEvidencePreview(result.evidence) }));
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
