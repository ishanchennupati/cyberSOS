import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Something didn't work", message, onRetry }: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-3 rounded-lg border border-urgent/30 bg-urgent-soft px-5 py-4"
    >
      <div className="flex items-center gap-2">
        <AlertTriangle size={18} className="text-urgent shrink-0" aria-hidden="true" />
        <p className="font-medium text-ink">{title}</p>
      </div>
      <p className="text-sm text-ink-muted">{message}</p>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
