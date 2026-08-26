"use client";

import { AddEvidenceFlow } from "@/components/evidence/add-evidence-flow";
import { EvidenceCard } from "@/components/evidence/evidence-card";
import { uploadEvidence } from "@/lib/api";
import type { Evidence, EvidenceType } from "@/types/evidence";

interface EvidenceDashboardProps {
  evidence: Evidence[];
  incidentId: string;
  onUploaded: (evidence: Evidence) => void;
  onView: (evidence: Evidence) => void;
  onDelete: (evidence: Evidence) => void;
}

export function EvidenceDashboard({
  evidence,
  incidentId,
  onUploaded,
  onView,
  onDelete,
}: EvidenceDashboardProps) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <h2 className="font-display text-2xl text-ink">Evidence for this incident</h2>
        <p className="text-sm text-ink-muted">
          {evidence.length} {evidence.length === 1 ? "piece" : "pieces"} of evidence added
        </p>
      </div>

      {evidence.length > 0 && (
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {evidence.map((item) => (
            <EvidenceCard
              key={item.id}
              evidence={item}
              onView={() => onView(item)}
              onDelete={() => onDelete(item)}
            />
          ))}
        </div>
      )}

      <div className="mt-5">
        <AddEvidenceFlow
          onUpload={(file, evidenceType) => uploadEvidence(incidentId, file, evidenceType)}
          onUploaded={onUploaded}
        />
      </div>
    </div>
  );
}
