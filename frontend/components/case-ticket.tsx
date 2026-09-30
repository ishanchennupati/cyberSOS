import { ShieldCheck } from "lucide-react";

/**
 * The page's signature element: a stamped "intake ticket" that reads like
 * a real civic-service form stub, not a product screenshot. It exists to
 * illustrate a synthetic draft; it is not an official or tracked case.
 */
export function CaseTicket() {
  return (
    <div className="relative w-full max-w-sm rounded-lg border border-line2 bg-surface shadow-card">
      <div className="flex items-center justify-between border-b border-dashed border-line2 px-5 py-3">
        <span className="font-mono text-[11px] uppercase tracking-widest text-ink-muted">
          Case intake
        </span>
        <span className="font-mono text-[11px] uppercase tracking-widest text-calm">
          Draft
        </span>
      </div>

      <div className="space-y-4 px-5 py-5">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-widest text-ink-faint">
            Reference
          </p>
          <p className="font-mono text-lg text-ink">CYS-2026-04021</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-ink-faint">
              Category
            </p>
            <p className="text-sm text-ink">Financial fraud</p>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-ink-faint">
              Method
            </p>
            <p className="text-sm text-ink">UPI</p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-md bg-calm-soft px-3 py-2">
          <ShieldCheck size={16} className="text-calm shrink-0" aria-hidden="true" />
          <p className="text-xs text-calm">Evidence checklist ready when you are</p>
        </div>
      </div>

      <div className="border-t border-dashed border-line2 px-5 py-3">
        <p className="font-mono text-[11px] text-ink-faint">Sample only — not a real case</p>
      </div>
    </div>
  );
}
