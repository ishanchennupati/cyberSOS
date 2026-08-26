"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { TimelineEvent } from "@/types/evidence";

interface TimelinePanelProps {
  events: TimelineEvent[];
  onAdd: (eventTimeIso: string, description: string) => Promise<void> | void;
  busy?: boolean;
}

function formatDay(iso: string): string {
  return new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

export function TimelinePanel({ events, onAdd, busy }: TimelinePanelProps) {
  const [adding, setAdding] = useState(false);
  const [when, setWhen] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const grouped = events.reduce<Record<string, TimelineEvent[]>>((acc, event) => {
    const day = formatDay(event.event_time);
    (acc[day] ??= []).push(event);
    return acc;
  }, {});

  async function handleAdd() {
    if (!when || !description.trim()) {
      setError("Please provide both a time and a short description.");
      return;
    }
    setError(null);
    await onAdd(new Date(when).toISOString(), description.trim());
    setWhen("");
    setDescription("");
    setAdding(false);
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-xl text-ink">Timeline</h3>
        {!adding && (
          <Button variant="outline" size="sm" onClick={() => setAdding(true)}>
            <Plus size={14} aria-hidden="true" />
            Add event
          </Button>
        )}
      </div>

      {events.length === 0 && !adding && (
        <p className="mt-3 text-sm text-ink-muted">
          No events yet. Add the moments that matter — when you were contacted, when money moved,
          when you realized something was wrong.
        </p>
      )}

      {Object.entries(grouped).map(([day, dayEvents]) => (
        <div key={day} className="mt-5 first:mt-4">
          <p className="font-mono text-xs uppercase tracking-widest text-ink-muted">{day}</p>
          <ol className="mt-2 space-y-3 border-l border-line pl-4">
            {dayEvents.map((event) => (
              <li key={event.id}>
                <p className="font-mono text-xs text-ink-muted">{formatTime(event.event_time)}</p>
                <p className="text-sm text-ink">{event.description}</p>
              </li>
            ))}
          </ol>
        </div>
      ))}

      {adding && (
        <div className="mt-4 space-y-3 rounded-md border border-line2 bg-paper p-4">
          <label className="block text-sm">
            <span className="text-ink-muted">When</span>
            <input
              type="datetime-local"
              value={when}
              onChange={(e) => setWhen(e.target.value)}
              className="mt-1 w-full rounded-md border border-line2 bg-white px-3 py-2 text-[15px] text-ink focus-visible:outline-none"
            />
          </label>
          <label className="block text-sm">
            <span className="text-ink-muted">What happened</span>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Suspicious call received"
              className="mt-1 w-full rounded-md border border-line2 bg-white px-3 py-2 text-[15px] text-ink focus-visible:outline-none"
            />
          </label>
          {error && (
            <p role="alert" className="text-sm text-urgent">
              {error}
            </p>
          )}
          <div className="flex gap-3">
            <Button variant="calm" size="sm" onClick={handleAdd} disabled={busy}>
              Save event
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setAdding(false)} disabled={busy}>
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
