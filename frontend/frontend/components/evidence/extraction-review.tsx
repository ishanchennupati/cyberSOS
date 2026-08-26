"use client";

import { useState } from "react";
import { AlertTriangle, Check, Pencil } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  EMPTY_EXTRACTED_DATA,
  EXTRACTED_FIELD_LABELS,
  type ComparisonResult,
  type ExtractedFinancialData,
} from "@/types/evidence";

interface ExtractionReviewProps {
  data: ExtractedFinancialData | null;
  status: "pending" | "processing" | "completed" | "failed";
  verified: boolean;
  comparison: ComparisonResult | null;
  onConfirm: (data: ExtractedFinancialData) => Promise<void> | void;
  busy?: boolean;
}

const FIELD_ORDER: (keyof ExtractedFinancialData)[] = [
  "amount",
  "transaction_id",
  "payment_method",
  "date",
  "time",
  "bank",
  "wallet",
  "merchant",
  "upi_id",
  "phone_number",
  "email",
  "website_url",
];

export function ExtractionReview({
  data,
  status,
  verified,
  comparison,
  onConfirm,
  busy,
}: ExtractionReviewProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<ExtractedFinancialData>(data ?? EMPTY_EXTRACTED_DATA);

  if (status === "processing" || status === "pending") {
    return (
      <div className="rounded-lg border border-line bg-surface p-5 text-sm text-ink-muted">
        Reading this file for useful details…
      </div>
    );
  }

  if (status === "failed" || !data) {
    return (
      <div className="rounded-lg border border-line bg-surface p-5">
        <p className="text-sm text-ink-muted">
          Extraction unavailable. You can enter these details yourself instead.
        </p>
        <ManualEntryForm
          draft={draft}
          setDraft={setDraft}
          onConfirm={onConfirm}
          busy={busy}
        />
      </div>
    );
  }

  const populatedFields = FIELD_ORDER.filter((f) => data[f] !== null && data[f] !== undefined);

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <h3 className="font-display text-xl text-ink">We found these details</h3>
      <p className="mt-2 text-sm text-ink-muted">
        Please verify these details. Information extracted from uploaded evidence may be
        incorrect.
      </p>

      {!editing ? (
        <>
          {populatedFields.length === 0 ? (
            <p className="mt-4 text-sm text-ink-muted">
              We couldn&apos;t confidently find any details in this file. You can enter them
              manually.
            </p>
          ) : (
            <dl className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              {populatedFields.map((field) => (
                <div key={field}>
                  <dt className="text-xs uppercase tracking-wide text-ink-muted">
                    {EXTRACTED_FIELD_LABELS[field]}
                  </dt>
                  <dd className="mt-0.5 text-[15px] font-medium text-ink">
                    {field === "amount" && data.amount !== null
                      ? `₹${data.amount.toLocaleString("en-IN")}`
                      : String(data[field])}
                  </dd>
                </div>
              ))}
            </dl>
          )}

          <div className="mt-6 flex flex-wrap gap-3">
            <Button
              variant="calm"
              onClick={() => onConfirm(data)}
              disabled={busy || verified}
            >
              <Check size={16} aria-hidden="true" />
              {verified ? "Confirmed" : "Confirm details"}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setDraft(data);
                setEditing(true);
              }}
              disabled={busy}
            >
              <Pencil size={16} aria-hidden="true" />
              Edit
            </Button>
          </div>
        </>
      ) : (
        <ManualEntryForm
          draft={draft}
          setDraft={setDraft}
          onConfirm={async (d) => {
            await onConfirm(d);
            setEditing(false);
          }}
          onCancel={() => setEditing(false)}
          busy={busy}
        />
      )}

      {comparison && comparison.comparisons.length > 0 && (
        <ComparisonPanel comparison={comparison} />
      )}
    </div>
  );
}

function ManualEntryForm({
  draft,
  setDraft,
  onConfirm,
  onCancel,
  busy,
}: {
  draft: ExtractedFinancialData;
  setDraft: (d: ExtractedFinancialData) => void;
  onConfirm: (d: ExtractedFinancialData) => Promise<void> | void;
  onCancel?: () => void;
  busy?: boolean;
}) {
  function set<K extends keyof ExtractedFinancialData>(key: K, value: string) {
    setDraft({
      ...draft,
      [key]: key === "amount" ? (value.trim() ? Number(value) : null) : value.trim() || null,
    });
  }

  return (
    <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
      {FIELD_ORDER.map((field) => (
        <label key={field} className="block text-sm">
          <span className="text-ink-muted">{EXTRACTED_FIELD_LABELS[field]}</span>
          <input
            type={field === "amount" ? "number" : "text"}
            value={draft[field] ?? ""}
            onChange={(e) => set(field, e.target.value)}
            className="mt-1 w-full rounded-md border border-line2 bg-white px-3 py-2 text-[15px] text-ink focus-visible:outline-none"
          />
        </label>
      ))}
      <div className="col-span-full mt-2 flex flex-wrap gap-3">
        <Button variant="calm" onClick={() => onConfirm(draft)} disabled={busy}>
          <Check size={16} aria-hidden="true" />
          Confirm details
        </Button>
        {onCancel && (
          <Button variant="outline" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
        )}
      </div>
    </div>
  );
}

function ComparisonPanel({ comparison }: { comparison: ComparisonResult }) {
  return (
    <div
      className={cn(
        "mt-6 rounded-md border px-4 py-4",
        comparison.all_match ? "border-calm bg-calm-soft" : "border-warn bg-warn-soft"
      )}
    >
      <p className="flex items-center gap-2 font-medium text-ink">
        {comparison.all_match ? (
          <>
            <Check size={16} className="text-calm" aria-hidden="true" />
            Evidence matches your incident
          </>
        ) : (
          <>
            <AlertTriangle size={16} className="text-warn" aria-hidden="true" />
            Check required
          </>
        )}
      </p>
      <ul className="mt-3 space-y-2 text-sm">
        {comparison.comparisons.map((c) => (
          <li key={c.field}>
            {c.matches ? (
              <span className="text-ink">
                <Check size={14} className="mr-1 inline text-calm" aria-hidden="true" />
                {c.label} matches
              </span>
            ) : (
              <div className="text-ink">
                <span>
                  <AlertTriangle size={14} className="mr-1 inline text-warn" aria-hidden="true" />
                  {c.label} differs
                </span>
                <div className="mt-1 ml-5 grid grid-cols-2 gap-2 text-ink-muted">
                  <span>Incident: {c.incident_value ?? "—"}</span>
                  <span>Evidence: {c.evidence_value ?? "—"}</span>
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>
      {!comparison.all_match && (
        <p className="mt-3 text-sm text-ink-muted">
          Please verify this information. Nothing has been changed automatically — you decide
          which value is correct.
        </p>
      )}
    </div>
  );
}
