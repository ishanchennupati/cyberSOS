"""Synthetic regression for natural payment names and the verification loop."""
import json
import pytest
from tests.test_phase3_understanding import candidate
from tests.test_phase3r_case_agent import install, move, send


@pytest.mark.parametrize('wording,canonical', [
    ('net banking', 'net_banking'), ('Internet banking', 'net_banking'),
    ('UPI', 'upi'), ('bank transfer', 'bank_transfer'), ('debit card', 'debit_card'),
])
def test_explicit_payment_names_normalize_before_merge(client, monkeypatch, wording, canonical):
    install(monkeypatch, [candidate('money_lost', True, 'sent'),
        candidate('payment_method', wording, wording)], move())
    state, _, _ = send(client, 'I sent money using ' + wording + '.')
    assert state['facts']['payment_method'] == canonical
    assert state['turns'][-1]['fact_changes']['understanding']['candidates'][1]['value'] == canonical


def uncertain_rail(client, monkeypatch, *, quick_replies=None):
    rail = candidate('payment_method', 'net banking', 'net banking')
    rail.update(extraction='inference', uncertainty='Citizen is unsure')
    install(monkeypatch, [candidate('money_lost', True, 'sent'), rail],
        move('VERIFY_INFORMATION', 'payment_method', 'Was it net banking?',
            quick_replies=quick_replies or []))
    state, _, _ = send(client, 'I sent money. I think it was net banking.')
    return state


def test_grounded_verification_wording_and_yes_no_replies_are_kept(client, monkeypatch):
    state = uncertain_rail(client, monkeypatch, quick_replies=['Yes', 'No', 'Not sure'])
    assert state['next_move']['message'] == 'Was it net banking?'
    assert state['next_move']['quick_replies'] == ['Yes', 'No', 'Not sure']
    assert state['facts']['payment_method'] == 'unknown'


@pytest.mark.parametrize('answer', ['Yes', 'That is right, that was how I paid.'])
def test_natural_confirmation_settles_only_active_payment_candidate(client, monkeypatch, answer):
    state = uncertain_rail(client, monkeypatch)
    confirmed = candidate('payment_method', 'net banking', answer, confirms_pending=True)
    provider = install(monkeypatch, [confirmed], move())
    state, path, payload = send(client, answer, state)
    assert state['facts']['payment_method'] == 'net_banking'
    assert not state['turns'][-1]['fact_changes']['unresolved_candidates']
    provenance = next(p for p in state['facts']['provenance'] if p['field'] == 'payment_method')
    assert provenance['origin'] == 'user_verification' and provenance['verified']
    assert provenance['source_text'] == answer
    assert len(state['turns']) == 2
    assert state['turns'][0]['text'] == 'I sent money. I think it was net banking.'
    assert client.post(path + '/turns', json=payload).json() == state
    assert len(provider.decision_contexts) == 1
    install(monkeypatch, [], move('ACKNOWLEDGE_AND_WAIT', None, 'Ready when you are.'))
    state, _, _ = send(client, 'Thanks, I need a moment.', state)
    assert state['next_move']['type'] == 'ACKNOWLEDGE_AND_WAIT'
    assert not state['turns'][-1]['fact_changes']['unresolved_candidates']


def test_confirmation_cannot_invent_a_rail_without_active_verification(client, monkeypatch):
    install(monkeypatch, [candidate('payment_method', 'net banking', 'Yes', confirms_pending=True)], move())
    state, _, _ = send(client, 'Yes')
    assert state['facts']['payment_method'] == 'unknown'


def test_denial_does_not_promote_the_pending_candidate(client, monkeypatch):
    state = uncertain_rail(client, monkeypatch)
    denial = 'No, that is not what I used.'
    install(monkeypatch, [candidate('payment_method', 'net_banking', denial, confirms_pending=False)],
        move('CONTINUE_OPEN_CONVERSATION', 'story', 'What else happened?'))
    state, _, _ = send(client, denial, state)
    assert state['facts']['payment_method'] == 'unknown'
    assert not state['turns'][-1]['fact_changes']['unresolved_candidates']
    install(monkeypatch, [], move('ACKNOWLEDGE_AND_WAIT', None, 'Ready when you are.'))
    state, _, _ = send(client, 'I need a moment.', state)
    assert not state['turns'][-1]['fact_changes']['unresolved_candidates']


def test_confirmation_cannot_replace_target_with_another_rail(client, monkeypatch):
    state = uncertain_rail(client, monkeypatch)
    install(monkeypatch, [candidate('payment_method', 'upi', 'Yes', confirms_pending=True)], move())
    state, _, _ = send(client, 'Yes', state)
    assert state['facts']['payment_method'] == 'unknown'


def test_uncertain_confirmation_remains_unknown(client, monkeypatch):
    state = uncertain_rail(client, monkeypatch)
    unsure = candidate('payment_method', 'net banking', 'I am not sure', confirms_pending=True)
    unsure.update(extraction='inference', uncertainty='Citizen unsure')
    install(monkeypatch, [unsure], move())
    state, _, _ = send(client, 'I am not sure', state)
    assert state['facts']['payment_method'] == 'unknown'


def test_yes_no_is_not_allowed_for_vague_rail_verification(client, monkeypatch):
    rail = candidate('payment_method', 'net_banking', 'net banking')
    rail.update(extraction='inference', uncertainty='Citizen unsure')
    install(monkeypatch, [rail], move('VERIFY_INFORMATION', 'payment_method',
        'Was the payment method correct?', quick_replies=['Yes', 'No']))
    state, _, _ = send(client, 'I think it was net banking.')
    assert state['next_move'] is None
    assert state['turns'][-1]['fact_changes']['agent']['rejection_reason'] == 'VERIFICATION_TARGET_MISMATCH'


@pytest.mark.parametrize('question', ['Was it UPI?', 'Was it net banking or UPI?', 'Was the payment method correct?'])
def test_payment_verification_must_name_only_active_target_without_buttons(client, monkeypatch, question):
    rail = candidate('payment_method', 'net banking', 'net banking')
    rail.update(extraction='inference', uncertainty='Citizen unsure')
    install(monkeypatch, [rail], move('VERIFY_INFORMATION', 'payment_method', question))
    state, _, _ = send(client, 'I think it was net banking.')
    assert state['next_move'] is None
    assert state['turns'][-1]['fact_changes']['agent']['rejection_reason'] == 'VERIFICATION_TARGET_MISMATCH'


def test_supported_payment_alias_can_be_verified(client, monkeypatch):
    rail = candidate('payment_method', 'net banking', 'net banking')
    rail.update(extraction='inference', uncertainty='Citizen unsure')
    install(monkeypatch, [rail], move('VERIFY_INFORMATION', 'payment_method',
        'Was it internet banking?', quick_replies=['Yes', 'No']))
    state, _, _ = send(client, 'I think it was net banking.')
    assert state['next_move']['message'] == 'Was it internet banking?'
    install(monkeypatch, [candidate('payment_method', 'net_banking', 'Yes', confirms_pending=True)], move())
    state, _, _ = send(client, 'Yes', state)
    assert state['facts']['payment_method'] == 'net_banking'


def test_unknown_rail_cannot_be_verified_as_a_supported_method(client, monkeypatch):
    rail = candidate('payment_method', 'GPay', 'GPay')
    rail.update(extraction='inference', uncertainty='App does not establish rail')
    install(monkeypatch, [rail], move('VERIFY_INFORMATION', 'payment_method', 'Was the payment through GPay?',
        quick_replies=['Yes', 'No']))
    state, _, _ = send(client, 'I used GPay.')
    assert state['next_move'] is None
    assert state['facts']['payment_method'] == 'unknown'
    assert not state['turns'][-1]['fact_changes']['unresolved_candidates']


def test_provider_payment_grammar_uses_canonical_domain_values():
    from app.services.ai_provider import provider_schema
    from app.schemas.understanding import Understanding
    from app.models.incident import PaymentMethod
    variants = provider_schema(Understanding)['$defs']['Candidate']['anyOf']
    rail = next(v for v in variants if v['properties']['field']['enum'] == ['payment_method'])
    assert set(rail['properties']['value']['enum']) == {p.value for p in PaymentMethod}
