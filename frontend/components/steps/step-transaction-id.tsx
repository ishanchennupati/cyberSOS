interface StepTransactionIdProps {
  value: string;
  onChange: (value: string) => void;
  status: "unknown" | "pending" | "completed";
  onStatusChange: (value: "unknown" | "pending" | "completed") => void;
  ongoing: boolean;
  onOngoingChange: (value: boolean) => void;
}

export function StepTransactionId({ value, onChange, status, onStatusChange, ongoing, onOngoingChange }: StepTransactionIdProps) {
  return (
    <div>
      <h1 className="font-display text-3xl text-ink sm:text-4xl">
        Do you have the transaction ID / UTR?
      </h1>
      <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-ink-muted">
        This is optional — many people don&rsquo;t have it in front of them. If you can add it,
        1930 and your bank can find the debit much faster.
      </p>

      <label className="mt-8 block">
        <span className="text-sm font-medium text-ink">Transaction ID / UTR</span>
        <input
          type="text"
          inputMode="text"
          autoComplete="off"
          spellCheck={false}
          placeholder="e.g. 123456789012"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="mt-2 h-12 w-full rounded-md border border-line2 bg-white px-4 font-mono text-[15px] text-ink"
        />
      </label>

      <label className="mt-6 block">
        <span className="text-sm font-medium text-ink">Transaction status</span>
        <select value={status} onChange={(event) => onStatusChange(event.target.value as "unknown" | "pending" | "completed")} className="mt-2 h-12 w-full rounded-md border border-line2 bg-white px-4 text-[15px] text-ink">
          <option value="unknown">I&apos;m not sure</option>
          <option value="pending">Still pending</option>
          <option value="completed">Completed</option>
        </select>
      </label>

      <label className="mt-5 flex items-start gap-3 text-sm text-ink">
        <input type="checkbox" checked={ongoing} onChange={(event) => onOngoingChange(event.target.checked)} className="mt-1 h-4 w-4" />
        <span>I think unauthorized activity may still be continuing or more money could be lost.</span>
      </label>

      <div className="mt-6 rounded-md border border-line bg-surface px-5 py-4 text-sm leading-relaxed text-ink-muted">
        <p className="font-medium text-ink">Where to find it</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>UPI app → transaction history → this payment → UTR / transaction ID</li>
          <li>The debit SMS from your bank (often labelled UTR, Txn ID, or Ref)</li>
          <li>Your bank statement or passbook entry for this debit</li>
        </ul>
        <p className="mt-3">You can continue without it and still get an action plan.</p>
      </div>
    </div>
  );
}
