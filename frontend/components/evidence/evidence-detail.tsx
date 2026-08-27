"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EvidencePreview } from "@/components/evidence/evidence-preview";
import { EvidenceCategoryPicker } from "@/components/evidence/evidence-category-picker";
import { ExtractionReview } from "@/components/evidence/extraction-review";
import { compareEvidence, extractEvidence, updateEvidence, verifyEvidence } from "@/lib/api";
import type {
  ComparisonResult,
  Evidence,
  EvidenceType,
  ExtractedFinancialData,
} from "@/types/evidence";

interface EvidenceDetailProps {
  evidence: Evidence;
  onClose: () => void;
  onDelete: () => void;
  onChange: (updated: Evidence) => void;
}

export function EvidenceDetail({ evidence, onClose, onDelete, onChange }: EvidenceDetailProps) {
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [showHash, setShowHash] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      // Kick off extraction automatically the first time we open evidence
      // that hasn't been processed yet — the citizen still must confirm.
      if (evidence.extraction_status === "pending") {
        try {
          const updated = await extractEvidence(evidence.id);
          if (!cancelled) onChange(updated);
        } catch {
          if (!cancelled) setError("Extraction unavailable. You can enter these details manually.");
        }
      }
      try {
        const cmp = await compareEvidence(evidence.id);
        if (!cancelled) setComparison(cmp);
      } catch {
        // Comparison is a convenience — silently skip if unavailable.
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evidence.id, evidence.extraction_status]);

  async function handleConfirm(data: ExtractedFinancialData) {
    setBusy(true);
    setError(null);
    try {
      const result = await verifyEvidence(evidence.id, data);
      onChange(result.evidence);
      setComparison(result.comparison);
    } catch {
      setError("We couldn't save your verification. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCategoryChange(type: EvidenceType) {
    setBusy(true);
    try {
      const updated = await updateEvidence(evidence.id, { evidence_type: type });
      onChange(updated);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border-2 border-ink bg-white p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
          Evidence details
        </p>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close evidence details"
          className="text-ink-muted hover:text-ink"
        >
          <X size={18} aria-hidden="true" />
        </button>
      </div>

      <div className="mt-4">
        <EvidencePreview evidence={evidence} />
      </div>

      <div className="mt-4">
        <EvidenceCategoryPicker value={evidence.evidence_type} onChange={handleCategoryChange} />
      </div>

      <div className="mt-4">
        <ExtractionReview
          data={evidence.extracted_data}
          status={evidence.extraction_status}
          verified={evidence.verification_status === "verified"}
          comparison={comparison}
          onConfirm={handleConfirm}
          busy={busy}
        />
      </div>

      {error && (
        <p role="alert" className="mt-3 text-sm text-urgent">
          {error}
        </p>
      )}

      <div className="mt-5 border-t border-line pt-4">
        <button
          type="button"
          onClick={() => setShowHash((v) => !v)}
          className="flex items-center gap-2 text-sm font-medium text-ink-muted hover:text-ink"
        >
          {showHash ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          Evidence details
        </button>
        {showHash && (
          <dl className="mt-3 space-y-2 text-sm">
            <div>
              <dt className="text-ink-muted">Evidence ID</dt>
              <dd className="font-mono text-ink">{evidence.id}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">SHA-256</dt>
              <dd className="break-all font-mono text-ink">{evidence.sha256_hash}</dd>
            </div>
            <div>
              <dt className="text-ink-muted">Verification</dt>
              <dd className="text-ink">
                {evidence.verification_status === "verified"
                  ? "User verified"
                  : evidence.verification_status === "needs_review"
                  ? "Needs review"
                  : "Not yet verified"}
              </dd>
            </div>
          </dl>
        )}
        <p className="mt-3 text-xs leading-relaxed text-ink-muted">
          SHA-256 is a digital fingerprint of this file. It helps identify whether the file
          changes after upload. This does not prove the evidence is legally valid.
        </p>
      </div>

      <div className="mt-5 border-t border-line pt-4">
        <Button variant="ghost" size="sm" onClick={onDelete}>
          <Trash2 size={14} aria-hidden="true" />
          Delete this evidence
        </Button>
      </div>
    </div>
  );
}
