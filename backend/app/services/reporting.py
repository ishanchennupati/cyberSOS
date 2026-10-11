"""Reviewed reporting snapshots through the existing owned case boundary."""
import hashlib
import json
from datetime import datetime,timezone
from fastapi import HTTPException
from sqlalchemy import select,update
from app.models.conversation import ConversationState
from app.models.evidence import Evidence
from app.models.reporting import ReportingSnapshot
from app.schemas.reporting import ReviewedCasePacket,PacketFact,ReportingDraft
from app.services import conversation_service
from app.services.reporting_mapping import mapping


FIELDS={'platform':'Affected service','signals':'Working incident signals','money_lost':'Reported money loss',
    'amount':'Amount','currency':'Currency','payment_method':'Payment method','payment_app':'Payment app',
    'authorization':'Payment approval','transaction_id':'Transaction reference','recipient':'Recipient',
    'time_window':'Approximate incident time','occurred_at':'Incident time','timestamp_text':'Reported timestamp',
    'identifiers':'Known identifiers','claimed_organization':'Organization claimed by the caller',
    'claimed_person':'Person claimed by the caller','message_text':'Reported message text','threat_text':'Reported threat text',
    'account_compromised':'Reported account access','remote_access':'Reported device access',
    'immediate_danger':'Reported immediate physical danger','blackmail':'Reported blackmail',
    'private_image_threat':'Reported private-image threat'}


def display(value):
    if isinstance(value,dict):return value.get('original') or '; '.join(f'{k}: {display(v)}' for k,v in value.items())
    if isinstance(value,list):return '; '.join(display(v) for v in value)
    if isinstance(value,bool):return 'yes' if value else 'no'
    return str(value)


def statement(field,value):
    rendered=display(value)
    if field=='signals':return 'My reported concerns include possible '+', '.join(item.replace('_',' ') for item in value)+'.'
    if field=='platform':return f'The affected service I identified was {rendered}.'
    if field=='amount':return f'The amount I reported was {rendered}.'
    if field=='currency':return f'I identified the currency as {rendered}.'
    if field=='authorization':return 'I approved the payment.' if value=='authorized' else 'I did not approve the transaction.'
    if field=='payment_method':return f'The payment method I identified was {rendered.replace("_"," ")}.'
    if field=='time_window':return f'I described the time as {value["original"]}; the approximate interval is {value["start"]} to {value["end"]} ({value["timezone"]}).'
    if field=='money_lost':return 'I reported that money was lost or sent.' if value else 'I reported that no money was lost or sent.'
    if field=='private_image_threat':return 'I reported a threat to share private images.' if value else 'I reported no threat to share private images.'
    if field=='blackmail':return 'I described the situation as blackmail.' if value else 'I said there was no blackmail.'
    if field=='account_compromised':return 'I reported access to my account by someone else.' if value else 'I reported no current account access by someone else.'
    if field=='remote_access':return 'I reported that someone else still had access to my device.' if value else 'I reported no remaining device access by someone else.'
    if field=='immediate_danger':return 'I reported immediate physical danger.' if value else 'I reported no immediate physical danger.'
    return f'I reported {FIELDS[field].lower()}: {rendered}.'


def source(db,incident):
    state=conversation_service.read(db,incident)
    facts=state.facts.model_dump(mode='json')
    latest_provenance={p.field:p for p in state.facts.provenance}
    eligible={field for field,p in latest_provenance.items() if p.origin!='legacy' and
        (p.origin not in {'inference','evidence_extraction'} or p.verified)}
    # Signal derivation can accompany explicitly accepted facts, but legacy
    # columns, summaries and unreviewed extraction never enter this packet.
    selected={key:value for key,value in facts.items() if key in FIELDS and key in eligible and value not in (None,'unknown',[],{})}
    by_identifier={p.identifier_value:p for p in state.facts.provenance if p.field=='identifiers' and p.identifier_value}
    identifiers=[item for item in facts['identifiers'] if item['value'] in by_identifier and
        by_identifier[item['value']].origin!='legacy' and
        (by_identifier[item['value']].origin not in {'inference','evidence_extraction'} or by_identifier[item['value']].verified)]
    selected.pop('identifiers',None)
    if identifiers:selected['identifiers']=identifiers
    evidence=[{'id':str(e.id),'name':e.original_filename,'mime_type':e.mime_type,'size_bytes':e.file_size,
        'analysis':e.extraction_status.value,'meaning':'Attached original; inventory does not verify its contents'}
        for e in db.scalars(select(Evidence).where(Evidence.incident_id==incident.id).order_by(Evidence.id))]
    latest_actions={}
    for completion in sorted(state.completions,key=lambda c:(c.updated_at.replace(tzinfo=timezone.utc) if c.updated_at.tzinfo is None else c.updated_at,str(c.id))):
        latest_actions[completion.action_id]=completion
    actions=[{'action_id':c.action_id,'completed':c.completed,'reference':c.user_recorded_reference,
        'recorded_at':c.updated_at.isoformat(),'meaning':'Latest state recorded by you'} for _,c in sorted(latest_actions.items())]
    conflicts=state.memory.get('open_issues',[])
    basis={'revision':state.revision,'facts':facts,'evidence':evidence,'recorded_actions':actions,
        'conflicts':conflicts,'mapping':mapping(facts['signals'])}
    digest=hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return state,selected,evidence,actions,conflicts,digest


def packet(state,selected,evidence,actions):
    provenance={}
    for item in state.facts.provenance:
        key=(item.field,item.identifier_value if item.field=='identifiers' else None)
        provenance[key]=item
    def refs(field,value):
        keys=[(field,item['value']) for item in value] if field=='identifiers' else [(field,None)]
        return [{'conversation_turn':str(provenance[key].source_turn) if provenance[key].source_turn else None,
            'evidence_id':str(provenance[key].evidence_id) if provenance[key].evidence_id else None,
            'original_deleted':provenance[key].source_deleted} for key in keys if key in provenance]
    unknowns=[name for name in ['Incident date/time','Suspect identity'] if
        (name!='Incident date/time' or not selected.keys()&{'occurred_at','time_window','timestamp_text'})]
    if 'financial' in state.facts.signals:
        unknowns += [FIELDS[field] for field in ['amount','currency','payment_method','transaction_id','authorization'] if field not in selected]
        unknowns.append('Bank/wallet/merchant name: enter the applicable name on the official portal; caller claims do not establish your bank.')
    result=ReviewedCasePacket(incident_id=state.incident_id,source_revision=state.revision,
        facts=[PacketFact(id=key,label=FIELDS[key],value=value,statement=statement(key,value),source_refs=refs(key,value))
            for key,value in selected.items()],unknowns=unknowns,evidence=evidence,recorded_actions=actions,
        mapping=mapping(state.facts.signals))
    from app.services.reporting_handoff import OfficialPortalHandoff
    result.handoff=OfficialPortalHandoff().prepare(result)
    return result


def draft_read(row):
    return ReportingDraft(id=row.id,source_revision=row.source_revision,source_digest=row.source_digest,
        packet=row.packet,narrative=public_narrative(row.narrative),reviewed=row.reviewed_at is not None,reviewed_at=row.reviewed_at)


def public_narrative(narrative):
    return {key:value for key,value in narrative.items() if key in {'text','portal_text','claims','warnings'}}


def preview(db,incident):
    state,selected,evidence,actions,conflicts,digest=source(db,incident)
    rows=list(db.scalars(select(ReportingSnapshot).where(ReportingSnapshot.incident_id==incident.id).order_by(ReportingSnapshot.created_at.desc())))
    latest=next((row for row in rows if row.source_digest==digest),None)
    ready=bool(selected) and bool(state.facts.signals) and not conflicts and not state.memory.get('incident_scope_pending')
    status='ready_for_handoff' if ready and latest and latest.reviewed_at else 'ready_to_review' if ready else 'gathering'
    return {'state':status,'revision':state.revision,'facts_reviewed':state.understanding_review['reviewed'],
        'facts':[{'id':key,'label':FIELDS[key],'value':value} for key,value in selected.items()],
        'conflicts':conflicts,'mapping':mapping(state.facts.signals),
        'draft':draft_read(latest) if latest else None,'has_stale_draft':bool(rows) and latest is None}


def lock_revision(db,incident_id,revision):
    claimed=db.execute(update(ConversationState).where(ConversationState.incident_id==incident_id,
        ConversationState.revision==revision).values(revision=revision))
    if claimed.rowcount!=1:raise HTTPException(409,'The case changed. Reload and review the current case.')


def prepare(db,incident,request):
    state,selected,evidence,actions,conflicts,digest=source(db,incident)
    if state.revision!=request.expected_revision or not state.understanding_review['reviewed'] or not selected or conflicts or state.memory.get('incident_scope_pending'):
        raise HTTPException(409,'Review current facts and resolve conflicting information in chat before preparing a report.')
    existing=db.get(ReportingSnapshot,request.draft_id)
    if existing:
        if existing.incident_id!=incident.id:raise HTTPException(404,'Draft not found')
        if existing.source_digest!=digest:raise HTTPException(409,'This draft is stale. Prepare a new draft.')
        return draft_read(existing)
    reviewed=packet(state,selected,evidence,actions)
    from app.services.reporting_narrative import generate
    narrative=generate(reviewed)
    # Provider work happens before acquiring the mutation lock. Never seal a
    # draft against stale facts if another turn arrived during generation.
    db.expire_all()
    current,*_,current_digest=source(db,incident)
    if current.revision!=state.revision or current_digest!=digest:
        raise HTTPException(409,'The case changed during drafting. Reload and prepare the current case.')
    lock_revision(db,incident.id,state.revision)
    row=ReportingSnapshot(id=request.draft_id,incident_id=incident.id,source_revision=state.revision,source_digest=digest,
        packet=reviewed.model_dump(mode='json'),narrative=narrative)
    db.add(row)
    from sqlalchemy.exc import IntegrityError
    try:db.commit()
    except IntegrityError:
        db.rollback()
        existing=db.get(ReportingSnapshot,request.draft_id)
        if existing is None or existing.incident_id!=incident.id:raise HTTPException(409,'Draft retry conflicted. Reload the reporting preview.')
        if existing.source_digest!=digest:raise HTTPException(409,'The case changed. Prepare a new draft.')
        return draft_read(existing)
    db.refresh(row)
    return draft_read(row)


def current_row(db,incident,draft_id):
    row=db.get(ReportingSnapshot,draft_id)
    if row is None or row.incident_id!=incident.id:raise HTTPException(404,'Draft not found')
    state,*_,digest=source(db,incident)
    if row.source_revision!=state.revision or row.source_digest!=digest:raise HTTPException(409,'This packet is stale. Review the current case and prepare a new packet.')
    return row,state


def review(db,incident,draft_id,request):
    row,state=current_row(db,incident,draft_id)
    if request.expected_revision!=state.revision:raise HTTPException(409,'The case changed. Review the current case.')
    lock_revision(db,incident.id,state.revision)
    if row.reviewed_at is None:row.reviewed_at=datetime.now(timezone.utc)
    db.commit();db.refresh(row)
    return draft_read(row)


def export(db,incident,draft_id):
    row,state=current_row(db,incident,draft_id)
    if row.reviewed_at is None:raise HTTPException(409,'Review this reporting packet before exporting it.')
    return {'packet':row.packet,'narrative':public_narrative(row.narrative),'reviewed_at':row.reviewed_at.isoformat()}
