import { ExternalLink, Phone } from "lucide-react";

const WOMEN_CHILDREN_URL = "https://cybercrime.gov.in/Webform/Crime_ReportAnonymously.aspx";

export function StepWomenChildrenRedirect() {
  return (
    <div>
      <h1 className="font-display text-3xl text-ink sm:text-4xl">
        Please report this directly on the official portal.
      </h1>
      <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-ink-muted">
        Women and children related cyber crime can involve highly sensitive and urgent harm. CyberSOS
        will not collect incident details, evidence, or personal information for this category in this
        prototype. Please use the official government reporting path below.
      </p>
      <div className="mt-8 rounded-lg border border-line bg-surface px-5 py-5">
        <a
          href={WOMEN_CHILDREN_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-md bg-urgent px-4 py-3 text-sm font-medium text-white hover:bg-urgent-hover"
        >
          <ExternalLink size={16} aria-hidden="true" />
          Open official Women/Children reporting section
        </a>
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {[
            ["Women Helpline", "181"],
            ["Childline", "1098"],
            ["Cyber fraud helpline", "1930"],
          ].map(([label, phone]) => (
            <a
              key={phone}
              href={`tel:${phone}`}
              className="flex items-center gap-3 rounded-md border border-line2 bg-white px-4 py-3 text-ink hover:border-ink"
            >
              <Phone size={16} aria-hidden="true" />
              <span>
                <span className="block text-xs uppercase tracking-widest text-ink-muted">{label}</span>
                <span className="block text-lg font-medium">{phone}</span>
              </span>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
