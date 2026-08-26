"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";

const MAX_LEN = 4000;

interface IncidentDescriptionProps {
  value: string;
  onSave: (value: string) => Promise<void> | void;
  busy?: boolean;
}

export function IncidentDescription({ value, onSave, busy }: IncidentDescriptionProps) {
  const [draft, setDraft] = useState(value);
  const [saved, setSaved] = useState(true);

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <h3 className="font-display text-xl text-ink">Tell us what happened</h3>
      <p className="mt-1 text-sm text-ink-muted">
        Describe what happened, when it happened, how the person contacted you, what you were
        asked to do, and what happened afterward.
      </p>
      <textarea
        value={draft}
        onChange={(e) => {
          setDraft(e.target.value.slice(0, MAX_LEN));
          setSaved(false);
        }}
        rows={8}
        className="mt-4 w-full rounded-md border border-line2 bg-white px-3 py-3 text-[15px] leading-relaxed text-ink focus-visible:outline-none"
        placeholder="In your own words…"
      />
      <div className="mt-2 flex items-center justify-between">
        <p className="font-mono text-xs text-ink-muted">
          Characters: {draft.length} / {MAX_LEN}
        </p>
        <Button
          variant="outline"
          size="sm"
          disabled={busy || saved}
          onClick={async () => {
            await onSave(draft);
            setSaved(true);
          }}
        >
          {saved ? "Saved" : "Save description"}
        </Button>
      </div>
    </div>
  );
}
