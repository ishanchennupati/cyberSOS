"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { DemoDataBanner, IndependentPrototypeBanner } from "@/components/evidence/demo-banner";
import { EvidenceDashboard } from "@/components/evidence/evidence-dashboard";
import { EvidenceDetail } from "@/components/evidence/evidence-detail";
import { IncidentDescription } from "@/components/evidence/incident-description";
import { ReadinessPanel } from "@/components/evidence/readiness-panel";
import { SummaryGenerator } from "@/components/evidence/summary-generator";
import { SuspectForm } from "@/components/evidence/suspect-form";
import { TimelinePanel } from "@/components/evidence/timeline-panel";
import { UrlEvidenceForm } from "@/components/evidence/url-evidence-form";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import {
  ApiError,
  createSuspect,
  createTimelineEvent,
  deleteEvidence as apiDeleteEvidence,
  deleteSuspect,
  generateIncidentSummary,
  getEvidenceReadiness,
  getIncident,
  listEvidence,
  listSuspects,
  listTimelineEvents,
  updateIncidentDescription,
} from "@/lib/api";
import type { Incident } from "@/types/incident";
import type { Evidence, EvidenceReadiness, SuspectIdentifier, TimelineEvent } from "@/types/evidence";

export default function EvidenceVaultPage() {
  const params = useParams<{ id: string }>();
  const incidentId = params.id;

  const [incident, setIncident] = useState<Incident | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [suspects, setSuspects] = useState<SuspectIdentifier[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [readiness, setReadiness] = useState<EvidenceReadiness | null>(null);

  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refreshReadiness = useCallback(async () => {
    try {
      const r = await getEvidenceReadiness(incidentId);
      setReadiness(r);
    } catch {
      // Readiness is a convenience panel — a failed refresh shouldn't block the page.
    }
  }, [incidentId]);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [inc, ev, sus, tl] = await Promise.all([
        getIncident(incidentId),
        listEvidence(incidentId),
        listSuspects(incidentId),
        listTimelineEvents(incidentId),
      ]);
      setIncident(inc);
      setEvidence(ev);
      setSuspects(sus);
      setTimeline(tl);
      await refreshReadiness();
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "We couldn't load your evidence vault. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }, [incidentId, refreshReadiness]);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const selectedEvidence = evidence.find((e) => e.id === selectedEvidenceId) ?? null;

  function handleEvidenceUploaded(item: Evidence) {
    setEvidence((prev) => [...prev, item]);
    setSelectedEvidenceId(item.id);
    void refreshReadiness();
  }

  function handleEvidenceChanged(updated: Evidence) {
    setEvidence((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    void refreshReadiness();
  }

  async function handleEvidenceDelete(item: Evidence) {
    if (!confirm(`Remove "${item.original_filename}" from this incident?`)) return;
    try {
      await apiDeleteEvidence(item.id);
      setEvidence((prev) => prev.filter((e) => e.id !== item.id));
      if (selectedEvidenceId === item.id) setSelectedEvidenceId(null);
      void refreshReadiness();
    } catch {
      alert("We couldn't remove this evidence. Please try again.");
    }
  }

  async function handleAddSuspect(type: SuspectIdentifier["type"], value: string) {
    const created = await createSuspect(incidentId, { type, value });
    setSuspects((prev) => [...prev, created]);
    void refreshReadiness();
  }

  async function handleDeleteSuspect(id: string) {
    await deleteSuspect(id);
    setSuspects((prev) => prev.filter((s) => s.id !== id));
    void refreshReadiness();
  }

  async function handleAddUrl(url: string) {
    const created = await createSuspect(incidentId, { type: "website", value: url });
    setSuspects((prev) => [...prev, created]);
    void refreshReadiness();
  }

  async function handleAddTimelineEvent(eventTimeIso: string, description: string) {
    const created = await createTimelineEvent(incidentId, {
      event_time: eventTimeIso,
      description,
    });
    setTimeline((prev) => [...prev, created].sort((a, b) => a.event_time.localeCompare(b.event_time)));
  }

  async function handleSaveDescription(description: string) {
    const updated = await updateIncidentDescription(incidentId, description);
    setIncident(updated);
    void refreshReadiness();
  }

  async function handleGenerateSummary() {
    try {
      return await generateIncidentSummary(incidentId);
    } catch {
      alert("We couldn't generate a draft right now. Please try again.");
      return null;
    }
  }

  return (
    <main className="min-h-screen bg-paper">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <Link
            href={`/incident/${incidentId}/result`}
            className="flex items-center gap-2 text-sm text-ink-muted hover:text-ink"
          >
            <ArrowLeft size={16} aria-hidden="true" />
            Back to action plan
          </Link>
          <span className="font-display text-lg italic text-ink">CyberSOS</span>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="space-y-3">
          <IndependentPrototypeBanner />
          <DemoDataBanner />
        </div>

        <div className="mt-8">
          <h1 className="font-display text-3xl text-ink">Evidence for your incident</h1>
          <p className="mt-2 max-w-xl text-[15px] leading-relaxed text-ink-muted">
            Upload documents, screenshots, messages, receipts or other information that may help
            explain what happened. Nothing here is submitted anywhere automatically.
          </p>
        </div>

        {loading && (
          <div className="mt-8">
            <LoadingState message="Loading your evidence vault…" />
          </div>
        )}

        {error && !loading && (
          <div className="mt-8">
            <ErrorState message={error} onRetry={loadAll} />
          </div>
        )}

        {!loading && !error && incident && (
          <div className="mt-8 space-y-8">
            <EvidenceDashboard
              evidence={evidence}
              incidentId={incidentId}
              onUploaded={handleEvidenceUploaded}
              onView={(item) => setSelectedEvidenceId(item.id)}
              onDelete={handleEvidenceDelete}
            />

            {selectedEvidence && (
              <EvidenceDetail
                evidence={selectedEvidence}
                onClose={() => setSelectedEvidenceId(null)}
                onDelete={() => handleEvidenceDelete(selectedEvidence)}
                onChange={handleEvidenceChanged}
              />
            )}

            <SuspectForm suspects={suspects} onAdd={handleAddSuspect} onDelete={handleDeleteSuspect} />

            <UrlEvidenceForm onAdd={handleAddUrl} />

            <ReadinessPanel readiness={readiness} />

            <TimelinePanel events={timeline} onAdd={handleAddTimelineEvent} />

            <IncidentDescription value={incident.description ?? ""} onSave={handleSaveDescription} />

            <SummaryGenerator onGenerate={handleGenerateSummary} />
          </div>
        )}
      </div>
    </main>
  );
}
