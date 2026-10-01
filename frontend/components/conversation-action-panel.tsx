"use client";

import { Check, ExternalLink, Phone, Siren } from 'lucide-react';
import type { ActionItem } from '@/types/incident';

// Presentation of server-approved actions only; no facts or action selection here.
export function isImmediateAction(action: ActionItem) {
  // Containment is presented as ACT NOW; reporting joins it only when the
  // playbook explicitly marks that reporting action critical.
  return action.phase === 'CONTAIN' || (action.phase === 'REPORT' && action.critical);
}

interface Props {
  actions: ActionItem[];
  completed: Map<string, boolean>;
  disabled: boolean;
  onComplete: (actionId: string, completed: boolean) => void;
}

function ActionCard({ action, completed, disabled, onComplete }: {
  action: ActionItem; completed: boolean; disabled: boolean; onComplete: Props['onComplete'];
}) {
  const immediate = isImmediateAction(action);
  const control = 'inline-flex min-h-12 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2';
  return <li value={action.order} data-action-id={action.id} data-action-order={action.order}
    data-action-phase={action.phase} data-action-priority={action.priority}
    className="flex gap-3 border-b border-line p-4 last:border-0 sm:gap-4 sm:p-5">
    <span aria-hidden="true" className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-mono text-sm text-white ${immediate ? 'bg-urgent' : 'bg-ink'}`}>{action.order}</span>
    <div className="min-w-0 flex-1">
      <span className="sr-only">Step {action.order}.</span>
      <h3 className="font-sans text-base font-semibold leading-snug">{action.title}</h3>
      <p className="mt-2 text-sm leading-relaxed">{action.instruction}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {action.phone && <a href={`tel:${action.phone}`} className={`${control} ${immediate ? 'bg-urgent text-white hover:bg-urgent-hover' : 'bg-ink text-white'}`}><Phone size={16} aria-hidden="true" />Call {action.phone}</a>}
        {action.can_mark_complete && <button type="button" aria-pressed={completed} aria-disabled={disabled}
          aria-label={`${completed ? 'Mark not done' : 'Mark done'}: ${action.title}`}
          className={`${control} border border-line2 ${completed ? 'bg-calm-soft text-calm' : 'bg-white text-ink'} ${disabled ? 'opacity-50' : 'hover:border-ink'}`}
          onClick={() => { if (!disabled) onComplete(action.id, !completed); }}>
          {completed && <Check size={16} aria-hidden="true" />}{completed ? 'Done' : 'Mark done'}
        </button>}
      </div>
      {completed && <p className="mt-2 text-xs text-calm">You say you took this step.</p>}
      <details className="mt-2 text-sm">
        <summary className="min-h-11 cursor-pointer py-3 text-ink-muted underline decoration-line2 underline-offset-4">Why this step / official source</summary>
        <p className="leading-relaxed text-ink-muted">{action.why}</p>
        <p className="mt-2 text-xs text-ink-muted">Recorded priority: {action.priority.replaceAll('_', ' ')}</p>
        {action.url && <a href={action.url} target="_blank" rel="noopener noreferrer" className={`${control} mt-2 border border-line2`}><ExternalLink size={16} aria-hidden="true" />{action.url_label ?? 'External official source'}</a>}
      </details>
    </div>
  </li>;
}

export function ConversationActionPanel({ actions, completed, disabled, onComplete }: Props) {
  // Use server order. Priority and phase are displayed, never inferred from facts.
  const ordered = [...actions].sort((a, b) => a.order - b.order);
  const immediate = ordered.filter(isImmediateAction);
  const remaining = ordered.filter(a => !isImmediateAction(a));
  const phases = [
    ['PRESERVE', 'PRESERVE'], ['REPORT', 'REPORT'], ['FOLLOW_UP', 'FOLLOW THROUGH'],
  ] as const;
  function cards(items: ActionItem[]) {
    return <ol role="list" aria-label="Steps in response-plan order" className="list-none">{items.map(action => <ActionCard key={action.id} action={action}
      completed={completed.get(action.id) ?? false} disabled={disabled} onComplete={onComplete} />)}</ol>;
  }
  return <section id="current-actions" aria-label="Applicable actions" className="scroll-mt-20 min-w-0 space-y-4 lg:sticky lg:top-6 lg:max-h-[calc(100dvh-3rem)] lg:overflow-y-auto lg:overscroll-contain">
    <div><p className="font-mono text-xs uppercase tracking-widest text-ink-muted">Your response plan</p>
      <p className="mt-2 text-sm text-ink-muted">Take these steps while we work through what happened. Done means only that you say you acted.</p></div>
    {immediate.length > 0 && <section data-action-group="ACT NOW" aria-labelledby="act-now-heading" className="overflow-hidden rounded-lg border-2 border-urgent bg-surface shadow-card">
      <div className="flex items-center gap-3 bg-urgent-soft px-4 py-5 text-urgent sm:px-5">
        <Siren size={30} aria-hidden="true" /><div><h2 id="act-now-heading" tabIndex={-1} className="scroll-mt-24 font-display text-3xl font-bold">ACT NOW</h2>
          <p className="mt-1 text-sm font-medium">Start here. Follow the numbered steps.</p></div>
      </div>
      {cards(immediate)}
    </section>}
    {phases.map(([phase, title]) => {
      const items = remaining.filter(a => a.phase === phase);
      return items.length > 0 && <details key={phase} data-action-group={title} className="overflow-hidden rounded-lg border border-line2 bg-surface">
        <summary className="min-h-12 cursor-pointer px-4 py-4 font-mono text-sm font-semibold tracking-wide sm:px-5">{title}<span className="ml-2 font-sans font-normal tracking-normal text-ink-muted">{items.length} {items.length === 1 ? 'step' : 'steps'}</span></summary>
        {cards(items)}
      </details>;
    })}
  </section>;
}
