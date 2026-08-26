import { cn } from "@/lib/utils";

interface OptionCardProps {
  selected: boolean;
  onSelect: () => void;
  label: string;
  description?: string;
  disabled?: boolean;
  badge?: string;
  name?: string;
}

export function OptionCard({
  selected,
  onSelect,
  label,
  description,
  disabled = false,
  badge,
  name,
}: OptionCardProps) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      aria-disabled={disabled}
      disabled={disabled}
      name={name}
      onClick={onSelect}
      className={cn(
        "flex items-start gap-3 rounded-md border px-5 py-4 text-left transition-colors",
        disabled && "cursor-not-allowed opacity-60",
        selected && !disabled && "border-ink bg-white shadow-card",
        !selected && !disabled && "border-line bg-surface hover:border-line2",
        disabled && "border-line bg-surface"
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2",
          selected && !disabled ? "border-ink" : "border-line2"
        )}
      >
        {selected && !disabled && <span className="h-2.5 w-2.5 rounded-full bg-ink" />}
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex flex-wrap items-center gap-2">
          <span className="text-[15px] text-ink">{label}</span>
          {badge && (
            <span className="rounded-full border border-line2 px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest text-ink-muted">
              {badge}
            </span>
          )}
        </span>
        {description && (
          <span className="mt-1 block text-sm leading-relaxed text-ink-muted">{description}</span>
        )}
      </span>
    </button>
  );
}
