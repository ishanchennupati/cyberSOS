import { AlertTriangle, Info } from "lucide-react";

export function DemoDataBanner() {
  return (
    <div className="flex items-start gap-3 rounded-md border border-warn/40 bg-warn-soft px-4 py-3">
      <AlertTriangle size={18} className="mt-0.5 shrink-0 text-warn" aria-hidden="true" />
      <p className="text-sm leading-relaxed text-ink">
        <span className="font-medium">Demo environment — use synthetic data only.</span>{" "}
        Do not upload real identity documents or sensitive financial information.
      </p>
    </div>
  );
}

export function IndependentPrototypeBanner() {
  return (
    <div className="flex items-start gap-3 rounded-md border border-line bg-surface px-4 py-3">
      <Info size={18} className="mt-0.5 shrink-0 text-ink-muted" aria-hidden="true" />
      <p className="text-sm leading-relaxed text-ink-muted">
        <span className="font-medium text-ink">CyberSOS is an independent prototype.</span> It
        does not replace the official Government of India Cyber Crime Reporting Portal.
        Information and evidence prepared here must be reviewed by you before being used in an
        official complaint.
      </p>
    </div>
  );
}
