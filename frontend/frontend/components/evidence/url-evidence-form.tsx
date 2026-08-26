"use client";

import { useState } from "react";
import { Link2, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";

function isValidUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

interface UrlEvidenceFormProps {
  onAdd: (url: string) => Promise<void> | void;
  busy?: boolean;
}

export function UrlEvidenceForm({ onAdd, busy }: UrlEvidenceFormProps) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleAdd() {
    const trimmed = value.trim();
    if (!trimmed || !isValidUrl(trimmed)) {
      setError("Please enter a valid website address, starting with https://");
      return;
    }
    setError(null);
    await onAdd(trimmed);
    setValue("");
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <h3 className="font-display text-xl text-ink">Add suspicious URL</h3>
      <p className="mt-1 text-sm text-ink-muted">
        Save a website, social media profile, or link involved in the incident. CyberSOS does
        not visit or scan the link.
      </p>
      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <label className="sr-only" htmlFor="suspicious-url">
          Website / URL
        </label>
        <div className="relative flex-1">
          <Link2
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"
            aria-hidden="true"
          />
          <input
            id="suspicious-url"
            type="url"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="https://"
            className="w-full rounded-md border border-line2 bg-white py-2 pl-9 pr-3 text-[15px] text-ink focus-visible:outline-none"
          />
        </div>
        <Button variant="outline" onClick={handleAdd} disabled={busy}>
          <Plus size={16} aria-hidden="true" />
          Add URL
        </Button>
      </div>
      {error && (
        <p role="alert" className="mt-2 text-sm text-urgent">
          {error}
        </p>
      )}
    </div>
  );
}
