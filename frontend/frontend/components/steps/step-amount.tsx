import { OptionCard } from "@/components/option-card";
import { formatInr, parseAmountInput } from "@/lib/format";
import { PAYMENT_METHOD_OPTIONS, type PaymentMethod } from "@/types/incident";

interface StepAmountProps {
  amount: string;
  paymentMethod: PaymentMethod | null;
  onAmountChange: (value: string) => void;
  onPaymentMethodChange: (value: PaymentMethod) => void;
}

export function StepAmount({
  amount,
  paymentMethod,
  onAmountChange,
  onPaymentMethodChange,
}: StepAmountProps) {
  const parsed = parseAmountInput(amount);

  return (
    <div>
      <h1 className="font-display text-3xl text-ink sm:text-4xl">How much, and how was it paid?</h1>
      <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-ink-muted">
        The amount and the payment method change who you call and how a reversal is requested.
      </p>

      <label className="mt-8 block">
        <span className="text-sm font-medium text-ink">Amount involved</span>
        <span className="mt-2 flex items-center gap-2 rounded-md border border-line2 bg-white px-4 focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-ink">
          <span className="font-display text-2xl text-ink-muted" aria-hidden="true">
            ₹
          </span>
          <input
            type="text"
            inputMode="decimal"
            autoComplete="off"
            placeholder="0"
            value={amount}
            onChange={(event) => onAmountChange(event.target.value)}
            className="h-14 w-full bg-transparent text-2xl text-ink outline-none"
            aria-describedby="amount-help"
          />
        </span>
        <span id="amount-help" className="mt-2 block text-sm text-ink-muted">
          {parsed !== null && parsed > 0
            ? `That's ₹${formatInr(parsed)}`
            : "Enter the amount that left your account, as on the debit SMS."}
        </span>
      </label>

      <h2 className="mt-10 text-lg font-medium text-ink">Payment method</h2>
      <div
        role="radiogroup"
        aria-label="Payment method"
        className="mt-4 flex flex-col gap-3"
      >
        {PAYMENT_METHOD_OPTIONS.map((option) => (
          <OptionCard
            key={option.id}
            selected={paymentMethod === option.id}
            onSelect={() => onPaymentMethodChange(option.id)}
            label={option.label}
            description={option.description}
          />
        ))}
      </div>
    </div>
  );
}
