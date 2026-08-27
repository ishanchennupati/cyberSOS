"use client";

import { Check, Minus } from "lucide-react";

import { cn } from "@/lib/utils";
import type { EvidenceReadiness } from "@/types/evidence";

interface ReadinessPanelProps {
  readiness: EvidenceReadiness | null;
  loading?: boolean;
}

export function ReadinessPanel({ readiness, loading }: ReadinessPanelProps) {
  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <h3 className="font-display text-xl text-ink">Evidence readiness</h3>

      {loading || !readiness ? (
        <p className="mt-3 text-sm text-ink-muted">Checking what you have so far…</p>
      ) : (
        <>
          <div className="mt-4">
            <div
              role="progressbar"
              aria-valuenow={readiness.percent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Evidence readiness"
              className="h-3 w-full overflow-hidden rounded-full bg-line"
            >
              <div
                className="h-full rounded-full bg-calm transition-all"
                style={{ width: `${readiness.percent}%` }}
              />
            </div>
            <p className="mt-2 font-mono text-sm text-ink-muted">{readiness.percent}%</p>
          </div>

          <ul className="mt-4 space-y-2">
            {readiness.items.map((item) => (
              <li key={item.id} className="flex items-center gap-2 text-sm">
                <span
                  aria-hidden="true"
                  className={cn(
                    "flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
                    item.met ? "bg-calm-soft text-calm" : "bg-line text-ink-muted"
                  )}
                >
                  {item.met ? <Check size={12} /> : <Minus size={12} />}
                </span>
                <span className={item.met ? "text-ink" : "text-ink-muted"}>{item.label}</span>
              </li>
            ))}
          </ul>

          <p className="mt-4 text-sm text-ink-muted">
            {readiness.missing_summary
              ? `Some useful information is still missing. You can continue and provide it later if available. (${readiness.missing_summary})`
              : "You have provided all the recommended information. You can still add more evidence any time."}
          </p>
        </>
      )}
    </div>
  );
}
