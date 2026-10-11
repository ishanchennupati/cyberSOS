"""Reviewed canonical case -> private reporting packet; synthetic cases only."""
import uuid
import pytest
from tests.test_phase3r_case_agent import install, move, send
from tests.test_phase3_understanding import candidate


@pytest.mark.parametrize('signal,platform',[('harassment','Instagram'),('account_takeover','Google')])
def test_reporting_requires_facts_review_and_separate_packet_approval(client,monkeypatch,signal,platform):
    install(monkeypatch,[candidate('signals',[signal],'problem'),candidate('platform',platform,platform)],
        move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded those details.'))
    state,path,_=send(client,f'I have a problem on {platform}.')
    report=path.replace('/conversation','/reporting')
    preview=client.get(report)
    assert preview.status_code==200
    assert preview.json()['state']=='ready_to_review'
    draft_id=str(uuid.uuid4())
    assert client.post(report+'/drafts',json={'draft_id':draft_id,'expected_revision':state['revision']}).status_code==409
    state=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'case_review'}).json()
    prepared=client.post(report+'/drafts',json={'draft_id':draft_id,'expected_revision':state['revision']})
    assert prepared.status_code==200
    draft=prepared.json()
    assert draft['reviewed'] is False
    assert client.get(report+f'/drafts/{draft_id}/export').status_code==409
    approved=client.post(report+f'/drafts/{draft_id}/review',json={'expected_revision':state['revision']})
    assert approved.status_code==200
    assert client.get(report).json()['state']=='ready_for_handoff'
    exported=client.get(report+f'/drafts/{draft_id}/export')
    assert exported.status_code==200
    assert 'storage_path' not in exported.text and 'submitted' not in exported.json()
    assert 'provider' not in exported.json()['narrative'] and 'failure' not in exported.json()['narrative']
    corrected=candidate('platform','Facebook','Facebook');corrected['correction_source']='Correction'
    install(monkeypatch,[corrected],move('ACKNOWLEDGE_AND_WAIT',None,'I have updated this.'))
    send(client,'Correction: this was on Facebook.',state)
    assert client.get(report+f'/drafts/{draft_id}/export').status_code==409
    assert client.get(report).json()['state']=='ready_to_review'


def test_reporting_packets_are_owned(client):
    created=client.post('/api/v1/incidents',json={'conversation_first':True}).json()
    path=f"/api/v1/incidents/{created['id']}/reporting"
    client.cookies.clear()
    assert client.get(path).status_code==404


def test_actual_pdf_export_is_private_and_reviewed(client,monkeypatch):
    install(monkeypatch,[candidate('signals',['harassment'],'harassed'),candidate('platform','Instagram','Instagram')],
        move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,path,_=send(client,'I was harassed on Instagram.')
    state=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'case_review'}).json()
    report=path.replace('/conversation','/reporting');draft_id=str(uuid.uuid4())
    assert client.post(report+'/drafts',json={'draft_id':draft_id,'expected_revision':state['revision']}).status_code==200
    client.post(report+f'/drafts/{draft_id}/review',json={'expected_revision':state['revision']})
    pdf=client.get(report+f'/drafts/{draft_id}/export?format=pdf')
    assert pdf.headers['content-type']=='application/pdf'
    assert pdf.content.startswith(b'%PDF-') and b'%%EOF' in pdf.content
    assert 'no-store' in pdf.headers['cache-control']
    assert 'attachment;' in pdf.headers['content-disposition']
    from io import BytesIO
    from pypdf import PdfReader
    document=PdfReader(BytesIO(pdf.content))
    rendered='\n'.join(page.extract_text() for page in document.pages)
    assert 'Instagram' in rendered and 'not an official receipt' in rendered
    assert 'storage_path' not in rendered and 'MALFORMED_OUTPUT' not in rendered
    assert all('/Annots' not in page for page in document.pages)


def test_packet_only_narrative_rejects_unsupported_claim():
    from app.schemas.reporting import ReviewedCasePacket,PacketFact
    from app.services.reporting_narrative import validate_claims
    packet=ReviewedCasePacket(incident_id=uuid.uuid4(),source_revision=1,facts=[PacketFact(id='platform',label='Service',value='Instagram',statement='I reported the service: Instagram.')],unknowns=[],evidence=[],recorded_actions=[],mapping={})
    with pytest.raises(ValueError):
        validate_claims({'claims':[{'fact_id':'platform','text':'The police accepted my complaint.'}]},packet)


def test_reporting_field_mapping_is_relevant_not_route_hint(client,monkeypatch):
    install(monkeypatch,[candidate('signals',['harassment'],'harassed'),candidate('platform','Instagram','Instagram')],
        move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,path,_=send(client,'I was harassed on Instagram.')
    client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'route_hint','route_hint':'financial'})
    preview=client.get(path.replace('/conversation','/reporting')).json()
    assert 'transaction_id' not in [f['id'] for f in preview['mapping']['fields']]
    assert preview['mapping']['suggested_routes']==['Other Cyber Crime']


def test_public_route_requirements_do_not_apply_anonymous_limits_to_other_reports():
    from app.services.reporting_mapping import mapping
    result=mapping(['harassment'])
    assert result['narrative']['maximum_characters'] is None
    assert result['suggested_routes']==['Other Cyber Crime']
    assert result['identity_document']['accepted_extensions']==['jpeg','jpg','png']
    assert result['identity_document']['maximum_bytes']==5*1024*1024
    branch=result['route_requirements'][0]
    assert branch['id']=='women_children_anonymous'
    assert branch['narrative']['maximum_characters']==1500
    assert branch['eligibility_established'] is False
    assert branch['evidence']['accepted_extensions'] is None
    assert branch['source_ids']==['NCRP-FAQ','NCRP-ANONYMOUS']
    assert result['evidence']['maximum_bytes']==10*1024*1024


def test_reporting_draft_retry_and_foreign_snapshot_are_safe(client,monkeypatch):
    install(monkeypatch,[candidate('signals',['financial'],'scammer'),candidate('money_lost',True,'sent'),
        candidate('amount','5000','5000'),candidate('currency','INR','INR'),candidate('payment_method','upi','UPI')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,path,_=send(client,'I sent INR 5000 via UPI to a scammer.')
    state=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'case_review'}).json()
    report=path.replace('/conversation','/reporting');payload={'draft_id':str(uuid.uuid4()),'expected_revision':state['revision']}
    first=client.post(report+'/drafts',json=payload)
    assert first.status_code==200
    assert client.post(report+'/drafts',json=payload).json()==first.json()
    assert 'transaction_id' in [f['id'] for f in first.json()['packet']['mapping']['fields']]
    assert 'Transaction reference' in first.json()['packet']['unknowns']
    other=client.post('/api/v1/incidents',json={'conversation_first':True}).json()['id']
    assert client.get(f"/api/v1/incidents/{other}/reporting/drafts/{payload['draft_id']}/export").status_code==404


def test_mixed_identifier_provenance_does_not_promote_legacy(client,monkeypatch,db):
    from app.models.incident import Incident
    from app.domain.facts import FACTS_ADAPTER
    from app.services.response_service import record_plan
    from datetime import datetime,timezone
    install(monkeypatch,[candidate('signals',['harassment'],'harassed'),candidate('identifiers',[{'type':'email','value':'known@example.test'}],'known@example.test')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,path,_=send(client,'I was harassed by known@example.test.')
    incident=db.get(Incident,uuid.UUID(state['incident_id']))
    data=dict(incident.facts)
    data['identifiers']=[{'type':'email','value':'legacy@example.test'},*data['identifiers']]
    data['provenance']=[{'field':'identifiers','origin':'legacy','identifier_value':'legacy@example.test'},*data['provenance']]
    record_plan(db,incident,FACTS_ADAPTER.validate_python(data),as_of=datetime.now(timezone.utc));db.commit()
    preview=client.get(path.replace('/conversation','/reporting')).json()
    identifiers=next(f['value'] for f in preview['facts'] if f['id']=='identifiers')
    assert identifiers==[{'type':'email','value':'known@example.test'}]


def test_recorded_action_projection_uses_latest_citizen_state(client,monkeypatch,db):
    from datetime import datetime,timezone,timedelta
    from app.models.incident import Incident
    from app.models.response import ActionCompletionRecord
    from app.domain.facts import FACTS_ADAPTER
    from app.services.response_service import record_plan
    install(monkeypatch,[candidate('signals',['harassment'],'harassed')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,path,_=send(client,'I was harassed online.')
    incident=db.get(Incident,uuid.UUID(state['incident_id']))
    first=uuid.UUID(state['plan']['id'])
    second=record_plan(db,incident,FACTS_ADAPTER.validate_python(incident.facts),as_of=datetime.now(timezone.utc))
    db.add_all([ActionCompletionRecord(incident_id=incident.id,plan_id=first,action_id='preserve_evidence',completed=True,updated_at=datetime.now(timezone.utc)-timedelta(minutes=1)),
        ActionCompletionRecord(incident_id=incident.id,plan_id=second.id,action_id='preserve_evidence',completed=False,updated_at=datetime.now(timezone.utc))]);db.commit()
    state=client.get(path).json()
    state=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'case_review'}).json()
    draft=client.post(path.replace('/conversation','/reporting')+'/drafts',json={'draft_id':str(uuid.uuid4()),'expected_revision':state['revision']})
    assert draft.status_code==200
    actions=draft.json()['packet']['recorded_actions']
    assert len(actions)==1 and actions[0]['completed'] is False


@pytest.mark.parametrize('failure',['timeout','quota','malformed','unsupported'])
def test_narrative_failure_preserves_only_packet_facts(monkeypatch,failure):
    import json
    from app.schemas.reporting import ReviewedCasePacket,PacketFact
    from app.services import reporting_narrative
    packet=ReviewedCasePacket(incident_id=uuid.uuid4(),source_revision=1,
        facts=[PacketFact(id='platform',label='Affected service',value='Instagram',statement='The affected service I identified was Instagram.')],
        unknowns=['Incident time'],evidence=[],recorded_actions=[],mapping={})
    contexts=[]
    class Quota(Exception):code=429
    class Provider:
        async def draft(self,encoded):
            contexts.append(json.loads(encoded))
            if failure=='timeout':raise TimeoutError()
            if failure=='quota':raise Quota()
            return '{}' if failure=='malformed' else json.dumps({'claims':[{'fact_id':'platform','text':'The police accepted my complaint.'}]})
    monkeypatch.setattr(reporting_narrative,'get_provider',lambda:Provider())
    result=reporting_narrative.generate(packet)
    assert contexts==[packet.model_dump(mode='json')]
    assert result['status']=='local_fallback'
    assert result['text']==packet.facts[0].statement
    assert 'police accepted' not in result['text'].lower()


def test_print_and_pdf_treat_untrusted_text_as_data():
    from app.services.reporting_export import printable,pdf
    from io import BytesIO
    from pypdf import PdfReader
    hostile='<img src="https://attacker.invalid" onerror="alert(1)"> user_name@example.test'
    data={'packet':{'facts':[{'label':'Reported text','value':hostile}], 'unknowns':[], 'evidence':[], 'recorded_actions':[], 'mapping':{'sources':[]}},
        'narrative':{'text':hostile,'portal_text':hostile}}
    rendered=printable(data)
    assert '<img ' not in rendered and '&lt;img ' in rendered
    document=PdfReader(BytesIO(pdf(data)))
    content='\n'.join(page.extract_text() for page in document.pages)
    assert 'user_name@example.test' in content
    assert all('/Annots' not in page for page in document.pages)


def test_conversation_case_cannot_bypass_packet_review_with_legacy_summary(client,monkeypatch):
    install(monkeypatch,[candidate('signals',['harassment'],'harassed')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,path,_=send(client,'I was harassed online.')
    response=client.post(path.replace('/conversation','/generate-summary'))
    assert response.status_code==409
    assert 'reporting packet' in response.json()['detail'].lower()


def test_overlapping_signals_share_one_reviewed_packet(client,monkeypatch):
    story='I was harassed on Instagram and paid INR 5000 via UPI to a scammer.'
    install(monkeypatch,[candidate('signals',['harassment','financial'],story),candidate('platform','Instagram','Instagram'),
        candidate('money_lost',True,'paid'),candidate('amount','5000','5000'),candidate('currency','INR','INR'),
        candidate('payment_method','upi','UPI')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,path,_=send(client,story)
    state=client.post(path+'/turns',json={'turn_id':str(uuid.uuid4()),'expected_revision':state['revision'],'type':'case_review'}).json()
    result=client.post(path.replace('/conversation','/reporting')+'/drafts',json={'draft_id':str(uuid.uuid4()),'expected_revision':state['revision']})
    assert result.status_code==200
    packet=result.json()['packet']
    assert packet['incident_id']==state['incident_id']
    assert packet['mapping']['suggested_routes']==['Financial Fraud','Other Cyber Crime']
    assert {f['id'] for f in packet['facts']} >= {'platform','amount','signals'}


def test_unresolved_conflict_blocks_reporting_approval_path(client,monkeypatch):
    install(monkeypatch,[candidate('signals',['harassment'],'harassed'),candidate('platform','Instagram','Instagram')],move('ACKNOWLEDGE_AND_WAIT',None,'I have recorded this.'))
    state,path,_=send(client,'I was harassed on Instagram.')
    install(monkeypatch,[candidate('platform','Facebook','Facebook')],move('ACKNOWLEDGE_AND_WAIT',None,'Your statements differ.'))
    state,_,_=send(client,'This was on Facebook.',state)
    preview=client.get(path.replace('/conversation','/reporting')).json()
    assert preview['state']=='gathering' and 'platform' in preview['conflicts']
    assert client.post(path.replace('/conversation','/reporting')+'/drafts',json={'draft_id':str(uuid.uuid4()),'expected_revision':state['revision']}).status_code==409
