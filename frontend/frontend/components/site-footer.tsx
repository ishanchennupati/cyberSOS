import { ExternalLink, Phone } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <p className="font-mono text-xs uppercase tracking-wide text-ink-muted mb-4">
          Official channels
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <a
            href="https://cybercrime.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-3 rounded-md border border-line bg-paper px-4 py-3 hover:border-ink transition-colors"
          >
            <ExternalLink size={18} className="mt-0.5 shrink-0 text-calm" aria-hidden="true" />
            <span>
              <span className="block font-medium text-ink">
                National Cyber Crime Reporting Portal
              </span>
              <span className="block text-sm text-ink-muted">cybercrime.gov.in</span>
            </span>
          </a>

          <a
            href="tel:1930"
            className="flex items-start gap-3 rounded-md border border-line bg-paper px-4 py-3 hover:border-ink transition-colors"
          >
            <Phone size={18} className="mt-0.5 shrink-0 text-urgent" aria-hidden="true" />
            <span>
              <span className="block font-medium text-ink">
                1930 — Financial Cyber Fraud Helpline
              </span>
              <span className="block text-sm text-ink-muted">Call now, 24x7</span>
            </span>
          </a>
        </div>

        <p className="mt-8 text-xs leading-relaxed text-ink-muted max-w-2xl">
          CyberSOS is an independent prototype. It is not affiliated with, and does not
          replace, the official Government of India Cyber Crime Reporting Portal or the
          1930 helpline.
        </p>
      </div>
    </footer>
  );
}
