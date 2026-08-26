import Link from "next/link";
import { ClipboardList, FileSearch, ListChecks, ShieldAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import { CaseTicket } from "@/components/case-ticket";
import { SiteFooter } from "@/components/site-footer";

const steps = [
  {
    icon: ShieldAlert,
    title: "Understand the urgency",
    description: "A few quick questions tell you what needs to happen right now versus later.",
  },
  {
    icon: ClipboardList,
    title: "Take the right immediate steps",
    description: "Clear, ordered actions — blocking cards, freezing accounts, saving evidence.",
  },
  {
    icon: FileSearch,
    title: "Organize your evidence",
    description: "Keep screenshots, transaction IDs, and messages in one place, in order.",
  },
  {
    icon: ListChecks,
    title: "Prepare your official complaint",
    description: "Everything formatted and ready before you file with cybercrime.gov.in.",
  },
];

export default function HomePage() {
  return (
    <main>
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <span className="font-display text-lg italic text-ink">CyberSOS</span>
          <span className="hidden sm:block font-mono text-xs uppercase tracking-widest text-ink-muted">
            Fraud response prototype
          </span>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-6 pt-14 pb-16 sm:pt-20">
        <div className="grid gap-12 lg:grid-cols-[1.2fr_1fr] lg:items-center">
          <div>
            <h1 className="font-display text-[2.5rem] leading-[1.1] text-ink sm:text-[3.25rem]">
              I&rsquo;ve been scammed.
              <br />
              <span className="italic">What do I do now?</span>
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-relaxed text-ink-muted">
              CyberSOS helps you take the right immediate steps, organize your evidence, and
              reach the official cybercrime reporting channels.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link href="/incident/start">
                <Button variant="urgent" size="lg" className="w-full sm:w-auto">
                  I&rsquo;ve Been Scammed
                </Button>
              </Link>
              <a href="#how-it-works">
                <Button variant="outline" size="lg" className="w-full sm:w-auto">
                  How CyberSOS Works
                </Button>
              </a>
            </div>

            <p className="mt-8 max-w-lg text-sm leading-relaxed text-ink-muted border-l-2 border-line2 pl-4">
              CyberSOS is an independent prototype. It does not replace the official
              Government of India Cyber Crime Reporting Portal or the 1930 helpline.
            </p>
          </div>

          <div className="flex justify-center lg:justify-end">
            <CaseTicket />
          </div>
        </div>
      </section>

      <section id="how-it-works" className="border-t border-line bg-surface">
        <div className="mx-auto max-w-5xl px-6 py-16">
          <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
            How CyberSOS works
          </p>
          <h2 className="mt-2 font-display text-2xl text-ink sm:text-3xl">
            Four steps, in the order they actually matter.
          </h2>

          <ol className="mt-10 grid gap-8 sm:grid-cols-2">
            {steps.map((step, idx) => (
              <li key={step.title} className="flex gap-4">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-line2 font-mono text-sm text-ink-muted">
                  {idx + 1}
                </div>
                <div>
                  <p className="font-medium text-ink">{step.title}</p>
                  <p className="mt-1 text-sm leading-relaxed text-ink-muted">
                    {step.description}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <SiteFooter />
    </main>
  );
}
