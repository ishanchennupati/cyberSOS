interface LoadingStateProps {
  /**
   * Keep this to what is actually happening. Never imply a government
   * system, bank, or authority is being contacted unless it truly is.
   */
  message?: string;
}

export function LoadingState({ message = "Preparing your incident…" }: LoadingStateProps) {
  return (
    <div role="status" className="flex items-center gap-3 py-4 text-ink-muted">
      <span
        aria-hidden="true"
        className="h-4 w-4 animate-spin rounded-full border-2 border-line2 border-t-ink"
      />
      <span className="text-sm">{message}</span>
    </div>
  );
}
