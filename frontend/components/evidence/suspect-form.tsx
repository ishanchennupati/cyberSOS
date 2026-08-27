"use client";

import { useState } from "react";
import { Plus, ShieldCheck, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SUSPECT_TYPE_OPTIONS, type SuspectIdentifier, type SuspectIdentifierType } from "@/types/evidence";

interface SuspectFormProps {
  suspects: SuspectIdentifier[];
  onAdd: (type: SuspectIdentifierType, value: string) => Promise<void> | void;
  onDelete: (id: string) => Promise<void> | void;
  busy?: boolean;
}

export function SuspectForm({ suspects, onAdd, onDelete, busy }: SuspectFormProps) {
  const [type, setType] = useState<SuspectIdentifierType>("phone");
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleAdd() {
    if (!value.trim()) {
      setError("Please enter a value before adding it.");
      return;
    }
    setError(null);
    await onAdd(type, value.trim());
    setValue("");
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <h3 className="font-display text-xl text-ink">Suspect information</h3>
      <p className="mt-1 text-sm text-ink-muted">
        Provide any information about the suspected person, account or website if known. All
        fields are optional.
      </p>

      {suspects.length > 0 && (
        <ul className="mt-4 space-y-2">
          {suspects.map((s) => {
            const label = SUSPECT_TYPE_OPTIONS.find((t) => t.id === s.type)?.label ?? s.type;
            return (
              <li
                key={s.id}
                className="flex items-center justify-between gap-3 rounded-md border border-line bg-paper px-3 py-2 text-sm"
              >
                <div className="min-w-0">
                  <span className="text-ink-muted">{label}: </span>
                  <span className="font-medium text-ink break-all">{s.value}</span>
                  {s.source_evidence_id && (
                    <span className="ml-2 text-xs text-ink-muted">(found in evidence)</span>
                  )}
                  {s.verified && (
                    <span className="ml-2 inline-flex items-center gap-1 text-xs text-calm">
                      <ShieldCheck size={12} aria-hidden="true" /> verified
                    </span>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(s.id)}
                  aria-label={`Remove ${label} ${s.value}`}
                  disabled={busy}
                >
                  <Trash2 size={14} aria-hidden="true" />
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end">
        <label className="block text-sm sm:w-48">
          <span className="text-ink-muted">Type</span>
          <select
            value={type}
            onChange={(e) => setType(e.target.value as SuspectIdentifierType)}
            className="mt-1 w-full rounded-md border border-line2 bg-white px-3 py-2 text-[15px] text-ink focus-visible:outline-none"
          >
            {SUSPECT_TYPE_OPTIONS.map((opt) => (
              <option key={opt.id} value={opt.id}>
                {opt.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block flex-1 text-sm">
          <span className="text-ink-muted">Value</span>
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="e.g. 98765xxxxx, scammer@upi, https://fake-bank.example"
            className="mt-1 w-full rounded-md border border-line2 bg-white px-3 py-2 text-[15px] text-ink focus-visible:outline-none"
          />
        </label>
        <Button variant="outline" onClick={handleAdd} disabled={busy} className="sm:mb-0">
          <Plus size={16} aria-hidden="true" />
          Add another identifier
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
