import { useState, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { OptionCard } from "@/components/option-card";
import { cn } from "@/lib/utils";

export const SITUATION_OPTIONS = [
  // Financial / Payment Related
  { id: "money_taken", label: "Money was taken from my account" },
  { id: "tricked_into_sending", label: "I was tricked into sending money" },
  { id: "account_accessed", label: "Someone accessed my bank/payment account" },
  // Other Cybercrime
  { id: "account_hacked", label: "My account was hacked" },
  { id: "suspicious_message", label: "I received a suspicious message, email or link" },
  { id: "other_cybercrime", label: "Other cybercrime" },
  { id: "not_sure", label: "I'm not sure what happened" },
] as const;

export type SituationId = (typeof SITUATION_OPTIONS)[number]["id"];

interface StepSituationProps {
  value: SituationId | null;
  onChange: (value: SituationId) => void;
  description: string;
  onDescriptionChange: (description: string) => void;
}

export function StepSituation({
  value,
  onChange,
  description,
  onDescriptionChange,
}: StepSituationProps) {
  const financialOptionIds = ["money_taken", "tricked_into_sending", "account_accessed"];
  const otherOptionIds = ["account_hacked", "suspicious_message", "other_cybercrime", "not_sure"];

  const isOtherSelected = value !== null && otherOptionIds.includes(value);
  const [showOther, setShowOther] = useState(isOtherSelected);

  // Sync state if value changes (e.g., initial load or back button)
  useEffect(() => {
    if (isOtherSelected) {
      setShowOther(true);
    }
  }, [isOtherSelected, value]);

  const financialOptions = SITUATION_OPTIONS.filter((opt) =>
    financialOptionIds.includes(opt.id)
  );

  const otherOptions = SITUATION_OPTIONS.filter((opt) =>
    otherOptionIds.includes(opt.id)
  );

  return (
    <div>
      <h1 className="font-display text-3xl text-ink sm:text-4xl">
        Let&rsquo;s understand what happened.
      </h1>
      <h2 className="mt-8 text-lg font-medium text-ink">
        Please select the option that best describes your complaint.
      </h2>

      {/* Financial / Payment Related Section */}
      <div className="mt-8">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-ink-muted mb-3">
          Financial / Payment Related
        </h3>
        <div role="radiogroup" aria-label="Financial / Payment Related" className="flex flex-col gap-3">
          {financialOptions.map((option) => (
            <OptionCard
              key={option.id}
              selected={value === option.id}
              onSelect={() => {
                onChange(option.id);
                setShowOther(false);
              }}
              label={option.label}
            />
          ))}
        </div>
      </div>

      {/* Other Cybercrime Trigger and Section */}
      <div className="mt-6">
        <button
          type="button"
          onClick={() => setShowOther(!showOther)}
          className={cn(
            "flex w-full items-center justify-between rounded-md border px-5 py-4 text-left transition-colors",
            showOther
              ? "border-ink bg-white shadow-card"
              : "border-line bg-surface hover:border-line2"
          )}
        >
          <span className="text-[15px] text-ink">Other Cybercrime</span>
          <ChevronDown
            size={18}
            className={cn(
              "text-ink-muted transition-transform duration-200",
              showOther && "rotate-180 text-ink"
            )}
          />
        </button>

        {showOther && (
          <div
            role="radiogroup"
            aria-label="Other Cybercrime"
            className="mt-3 ml-4 flex flex-col gap-3 border-l border-line pl-4 transition-all duration-300 ease-in-out"
          >
            {otherOptions.map((option) => (
              <div key={option.id} className="flex flex-col gap-2">
                <OptionCard
                  selected={value === option.id}
                  onSelect={() => onChange(option.id)}
                  label={option.label}
                />
                {option.id === "other_cybercrime" && value === "other_cybercrime" && (
                  <div className="mt-1 ml-4 animate-in fade-in slide-in-from-top-2 duration-200">
                    <textarea
                      value={description}
                      onChange={(e) => onDescriptionChange(e.target.value)}
                      placeholder="Explain your situation here..."
                      rows={3}
                      className="w-full rounded-md border border-line2 bg-white px-4 py-3 text-[15px] text-ink placeholder-ink-faint focus:border-ink focus:outline-none transition-colors duration-200 resize-y"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

