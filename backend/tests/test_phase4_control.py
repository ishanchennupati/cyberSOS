import json
from tests.test_phase3r_case_agent import install, move, send


def test_mixed_skip_and_question_is_remembered_without_fact_defaults(client, monkeypatch):
    provider = install(monkeypatch, [], move(field='remote_access', message='Can someone else still access your device?'))
    state,_,_ = send(client,'I installed AnyDesk.')
    provider.output=json.dumps({'language':'en','candidates':[], 'intents':['skip'], 'intent_source':'skip that question'})
    provider.next_move=json.dumps(move('ANSWER_RELEVANT_QUESTION',None,'We can leave that detail unknown. The question helps understand current access.'))
    state,_,_=send(client,'Please skip that question, and why do you need it?',state)
    assert state['turns'][-1]['fact_changes']['understanding']['status']=='understood'
    assert 'remote_access' in state['memory']['declined_fields']
    assert state['facts']['remote_access'] is None
    assert state['next_move']['type']=='ANSWER_RELEVANT_QUESTION'


def test_unrelated_and_feedback_messages_cannot_mutate_facts(client,monkeypatch):
    provider=install(monkeypatch,[],move('ACKNOWLEDGE_AND_WAIT',None,'I can help with your cyber incident here.'))
    provider.output=json.dumps({'language':'en','candidates':[], 'intents':['unrelated'], 'intent_source':'birthday poem'})
    state,_,_=send(client,'Write a birthday poem about losing 5000.')
    assert state['facts']['amount'] is None
    assert state['turns'][-1]['fact_changes']['understanding']['status']=='understood'


def test_natural_skip_survives_reasoning_failure(client,monkeypatch):
    provider=install(monkeypatch,[],move(field='remote_access',message='Can someone else still access your device?'))
    state,_,_=send(client,'I installed AnyDesk.')
    provider.output=json.dumps({'language':'en','candidates':[],'intents':['skip'],'intent_source':'skip that question'})
    provider.next_move='malformed'
    state,_,_=send(client,'Please skip that question.',state)
    assert state['pending_question'] is None or state['pending_question']['field']!='remote_access'


def test_pause_persists_through_reload_and_failed_reasoning(client,monkeypatch):
    provider=install(monkeypatch,[],move(field='remote_access',message='Can someone else still access your device?'))
    state,case,_=send(client,'I installed AnyDesk.')
    provider.output=json.dumps({'language':'en','candidates':[],'intents':['pause'],'intent_source':'pause questions'})
    provider.next_move='malformed'
    state,_,_=send(client,'Please pause questions.',state)
    assert state['pending_question'] is None
    assert client.get(f'/api/v1/incidents/{state["incident_id"]}/conversation').json()['memory']['questions_paused'] is True
    provider.output=json.dumps({'language':'en','candidates':[]})
    state,_,_=send(client,'Thanks.',state)
    assert state['pending_question'] is None


def test_skipping_approximate_time_suppresses_exact_time_fallback(client,monkeypatch):
    provider=install(monkeypatch,[],move(field='time_window',message='About when did this happen?'))
    state,_,_=send(client,'A synthetic incident happened.')
    provider.output=json.dumps({'language':'en','candidates':[],'intents':['skip'],'intent_source':'skip the time'})
    provider.next_move='malformed'
    state,_,_=send(client,'Please skip the time question.',state)
    assert state['pending_question'] is None or state['pending_question']['field']!='occurred_at'
