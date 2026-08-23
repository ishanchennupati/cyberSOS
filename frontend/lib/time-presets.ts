export type TimePreset =
  | "just_now"
  | "within_hour"
  | "today"
  | "yesterday"
  | "this_week"
  | "longer_ago"
  | "exact";

export const TIME_PRESETS: {
  id: Exclude<TimePreset, "exact">;
  label: string;
  hint: string;
}[] = [
  { id: "just_now", label: "Just now", hint: "Seconds or a few minutes ago" },
  { id: "within_hour", label: "Within the hour", hint: "Less than 60 minutes ago" },
  { id: "today", label: "Today", hint: "Earlier today, more than an hour ago" },
  { id: "yesterday", label: "Yesterday", hint: "The calendar day before today" },
  { id: "this_week", label: "This week", hint: "In the last few days" },
  { id: "longer_ago", label: "Longer ago / not sure", hint: "More than a week, or you don't know" },
];

function hoursAgo(now: Date, hours: number): Date {
  return new Date(now.getTime() - hours * 60 * 60 * 1000);
}

function daysAgo(now: Date, days: number): Date {
  return new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
}

/**
 * Map a quick-select label to a real occurred_at timestamp.
 * Windows are chosen so each preset lands in a distinct urgency bucket
 * when the clock is a normal daytime hour.
 */
export function occurredAtFromPreset(preset: TimePreset, now: Date = new Date()): Date {
  switch (preset) {
    case "just_now":
      return now;
    case "within_hour":
      return new Date(now.getTime() - 30 * 60 * 1000);
    case "today": {
      const thisMorning = new Date(now);
      thisMorning.setHours(8, 0, 0, 0);
      const sixHours = hoursAgo(now, 6);
      if (now.getTime() - thisMorning.getTime() > 60 * 60 * 1000 && thisMorning < now) {
        return thisMorning;
      }
      return sixHours;
    }
    case "yesterday": {
      const yesterdayNoon = new Date(now);
      yesterdayNoon.setDate(yesterdayNoon.getDate() - 1);
      yesterdayNoon.setHours(12, 0, 0, 0);
      return yesterdayNoon;
    }
    case "this_week":
      return daysAgo(now, 5);
    case "longer_ago":
      return daysAgo(now, 45);
    case "exact":
      return now;
  }
}

export function toDateTimeLocalValue(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

export function fromDateTimeLocalValue(value: string): Date | null {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}
