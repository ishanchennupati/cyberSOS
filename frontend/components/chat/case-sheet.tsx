'use client';
import type {ConversationState} from '@/types/conversation';

function readable(value:unknown):string {
  if(Array.isArray(value))return value.map(readable).join(', ');
  if(value&&typeof value==='object'){
    if('original' in value)return String(value.original)+' (approximate)';
    if('type' in value&&'value' in value)return `${value.type}: ${value.value}`;
    return JSON.stringify(value);
  }
  return String(value).replaceAll('_',' ');
}

export function CaseSheet({state,full=false}:{state:ConversationState;full?:boolean}){
  const projection=state.projection;
  return <div className="space-y-3 text-sm" aria-label={full?'Case companion':'Draft CyberSOS case sheet'}>
    <h3 className="font-semibold">{full?'Your continuing case':'Draft CyberSOS case sheet'}</h3>
    <p className="text-xs text-ink-muted">Built from your current case. Draft presentation does not verify details or approve a reporting packet.</p>
    <p className="break-all">CyberSOS reference: {projection.reference}</p>
    <p>{projection.status} · revision {state.revision}</p>
    {!!projection.working_understanding.length&&<p>Working understanding: {projection.working_understanding.map(readable).join(', ')}</p>}
    <dl className="space-y-3">{Object.entries(projection.known_facts).filter(([field])=>field!=='signals').map(([field,fact])=><div key={field}>
      <dt className="font-medium">{field.replaceAll('_',' ')}</dt><dd className="whitespace-pre-wrap break-words">{readable(fact.value)}
      <span className="block text-xs text-ink-muted">{fact.evidence_id?`Reviewed attachment detail${fact.source_deleted?' · original deleted':''}`:fact.verified?'Established from your statement or review':'Working information · correct it in chat'}</span>
      {full&&fact.source_turn&&<span className="block text-xs text-ink-muted">Source: conversation {fact.source_turn.slice(0,8)}</span>}</dd></div>)}</dl>
    {!!projection.current_help?.unknowns.length&&<p>Unknown or unresolved: {projection.current_help.unknowns.map(readable).join(', ')}. You can leave these unknown.</p>}
    <p>{projection.evidence_count} saved attachments · {projection.completed_actions} steps recorded done by you</p>
    {!!projection.records?.length&&<div><h4 className="font-medium">Your notes and external references</h4>{projection.records.map((record,index)=><p key={`${record.source_turn}:${index}`} className="my-2 whitespace-pre-wrap break-words">{record.organization?`${record.organization}: `:''}{record.text}<span className="block text-xs text-ink-muted">{record.meaning} · {new Date(record.created_at).toLocaleDateString()}</span></p>)}</div>}
    {full&&!!projection.evidence?.length&&<div><h4 className="font-medium">Saved evidence</h4>{projection.evidence.map(file=><p key={file.id} className="my-2 break-words">{file.name}<span className="block text-xs text-ink-muted">Analysis: {readable(file.analysis)} · {readable(file.verification)}</span></p>)}</div>}
    {full&&<div><h4 className="font-medium">Case timeline</h4><ol className="space-y-2">{state.turns.map(turn=><li key={turn.id} className="border-l border-line pl-3"><time className="text-xs text-ink-muted">{new Date(turn.created_at).toLocaleString()}</time><p className="break-words">{turn.text}</p></li>)}{projection.timeline?.map(event=><li key={event.id}><time>{new Date(event.time).toLocaleString()}</time><p>{event.description} · {event.meaning}</p></li>)}</ol></div>}
    <p className="text-xs text-ink-muted">No bank, police or platform status is independently verified. Reporting review and export remain separate.</p>
  </div>;
}
