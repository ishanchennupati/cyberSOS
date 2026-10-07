"""Read-only implementation diagnosis, fake AI and synthetic disposable cases."""
import json
from tests.test_phase3r_case_agent import install, move, send
from tests.test_phase3_understanding import candidate
from app.services import case_agent
from app.services.ai_provider import FakeProvider


def test_fallback_repetition_and_plan_request_probe(client, monkeypatch):
    messages=[
        'Someone harassed me on Instagram.',
        'Why are you asking about money? I need help with the harassment.',
        'Enough questions. Tell me what to do now.',
        'Please summarize and conclude with the steps I can take.',
    ]
    state=None
    for index,text in enumerate(messages):
        candidates=[candidate('signals',['harassment'],'harassed'),candidate('platform','Instagram','Instagram')] if index==0 else []
        provider=install(monkeypatch,candidates,move('ACKNOWLEDGE_AND_WAIT',None,'Ready when you are.'))
        if index:
            provider.output=json.dumps({'language':'en','candidates':[], 'intents':['question'],'intent_source':text})
        monkeypatch.setattr(case_agent,'get_provider',lambda:FakeProvider(error=TimeoutError()))
        state,_,_=send(client,text,state)
        print('QUALITY_PROBE',json.dumps({'user':text,'pending':state['pending_question'],
            'reply':state['turns'][-1]['fact_changes'].get('acknowledgement'),
            'actions':[a['id'] for a in state['plan']['plan']['actions']],
            'paused':state['memory']['questions_paused']}))
    assert state['facts']['platform']=='Instagram'


def test_explicit_pause_when_understanding_fails_probe(client,monkeypatch):
    install(monkeypatch,[candidate('signals',['harassment'],'harassed')],move('ACKNOWLEDGE_AND_WAIT',None,'Ready when you are.'))
    state,_,_=send(client,'I was harassed online.')
    from app.services import understanding
    monkeypatch.setattr(understanding,'get_provider',lambda:FakeProvider(error=TimeoutError()))
    state,_,_=send(client,'Stop asking questions. Give me the plan.',state)
    print('PAUSE_PROBE',json.dumps({'pending':state['pending_question'],'paused':state['memory']['questions_paused'],
        'ack':state['turns'][-1]['fact_changes']['acknowledgement']}))
    assert state['turns'][-1]['fact_changes']['understanding']['status']=='fallback'
