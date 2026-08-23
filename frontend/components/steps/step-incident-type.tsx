import { OptionCard } from "@/components/option-card";
import { INCIDENT_TYPE_OPTIONS, type IncidentType } from "@/types/incident";

interface StepIncidentTypeProps {
  value: IncidentType | null;
  onChange: (value: IncidentType) => void;
}

export function StepIncidentType({ value, onChange }: StepIncidentTypeProps) {
  return (
    <div>
      <h1 className="font-display text-3xl text-ink sm:text-4xl">What kind of incident is this?</h1>
      <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-ink-muted">
        Phase 1 of CyberSOS is built for UPI and financial fraud. Other types are listed so you
        can see what&rsquo;s coming — they aren&rsquo;t available yet.
      </p>
      <div
        role="radiogroup"
        aria-label="Incident type"
        className="mt-8 flex flex-col gap-3"
      >
        {INCIDENT_TYPE_OPTIONS.map((option) => (
          <OptionCard
            key={option.id}
            selected={value === option.id}
            onSelect={() => onChange(option.id)}
            label={option.label}
            description={option.description}
            disabled={!option.enabled}
            badge={option.enabled ? undefined : "Coming soon"}
          />
        ))}
      </div>
    </div>
  );
}
