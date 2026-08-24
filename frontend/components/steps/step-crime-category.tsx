import { OptionCard } from "@/components/option-card";
import {
  TOP_LEVEL_CRIME_OPTIONS,
  type TopLevelCrimeCategory,
} from "@/types/incident";

interface StepCrimeCategoryProps {
  value: TopLevelCrimeCategory | null;
  onChange: (value: TopLevelCrimeCategory) => void;
}

export function StepCrimeCategory({ value, onChange }: StepCrimeCategoryProps) {
  return (
    <div>
      <h1 className="font-display text-3xl text-ink sm:text-4xl">
        What type of cyber crime do you want help with?
      </h1>
      <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-ink-muted">
        Choose the same top-level category used by the National Cyber Crime Reporting Portal.
      </p>
      <div role="radiogroup" aria-label="Cyber crime category" className="mt-8 flex flex-col gap-3">
        {TOP_LEVEL_CRIME_OPTIONS.map((option) => (
          <OptionCard
            key={option.id}
            selected={value === option.id}
            onSelect={() => onChange(option.id)}
            label={option.label}
            description={option.description}
          />
        ))}
      </div>
    </div>
  );
}
