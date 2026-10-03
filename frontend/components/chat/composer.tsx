'use client';
import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { Plus, ArrowUp } from 'lucide-react';

export const chatControl = 'min-h-11 rounded-xl px-3 py-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-calm disabled:opacity-50';

export function ChatComposer({ draft, onDraft, onSend, onFiles, busy, canSend, children }: {
  draft: string; onDraft: (text: string) => void; onSend: () => void;
  onFiles: (files: File[]) => void; busy: boolean; canSend: boolean; children?: React.ReactNode;
}) {
  const textarea = useRef<HTMLTextAreaElement>(null);
  const [hydrated,setHydrated] = useState(false);
  useEffect(()=>{setHydrated(true);},[]);
  const picker = useRef<HTMLInputElement>(null);
  useLayoutEffect(() => {
    if (!textarea.current) return;
    textarea.current.style.height = 'auto';
    textarea.current.style.height = `${Math.min(168, Math.max(48, textarea.current.scrollHeight))}px`;
  }, [draft]);
  return <form aria-label="Message CyberSOS" className="rounded-2xl border border-line2 bg-white p-2 shadow-card" onSubmit={event => {
    event.preventDefault(); if (canSend && !busy) onSend();
  }}>
    {children}
    <textarea ref={textarea} id="chat-message" aria-label="Message CyberSOS" rows={1} maxLength={8000} disabled={!hydrated}
      className="block max-h-[min(168px,25dvh)] min-h-12 w-full resize-none overflow-y-auto rounded-xl border-0 bg-transparent px-3 py-3 leading-6 outline-none focus-visible:ring-2 focus-visible:ring-calm"
      placeholder="Message CyberSOS…" value={draft} onChange={event => onDraft(event.target.value)}
      onKeyDown={event => {
        if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
          event.preventDefault(); if (canSend && !busy) onSend();
        }
      }} />
    <div className="flex items-center justify-between gap-3">
      <input ref={picker} type="file" multiple accept="image/jpeg,image/png,application/pdf,.jpg,.jpeg,.png,.pdf" className="sr-only" tabIndex={-1}
        onChange={event => { onFiles(Array.from(event.target.files ?? [])); event.target.value = ''; }} />
      <button type="button" aria-label="Attach files" disabled={busy} className={`${chatControl} inline-flex items-center gap-1`} onClick={() => picker.current?.click()}><Plus size={20} aria-hidden="true" />Attach</button>
      <span className="hidden text-xs text-ink-muted sm:inline">Shift + Enter for a new line</span>
      <button type="submit" aria-label="Send message" disabled={!canSend || busy} className={`${chatControl} flex items-center gap-2 bg-ink text-white`}><ArrowUp size={18} aria-hidden="true" />{busy ? 'Saving…' : 'Send'}</button>
    </div>
  </form>;
}
