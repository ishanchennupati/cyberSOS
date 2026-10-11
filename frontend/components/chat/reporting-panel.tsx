'use client';
import {useEffect,useRef,useState} from 'react';
import {ApiError,downloadReporting,getConversation,getReporting,getReviewedReporting,prepareReporting,reportingExportUrl,reviewReporting,sendConversationTurn} from '@/lib/api';
import type {ConversationState} from '@/types/conversation';
import type {ReportingPreview} from '@/types/reporting';
import {chatControl} from '@/components/chat/composer';

function text(value:unknown):string{
  if(value&&typeof value==='object'&&'original' in value)return `${value.original} (approximate)${'start' in value&&'end' in value?` · ${value.start} to ${value.end}`:''}`;
  if(Array.isArray(value))return value.map(text).join('; ');
  if(value&&typeof value==='object')return Object.entries(value).map(([key,v])=>`${key}: ${text(v)}`).join('; ');
  return typeof value==='boolean'?(value?'Yes':'No'):String(value);
}

export function ReportingPanel({caseState,onCaseChange}:{caseState:ConversationState;onCaseChange:(state:ConversationState)=>void}){
  const [preview,setPreview]=useState<ReportingPreview|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  const retry=useRef<{draft_id:string;expected_revision:number}|null>(null),reviewRetry=useRef<{turn_id:string;expected_revision:number}|null>(null);
  const readSequence=useRef(0),previousCase=useRef(caseState.incident_id);
  const id=caseState.incident_id;
  useEffect(()=>{
    if(previousCase.current!==id){retry.current=null;reviewRetry.current=null;setPreview(null);previousCase.current=id;}
    if(reviewRetry.current?.expected_revision!==caseState.revision)reviewRetry.current=null;
    let active=true;const sequence=++readSequence.current;
    getReporting(id).then(value=>{if(active&&sequence===readSequence.current)setPreview(value);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};
  },[id,caseState.revision]);
  const current=preview?.revision===caseState.revision,draft=current?preview?.draft:null,approved=!!draft?.reviewed;
  async function refresh(){const sequence=++readSequence.current,value=await getReporting(id);if(sequence===readSequence.current)setPreview(value);}
  async function recover(e:unknown){
    setError(e instanceof Error?e.message:'Reporting request failed.');
    if(e instanceof ApiError&&e.status===409){reviewRetry.current=null;retry.current=null;const state=await getConversation(id);onCaseChange(state);await refresh();}
  }
  async function prepare(){
    if(!preview||!current||busy)return;setBusy(true);setError('');setNotice('Preparing from reviewed facts…');
    try{
      let revision=preview.revision;
      if(!preview.facts_reviewed){const request=reviewRetry.current??{turn_id:crypto.randomUUID(),expected_revision:revision};reviewRetry.current=request;
        const state=await sendConversationTurn(id,{...request,type:'case_review'});reviewRetry.current=null;revision=state.revision;onCaseChange(state);}
      if(!retry.current||retry.current.expected_revision!==revision)retry.current={draft_id:crypto.randomUUID(),expected_revision:revision};
      await prepareReporting(id,retry.current);retry.current=null;await refresh();setNotice('Draft prepared. Review the narrative and packet before transferring.');
    }catch(e){await recover(e).catch(()=>{});setNotice('Your case and chat draft remain saved. Retry or correct details in chat.');}
    finally{setBusy(false);}
  }
  async function approve(){if(!draft||!preview||busy)return;setBusy(true);setError('');try{await reviewReporting(id,draft.id,preview.revision);await refresh();setNotice('Packet reviewed. You can copy or export it and continue on the official portal.');}catch(e){setError(e instanceof Error?e.message:'Review failed.');}finally{setBusy(false);}}
  async function copy(field:string,label:string,identifier?:string){
    if(!draft||!approved)return;setError('');setNotice('Checking reviewed packet…');
    try{const sealed=await getReviewedReporting(id,draft.id);const fact=sealed.packet.facts.find(value=>value.id===field);
      if(field!=='narrative'&&!fact)throw new Error('This field is not in the reviewed packet.');
      let value=field==='narrative'?sealed.narrative.portal_text:text(fact!.value);
      if(identifier){
        const items=Array.isArray(fact?.value)?fact.value:[];
        const match=items.find(item=>item&&typeof item==='object'&&'value' in item&&item.value===identifier);
        if(!match)throw new Error('This identifier is not in the current reviewed packet.');
        value=identifier;
      }
      await navigator.clipboard.writeText(value);setNotice(`${label} copied.`);
    }catch(e){await recover(e).catch(()=>{});setNotice('Copy unavailable until the current packet is reviewed.');}
  }
  async function download(format:'pdf'|'json'){if(!draft||!approved)return;setError('');try{const blob=await downloadReporting(id,draft.id,format),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`CyberSOS-${draft.id}.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);setNotice(`${format.toUpperCase()} download started.`);}catch(e){setError(e instanceof Error?e.message:'Download failed.');}}
  return <div className="space-y-4 text-sm">
    <p>Review the information already gathered. Correct anything through the conversation below.</p>
    <p role="status" aria-live="polite">{notice||(!preview?'Loading reporting preview…':preview.state==='ready_for_handoff'?'Reviewed packet · ready to transfer':preview.state==='gathering'?'More understanding or conflict review is needed':'Ready to review')}</p>
    {error&&<p role="alert">{error}<button className={`${chatControl} underline`} onClick={()=>void refresh().catch(e=>setError(e.message))}>Reload reporting preview</button></p>}
    {preview?.has_stale_draft&&<p role="status">Your case changed. The earlier packet needs a new review and draft.</p>}
    {!!preview?.conflicts.length&&<p>Clarify these differences in chat: {preview.conflicts.join(', ')}.</p>}
    <dl className="space-y-3">{(draft?.packet.facts??preview?.facts??[]).map(fact=><div key={fact.id}><dt className="font-medium">{fact.label}</dt><dd className="whitespace-pre-wrap break-words">{text(fact.value)}</dd>{approved&&(fact.id==='identifiers'&&Array.isArray(fact.value)?fact.value.map(item=><button key={`${item.type}:${item.value}`} className={`${chatControl} underline`} onClick={()=>void copy(fact.id,`${item.type} identifier`,item.value)}>Copy {item.type} identifier</button>):<button className={`${chatControl} underline`} onClick={()=>void copy(fact.id,fact.label)}>Copy {fact.label}</button>)}</div>)}</dl>
    {preview?.state!=='gathering'&&current&&!draft&&<button disabled={busy} className={`${chatControl} border border-line2`} onClick={()=>void prepare()}>{busy?'Preparing…':preview?.facts_reviewed?'Prepare reporting draft':'Facts look right · prepare reporting draft'}</button>}
    {draft&&<>
      <section aria-label="Citizen complaint narrative"><h3 className="font-semibold">Citizen account</h3><p className="mt-2 whitespace-pre-wrap break-words">{draft.narrative.text}</p></section>
      {draft.narrative.portal_text!==draft.narrative.text&&<section><h3 className="font-semibold">Portal transfer copy</h3><p className="whitespace-pre-wrap break-words">{draft.narrative.portal_text}</p></section>}
      {draft.narrative.warnings.map(warning=><p key={warning}>{warning}</p>)}
      {!!draft.packet.unknowns.length&&<section><h3 className="font-semibold">Unknown information</h3><ul className="list-disc pl-5">{draft.packet.unknowns.map(value=><li key={value}>{value}</li>)}</ul></section>}
      <section><h3 className="font-semibold">Evidence inventory</h3>{draft.packet.evidence.length?draft.packet.evidence.map(file=><p key={file.id} className="break-words">{file.name} · {file.size_bytes} bytes. Attached original; contents are not verified by this inventory.</p>):<p>No attachments listed.</p>}</section>
      {!!draft.packet.recorded_actions.length&&<section><h3 className="font-semibold">Actions recorded by you</h3>{draft.packet.recorded_actions.map(action=><p key={action.action_id}>{action.action_id.replaceAll('_',' ')} · {action.completed?'recorded complete':'not completed'}{action.reference?` · ${action.reference} (recorded by you)`:''}</p>)}</section>}
      {!approved?<button disabled={busy} className={`${chatControl} border border-line2`} onClick={()=>void approve()}>I reviewed this packet · ready to transfer</button>:<div className="flex flex-wrap gap-2"><button className={`${chatControl} underline`} onClick={()=>void copy('narrative','Narrative')}>Copy narrative</button><button className={`${chatControl} underline`} onClick={()=>void download('pdf')}>Download reviewed PDF</button><button className={`${chatControl} underline`} onClick={()=>void download('json')}>Download reviewed JSON</button><a className={`${chatControl} underline`} href={reportingExportUrl(id,draft.id,'html')} target="_blank" rel="noopener noreferrer">Print reviewed packet</a></div>}
    </>}
    {preview&&<details>
      <summary className="min-h-11 cursor-pointer py-2">Official portal fields and requirements</summary>
      {preview.mapping.fields.map(field=><p className="my-2" key={field.id}><strong>{field.label}</strong> · {field.required?'Required on the referenced portal page':'Optional if known'}. {field.format}</p>)}
      <p>Enter directly on the official portal: {preview.mapping.portal_only.join(', ')}.</p>
      <p>The public checklist allows relevant evidence up to {(preview.mapping.evidence.maximum_bytes??0)/1024/1024} MB each. Its evidence file types are not specified; check the applicable official form. Identity images there are JPEG/JPG/PNG, up to {preview.mapping.identity_document.maximum_bytes/1024/1024} MB. CyberSOS does not request these identity documents.</p>
      {preview.mapping.route_requirements.map(route=><section key={route.id} className="my-3"><h3 className="font-semibold">{route.label}</h3><p>{route.eligibility}</p><p>The public anonymous form requests: {route.required_fields.join('; ')}. Its incident narrative accepts {route.narrative.minimum_characters}–{route.narrative.maximum_characters} characters. These are separate from the limits of registered reporting routes.</p><p>{route.meaning}</p></section>)}
      {preview.mapping.limitations.map(value=><p className="my-2" key={value}>{value}</p>)}
      {preview.mapping.sources.map(source=><a key={source.id} className="block min-h-11 py-2 underline" href={source.url} target="_blank" rel="noopener noreferrer">{{'NCRP-LOGIN':'Official portal checklist','NCRP-FAQ':'Official reporting FAQ','NCRP-ANONYMOUS':'Official anonymous content form','NCRP-MANUAL-2019':'Official citizen manual (historical)'}[source.id as 'NCRP-LOGIN']??source.id}</a>)}
    </details>}
    {approved&&preview&&<section><h3 className="font-semibold">Continue on the official portal</h3><p>Prepared by CyberSOS, an independent companion. Registration, identity verification and submission happen there. Opening the portal does not submit this packet.</p><p>Choose the applicable reporting route on the portal. {preview.mapping.suggested_routes.join(' / ')} may apply based on your reviewed story.</p><a className={`${chatControl} mt-2 underline`} href={preview.mapping.destination} target="_blank" rel="noopener noreferrer">Open official reporting portal</a></section>}
  </div>;
}
