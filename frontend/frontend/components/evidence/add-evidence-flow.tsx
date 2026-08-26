"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { EvidenceCategoryPicker } from "@/components/evidence/evidence-category-picker";
import { EvidenceUpload } from "@/components/evidence/evidence-upload";
import { formatFileSize } from "@/lib/format";
import type { Evidence, EvidenceType } from "@/types/evidence";

interface AddEvidenceFlowProps {
  onUpload: (file: File, evidenceType: EvidenceType) => Promise<Evidence>;
  onUploaded: (evidence: Evidence) => void;
}

export function AddEvidenceFlow({ onUpload, onUploaded }: AddEvidenceFlowProps) {
  const [file, setFile] = useState<File | null>(null);
  const [evidenceType, setEvidenceType] = useState<EvidenceType | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload() {
    if (!file || !evidenceType) return;
    setUploading(true);
    setError(null);
    try {
      const evidence = await onUpload(file, evidenceType);
      onUploaded(evidence);
      setFile(null);
      setEvidenceType(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  if (!file) {
    return <EvidenceUpload onFileSelected={setFile} />;
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">Selected file</p>
      <p className="mt-1 font-medium text-ink">{file.name}</p>
      <p className="text-sm text-ink-muted">{formatFileSize(file.size)}</p>

      <div className="mt-5">
        <EvidenceCategoryPicker value={evidenceType} onChange={setEvidenceType} />
      </div>

      {error && (
        <p role="alert" className="mt-3 text-sm text-urgent">
          {error}
        </p>
      )}

      <div className="mt-5 flex flex-wrap gap-3">
        <Button
          variant="calm"
          onClick={handleUpload}
          disabled={!evidenceType || uploading}
        >
          {uploading ? "Uploading…" : "Add evidence"}
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            setFile(null);
            setEvidenceType(null);
            setError(null);
          }}
          disabled={uploading}
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}
