"use client";

import { FileText } from "lucide-react";

import { formatDateTime, formatFileSize } from "@/lib/format";
import { EVIDENCE_TYPE_OPTIONS, type Evidence } from "@/types/evidence";

interface EvidencePreviewProps {
  evidence: Evidence;
}

export function EvidencePreview({ evidence }: EvidencePreviewProps) {
  const typeLabel =
    EVIDENCE_TYPE_OPTIONS.find((t) => t.id === evidence.evidence_type)?.label ??
    evidence.evidence_type;
  const isImage = evidence.mime_type === "image/png" || evidence.mime_type === "image/jpeg";
  const isPdf = evidence.mime_type === "application/pdf";

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
        Evidence preview
      </p>
      <p className="mt-1 font-medium text-ink">{evidence.original_filename}</p>

      <div className="mt-4 overflow-hidden rounded-md border border-line bg-paper">
        {isImage && evidence.preview_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={evidence.preview_url}
            alt={`Preview of ${evidence.original_filename}`}
            className="mx-auto max-h-80 w-auto object-contain"
          />
        ) : isPdf && evidence.preview_url ? (
          <iframe
            src={evidence.preview_url}
            title={`Preview of ${evidence.original_filename}`}
            className="h-80 w-full"
          />
        ) : (
          <div className="flex h-40 flex-col items-center justify-center gap-2 text-ink-muted">
            <FileText size={28} aria-hidden="true" />
            <p className="text-sm">Preview unavailable. The file has been securely stored.</p>
          </div>
        )}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-ink-muted">Type</dt>
          <dd className="mt-0.5 font-medium text-ink">{typeLabel}</dd>
        </div>
        <div>
          <dt className="text-ink-muted">Size</dt>
          <dd className="mt-0.5 font-medium text-ink">{formatFileSize(evidence.file_size)}</dd>
        </div>
        <div>
          <dt className="text-ink-muted">Uploaded</dt>
          <dd className="mt-0.5 font-medium text-ink">{formatDateTime(evidence.uploaded_at)}</dd>
        </div>
      </dl>
    </div>
  );
}
