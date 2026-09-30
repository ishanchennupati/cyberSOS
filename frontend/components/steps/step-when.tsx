import { OptionCard } from "@/components/option-card";
import {
  TIME_PRESETS,
  type TimePreset,
  toDateTimeLocalValue,
} from "@/lib/time-presets";
import { cn } from "@/lib/utils";

interface StepWhenProps {
  preset: TimePreset | null;
  exactValue: string;
  onPreset: (preset: TimePreset) => void;
  onExactChange: (value: string) => void;
}

export function StepWhen({ preset, exactValue, onPreset, onExactChange }: StepWhenProps) {
  const exactSelected = preset === "exact";

  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-widest text-urgent">
        Incident timing
      </p>
      <h1 className="mt-2 font-display text-3xl text-ink sm:text-4xl">When did this happen?</h1>
      <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-ink-muted">
        This helps organize the incident timeline. Pick the closest option or enter an exact time
        if you know it. CyberSOS cannot predict whether funds will be recovered.
      </p>

      <div
        role="radiogroup"
        aria-label="When the incident happened"
        className="mt-8 grid gap-3 sm:grid-cols-2"
      >
        {TIME_PRESETS.map((option) => (
          <OptionCard
            key={option.id}
            selected={preset === option.id}
            onSelect={() => onPreset(option.id)}
            label={option.label}
            description={option.hint}
          />
        ))}
      </div>

      <div className="mt-6 rounded-md border border-line bg-surface px-5 py-4">
        <button
          type="button"
          role="radio"
          aria-checked={exactSelected}
          onClick={() => onPreset("exact")}
          className="flex w-full items-center gap-3 text-left"
        >
          <span
            aria-hidden="true"
            className={cn(
              "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2",
              exactSelected ? "border-ink" : "border-line2"
            )}
          >
            {exactSelected && <span className="h-2.5 w-2.5 rounded-full bg-ink" />}
          </span>
          <span className="text-[15px] font-medium text-ink">I know the exact date and time</span>
        </button>
        <label className="mt-4 block">
          <span className="sr-only">Exact date and time of the transaction</span>
          <input
            type="datetime-local"
            value={exactValue}
            max={toDateTimeLocalValue(new Date())}
            onChange={(event) => onExactChange(event.target.value)}
            className="h-12 w-full rounded-md border border-line2 bg-white px-3 text-[15px] text-ink"
          />
        </label>
        <p className="mt-2 text-sm text-ink-muted">Use the time shown on the debit SMS or UPI receipt.</p>
      </div>
    </div>
  );
}
