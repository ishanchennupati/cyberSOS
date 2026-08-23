import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

export interface ProgressStep {
  label: string;
}

interface ProgressStepsProps {
  steps: ProgressStep[];
  /** 1-based index of the step currently active. Steps after this are "upcoming". */
  currentStep: number;
}

export function ProgressSteps({ steps, currentStep }: ProgressStepsProps) {
  return (
    <ol
      aria-label="Incident report progress"
      className="flex flex-col gap-0 sm:flex-row sm:items-stretch sm:gap-0 border border-line rounded-lg bg-surface overflow-hidden"
    >
      {steps.map((step, idx) => {
        const stepNumber = idx + 1;
        const status =
          stepNumber < currentStep ? "done" : stepNumber === currentStep ? "active" : "upcoming";

        return (
          <li
            key={step.label}
            aria-current={status === "active" ? "step" : undefined}
            className={cn(
              "flex flex-1 items-center gap-3 px-4 py-3 border-b sm:border-b-0 sm:border-r border-line last:border-0",
              status === "active" && "bg-calm-soft",
              status === "upcoming" && "opacity-50"
            )}
          >
            <span
              className={cn(
                "flex h-7 w-7 shrink-0 items-center justify-center rounded-full font-mono text-xs font-medium",
                status === "done" && "bg-calm text-white",
                status === "active" && "bg-ink text-white",
                status === "upcoming" && "border border-line2 text-ink-muted"
              )}
            >
              {status === "done" ? <Check size={14} aria-hidden="true" /> : stepNumber}
            </span>
            <span
              className={cn(
                "text-sm font-medium",
                status === "upcoming" ? "text-ink-muted" : "text-ink"
              )}
            >
              {step.label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
