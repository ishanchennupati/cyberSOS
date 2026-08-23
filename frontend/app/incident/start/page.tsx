"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ProgressSteps } from "@/components/progress-steps";
import { ErrorState } from "@/components/error-state";
import { LoadingState } from "@/components/loading-state";
import { createIncident, ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

const STEPS = [
  { label: "What happened" },
  { label: "Your incident" },
  { label: "Take action" },
  { label: "Evidence" },
  { label: "Report" },
];

const OPTIONS = [
  { id: "money_taken", label: "Money was taken from my account" },
  { id: "tricked_into_sending", label: "I was tricked into sending money" },
  { id: "account_accessed", label: "Someone accessed my bank/payment account" },
  { id: "not_sure", label: "I'm not sure what happened" },
] as const;

type Status = "idle" | "loading" | "error" | "success";

export default function IncidentStartPage() {
  const [selected, setSelected] = useState<(typeof OPTIONS)[number]["id"] | null>(null);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleContinue() {
    if (!selected) return;
    setStatus("loading");
    setErrorMessage("");

    try {
      // All financial-related options lead to the financial-fraud flow for now.
      await createIncident({
        incident_type: "financial_fraud",
        payment_method: "unknown",
      });
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMessage(
        err instanceof ApiError ? err.message : "Something went wrong. Please try again."
      );
    }
  }

  return (
    <main className="min-h-screen bg-paper">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2 text-sm text-ink-muted hover:text-ink">
            <ArrowLeft size={16} aria-hidden="true" />
            Back
          </Link>
          <span className="font-display text-lg italic text-ink">CyberSOS</span>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-6 py-10">
        <ProgressSteps steps={STEPS} currentStep={1} />

        <div className="mt-10">
          <h1 className="font-display text-3xl text-ink sm:text-4xl">
            Let&rsquo;s understand what happened.
          </h1>

          {status === "success" ? (
            <div className="mt-8 rounded-lg border border-calm/30 bg-calm-soft px-6 py-8">
              <p className="font-medium text-ink">Your incident has been started.</p>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                This confirms CyberSOS and the backend are talking to each other. The next
                steps — your incident details, immediate actions, and evidence collection —
                are built in the following phase.
              </p>
            </div>
          ) : (
            <>
              <h2 className="mt-8 text-lg font-medium text-ink">What happened?</h2>

              <div role="radiogroup" aria-label="What happened" className="mt-4 flex flex-col gap-3">
                {OPTIONS.map((option) => {
                  const isSelected = selected === option.id;
                  return (
                    <button
                      key={option.id}
                      type="button"
                      role="radio"
                      aria-checked={isSelected}
                      onClick={() => setSelected(option.id)}
                      className={cn(
                        "flex items-center gap-3 rounded-md border px-5 py-4 text-left text-[15px] transition-colors",
                        isSelected
                          ? "border-ink bg-white shadow-card"
                          : "border-line bg-surface hover:border-line2"
                      )}
                    >
                      <span
                        aria-hidden="true"
                        className={cn(
                          "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2",
                          isSelected ? "border-ink" : "border-line2"
                        )}
                      >
                        {isSelected && <span className="h-2.5 w-2.5 rounded-full bg-ink" />}
                      </span>
                      <span className="text-ink">{option.label}</span>
                    </button>
                  );
                })}
              </div>

              {status === "loading" && <div className="mt-6"><LoadingState /></div>}

              {status === "error" && (
                <div className="mt-6">
                  <ErrorState message={errorMessage} onRetry={handleContinue} />
                </div>
              )}

              <div className="mt-8">
                <Button
                  variant="urgent"
                  size="lg"
                  disabled={!selected || status === "loading"}
                  onClick={handleContinue}
                  className="w-full sm:w-auto"
                >
                  Continue
                  <ArrowRight size={18} aria-hidden="true" />
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
