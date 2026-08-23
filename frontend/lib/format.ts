export function formatInr(amount: number): string {
  const sign = amount < 0 ? "-" : "";
  const [rupees, paise] = Math.abs(amount).toFixed(2).split(".");
  let grouped: string;
  if (rupees.length <= 3) {
    grouped = rupees;
  } else {
    const last3 = rupees.slice(-3);
    let rest = rupees.slice(0, -3);
    const parts: string[] = [];
    while (rest.length > 0) {
      parts.push(rest.slice(-2));
      rest = rest.slice(0, -2);
    }
    grouped = `${parts.reverse().join(",")},${last3}`;
  }
  return `${sign}${grouped}.${paise}`;
}

export function parseAmountInput(raw: string): number | null {
  const trimmed = raw.trim().replace(/,/g, "");
  if (!trimmed) return null;
  const value = Number(trimmed);
  if (!Number.isFinite(value)) return null;
  return value;
}
