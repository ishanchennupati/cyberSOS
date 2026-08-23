import { ArrowLeft, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

interface FlowNavProps {
  onBack?: () => void;
  onNext: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  backLabel?: string;
  busy?: boolean;
}

export function FlowNav({
  onBack,
  onNext,
  nextLabel = "Continue",
  nextDisabled = false,
  backLabel = "Back",
  busy = false,
}: FlowNavProps) {
  return (
    <div className="mt-8 flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between">
      {onBack ? (
        <Button type="button" variant="outline" onClick={onBack} disabled={busy}>
          <ArrowLeft size={16} aria-hidden="true" />
          {backLabel}
        </Button>
      ) : (
        <span />
      )}
      <Button
        type="button"
        variant="urgent"
        size="lg"
        disabled={nextDisabled || busy}
        onClick={onNext}
        className="w-full sm:w-auto"
      >
        {nextLabel}
        <ArrowRight size={18} aria-hidden="true" />
      </Button>
    </div>
  );
}
