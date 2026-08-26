"use client";

import { OptionCard } from "@/components/option-card";
import { EVIDENCE_TYPE_OPTIONS, type EvidenceType } from "@/types/evidence";

interface EvidenceCategoryPickerProps {
  value: EvidenceType | null;
  onChange: (value: EvidenceType) => void;
}

export function EvidenceCategoryPicker({ value, onChange }: EvidenceCategoryPickerProps) {
  return (
    <div>
      <h3 className="font-display text-xl text-ink">What type of evidence is this?</h3>
      <div role="radiogroup" aria-label="Evidence category" className="mt-4 grid gap-3 sm:grid-cols-2">
        {EVIDENCE_TYPE_OPTIONS.map((option) => (
          <OptionCard
            key={option.id}
            name="evidence-category"
            label={option.label}
            selected={value === option.id}
            onSelect={() => onChange(option.id)}
          />
        ))}
      </div>
    </div>
  );
}
