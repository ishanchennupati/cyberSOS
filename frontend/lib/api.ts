import type {
  ActionPlan,
  Incident,
  IncidentCreatePayload,
  TriagePayload,
} from "@/types/incident";

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

export async function uploadEvidence(id: string, file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<{
    id: string;
    incident_id: string;
    original_filename: string;
    content_type: string | null;
    size_bytes: number;
    created_at: string;
  }>(`/api/v1/incidents/${id}/evidence`, {
    method: "POST",
    body: form,
    headers: {},
  });
}

export function getActionPlan(id: string) {
  return request<ActionPlan>(`/api/v1/incidents/${id}/action-plan`);
}
