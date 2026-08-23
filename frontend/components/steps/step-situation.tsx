import { OptionCard } from "@/components/option-card";

export const SITUATION_OPTIONS = [
  { id: "money_taken", label: "Money was taken from my account" },
  { id: "tricked_into_sending", label: "I was tricked into sending money" },
  { id: "account_accessed", label: "Someone accessed my bank/payment account" },
  { id: "not_sure", label: "I'm not sure what happened" },
] as const;

export type SituationId = (typeof SITUATION_OPTIONS)[number]["id"];

interface StepSituationProps {
  value: SituationId | null;
  onChange: (value: SituationId) => void;
}

export function StepSituation({ value, onChange }: StepSituationProps) {
  return (
    <div>
      <h1 className="font-display text-3xl text-ink sm:text-4xl">
        Let&rsquo;s understand what happened.
      </h1>
      <h2 className="mt-8 text-lg font-medium text-ink">What happened?</h2>
      <div role="radiogroup" aria-label="What happened" className="mt-4 flex flex-col gap-3">
        {SITUATION_OPTIONS.map((option) => (
          <OptionCard
            key={option.id}
            selected={value === option.id}
            onSelect={() => onChange(option.id)}
            label={option.label}
          />
        ))}
      </div>
    </div>
  );
}
