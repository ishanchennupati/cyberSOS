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

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
