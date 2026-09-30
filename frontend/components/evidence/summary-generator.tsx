"use client";

import { useState } from "react";
import { Check, FileText, Pencil, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

interface SummaryGeneratorProps {
  onGenerate: () => Promise<{ draft: string } | null>;
  busy?: boolean;
}

export function SummaryGenerator({ onGenerate, busy }: SummaryGeneratorProps) {
  const [draft, setDraft] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    try {
      const result = await onGenerate();
      if (result) {
        setDraft(result.draft);
        setAccepted(false);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <div className="flex items-center gap-2">
        <Sparkles size={18} className="text-calm" aria-hidden="true" />
        <h3 className="font-display text-xl text-ink">Incident summary</h3>
      </div>

      {draft === null ? (
        <>
          <p className="mt-2 text-sm text-ink-muted">
            Generate a draft narrative from the information you&apos;ve verified and your own
            description. Check every detail before using the draft. Nothing is submitted anywhere.
          </p>
          <Button variant="calm" className="mt-4" onClick={handleGenerate} disabled={loading || busy}>
            <FileText size={16} aria-hidden="true" />
            {loading ? "Generating…" : "Generate incident summary"}
          </Button>
        </>
      ) : (
        <div className="mt-4">
          <p className="text-xs font-medium uppercase tracking-wide text-warn">
            Draft from your information - review carefully before using.
          </p>
          {editing ? (
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              rows={7}
              className="mt-3 w-full rounded-md border border-line2 bg-white px-3 py-3 text-[15px] leading-relaxed text-ink focus-visible:outline-none"
            />
          ) : (
            <p className="mt-3 rounded-md border border-line bg-paper px-4 py-4 text-[15px] leading-relaxed text-ink">
              {draft}
            </p>
          )}

          <div className="mt-4 flex flex-wrap gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditing((v) => !v)}
              disabled={busy}
            >
              <Pencil size={14} aria-hidden="true" />
              {editing ? "Done editing" : "Edit"}
            </Button>
            <Button
              variant="calm"
              size="sm"
              onClick={() => setAccepted(true)}
              disabled={busy || accepted}
            >
              <Check size={14} aria-hidden="true" />
              {accepted ? "Accepted" : "Accept draft"}
            </Button>
            <Button variant="ghost" size="sm" onClick={handleGenerate} disabled={loading || busy}>
              Regenerate
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
