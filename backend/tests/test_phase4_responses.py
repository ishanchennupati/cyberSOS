import pytest
from datetime import datetime, timezone
from app.domain.facts import FACTS_ADAPTER
from app.domain.playbooks import evaluate
from app.schemas.next_move import NextMove
from app.services.case_agent import build_context, validate_move, MoveRejected
from tests.test_phase3r_case_agent import move


def context(message='Why are you asking when it happened?'):
    facts = FACTS_ADAPTER.validate_python({'kind':'financial_authorization_unknown', 'money_lost':True,
        'amount':'5000', 'currency':'INR'})
    return build_context(facts, {}, [], [], message, evaluate(facts, as_of=datetime.now(timezone.utc)), [], [])


def test_combined_acknowledgement_explanation_and_one_question():
    proposal = NextMove.model_validate(move(message='You reported losing ₹5,000. Knowing the time helps organize your timeline. About when did this happen?',
        fact_refs=[{'field':'amount','value':'5000'}, {'field':'currency','value':'INR'}]))
    assert validate_move(proposal, context()).message == proposal.message


def test_answer_uses_actual_retrieved_claim_and_source():
    case = context('What is the cybercrime reporting portal?')
    knowledge = next(item for item in case['knowledge'] if item['source_id']=='NCRP-REPORT')
    proposal = NextMove.model_validate(move('ANSWER_RELEVANT_QUESTION',None,
        'The National Cybercrime Reporting Portal is an external citizen reporting destination.',
        knowledge_refs=[{'id':knowledge['id'], 'claim':knowledge['text']}]))
    assert validate_move(proposal, case).message == proposal.message


@pytest.mark.parametrize('text', ['Your bank has frozen the funds.', 'You will get a refund tomorrow.',
    'Please transfer your remaining savings.', 'Tell me your password.', 'The police accepted your complaint.'])
def test_natural_reply_does_not_authorize_unsafe_claims(text):
    proposal = NextMove.model_validate(move('ACKNOWLEDGE_AND_WAIT', None, text))
    with pytest.raises(MoveRejected):
        validate_move(proposal, context())


def test_fact_reference_must_match_current_truth():
    proposal = NextMove.model_validate(move(message='About when did this happen?',fact_refs=[{'field':'amount','value':'9999'}]))
    with pytest.raises(MoveRejected):
        validate_move(proposal, context())


def test_citation_cannot_expand_reviewed_claim():
    case = context('What is the cybercrime reporting portal?')
    proposal = NextMove.model_validate(move('ANSWER_RELEVANT_QUESTION',None,'Recovery is guaranteed.',
        knowledge_refs=[{'id':'NCRP-REPORT:1','claim':'Recovery is guaranteed.'}]))
    with pytest.raises(MoveRejected):
        validate_move(proposal, case)


def test_provider_schema_keeps_reference_definitions_at_root():
    from app.services.ai_provider import provider_schema
    schema = provider_schema(NextMove, context())
    assert 'FactReference' in schema['$defs']
    assert 'KnowledgeReference' in schema['$defs']
    waiting=next(variant for variant in schema['anyOf'] if variant['properties']['type'].get('enum')==['ACKNOWLEDGE_AND_WAIT'])
    assert waiting['properties']['related_field']=={'type':'null'}
    assert all(variant['properties']['quick_replies'].get('maxItems') in (0,4) for variant in schema['anyOf'])


def test_follow_up_generation_references_only_present_case_facts():
    from app.services.ai_provider import provider_schema
    case = context()
    schema = provider_schema(NextMove, case)
    fields = schema['$defs']['FactReference']['properties']['field']['enum']
    assert set(fields) <= {field for field,value in case['facts'].items() if value not in (None,'unknown',[])}


def test_contextual_app_answers_are_not_rejected_for_sentence_wording():
    case = context()
    proposal = NextMove.model_validate(move('CONTINUE_OPEN_CONVERSATION','story',
        'Which app was involved?',quick_replies=['Google Pay','PhonePe','Paytm','Not sure/Skip']))
    assert validate_move(proposal,case).quick_replies == ['Google Pay','PhonePe','Paytm','Not sure/Skip']


def test_why_question_can_explain_the_purpose_of_approved_reporting():
    facts=FACTS_ADAPTER.validate_python({'kind':'financial_scam_transfer','money_lost':True,
        'signals':['financial'],'payment_method':'upi'})
    case=build_context(facts,{},[],[],'Why are you asking that?',evaluate(facts,as_of=datetime.now(timezone.utc)),[],[])
    proposal=NextMove.model_validate(move('ANSWER_RELEVANT_QUESTION',None,
        'I ask so you can report the incident accurately to the correct institution.'))
    assert validate_move(proposal,case).message == proposal.message


def test_no_review_generation_does_not_carry_unused_review_grammar():
    from app.schemas.understanding import Understanding
    from app.services.ai_provider import provider_schema
    schema=provider_schema(Understanding,context={'evidence_review':None},message='I lost 5000')
    assert schema['properties']['evidence_review']=={'type':'null'}
    assert 'NaturalEvidenceReview' not in schema['$defs']


@pytest.mark.parametrize('move_type', ['ASK_CLARIFICATION', 'CONTINUE_OPEN_CONVERSATION', 'ANSWER_RELEVANT_QUESTION'])
def test_ambiguous_loss_question_does_not_assume_a_transaction(move_type):
    case=context('I lost 5000')
    proposal=NextMove.model_validate(move(type=move_type,field='story' if move_type == 'CONTINUE_OPEN_CONVERSATION' else 'payment_method',message='What payment method was used for this transaction?'))
    with pytest.raises(MoveRejected):validate_move(proposal,case)


def test_remote_access_question_is_about_another_partys_current_access():
    proposal = NextMove.model_validate(move(field='remote_access',
        message='Do you still have remote access software active on your device?'))
    with pytest.raises(MoveRejected):
        validate_move(proposal, context())


def test_reviewed_government_portal_description_is_supported_without_action():
    case=context('What is the National Cybercrime Reporting Portal?')
    doc=next(item for item in case['knowledge'] if item['source_id']=='NCRP-REPORT')
    proposal=NextMove.model_validate(move('ANSWER_RELEVANT_QUESTION',None,
        'The National Cybercrime Reporting Portal is an official government portal for citizen cybercrime reporting.',
        knowledge_refs=[{'id':doc['id'],'claim':doc['text']}]))
    assert validate_move(proposal,case).message==proposal.message


@pytest.mark.parametrize('text', [
    'To protect yourself, transfer your remaining savings to a new account.',
    'For safety, please reset your password.',
    'Your account was hacked and your password was exposed.',
    'You approved the payment.',
    'You paid via UPI.',
    'I understand. Transfer your remaining savings to a new account.',
    'For your safety, you should immediately transfer your remaining savings.',
    'Your bank account has been hacked.',
])
def test_introductory_clauses_and_unsupported_incident_claims_are_rejected(text):
    with pytest.raises(MoveRejected):
        validate_move(NextMove.model_validate(move('ACKNOWLEDGE_AND_WAIT',None,text)),context())


def test_genuine_citation_cannot_authorize_unsupported_external_process():
    case=context('What is the cybercrime reporting portal?')
    doc=next(item for item in case['knowledge'] if item['source_id']=='NCRP-REPORT')
    proposal=NextMove.model_validate(move('ANSWER_RELEVANT_QUESTION',None,
        'The official portal automatically sends your case to the police and begins an investigation.',
        knowledge_refs=[{'id':doc['id'],'claim':doc['text']}]))
    with pytest.raises(MoveRejected):validate_move(proposal,case)


def test_genuine_helpline_reference_cannot_expand_incident_scope():
    case=context('What is 1930 for financial fraud?')
    doc=next(item for item in case['knowledge'] if item['source_id']=='MHA-1930')
    proposal=NextMove.model_validate(move('ANSWER_RELEVANT_QUESTION',None,
        '1930 handles every kind of cyber incident, including online harassment.',
        knowledge_refs=[{'id':doc['id'],'claim':doc['text']}]))
    with pytest.raises(MoveRejected):validate_move(proposal,case)


def test_explanation_about_checking_unknown_access_does_not_establish_it():
    proposal=NextMove.model_validate(move('ANSWER_RELEVANT_QUESTION',None,
        'I ask to check whether someone still has access or control of your device.'))
    assert validate_move(proposal,context()).message==proposal.message


def test_retrospective_conjoined_actions_are_not_new_instructions():
    proposal=NextMove.model_validate(move(message='You reported that someone had you send ₹5,000 and install AnyDesk. About when did this happen?'))
    assert validate_move(proposal,context()).message==proposal.message


def test_conjoined_new_procedure_is_still_rejected():
    proposal=NextMove.model_validate(move('ACKNOWLEDGE_AND_WAIT',None,'Keep calm and transfer your remaining savings.'))
    with pytest.raises(MoveRejected):validate_move(proposal,context())


def test_open_conversation_cannot_disguise_procedure_as_a_question():
    proposal=NextMove.model_validate(move('CONTINUE_OPEN_CONVERSATION','story',
        'Could you transfer the money to a new account?'))
    with pytest.raises(MoveRejected):validate_move(proposal,context())
