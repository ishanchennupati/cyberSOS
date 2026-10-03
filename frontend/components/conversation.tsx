'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { ApiError, createConversationCase, getConversation, sendConversationTurn, stageChatAttachment, deleteEvidence, getEvidence, evidenceFileUrl } from '@/lib/api';
import type { ConversationState, TurnRequest } from '@/types/conversation';
import { ConversationActionPanel, isImmediateAction } from '@/components/conversation-action-panel';
import { ChatComposer, chatControl } from '@/components/chat/composer';

type Staged = {id:string; name:string; file?:File; preview?:string; status:'uploading'|'ready'|'failed'; percent:number; error?:string};
const draftKey = (id?:string) => `cybersos-chat-draft:${id ?? 'start'}`;
const readable = (value:unknown):string => typeof value==='object'?JSON.stringify(value):String(value).replaceAll('_',' ');

export function Conversation({incidentId}:{incidentId?:string}) {
  const router=useRouter();
  const [state,setState]=useState<ConversationState|null>(null);
  const [createdId,setCreatedId]=useState<string>();
  const [draft,setDraft]=useState('');
  const [files,setFiles]=useState<Staged[]>([]);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [failed,setFailed]=useState<TurnRequest|null>(null);
  const [stale,setStale]=useState(false);
  const [artifact,setArtifact]=useState<'plan'|'case'|null>(null);
  const [away,setAway]=useState(false);
  const viewport=useRef<HTMLDivElement>(null), latest=useRef<HTMLDivElement>(null);
  const nearBottom=useRef(true), lock=useRef(false), initialized=useRef(false);
  const currentDraft=useRef(draft);currentDraft.current=draft;
  const artifactTrigger=useRef<HTMLButtonElement|null>(null);
  const creation=useRef<{id:string;secret:string}>();
  const creating=useRef<Promise<string>>();
  const cancelled=useRef(new Set<string>()), uploads=useRef(new Map<string,AbortController>());
  const id=incidentId ?? createdId;

  useEffect(()=>{
    let active=true;
    try {
      const stored=sessionStorage.getItem(draftKey(incidentId));
      if(stored){const saved=JSON.parse(stored);setDraft(saved.draft??'');setFailed(saved.failed??null);
        if(saved.failed)setError('A message was interrupted. Retry checks the same saved message key.');
        if(saved.caseId&&!incidentId)setCreatedId(saved.caseId);
        if(saved.files){setFiles(saved.files.map((item:Staged)=>({...item,status:'uploading',percent:0})));
          for(const item of saved.files as Staged[])getEvidence(item.id).then(()=>{if(active)setFiles(previous=>previous.map(file=>file.id===item.id?{...file,status:'ready'}:file));})
            .catch(()=>{if(active)setFiles(previous=>previous.map(file=>file.id===item.id?{...file,status:'failed',error:'Upload not confirmed. Remove it and select the file again.'}:file));});}}
      const key=sessionStorage.getItem('cybersos-chat-creation');if(key)creation.current=JSON.parse(key);
    }catch{/* In-memory drafts work when storage is unavailable. */}
    initialized.current=true;
    if(incidentId)getConversation(incidentId).then(next=>{if(active)setState(next);}).catch(e=>{if(active)setError(e.message);});
    return()=>{active=false;};
  },[incidentId]);
  useEffect(()=>{
    if(!initialized.current)return;
    try{if(!draft&&!failed&&!files.length)sessionStorage.removeItem(draftKey(incidentId));
      else sessionStorage.setItem(draftKey(incidentId),JSON.stringify({draft,failed,caseId:id,files:files.map(({id,name,status})=>({id,name,status}))}));}catch{/* Keep draft in memory. */}
  },[draft,failed,files,id,incidentId]);
  useEffect(()=>{if(nearBottom.current)latest.current?.scrollIntoView({block:'end'});},[state?.revision,files.length]);

  const ensureCase=useCallback(async()=>{
    if(id){if(!state)setState(await getConversation(id));return id;}
    if(creating.current)return creating.current;
    if(!creation.current){creation.current={id:crypto.randomUUID(),secret:crypto.randomUUID()+crypto.randomUUID()};
      try{sessionStorage.setItem('cybersos-chat-creation',JSON.stringify(creation.current));}catch{/* Keep key in memory. */}}
    const key=creation.current;
    creating.current=(async()=>{const incident=await createConversationCase(key.id,key.secret);
      setCreatedId(incident.id);setState(await getConversation(incident.id));return incident.id;})();
    try{return await creating.current;}finally{creating.current=undefined;}
  },[id,state]);

  async function upload(item:Staged){
    if(!item.file)return;
    const controller=new AbortController();uploads.current.set(item.id,controller);
    setFiles(previous=>previous.map(file=>file.id===item.id?{...file,status:'uploading',error:undefined}:file));
    try{const caseId=await ensureCase();if(cancelled.current.has(item.id))return;
      await stageChatAttachment(caseId,item.file,item.id,controller.signal,percent=>setFiles(previous=>previous.map(file=>file.id===item.id?{...file,percent}:file)));
      if(cancelled.current.has(item.id)){await deleteEvidence(item.id);return;}
      setFiles(previous=>previous.map(file=>file.id===item.id?{...file,status:'ready',percent:100}:file));
    }catch(e){if(!cancelled.current.has(item.id))setFiles(previous=>previous.map(file=>file.id===item.id?{...file,status:'failed',error:e instanceof Error?e.message:'Upload failed.'}:file));}
    finally{uploads.current.delete(item.id);}
  }
  function selectFiles(selected:File[]){
    if(files.length+selected.length>5){setError('Attach up to five files per message.');return;}
    const accepted:Staged[]=[];
    for(const file of selected){
      if(!/\.(jpe?g|png|pdf)$/i.test(file.name)||!['image/jpeg','image/png','application/pdf'].includes(file.type)){setError('Choose a JPG, PNG or PDF file.');continue;}
      if(file.size>10*1024*1024){setError('Each attachment must be 10 MB or smaller.');continue;}
      accepted.push({id:crypto.randomUUID(),name:file.name,file,preview:file.type.startsWith('image/')?URL.createObjectURL(file):undefined,status:'uploading',percent:0});}
    setFiles(previous=>[...previous,...accepted]);for(const item of accepted)void upload(item);
  }
  async function removeFile(item:Staged){
    cancelled.current.add(item.id);uploads.current.get(item.id)?.abort();setFiles(previous=>previous.filter(file=>file.id!==item.id));
    if(item.preview)URL.revokeObjectURL(item.preview);
    try{await deleteEvidence(item.id);}catch(e){if(!(e instanceof ApiError&&e.status===404))setError('Removal was not confirmed. Unsent staged files are cleaned up after 24 hours on the next case upload.');}
  }
  async function send(payload?:TurnRequest){
    if(lock.current)return;lock.current=true;setBusy(true);setError('');
    const request=payload??{turn_id:crypto.randomUUID(),expected_revision:state?.revision??0,type:'message' as const,
      ...(draft.trim()?{text:draft}:{}),attachment_ids:files.map(file=>file.id),timezone:Intl.DateTimeFormat().resolvedOptions().timeZone};
    setFailed(request);
    try{const caseId=await ensureCase();const next=await sendConversationTurn(caseId,request);
      nearBottom.current=true;setState(next);setFailed(null);setStale(false);
      const remainingDraft=request.type==='message'&&currentDraft.current===(request.text??'')?'':currentDraft.current;
      const sentFiles=new Set(request.attachment_ids??[]);
      const remainingFiles=files.filter(file=>!sentFiles.has(file.id));
      if(request.type==='message'){setDraft(remainingDraft);for(const file of files)if(sentFiles.has(file.id)&&file.preview)URL.revokeObjectURL(file.preview);setFiles(remainingFiles);}
      try{sessionStorage.removeItem('cybersos-chat-creation');sessionStorage.removeItem(draftKey(incidentId));}catch{/* Saved case is authoritative. */}
      if(!incidentId){try{if(remainingDraft||remainingFiles.length)sessionStorage.setItem(draftKey(caseId),JSON.stringify({draft:remainingDraft,files:remainingFiles.map(({id,name,status})=>({id,name,status}))}));}catch{/* Keep in-memory draft. */}router.replace(`/incident/${caseId}/conversation`);}
    }catch(e){setError(e instanceof Error?e.message:'Message could not be saved.');if(e instanceof ApiError&&e.status===409){setStale(true);if(id)try{setState(await getConversation(id));}catch{/* Reload available. */}}}
    finally{lock.current=false;setBusy(false);}
  }
  const completed=new Map(state?.completions.map(item=>[item.action_id,item.completed]));
  const immediate=state?.plan.plan.actions.filter(isImmediateAction)??[];
  const canSend=(!!draft.trim()||files.length>0)&&files.every(file=>file.status==='ready')&&!failed&&(!incidentId||!!state);
  const complete=(actionId:string,done:boolean)=>void send({turn_id:crypto.randomUUID(),expected_revision:state!.revision,type:'completion',action_id:actionId,value:done});
  function feedback(text:string){setDraft(text);document.getElementById('chat-message')?.focus();}
  return <main className="flex h-[100dvh] min-h-0 flex-col bg-paper text-ink">
    <header className="shrink-0 border-b border-line px-4 py-3"><div className="mx-auto flex max-w-6xl items-center justify-between gap-2">
      <Link href="/" className="font-display text-xl font-bold">CyberSOS</Link><div className="flex gap-1">
      {!!state?.plan.plan.actions.length&&<button className={chatControl} aria-expanded={artifact==='plan'} onClick={event=>{artifactTrigger.current=event.currentTarget;setArtifact(artifact==='plan'?null:'plan');}}>Response plan</button>}
      {!!state?.turns.length&&<button className={chatControl} aria-expanded={artifact==='case'} onClick={event=>{artifactTrigger.current=event.currentTarget;setArtifact(artifact==='case'?null:'case');}}>View case</button>}</div></div></header>
    <div className="mx-auto flex min-h-0 w-full max-w-6xl flex-1 flex-col md:flex-row"><section aria-label="Incident conversation" className="flex min-h-0 min-w-0 flex-1 flex-col">
      <div ref={viewport} className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4" onScroll={()=>{const el=viewport.current;if(el){nearBottom.current=el.scrollHeight-el.scrollTop-el.clientHeight<140;setAway(!nearBottom.current);}}}>
        {!state?.turns.length&&<div className="mx-auto flex min-h-[45dvh] max-w-2xl flex-col items-center justify-center text-center">
          <h1 className="font-display text-3xl sm:text-4xl">Tell us what happened</h1><p className="mt-4 max-w-lg leading-relaxed text-ink-muted">Start in your own words. CyberSOS helps make sense of what happened, asks what matters and organizes your case.</p>
          <p className="mt-3 text-sm text-ink-muted">Independent citizen support. No complaint is submitted here.</p></div>}
        <ol aria-label="Saved message history" className="mx-auto max-w-2xl space-y-7 py-6">{state?.turns.map(turn=><li key={turn.id} className="space-y-4">
          <div className="ml-10 rounded-2xl bg-surface p-4"><p className="sr-only">You</p>{turn.text&&<p className="whitespace-pre-wrap break-words leading-relaxed">{turn.text}</p>}
            {turn.attachments?.map(file=><div key={file.id} className="mt-2 rounded-xl border border-line p-3 text-sm"><p className="break-all">{file.original_filename}</p>
              {file.deleted?<p>Attachment deleted</p>:<>{file.mime_type.startsWith('image/')&&<Image unoptimized width={240} height={160} src={evidenceFileUrl(file.id)} alt={`Attached ${file.original_filename}`} className="mt-2 max-h-48 rounded-lg object-contain"/>}
                <a className="inline-block min-h-11 py-3 underline" href={evidenceFileUrl(file.id)} target="_blank" rel="noopener noreferrer">Open attachment</a><span className="ml-3 text-ink-muted">Uploaded · not analyzed</span>
                <button className={chatControl} disabled={busy} onClick={async()=>{try{await deleteEvidence(file.id);setState(await getConversation(state.incident_id));}catch(e){setError(e instanceof Error?e.message:'Deletion failed.');}}}>Delete attachment</button></>}
            </div>)}</div>
          <div className="mr-4 leading-relaxed"><p className="mb-2 text-sm font-semibold">CyberSOS</p>{turn.fact_changes.acknowledgement&&<p className="whitespace-pre-wrap break-words">{turn.fact_changes.acknowledgement}</p>}
            <p className="whitespace-pre-wrap break-words">{turn.fact_changes.next_move?.message??turn.pending_question?.question}</p>
            {turn.fact_changes.knowledge_sources?.map(source=><a key={source.id} href={source.url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block min-h-11 py-2 text-sm underline">{source.title} · reviewed {source.reviewed_on}</a>)}
          </div></li>)}</ol>
        {!!state?.next_move?.quick_replies.length&&<div className="mx-auto flex max-w-2xl flex-wrap gap-2 pb-4">{state.next_move.quick_replies.map(reply=><button key={reply} disabled={busy||!!failed} className={`${chatControl} border border-line2`} onClick={()=>void send({turn_id:crypto.randomUUID(),expected_revision:state.revision,type:'message',text:reply})}>{reply}</button>)}</div>}
        {immediate.length>0&&<div className="mx-auto max-w-2xl pb-5"><ConversationActionPanel actions={immediate} completed={completed} disabled={busy||!!failed} onComplete={complete}/></div>}<div ref={latest}/>
      </div>
      <div className="shrink-0 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2 sm:px-5"><div className="mx-auto max-w-2xl">
        {away&&<button className={`${chatControl} mb-2 border border-line2`} onClick={()=>{nearBottom.current=true;setAway(false);latest.current?.scrollIntoView({block:'end'});}}>Jump to latest</button>}
        {error&&<div role="alert" className="mb-2 rounded-xl border border-line2 p-3 text-sm"><p>{error}</p>{failed&&!stale&&<button className={`${chatControl} underline`} disabled={busy} onClick={()=>void send(failed)}>Retry message</button>}
          {failed&&<button className={`${chatControl} underline`} disabled={busy} onClick={()=>{setFailed(null);setError('');setStale(false);}}>Review draft</button>}
          {id&&<button className={`${chatControl} underline`} disabled={busy} onClick={async()=>{try{setState(await getConversation(id));setError('');}catch(e){setError(e instanceof Error?e.message:'Reload failed.');}}}>Reload conversation</button>}</div>}
        <ChatComposer draft={draft} onDraft={setDraft} onSend={()=>void send()} onFiles={selectFiles} busy={busy} canSend={!!canSend}>
          {files.length>0&&<ul aria-label="Pending attachments" className="flex max-h-[15dvh] flex-wrap gap-2 overflow-y-auto px-2 pt-2">{files.map(file=><li key={file.id} className="max-w-full rounded-xl border border-line p-2 text-sm">
            {file.preview&&<Image unoptimized width={80} height={64} src={file.preview} alt={`Preview ${file.name}`} className="h-16 w-20 rounded object-contain"/>}<p className="max-w-52 truncate">{file.name}</p>
            <p role="status">{file.status==='ready'?'Ready to send · not analyzed':file.status==='uploading'?`Uploading ${file.percent}%`:file.error}</p>
            {file.status==='failed'&&file.file&&<button type="button" className={`${chatControl} underline`} onClick={()=>void upload(file)}>Retry upload</button>}
            <button type="button" className={`${chatControl} underline`} disabled={busy||!!failed} onClick={()=>void removeFile(file)}>{file.status==='uploading'?'Cancel upload':'Remove attachment'}</button></li>)}</ul>}
        </ChatComposer>
        <div className="mt-2 flex flex-wrap justify-between gap-1 text-xs text-ink-muted"><span>Synthetic only · No OTPs, PINs, passwords or sensitive images. JPG, PNG, PDF · 10 MB.</span><span role="status" aria-live="polite">{busy?'Saving message…':files.some(file=>file.status==='uploading')?'Uploading…':state?.turns.length?'Saved in this private case':''}</span></div>
        {!!state?.turns.length&&<div className="flex gap-3"><button className="min-h-9 text-xs text-ink-muted underline" onClick={()=>feedback('I think you misunderstood what I said.')}>Misunderstood</button><button className="min-h-9 text-xs text-ink-muted underline" onClick={()=>feedback('You are asking something I already answered.')}>Repeating a question</button></div>}
      </div></div></section>
      {artifact&&state&&<aside aria-label={artifact==='plan'?'Response plan details':'Current case details'} className="order-first max-h-[25dvh] shrink-0 overflow-y-auto rounded-2xl border border-line2 bg-paper p-4 shadow-card md:order-last md:max-h-none md:w-96 md:rounded-none md:border-y-0 md:border-r-0">
        <div className="mb-3 flex items-center justify-between"><h2 className="font-semibold">{artifact==='plan'?'Current response plan':'Your current case'}</h2><button className={chatControl} onClick={()=>{setArtifact(null);artifactTrigger.current?.focus();}}>Close details</button></div>
        {artifact==='plan'?<ConversationActionPanel actions={state.plan.plan.actions.filter(action=>!isImmediateAction(action))} completed={completed} disabled={busy||!!failed} onComplete={complete}/>:<>
          <p className="break-all text-sm">CyberSOS reference: {state.projection.reference}</p><p className="mt-2 text-sm">{state.projection.status} · revision {state.projection.revision}</p>
          {state.projection.working_understanding.length>0&&<p className="mt-4 text-sm">Working understanding: {state.projection.working_understanding.map(readable).join(', ')}</p>}
          <dl className="mt-4 space-y-3">{Object.entries(state.projection.known_facts).filter(([field])=>field!=='signals').map(([field,fact])=><div key={field}><dt className="text-sm font-medium">{field.replaceAll('_',' ')}</dt><dd className="break-words text-sm">{readable(fact.value)}<span className="block text-xs text-ink-muted">{fact.verified?'Recorded from your statement':'Working information · correct it in chat'}</span></dd></div>)}</dl>
          <p className="mt-4 text-sm">{state.projection.evidence_count} saved attachments · {state.projection.completed_actions} steps recorded done by you</p><p className="mt-4 text-xs text-ink-muted">Bookmark this private case URL. Return requires your case cookie and its current expiry. No external status is verified.</p></>}
      </aside>}
    </div>
  </main>;
}
