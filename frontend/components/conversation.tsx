'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { ApiError, createConversationCase, getConversation, sendConversationTurn, stageChatAttachment, deleteEvidence, getEvidence, evidenceFileUrl, analyzeChatAttachment } from '@/lib/api';
import type { ConversationState, TurnRequest } from '@/types/conversation';
import { ConversationActionPanel, isImmediateAction } from '@/components/conversation-action-panel';
import { ChatComposer, chatControl } from '@/components/chat/composer';
import { EvidenceReview } from '@/components/chat/evidence-review';
import { Brand } from '@/components/brand';

type Staged = {id:string; name:string; file?:File; preview?:string; status:'uploading'|'ready'|'failed'; percent:number; error?:string};
const draftKey = (id?:string) => `cybersos-chat-draft:${id ?? 'start'}`;
const readable = (value:unknown):string => typeof value==='object'?JSON.stringify(value):String(value).replaceAll('_',' ');
const routes = [{value:'women_children',label:'Women/Children Related Crime'}, {value:'financial',label:'Financial Fraud'}, {value:'other',label:'Other Cyber Crime'}, {value:'not_sure',label:'Not sure'}] as const;

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
  const [analyzing,setAnalyzing]=useState<Record<string,boolean>>({});
  const [analysisErrors,setAnalysisErrors]=useState<Record<string,string>>({});
  const [activeReview,setActiveReview]=useState<string|null>(null);
  const [analysisCheckNeeded,setAnalysisCheckNeeded]=useState(false);
  const analysisRequests=useRef(new Map<string,{attempt_id:string;expected_revision:number}>());
  const viewport=useRef<HTMLDivElement>(null), latest=useRef<HTMLDivElement>(null);
  const nearBottom=useRef(true), lock=useRef(false), initialized=useRef(false);
  const currentDraft=useRef(draft);currentDraft.current=draft;
  const artifactTrigger=useRef<HTMLButtonElement|null>(null);
  const creation=useRef<{id:string;secret:string}>();
  const creating=useRef<Promise<string>>();
  const redirected=useRef(false);
  const cancelled=useRef(new Set<string>()), uploads=useRef(new Map<string,AbortController>());
  const id=incidentId ?? createdId;
  const activeCase=useRef(id);activeCase.current=id;
  const pendingAnalysis=(state?.turns.flatMap(turn=>turn.attachments??[]).filter(file=>!file.deleted&&['pending','processing'].includes(file.extraction_status??''))??[]);
  const analysisSignature=pendingAnalysis.map(file=>`${file.id}:${file.extraction_status}`).join('|');

  useEffect(()=>{
    let active=true;
    try {
      const stored=sessionStorage.getItem(draftKey(incidentId));
      if(stored){const saved=JSON.parse(stored);setDraft(saved.draft??'');setFailed(saved.failed??null);
        if(saved.failed)setError('Your reply was interrupted. Retry to check whether it arrived and continue.');
        if(saved.caseId&&!incidentId){setCreatedId(saved.caseId);getConversation(saved.caseId).then(next=>{if(active)setState(next);}).catch(e=>{if(active)setError(e.message);});}
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
    const key=draftKey(incidentId??(redirected.current?id:undefined));
    try{if(redirected.current&&id)sessionStorage.removeItem(draftKey());
      if(!draft&&!failed&&!files.length)sessionStorage.removeItem(key);
      else sessionStorage.setItem(key,JSON.stringify({draft,failed,caseId:id,files:files.map(({id,name,status})=>({id,name,status}))}));}catch{/* Keep draft in memory. */}
  },[draft,failed,files,id,incidentId]);
  useEffect(()=>{if(nearBottom.current)latest.current?.scrollIntoView({block:'end'});},[state?.revision,files.length,busy]);
  useEffect(()=>{
    if(!id||!analysisSignature)return;
    setAnalysisCheckNeeded(false);
    let active=true,inFlight=false,reads=0;
    const processing=analysisSignature.includes(':processing');
    const timer=setInterval(async()=>{
      if(inFlight)return;
      if(++reads>(processing?30:3)){clearInterval(timer);if(processing)setAnalysisCheckNeeded(true);return;}
      inFlight=true;
      try{const next=await getConversation(id);if(active&&activeCase.current===id)setState(previous=>previous&&previous.revision>next.revision?previous:next);}catch{/* Explicit reload/retry remains available. */}
      finally{inFlight=false;}
    },1500);
    return()=>{active=false;clearInterval(timer);};
  },[id,analysisSignature]);

  async function analyzeFile(caseId:string,fileId:string,revision:number,retry=false){
    if(analyzing[fileId])return;
    setAnalyzing(previous=>({...previous,[fileId]:true}));setAnalysisErrors(previous=>({...previous,[fileId]:''}));
    const request=analysisRequests.current.get(fileId)??{attempt_id:crypto.randomUUID(),expected_revision:revision};
    if(retry){request.attempt_id=crypto.randomUUID();request.expected_revision=revision;}
    analysisRequests.current.set(fileId,request);
    try{await analyzeChatAttachment(fileId,request);analysisRequests.current.delete(fileId);const next=await getConversation(caseId);
      if(activeCase.current===caseId)setState(previous=>previous&&previous.revision>next.revision?previous:next);}
    catch(e){if(e instanceof ApiError&&e.status===409)analysisRequests.current.delete(fileId);
      setAnalysisErrors(previous=>({...previous,[fileId]:e instanceof Error?e.message:'Analysis could not finish. You can keep talking.'}));}
    finally{setAnalyzing(previous=>({...previous,[fileId]:false}));}
  }

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
    try{await deleteEvidence(item.id);}catch(e){if(!(e instanceof ApiError&&e.status===404))setError('Removal was not confirmed. The unsent upload remains private and is cleared after 24 hours when you next attach a file.');}
  }
  async function send(payload?:TurnRequest){
    if(lock.current)return;lock.current=true;setBusy(true);setError('');
    const request=payload??{turn_id:crypto.randomUUID(),expected_revision:state?.revision??0,type:'message' as const,
      ...(draft.trim()?{text:draft}:{}),attachment_ids:files.map(file=>file.id),timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,
      ...(activeReview?{review_context_id:activeReview}:{})};
    setFailed(request);
    try{const caseId=await ensureCase();const next=await sendConversationTurn(caseId,request);
      nearBottom.current=true;setState(next);setFailed(null);setStale(false);
      const remainingDraft=request.type==='message'&&currentDraft.current===(request.text??'')?'':currentDraft.current;
      const sentFiles=new Set(request.attachment_ids??[]);
      const remainingFiles=files.filter(file=>!sentFiles.has(file.id));
      if(request.type==='message'){setActiveReview(null);setDraft(remainingDraft);for(const file of files)if(sentFiles.has(file.id)&&file.preview)URL.revokeObjectURL(file.preview);setFiles(remainingFiles);}
      try{sessionStorage.removeItem('cybersos-chat-creation');sessionStorage.removeItem(draftKey(incidentId));}catch{/* Saved case is authoritative. */}
      if(!incidentId){redirected.current=true;try{if(remainingDraft||remainingFiles.length)sessionStorage.setItem(draftKey(caseId),JSON.stringify({draft:remainingDraft,files:remainingFiles.map(({id,name,status})=>({id,name,status}))}));}catch{/* Keep in-memory draft. */}router.replace(`/incident/${caseId}/conversation`);}
      if(request.type==='case_review')setArtifact('plan');
      if(request.type==='message'&&request.attachment_ids?.length){
        // Run once after a durable send, never on render/reload. Analysis does not
        // hold the message pipeline or silently promote document candidates.
        void(async()=>{for(const fileId of request.attachment_ids!)await analyzeFile(caseId,fileId,next.revision);})();
      }
    }catch(e){setError(e instanceof Error?e.message:'Message could not be saved.');if(e instanceof ApiError&&e.status===409){setStale(true);if(id)try{setState(await getConversation(id));}catch{/* Reload available. */}}}
    finally{lock.current=false;setBusy(false);}
  }
  const completed=new Map(state?.completions.map(item=>[item.action_id,item.completed]));
  const immediate=state?.plan.plan.actions.filter(isImmediateAction)??[];
  const canSend=(!!draft.trim()||files.length>0)&&files.every(file=>file.status==='ready')&&!failed&&(!id||!!state);
  const complete=(actionId:string,done:boolean)=>void send({turn_id:crypto.randomUUID(),expected_revision:state!.revision,type:'completion',action_id:actionId,value:done});
  const review=(evidence_review:NonNullable<TurnRequest['evidence_review']>)=>void send({turn_id:crypto.randomUUID(),expected_revision:state!.revision,type:'evidence_review',evidence_review});
  const pending=busy&&failed&&!state?.turns.some(turn=>turn.id===failed.turn_id)?failed:null;
  function feedback(text:string){setDraft(text);document.getElementById('chat-message')?.focus();}
  return <main className="flex h-[100dvh] min-h-0 flex-col bg-paper text-ink">
    <header className="shrink-0 border-b border-line px-4 py-3"><div className="mx-auto flex max-w-6xl items-center justify-between gap-2">
      <Brand /><div className="flex gap-1">
      {!!state?.plan.plan.actions.length&&<button className={chatControl} aria-expanded={artifact==='plan'} onClick={event=>{artifactTrigger.current=event.currentTarget;setArtifact(artifact==='plan'?null:'plan');}}>Response plan</button>}
      {!!state?.turns.length&&<button className={chatControl} aria-expanded={artifact==='case'} onClick={event=>{artifactTrigger.current=event.currentTarget;setArtifact(artifact==='case'?null:'case');}}>View case</button>}</div></div></header>
    <div className="mx-auto flex min-h-0 w-full max-w-6xl flex-1 flex-col md:flex-row"><section aria-label="Incident conversation" className="flex min-h-0 min-w-0 flex-1 flex-col">
      <div ref={viewport} className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4" onScroll={()=>{const el=viewport.current;if(el){nearBottom.current=el.scrollHeight-el.scrollTop-el.clientHeight<140;setAway(!nearBottom.current);}}}>
        {!state?.turns.length&&!pending&&<div className="mx-auto flex min-h-[45dvh] max-w-2xl flex-col items-center justify-center text-center">
          <h1 className="font-display text-3xl sm:text-4xl">Tell us what happened</h1><p className="mt-4 max-w-lg leading-relaxed text-ink-muted">Start in your own words. CyberSOS helps make sense of what happened, asks what matters and organizes your case.</p>
          <p className="mt-3 text-sm text-ink-muted">Independent citizen support. No complaint is submitted here.</p></div>}
        <details open={!state?.turns.length&&!pending} className="mx-auto max-w-2xl pt-3">
          <summary className="min-h-11 cursor-pointer py-2 text-sm text-ink-muted">Optional starting choice{state?.route_hint?`: ${routes.find(r=>r.value===state.route_hint)?.label??''}`:''}</summary>
          <div className="flex flex-wrap gap-2 py-2">{routes.map(route=><button key={route.value} aria-pressed={state?.route_hint===route.value} disabled={busy||!!failed||!!id&&!state} className={`${chatControl} border border-line2`} onClick={()=>void send({turn_id:crypto.randomUUID(),expected_revision:state?.revision??0,type:'route_hint',route_hint:route.value})}>{route.label}</button>)}</div>
          <p className="text-xs text-ink-muted">You can change this, or start typing now. It does not classify your case.</p>
        </details>
        <ol aria-label="Saved message history" className="mx-auto max-w-2xl space-y-7 py-6">{state?.turns.map(turn=><li key={turn.id} className="space-y-4">
          <div className="ml-10 rounded-2xl bg-surface p-4"><p className="sr-only">You</p>{turn.text&&<p className="whitespace-pre-wrap break-words leading-relaxed">{turn.text}</p>}
            {turn.attachments?.map(file=><div key={file.id} className="mt-2 rounded-xl border border-line p-3 text-sm"><p className="break-all">{file.original_filename}</p>
              {file.deleted?<p>Attachment deleted</p>:<>{file.mime_type.startsWith('image/')&&<Image unoptimized width={240} height={160} src={evidenceFileUrl(file.id)} alt={`Attached ${file.original_filename}`} className="mt-2 max-h-48 rounded-lg object-contain"/>}
                <a className="inline-block min-h-11 py-3 underline" href={evidenceFileUrl(file.id)} target="_blank" rel="noopener noreferrer">Open attachment</a>
                <p role="status" className="text-ink-muted">{analyzing[file.id]?'Analyzing attachment…':(state.evidence_reviews??[]).find(r=>r.evidence_id===file.id)?.status==='failed'?'Analysis could not finish. You can retry, skip or keep talking.':file.extraction_status==='processing'?(analysisCheckNeeded?'Analysis has not finished. Check its progress or keep talking.':'Analyzing attachment…'):(state.evidence_reviews??[]).some(r=>r.evidence_id===file.id)?'Analyzed · check the details below':'Uploaded · ready to analyze'}</p>
                {analysisCheckNeeded&&file.extraction_status==='processing'&&<button className={chatControl} onClick={async()=>{try{setState(await getConversation(state.incident_id));}catch{setError('Progress could not be checked. You can reload the conversation.');}}}>Check analysis progress</button>}
                {analysisErrors[file.id]&&<p role="alert">{analysisErrors[file.id]}</p>}
                {!analyzing[file.id]&&(file.extraction_status!=='processing'||(state.evidence_reviews??[]).find(r=>r.evidence_id===file.id)?.status==='failed')&&!(state.evidence_reviews??[]).some(r=>r.evidence_id===file.id&&r.status==='review_needed')&&<button disabled={busy} className={chatControl} onClick={()=>void analyzeFile(state.incident_id,file.id,state.revision,!(analysisRequests.current.has(file.id)))}>{(state.evidence_reviews??[]).some(r=>r.evidence_id===file.id)||analysisErrors[file.id]?'Retry analysis':'Analyze attachment'}</button>}
                {(state.evidence_reviews??[]).filter(r=>r.evidence_id===file.id&&r.status==='review_needed').map(analysis=><EvidenceReview key={analysis.id} analysis={analysis} disabled={busy||!!failed} onReview={review} onChat={()=>{setActiveReview(analysis.id);document.getElementById('chat-message')?.focus();}}/>)}
                <p className="mt-2 text-xs text-ink-muted">Deleting removes the original and analysis. Details you confirmed remain in your case.</p>
                <button className={chatControl} disabled={busy} onClick={async()=>{try{await deleteEvidence(file.id);setState(await getConversation(state.incident_id));}catch(e){setError(e instanceof Error?e.message:'Deletion failed.');}}}>Delete attachment</button></>}
            </div>)}</div>
          <div className="mr-4 leading-relaxed"><p className="mb-2 text-sm font-semibold">CyberSOS</p>{turn.fact_changes.acknowledgement&&<p className="whitespace-pre-wrap break-words">{turn.fact_changes.acknowledgement}</p>}
            <p className="whitespace-pre-wrap break-words">{turn.fact_changes.next_move?.message??turn.pending_question?.question}</p>
            {turn.fact_changes.knowledge_sources?.map(source=><a key={source.id} href={source.url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block min-h-11 py-2 text-sm underline">{source.title} · reviewed {source.reviewed_on}</a>)}
          </div></li>)}</ol>
        {pending&&<div className="mx-auto max-w-2xl space-y-4 pb-6" aria-label="Pending message"><div className="ml-10 rounded-2xl bg-surface p-4"><p className="whitespace-pre-wrap break-words">{pending.text??(pending.type==='evidence_review'?'Reviewed attachment details':pending.type==='case_review'?'Show my response plan':pending.type==='route_hint'?routes.find(r=>r.value===pending.route_hint)?.label:'Updating your case…')}</p>
          {pending.attachment_ids?.map(fileId=><p key={fileId} className="mt-2 text-sm">{files.find(file=>file.id===fileId)?.name??'Attached file'}</p>)}</div><p role="status" aria-live="polite" className="text-sm text-ink-muted">CyberSOS is considering your reply…</p></div>}
        {!!state?.next_move?.quick_replies.length&&<div className="mx-auto flex max-w-2xl flex-wrap gap-2 pb-4">{state.next_move.quick_replies.map(reply=><button key={reply} disabled={busy||!!failed} className={`${chatControl} border border-line2`} onClick={()=>void send({turn_id:crypto.randomUUID(),expected_revision:state.revision,type:'message',text:reply})}>{reply}</button>)}</div>}
        {immediate.length>0&&<div className="mx-auto max-w-2xl pb-5"><ConversationActionPanel actions={immediate} completed={completed} disabled={busy||!!failed} onComplete={complete}/></div>}
        {state?.understanding_review?.available&&!state.understanding_review.has_reviewed&&<details className="mx-auto mb-4 max-w-2xl rounded-xl border border-line p-3"><summary className="min-h-11 cursor-pointer py-2">Review what I understood</summary><dl className="space-y-2">{Object.entries(state.understanding_review.summary).map(([field,fact])=><div key={field}><dt className="text-xs text-ink-muted">{field.replaceAll('_',' ')}</dt><dd className="break-words text-sm">{readable(fact.value)}</dd></div>)}</dl><p className="mt-3 text-sm">Correct anything in chat, or confirm this understanding to see your fuller plan.</p><button disabled={busy||!!failed} className={`${chatControl} mt-2 border border-line2`} onClick={()=>void send({turn_id:crypto.randomUUID(),expected_revision:state.revision,type:'case_review'})}>Looks right · show my plan</button></details>}
        <div ref={latest}/>
      </div>
      <div className="shrink-0 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2 sm:px-5"><div className="mx-auto max-w-2xl">
        {away&&<button className={`${chatControl} mb-2 border border-line2`} onClick={()=>{nearBottom.current=true;setAway(false);latest.current?.scrollIntoView({block:'end'});}}>Jump to latest</button>}
        {error&&<div role="alert" className="mb-2 rounded-xl border border-line2 p-3 text-sm"><p>{error}</p>{failed&&!stale&&<button className={`${chatControl} underline`} disabled={busy} onClick={()=>void send(failed)}>Retry message</button>}
          {failed&&<button className={`${chatControl} underline`} disabled={busy} onClick={()=>{setFailed(null);setError('');setStale(false);}}>Review draft</button>}
          {id&&<button className={`${chatControl} underline`} disabled={busy} onClick={async()=>{try{setState(await getConversation(id));setError('');}catch(e){setError(e instanceof Error?e.message:'Reload failed.');}}}>Reload conversation</button>}</div>}
        <ChatComposer draft={draft} onDraft={setDraft} onSend={()=>void send()} onFiles={selectFiles} busy={busy} canSend={!!canSend}>
          {activeReview&&<div role="status" className="px-3 py-2 text-sm">Reviewing the selected attachment in chat. Name the details to confirm or correct.<button type="button" className={`${chatControl} underline`} onClick={()=>setActiveReview(null)}>Cancel review focus</button></div>}
          {files.length>0&&<ul aria-label="Pending attachments" className="flex max-h-[15dvh] flex-wrap gap-2 overflow-y-auto px-2 pt-2">{files.map(file=><li key={file.id} className="max-w-full rounded-xl border border-line p-2 text-sm">
            {file.preview&&<Image unoptimized width={80} height={64} src={file.preview} alt={`Preview ${file.name}`} className="h-16 w-20 rounded object-contain"/>}<p className="max-w-52 truncate">{file.name}</p>
            <p role="status">{file.status==='ready'?'Ready to send · not analyzed':file.status==='uploading'?`Uploading ${file.percent}%`:file.error}</p>
            {file.status==='failed'&&file.file&&<button type="button" className={`${chatControl} underline`} onClick={()=>void upload(file)}>Retry upload</button>}
            <button type="button" className={`${chatControl} underline`} disabled={busy||!!failed} onClick={()=>void removeFile(file)}>{file.status==='uploading'?'Cancel upload':'Remove attachment'}</button></li>)}</ul>}
        </ChatComposer>
        <div className="mt-2 flex flex-wrap justify-between gap-1 text-xs text-ink-muted"><span>Synthetic only · No OTPs, PINs, passwords or sensitive images. JPG, PNG, PDF · 10 MB.</span><span role="status" aria-live="polite">{files.some(file=>file.status==='uploading')?'Uploading…':state?.turns.length?'Private case':''}</span></div>
        {!!state?.turns.length&&<div className="flex gap-3"><button className="min-h-9 text-xs text-ink-muted underline" onClick={()=>feedback('I think you misunderstood what I said.')}>Misunderstood</button><button className="min-h-9 text-xs text-ink-muted underline" onClick={()=>feedback('You are asking something I already answered.')}>Repeating a question</button></div>}
      </div></div></section>
      {artifact&&state&&<aside aria-label={artifact==='plan'?'Response plan details':'Current case details'} className="order-first max-h-[25dvh] shrink-0 overflow-y-auto rounded-2xl border border-line2 bg-paper p-4 shadow-card md:order-last md:max-h-none md:w-96 md:rounded-none md:border-y-0 md:border-r-0">
        <div className="mb-3 flex items-center justify-between"><h2 className="font-semibold">{artifact==='plan'?'Current response plan':'Your current case'}</h2><button className={chatControl} onClick={()=>{setArtifact(null);artifactTrigger.current?.focus();}}>Close details</button></div>
        {artifact==='plan'?(state.understanding_review&&!state.understanding_review.has_reviewed?<><p className="text-sm">Review the current understanding before opening your fuller plan. Urgent applicable help remains in the conversation.</p><dl className="mt-3 space-y-2">{Object.entries(state.understanding_review.summary).map(([field,fact])=><div key={field}><dt className="text-xs text-ink-muted">{field.replaceAll('_',' ')}</dt><dd className="break-words text-sm">{readable(fact.value)}</dd></div>)}</dl><p className="mt-3 text-sm">Correct anything in chat.</p>{state.understanding_review.available&&<button disabled={busy||!!failed} className={`${chatControl} mt-3 border border-line2`} onClick={()=>void send({turn_id:crypto.randomUUID(),expected_revision:state.revision,type:'case_review'})}>Looks right · show my plan</button>}</>:<>{state.understanding_review&&!state.understanding_review.reviewed&&<p role="status" className="mb-3 text-sm">Your case changed since review. This plan follows your current facts; you can correct them in chat.</p>}<ConversationActionPanel actions={state.plan.plan.actions.filter(action=>!isImmediateAction(action))} completed={completed} disabled={busy||!!failed} onComplete={complete}/></>):<>
          <p className="break-all text-sm">CyberSOS reference: {state.projection.reference}</p><p className="mt-2 text-sm">{state.projection.status} · revision {state.projection.revision}</p>
          {state.projection.working_understanding.length>0&&<p className="mt-4 text-sm">Working understanding: {state.projection.working_understanding.map(readable).join(', ')}</p>}
          <dl className="mt-4 space-y-3">{Object.entries(state.projection.known_facts).filter(([field])=>field!=='signals').map(([field,fact])=><div key={field}><dt className="text-sm font-medium">{field.replaceAll('_',' ')}</dt><dd className="break-words text-sm">{readable(fact.value)}<span className="block text-xs text-ink-muted">{fact.evidence_id?`Reviewed attachment detail${fact.source_deleted?' · original deleted':''}`:fact.verified?'Reviewed with you':'Working information · correct it in chat'}</span></dd></div>)}</dl>
          <p className="mt-4 text-sm">{state.projection.evidence_count} saved attachments · {state.projection.completed_actions} steps recorded done by you</p><p className="mt-4 text-xs text-ink-muted">Bookmark this private case URL. Return requires your case cookie and its current expiry. No external status is verified.</p></>}
      </aside>}
    </div>
  </main>;
}
