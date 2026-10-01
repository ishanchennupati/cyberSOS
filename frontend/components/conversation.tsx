"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ApiError, createIncident, getConversation, sendConversationTurn } from '@/lib/api';
import type { ConversationState, FactField, ReplyValue, TurnRequest } from '@/types/conversation';
import { ConversationActionPanel, isImmediateAction } from '@/components/conversation-action-panel';

const labels: Record<FactField, string> = {
  authorization: 'Payment approval', ongoing_loss: 'Ongoing loss', remote_access: 'Remote access',
  account_compromised: 'Account access', credentials_exposed: 'Credentials exposed', occurred_at: 'Approximate time',
  payment_method: 'Payment method', transaction_status: 'Payment status', amount: 'Amount',
  transaction_id: 'Transaction reference', evidence_available: 'Safe records available',
};
const controls = 'min-h-12 rounded-md border border-line2 px-4 py-3 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-calm disabled:opacity-50';
const booleanFields = new Set<FactField>(['ongoing_loss', 'remote_access', 'account_compromised', 'credentials_exposed', 'evidence_available']);

function display(value: ReplyValue | undefined) {
  if (value == null || value === 'unknown') return 'Not sure';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return ({ authorized: 'I approved it after deception', unauthorized: 'I did not approve it' } as Record<string, string>)[value] ?? value.replaceAll('_', ' ');
}

export function Conversation({ incidentId }: { incidentId?: string }) {
  const router = useRouter();
  const [state, setState] = useState<ConversationState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [failed, setFailed] = useState<TurnRequest | null>(null);
  const [stale, setStale] = useState(false);
  const [edit, setEdit] = useState<FactField | null>(null);
  const [value, setValue] = useState('');
  const [createdId, setCreatedId] = useState<string | null>(null);
  const lock = useRef(false);
  const questionRef = useRef<HTMLHeadingElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);
  const focusNextQuestion = useRef(false);
  const id = incidentId ?? createdId;
  const field = edit ?? state?.pending_question?.field;

  const load = useCallback(async () => {
    if (!id) return;
    setBusy(true);
    try { setState(await getConversation(id)); setError(''); }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not load conversation.'); }
    finally { setBusy(false); }
  }, [id]);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => { setValue(''); }, [field]);
  useEffect(() => {
    if (focusNextQuestion.current && !failed) {
      setValue(''); questionRef.current?.focus({ preventScroll: true }); focusNextQuestion.current = false;
    }
  }, [state?.revision, failed]);
  useEffect(() => { setValue(''); if (edit) questionRef.current?.focus({ preventScroll: true }); }, [edit]);
  useEffect(() => { if (error) errorRef.current?.focus(); }, [error]);

  async function start() {
    if (lock.current) return;
    lock.current = true; setBusy(true); setError('');
    try {
      const incident = await createIncident({ incident_type: 'financial_fraud', payment_method: 'unknown' });
      setCreatedId(incident.id);
      const payload: TurnRequest = { turn_id: crypto.randomUUID(), expected_revision: 0, type: 'shortcut', field: null, value: 'money_gone' };
      try { await sendConversationTurn(incident.id, payload); }
      catch (e) { setFailed(payload); throw e; }
      router.replace(`/incident/${incident.id}/conversation`);
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not start. Try again.'); }
    finally { lock.current = false; setBusy(false); }
  }

  async function send(payload: TurnRequest) {
    if (!id || lock.current) return;
    lock.current = true; setBusy(true); setError(''); setFailed(payload);
    try {
      const next = await sendConversationTurn(id, payload);
      focusNextQuestion.current = payload.type !== 'completion';
      setState(next);
      setFailed(null); setStale(false);
      if (payload.type !== 'completion') setEdit(null);
      if (!incidentId) router.replace(`/incident/${id}/conversation`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Reply could not be saved.');
      if (e instanceof ApiError && e.status === 409) {
        setStale(true);
        try { setState(await getConversation(id)); } catch { /* Explicit reload remains available. */ }
      }
    } finally { lock.current = false; setBusy(false); }
  }

  function reply(answer: ReplyValue) {
    if (!state || !field) return;
    void send({ turn_id: crypto.randomUUID(), expected_revision: state.revision,
      type: edit ? 'correction' : 'answer', field, value: answer });
  }

  const disabled = busy || !!failed;
  const options: [string, ReplyValue][] = field === 'authorization'
    ? [['I approved it after deception', 'authorized'], ['I did not approve it', 'unauthorized']]
    : field && booleanFields.has(field) ? [['Yes', true], ['No', false]]
    : field === 'payment_method' ? [['UPI', 'upi'], ['Bank transfer', 'bank_transfer'], ['Debit card', 'debit_card'], ['Credit card', 'credit_card'], ['Net banking', 'net_banking'], ['Wallet', 'wallet']]
    : field === 'transaction_status' ? [['Pending', 'pending'], ['Completed', 'completed']] : [];
  const textField = field && !options.length;
  const completed = new Map(state?.completions.map(item => [item.action_id, item.completed]));
  const immediate = useMemo(() => state?.plan.plan.actions.filter(isImmediateAction) ?? [], [state?.plan.plan.actions]);
  const remainingImmediate = immediate.filter(action => !completed.get(action.id)).length;
  const previousUrgentIds = useRef<string[]>([]);
  const [actionAnnouncement, setActionAnnouncement] = useState('');
  useEffect(() => {
    const added = immediate.filter(action => !previousUrgentIds.current.includes(action.id));
    if (added.length) setActionAnnouncement(`ACT NOW: ${added.length} ${added.length === 1 ? 'new action is' : 'new actions are'} available. ${added.map(action => action.title).join('. ')}`);
    previousUrgentIds.current = immediate.map(action => action.id);
  }, [immediate]);
  const known = state ? (Object.keys(labels) as FactField[]).filter(f => state.answered.includes(f) || (state.facts[f] != null && state.facts[f] !== 'unknown')) : [];

  return <main className="min-h-screen bg-paper text-ink">
    <header className="border-b border-line bg-surface"><div className="mx-auto flex max-w-6xl flex-wrap justify-between gap-3 p-5">
      <Link href="/" className="underline">CyberSOS home</Link><span>Independent citizen support</span>
    </div></header>
    <div className="mx-auto max-w-6xl px-4 py-5 sm:p-8">
      <h1 className="font-display text-3xl sm:text-4xl">Tell us what happened.</h1>
      <p className="mt-3 max-w-2xl text-ink-muted">{state ? 'Start with your response plan. Then answer one question at a time.' : 'Choose a shortcut to begin. This version supports financial incidents using structured replies. It does not interpret free text.'}</p>
      <p className="mt-2 text-sm">Use synthetic data only. Never enter OTPs, PINs, passwords or full card details.</p>
      <div role="status" aria-live="polite" className="mt-3 text-sm text-ink-muted">{busy ? 'Saving or loading…' : state ? 'Saved. Your conversation is up to date.' : ''}</div>
      <div role="status" aria-label="Action updates" aria-live="polite" aria-atomic="true" className="sr-only">{actionAnnouncement}</div>
      {(error || (failed && !busy)) && <div ref={errorRef} tabIndex={-1} role="alert" className="my-4 rounded border border-urgent p-4">
        <p>{error || 'Your reply is awaiting confirmation.'}</p>
        {failed && <p>Your reply has not been confirmed saved. {stale ? 'Review the latest conversation before sending a new reply.' : 'Retry checks whether this reply was already saved.'}</p>}
        <div className="mt-3 flex flex-wrap gap-3">
          {failed && !stale && <button className={controls} disabled={busy} onClick={() => void send(failed)}>Retry unsaved reply</button>}
          {id && <button className={controls} disabled={busy} onClick={() => void load()}>Reload saved conversation</button>}
          {failed && <button className={controls} disabled={busy} onClick={() => { setFailed(null); setStale(false); setError(''); setEdit(null); }}>Discard unsaved reply and review</button>}
          {!id && <button className={controls} disabled={busy} onClick={() => void start()}>Retry starting incident</button>}
        </div>
      </div>}
      {!id && <section className="mt-8 max-w-2xl">
        <button className={`${controls} bg-calm text-white`} disabled={busy} onClick={() => void start()}>Money is gone</button>
        <p className="mt-5">Other incident conversations are not available yet. You can visit the <a className="underline" href="https://cybercrime.gov.in/" target="_blank" rel="noreferrer">external official reporting portal</a>.</p>
      </section>}
      {state && <>
        <nav aria-label="Conversation shortcuts" className="sticky top-0 z-20 -mx-4 mt-4 flex items-center justify-between gap-3 border-y border-line2 bg-paper px-4 py-2 shadow-card lg:hidden">
          <a className="min-h-12 py-3 text-sm font-semibold underline underline-offset-4" href="#act-now-heading" onClick={event => {
            event.preventDefault(); document.getElementById(immediate.length ? 'act-now-heading' : 'current-actions')?.scrollIntoView({ block: 'start' });
            document.getElementById('act-now-heading')?.focus({ preventScroll: true });
          }}>{remainingImmediate ? `${remainingImmediate} ${remainingImmediate === 1 ? 'action' : 'actions'} to take now` : 'View current actions'}</a>
          <a className="min-h-12 py-3 text-sm font-semibold text-ink underline underline-offset-4" href="#current-question" onClick={event => {
            event.preventDefault(); questionRef.current?.scrollIntoView({ block: 'start' }); questionRef.current?.focus({ preventScroll: true });
          }}>Next question</a>
        </nav>
        <div className="mt-5 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-8">
          <div className="lg:col-start-2 lg:row-start-1 lg:self-stretch">
            <ConversationActionPanel actions={state.plan.plan.actions} completed={completed} disabled={disabled}
              onComplete={(actionId, done) => void send({ turn_id: crypto.randomUUID(), expected_revision: state.revision, type: 'completion', field: null, value: done, action_id: actionId })} />
          </div>
        <section aria-label="Incident conversation" className="min-w-0 lg:col-start-1 lg:row-start-1">
          <section id="current-question" className="scroll-mt-20 rounded-lg border-2 border-line2 bg-surface p-5 sm:p-6" aria-label="Current question" aria-busy={busy}>
            <p className="mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-ink-muted">{edit ? 'Correct your answer' : field ? 'One important question' : 'Your conversation'}</p>
            <h2 ref={questionRef} tabIndex={-1} className="scroll-mt-24 text-lg font-medium">{edit ? `Correct ${labels[edit].toLowerCase()}` : state.pending_question?.question ?? 'You have answered the available questions. You can correct details or continue with your actions.'}</h2>
            {field && <>
              <div className="mt-4 flex flex-wrap gap-3">{options.map(([label, answer]) => <button key={label} className={controls} disabled={disabled} onClick={() => reply(answer)}>{label}</button>)}</div>
              {textField && <form className="mt-4" onSubmit={event => { event.preventDefault(); reply(field === 'occurred_at' ? new Date(value).toISOString() : value); }}>
                <label htmlFor="structured-answer" className="block">{labels[field]}</label>
                <input id="structured-answer" className={`${controls} mt-2 w-full`} disabled={disabled} required value={value}
                  type={field === 'occurred_at' ? 'datetime-local' : field === 'amount' ? 'number' : 'text'}
                  min={field === 'amount' ? '0.01' : undefined} max={field === 'amount' ? '9999999999.99' : undefined}
                  step={field === 'amount' ? '0.01' : undefined} maxLength={128}
                  onChange={event => setValue(event.target.value)} />
                <button className={`${controls} mt-3`} disabled={disabled} type="submit">Save answer</button>
              </form>}
              <button className={`${controls} mt-3`} disabled={disabled} onClick={() => reply(null)}>Not sure</button>
              {edit && <button className={`${controls} ml-3 mt-3`} disabled={disabled} onClick={() => setEdit(null)}>Cancel correction</button>}
            </>}
          </section>
          <details className="mt-5 rounded-lg border border-line2 bg-surface px-4"><summary className="min-h-12 cursor-pointer py-4 font-medium">Review or correct your answers</summary>
            <ul className="space-y-3">{known.map(f => <li key={f} className="flex flex-wrap items-center justify-between gap-3 border-b border-line py-3">
              <span className="break-words">{labels[f]}: {display(state.facts[f])}</span>
              <button className={controls} disabled={disabled} onClick={() => { setEdit(f); }}>Edit {labels[f].toLowerCase()}</button>
            </li>)}</ul>
          </details>
          <details className="mt-4 rounded-lg border border-line bg-surface px-4"><summary className="min-h-12 cursor-pointer py-4 font-medium">Saved conversation · {state.turns.length} replies</summary>
            <ol aria-label="Saved message history" className="space-y-3 pb-4">
              <li className="text-sm text-ink-muted">CyberSOS: Financial incident conversation started.</li>
              {state.turns.map(turn => <li key={turn.id} className="rounded border border-line bg-paper p-4">
                <p className="break-words">You: {turn.type === 'completion' || turn.type === 'shortcut' ? turn.text : `${turn.type === 'correction' ? 'Correction — ' : ''}${labels[turn.structured_reply.field!]}: ${display(turn.structured_reply.value)}`}</p>
                <time className="text-xs text-ink-muted" dateTime={turn.created_at}>{new Date(turn.created_at).toLocaleString()}</time>
                {turn.pending_question && <p className="mt-3 text-sm text-ink-muted">CyberSOS asked: {turn.pending_question.question}</p>}
              </li>)}
            </ol>
          </details>
          <p className="mt-5 text-sm">Bookmark this page to reopen the conversation in this browser. Access requires your private case cookie and expires under the current case policy.</p>
          <Link className="mt-4 inline-block min-h-12 py-3 underline" href={`/incident/${state.incident_id}/result`}>Review reporting draft</Link>
          <Link className="ml-4 inline-block min-h-12 py-3 underline" href={`/incident/${state.incident_id}/evidence`}>Optional safe evidence</Link>
        </section>
      </div></>}
    </div>
  </main>;
}
