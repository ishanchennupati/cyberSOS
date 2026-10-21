'use client';
import {useEffect,useState} from 'react';
import {confirmSignIn,deleteCase,getReturnSession,getSavedCases,makeRecoveryCode,recoverCase,requestSignIn,revokeSessions,saveCase,signOut} from '@/lib/api';
import type {ReturnSession} from '@/lib/api';
import {chatControl} from '@/components/chat/composer';

function clearPrivateDrafts(caseId?:string){
  try{for(const key of Object.keys(sessionStorage))if(key.startsWith('cybersos-')&&(!caseId||key.includes(caseId)||key==='cybersos-chat-creation'))sessionStorage.removeItem(key);}catch{/* Storage may be unavailable. */}
}

export function SecureReturn({caseId,expiresAt,onRestored}:{caseId?:string;expiresAt?:string;onRestored?:()=>void}){
  const [session,setSession]=useState<ReturnSession|null>(null),[email,setEmail]=useState('');
  const [notice,setNotice]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const [code,setCode]=useState(''),[recovery,setRecovery]=useState(''),[reference,setReference]=useState(caseId??'');
  const [token,setToken]=useState(''),[confirmDelete,setConfirmDelete]=useState(false);
  const [cases,setCases]=useState<Awaited<ReturnType<typeof getSavedCases>>['cases']>([]);
  async function refresh(){const current=await getReturnSession();setSession(current);if(current.signed_in)setCases((await getSavedCases()).cases);else setCases([]);}
  useEffect(()=>{void refresh().catch(()=>setError('Secure-return controls could not load. You can keep chatting.'));
    function readLink(){
      const fragment=new URLSearchParams(window.location.hash.slice(1));const supplied=fragment.get('token');
      if(supplied){setToken(supplied);window.history.replaceState(null,'',window.location.pathname);}
    }
    readLink();window.addEventListener('hashchange',readLink);
    return()=>window.removeEventListener('hashchange',readLink);
  },[]);
  async function run(action:()=>Promise<void>){if(busy)return;setBusy(true);setError('');setNotice('');try{await action();}catch(e){setError(e instanceof Error?e.message:'Please try again.');}finally{setBusy(false);}}
  return <div className="space-y-4 text-sm" aria-label="Secure return and privacy">
    <h3 className="font-semibold">Save access and return later</h3>
    <p>Chatting does not require an account. A bookmark alone cannot reopen a case after browser access expires.</p>
    {expiresAt&&<p>Case expiry: {new Date(expiresAt).toLocaleDateString()}. Citizen updates extend the 90-day inactivity period.</p>}
    {token&&<div><p>Confirm the sign-in you requested in this browser. This does not save any guest case automatically.</p><button disabled={busy} className={`${chatControl} border border-line2`} onClick={()=>void run(async()=>{await confirmSignIn(token);setToken('');await refresh();setNotice('Signed in. Return to your chat and choose Save this case, or open a saved case below.');})}>Confirm email sign-in</button></div>}
    {session?.signed_in?<div className="space-y-2"><p>Signed in as {session.email}</p>
      {!session.recently_verified&&<p>Verify your safe email again to save another case or change recovery access. Your chat and draft stay here.</p>}
      <button disabled={busy||!session.email_available} className={`${chatControl} underline`} onClick={()=>void run(async()=>{const result=await requestSignIn(session.email!);setNotice(result.message);})}>Verify my email again</button>
      <button disabled={busy} className={`${chatControl} underline`} onClick={()=>void run(async()=>{await refresh();setNotice('Sign-in status refreshed.');})}>I verified my email · refresh</button>
      {caseId&&<button disabled={busy} className={`${chatControl} border border-line2`} onClick={()=>void run(async()=>{await saveCase(caseId);await refresh();setNotice('This case is saved to your verified email.');})}>Save this case</button>}
      <button disabled={busy} className={`${chatControl} underline`} onClick={()=>void run(async()=>{await signOut();clearPrivateDrafts();window.location.assign('/return');})}>Sign out on this browser</button>
      <details><summary className="min-h-11 cursor-pointer py-2">Other signed-in sessions</summary><p>Revoking sessions requires email verification within the last 15 minutes. Saved recovery codes remain valid.</p><button disabled={busy} className={`${chatControl} underline`} onClick={()=>void run(async()=>{await revokeSessions();clearPrivateDrafts();await refresh();setNotice('Signed-in sessions and browser case credentials were revoked.');})}>Revoke signed-in sessions</button></details>
    </div>:<form className="space-y-2" onSubmit={event=>{event.preventDefault();void run(async()=>{const result=await requestSignIn(email);setNotice(result.message);});}}>
      <label className="block">Email you securely control<input type="email" required maxLength={254} value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email" className="mt-1 block min-h-11 w-full rounded border border-line bg-paper p-2"/></label>
      <p className="text-xs text-ink-muted">If your email was compromised, use another safe address or the recovery-code option.</p>
      <button disabled={busy||!session?.email_available} className={`${chatControl} border border-line2`}>Send sign-in link</button>
      {session&&!session.email_available&&<p>Email sign-in awaits local Resend configuration. You can keep chatting and save a recovery code.</p>}
      {session?.test_delivery_only&&<p className="text-xs text-ink-muted">Local testing: email delivery is restricted to the configured Resend account inbox.</p>}
      <button type="button" disabled={busy} className={`${chatControl} underline`} onClick={()=>void run(async()=>{await refresh();setNotice('Sign-in status refreshed.');})}>I verified my email · refresh</button>
    </form>}
    {!caseId&&session?.signed_in&&<section aria-label="Your saved cases"><h3 className="font-semibold">Your cases</h3>{cases.length?<ul>{cases.map(item=><li key={item.id} className="my-3 rounded border border-line p-3"><a className="block min-h-11 underline" href={`/incident/${item.id}/conversation`}>{item.signals.join(', ').replaceAll('_',' ')||'Continuing case'} · {item.id.slice(0,8)}</a><p>Updated {new Date(item.updated_at).toLocaleDateString()} · expires {new Date(item.expires_at).toLocaleDateString()}</p></li>)}</ul>:<p>No cases linked yet. Open an existing chat and choose Save this case after verifying your email.</p>}</section>}
    {caseId&&<button disabled={busy} className={`${chatControl} border border-line2`} onClick={()=>void run(async()=>{setCode((await makeRecoveryCode(caseId)).code);setNotice('Save the code privately with your case reference. Generating another code invalidates the previous code.');})}>Generate private recovery code</button>}
    {code&&<div role="status" className="rounded border border-line p-3"><p>Case reference: {reference||caseId}</p><p className="my-2 break-all font-mono" aria-label="New recovery code">{code}</p><p>Keep this private. Anyone with this code and case reference can access this case. Save this replacement before continuing; it is shown only here and rotates after recovery.</p><button className={`${chatControl} underline`} onClick={()=>setCode('')}>Hide recovery code</button>{!caseId&&<a className={`${chatControl} underline`} href={`/incident/${reference}/conversation`}>Continue this case</a>}{caseId&&onRestored&&<button className={`${chatControl} underline`} onClick={onRestored}>Continue conversation</button>}</div>}
    <details><summary className="min-h-11 cursor-pointer py-2">Return using a saved recovery code</summary>
      <form className="space-y-2" onSubmit={event=>{event.preventDefault();void run(async()=>{const result=await recoverCase(reference,recovery);setRecovery('');setCode(result.code);setNotice('Access restored. Save the replacement recovery code; the old code no longer works.');});}}>
        <label className="block">Case reference<input required value={reference} onChange={e=>setReference(e.target.value)} className="block min-h-11 w-full rounded border border-line bg-paper p-2"/></label>
        <label className="block">Private recovery code<input type="password" required autoComplete="off" value={recovery} onChange={e=>setRecovery(e.target.value)} className="block min-h-11 w-full rounded border border-line bg-paper p-2"/></label>
        <button disabled={busy} className={`${chatControl} border border-line2`}>Recover this case</button>
      </form>
    </details>
    {caseId&&<details><summary className="min-h-11 cursor-pointer py-2">Delete this case</summary><p>Delete this conversation, evidence, derived information and reporting packet. Saved copies outside CyberSOS and provider/backups have separate limits.</p><label className="my-2 flex min-h-11 items-center gap-2"><input type="checkbox" checked={confirmDelete} onChange={e=>setConfirmDelete(e.target.checked)}/>I want to permanently delete this case.</label><button disabled={busy||!confirmDelete} className={`${chatControl} border border-line2`} onClick={()=>void run(async()=>{await deleteCase(caseId);clearPrivateDrafts(caseId);window.location.assign('/return?deleted=1');})}>Permanently delete case</button></details>}
    <p className="text-xs text-ink-muted">If browser access expires and you have neither a linked safe email nor a recovery code, we cannot restore access. This development app uses synthetic data only.</p>
    {notice&&<p role="status" aria-live="polite">{notice}</p>}{error&&<p role="alert">{error}</p>}{busy&&<p role="status">Working…</p>}
  </div>;
}
