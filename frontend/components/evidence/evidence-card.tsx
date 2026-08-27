"use client";

import { Check, Clock, FileText, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { EVIDENCE_TYPE_OPTIONS, type Evidence } from "@/types/evidence";

interface EvidenceCardProps {
  evidence: Evidence;
  onView: () => void;
  onDelete: () => void;
}

export function EvidenceCard({ evidence, onView, onDelete }: EvidenceCardProps) {
  const typeLabel =
    EVIDENCE_TYPE_OPTIONS.find((t) => t.id === evidence.evidence_type)?.label ??
    evidence.evidence_type;

  const verified = evidence.verification_status === "verified";
  const needsReview = evidence.verification_status === "needs_review";

  const data = evidence.extracted_data;
  const summaryBits = [
    data?.amount ? `₹${data.amount.toLocaleString("en-IN")}` : null,
    data?.payment_method,
    data?.date,
  ].filter(Boolean);

  return (
    <div className="rounded-lg border border-line bg-surface p-5 shadow-card">
      <div className="flex items-start gap-3">
        <span
          className={cn(
            "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full",
            verified ? "bg-calm text-white" : needsReview ? "bg-warn text-white" : "bg-line2 text-ink-muted"
          )}
          aria-hidden="true"
        >
          {verified ? <Check size={14} /> : needsReview ? <Clock size={14} /> : <FileText size={14} />}
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-ink">{evidence.original_filename}</p>
          <p className="text-sm text-ink-muted">{typeLabel}</p>
          {summaryBits.length > 0 && (
            <p className="mt-1 text-sm text-ink-muted">{summaryBits.join(" · ")}</p>
          )}
          <p className="mt-2 text-sm">
            {verified && <span className="text-calm">Information verified</span>}
            {needsReview && <span className="text-warn">Needs review</span>}
            {evidence.verification_status === "unverified" && (
              <span className="text-ink-muted">Not yet verified</span>
            )}
          </p>
          <div className="mt-3 flex gap-2">
            <Button variant="outline" size="sm" onClick={onView}>
              View
            </Button>
            <Button variant="ghost" size="sm" onClick={onDelete} aria-label={`Delete ${evidence.original_filename}`}>
              <Trash2 size={14} aria-hidden="true" />
              Delete
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
