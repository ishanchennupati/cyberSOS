from datetime import datetime, timezone

from app.domain.facts import FACTS_ADAPTER
from app.domain.playbooks import evaluate

NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)


def plan(**values):
    return evaluate(FACTS_ADAPTER.validate_python({'kind': 'incident_understanding', **values}), as_of=NOW)


def test_ambiguous_loss_does_not_authorize_banking_or_fraud_reporting():
    result = plan(amount='5000', money_lost=True)
    assert not {a.id for a in result.actions} & {'call_1930', 'contact_bank_unknown', 'contact_bank_scam'}
    assert result.urgency.value not in {'HIGH', 'CRITICAL'}


def test_unknown_timing_is_not_urgent_and_unknown_authorization_is_not_citizen_uncertainty():
    result = plan(money_lost=True, signals=['financial'], payment_method='upi')
    assert result.urgency.value not in {'HIGH', 'CRITICAL'}
    assert all('you are unsure' not in a.instruction for a in result.actions)


def test_harassment_has_safe_records_and_platform_reporting_without_bank_actions():
    result = plan(signals=['harassment'], platform='Instagram')
    ids = {a.id for a in result.actions}
    assert 'report_platform_abuse' in ids
    assert 'preserve_evidence' in ids
    assert not any('bank' in a.id or a.id == 'call_1930' for a in result.actions)
    assert all(a.priority.value != 'CRITICAL' for a in result.actions)


def test_physical_danger_authorizes_emergency_handoff_only_when_affirmative():
    assert 'contact_112' not in {a.id for a in plan(signals=['threats']).actions}
    result = plan(signals=['threats'], immediate_danger=True)
    action = next(a for a in result.actions if a.id == 'contact_112')
    assert action.phone == '112' and action.official_source_id == 'INDIA-EMERGENCY'


def test_google_takeover_reuses_shared_policy_and_requires_current_access_fact():
    result = plan(signals=['account_takeover'], platform='Google', account_compromised=True)
    assert 'secure_google_account' in {a.id for a in result.actions}
    assert 'secure_google_account' not in {a.id for a in plan(signals=['account_takeover'], platform='Google').actions}


def test_financial_plus_harassment_keeps_both_action_sets():
    result = plan(kind='financial_scam_transfer', money_lost=True, payment_method='upi',
                  signals=['financial', 'harassment'], platform='Instagram')
    assert {'contact_bank_scam', 'call_1930', 'report_platform_abuse'} <= {a.id for a in result.actions}


def test_authorized_wallet_payment_does_not_prove_bank_involvement():
    result = plan(kind='financial_scam_transfer', money_lost=True, signals=['financial'], payment_method='wallet')
    assert not any(a.id.startswith('contact_bank') for a in result.actions)


def test_impersonation_does_not_prove_a_social_platform_was_involved():
    assert 'report_platform_abuse' not in {a.id for a in plan(signals=['impersonation']).actions}
    assert 'report_platform_abuse' not in {a.id for a in plan(signals=['account_takeover','impersonation'],platform='Google').actions}


def test_old_conversation_plan_refreshes_policy_without_rewriting_history(client,db):
    from app.models.response import ResponsePlanRecord
    from sqlalchemy import select
    from tests.test_phase4_durability import create
    case=create(client)
    path=f'/api/v1/incidents/{case}/conversation'
    state=client.get(path).json()
    row=db.scalar(select(ResponsePlanRecord).where(ResponsePlanRecord.incident_id==__import__('uuid').UUID(case)))
    old=dict(row.plan)
    old['playbook_version']='1.1.0'
    row.plan=old
    db.commit()
    next_state=client.get(path).json()
    assert next_state['plan']['plan']['playbook_version']=='1.2.0'
    assert next_state['revision']==state['revision']+1
    db.refresh(row)
    assert row.plan['playbook_version']=='1.1.0'
    assert len(client.get(path.removesuffix('/conversation')+'/plans').json())==2
