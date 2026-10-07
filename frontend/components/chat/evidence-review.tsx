'use client';
import { useState } from 'react';
import type { EvidenceAnalysis, TurnRequest } from '@/types/conversation';
import { chatControl } from './composer';

export function EvidenceReview({analysis, disabled, onReview, onChat}:{analysis:EvidenceAnalysis; disabled:boolean;
  onReview:(review:NonNullable<TurnRequest['evidence_review']>)=>void; onChat:()=>void}) {
  const [editing,setEditing]=useState<string|null>(null), [value,setValue]=useState('');
  const remaining=analysis.candidates.filter(c=>!c.reviewed);
  if(!remaining.length)return <p role="status" className="mt-2 text-sm">Review recorded · only accepted details update your case.</p>;
  return <details open className="mt-3 rounded-xl border border-line p-3">
    <summary className="min-h-11 cursor-pointer font-medium">Details to review · {remaining.length}</summary>
    <p className="text-xs text-ink-muted">Found in this attachment, not independently verified. Confirm only what you recognize, or correct it in chat.</p>
    <button disabled={disabled} className={`${chatControl} mt-2 underline`} onClick={onChat}>Review these details in chat</button>
    <ul className="mt-3 space-y-4">{remaining.map(candidate=>{
      const send=(decision:'accept'|'reject'|'correct', corrected?:string)=>onReview({attempt_id:analysis.id,
        decisions:[{candidate_id:candidate.id,decision,...(corrected?{value:corrected}:{}),resolve_conflict:candidate.conflict||candidate.changed_since_analysis}]});
      return <li key={candidate.id} className="border-t border-line pt-3">
        <p className="font-medium">{candidate.field.replaceAll('_',' ')}</p><p className="whitespace-pre-wrap break-words">{candidate.value}</p>
        {candidate.page&&<p className="text-xs text-ink-muted">Page {candidate.page}</p>}
        {candidate.uncertainty&&<p className="text-xs text-ink-muted">Uncertain: {candidate.uncertainty}</p>}
        {(candidate.conflict||candidate.changed_since_analysis)&&<p className="mt-2 break-words text-sm">Your current case says {typeof candidate.current_value==='object'?JSON.stringify(candidate.current_value):String(candidate.current_value??'unknown')}. Choose which value to keep.</p>}
        <div className="mt-2 flex flex-wrap gap-1"><button disabled={disabled} className={`${chatControl} border border-line2`} onClick={()=>send('accept')}>{candidate.conflict?'Use attachment value':'Confirm detail'}</button>
          <button disabled={disabled} className={chatControl} onClick={()=>send('reject')}>{candidate.conflict?'Keep current value':'Skip this detail'}</button>
          <button disabled={disabled} className={chatControl} onClick={()=>{setEditing(candidate.id);setValue(candidate.value);}}>Correct</button></div>
        {editing===candidate.id&&<div className="mt-2"><label className="text-sm">Correct {candidate.field.replaceAll('_',' ')}<input autoFocus maxLength={2000} value={value} onChange={e=>setValue(e.target.value)} className="mt-1 block w-full rounded-lg border border-line2 p-2 focus-visible:outline focus-visible:outline-2"/></label>
          <button disabled={disabled||!value.trim()} className={chatControl} onClick={()=>{send('correct',value);setEditing(null);}}>Confirm correction</button><button className={chatControl} onClick={()=>setEditing(null)}>Cancel</button></div>}
      </li>;
    })}</ul>
  </details>;
}
