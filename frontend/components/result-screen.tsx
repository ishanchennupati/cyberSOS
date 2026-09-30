"use client";

import { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Check,
  Clock,
  Copy,
  ExternalLink,
  FileText,
  Phone,
  Siren,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ActionItem, ActionPlan, Urgency } from "@/types/incident";

const BADGE: Record<
  Urgency,
  {
    label: string;
    icon: typeof Siren;
    className: string;
    iconClass: string;
  }
> = {
  critical: {
    label: "ACT NOW",
    icon: Siren,
    className: "bg-urgent text-white border-urgent",
    iconClass: "text-white",
  },
  high: {
    label: "ACT TODAY",
    icon: AlertTriangle,
    className: "bg-warn text-white border-warn",
    iconClass: "text-white",
  },
  medium: {
    label: "ACT THIS WEEK",
    icon: Clock,
    className: "bg-warn-soft text-warn border-warn",
    iconClass: "text-warn",
  },
  medium_low: {
    label: "FILE WHEN READY",
    icon: FileText,
    className: "bg-calm-soft text-calm border-calm",
    iconClass: "text-calm",
  },
  standard: {
    label: "FILE WHEN READY",
    icon: FileText,
    className: "bg-calm-soft text-calm border-calm",
    iconClass: "text-calm",
  },
  low: {
    label: "FILE WHEN READY",
    icon: FileText,
    className: "bg-calm-soft text-calm border-calm",
    iconClass: "text-calm",
  },
};

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.left = "-9999px";
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(area);
      return ok;
    } catch {
      return false;
    }
  }
}

function ActionRow({ item, index }: { item: ActionItem; index: number }) {
  return (
    <li className="flex gap-4 border-b border-line px-5 py-5 last:border-0">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink font-mono text-sm text-white">
        {index}
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-ink">{item.title}</p>
        <p className="mt-1 text-sm leading-relaxed text-ink">{item.instruction}</p>
        <p className="mt-1 text-sm leading-relaxed text-ink-muted">{item.why}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {item.phone && (
            <a
              href={`tel:${item.phone}`}
              className="inline-flex items-center gap-2 rounded-md bg-urgent px-3 py-2 text-sm font-medium text-white hover:bg-urgent-hover"
            >
              <Phone size={14} aria-hidden="true" />
              Call {item.phone}
            </a>
          )}
          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-md border border-line2 bg-white px-3 py-2 text-sm font-medium text-ink hover:border-ink"
            >
              <ExternalLink size={14} aria-hidden="true" />
              {item.url_label ?? item.url.replace(/^https?:\/\//, "")}
            </a>
          )}
        </div>
      </div>
    </li>
  );
}

interface ResultScreenProps {
  plan: ActionPlan;
  incidentId: string;
}

export function ResultScreen({ plan, incidentId }: ResultScreenProps) {
  const badge = BADGE[plan.urgency];
  const Icon = badge.icon;
  const [showDraft, setShowDraft] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    const ok = await copyText(plan.complaint_draft.body);
    if (ok) {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div>
      <div
        role="status"
        className={cn(
          "rounded-lg border-2 px-6 py-8 sm:px-8",
          badge.className
        )}
      >
        <div className="flex items-start gap-4">
          <Icon size={40} className={cn("shrink-0", badge.iconClass)} aria-hidden="true" />
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.2em] opacity-80">Urgency</p>
            <p className="mt-1 font-display text-4xl leading-none sm:text-5xl">{plan.urgency_label}</p>
            <p className="mt-4 max-w-xl text-[15px] leading-relaxed sm:text-base">
              {plan.core_message}
            </p>
          </div>
        </div>
      </div>

      {Boolean(plan.urgency_reasons?.length) && (
        <section className="mt-6 rounded-lg border border-line bg-surface px-5 py-5" aria-labelledby="urgency-reasons">
          <h2 id="urgency-reasons" className="font-display text-2xl text-ink">Why this is urgent</h2>
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-relaxed text-ink-muted">
            {plan.urgency_reasons?.map((reason) => (
              <li key={reason.rule_id}>{reason.human_readable_reason}</li>
            ))}
          </ul>
        </section>
      )}

      <h2 className="mt-10 font-display text-2xl text-ink">Do these, in this order</h2>
      <ol className="mt-4 overflow-hidden rounded-lg border border-line bg-surface">
        {plan.actions.map((item, index) => (
          <ActionRow key={`${item.id}-${index}`} item={item} index={index + 1} />
        ))}
      </ol>

      <div className="mt-10 rounded-lg border-2 border-ink bg-white px-6 py-8 shadow-card">
        <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">
          Official complaint
        </p>
        <h2 className="mt-2 font-display text-2xl text-ink">Prepare your complaint</h2>
        <p className="mt-2 max-w-xl text-[15px] leading-relaxed text-ink-muted">
          Your answers are now a complaint draft. Review it, then open the official portal to file
          it yourself. CyberSOS does not submit complaints or track government responses.
        </p>
        {!showDraft ? (
          <Button
            variant="calm"
            size="lg"
            className="mt-6 w-full sm:w-auto"
            onClick={() => setShowDraft(true)}
          >
            <FileText size={18} aria-hidden="true" />
            Prepare complaint
          </Button>
        ) : (
          <div className="mt-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-medium text-ink">Complaint draft</p>
              <Button variant="outline" size="sm" onClick={handleCopy}>
                {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
                {copied ? "Copied" : "Copy to clipboard"}
              </Button>
            </div>
            <pre className="mt-3 max-h-[28rem] overflow-auto whitespace-pre-wrap rounded-md border border-line bg-paper px-4 py-4 font-mono text-[13px] leading-relaxed text-ink">
              {plan.complaint_draft.body}
            </pre>
            <a
              href="https://cybercrime.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-calm hover:underline"
            >
              Open official filing portal
              <ExternalLink size={14} aria-hidden="true" />
            </a>
          </div>
        )}
      </div>

      <div className="mt-10 rounded-lg border-2 border-calm bg-calm-soft px-6 py-8 sm:px-8">
        <p className="font-mono text-xs uppercase tracking-widest text-calm">Next step</p>
        <h2 className="mt-2 font-display text-2xl text-ink">Add your evidence</h2>
        <p className="mt-2 max-w-xl text-[15px] leading-relaxed text-ink-muted">
          Screenshots, receipts, messages, and suspect details — organized in one place before you
          file. Nothing is submitted anywhere on your behalf.
        </p>
        <Link href={`/incident/${incidentId}/evidence`}>
          <Button variant="calm" size="lg" className="mt-6 w-full sm:w-auto">
            <FileText size={18} aria-hidden="true" />
            Go to evidence vault
          </Button>
        </Link>
      </div>

      <div className="mt-8 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
        <Link href={`/incident/start?id=${incidentId}`} className="text-sm font-medium text-calm underline-offset-2 hover:underline">
          Go back to edit your answers
        </Link>
        <span className="hidden sm:inline text-line" aria-hidden="true">|</span>
        <Link href="/" className="text-sm text-ink-muted underline-offset-2 hover:underline">
          Back to CyberSOS home
        </Link>
      </div>
    </div>
  );
}
