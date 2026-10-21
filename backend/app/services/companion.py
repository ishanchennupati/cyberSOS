"""Case presentation/control derived from durable turns, never fact approval."""
import re


def has_case_context(facts):
    """Reject empty greetings without making classification a presentation gate."""
    values = facts.model_dump(mode='json') if hasattr(facts, 'model_dump') else facts
    return bool(values.get('signals') or values.get('threat_text') or values.get('message_text') or
        values.get('account_compromised') is True or values.get('remote_access') is True or
        values.get('money_lost') is True and (values.get('transaction_id') or values.get('bank_involved') is True or
            values.get('payment_method') not in (None,'unknown')))


def state(turns):
    presented_at = None
    offer = None
    for turn in turns:
        changes = turn.fact_changes
        if changes.get('companion_presented') and presented_at is None:
            presented_at = turn.revision
        if changes.get('evidence_offer'):
            offer = changes['evidence_offer']
        elif offer == 'offered':
            move = changes.get('next_move') or {}
            if '?' in move.get('message', '') or turn.pending_question:
                offer = None
    return {'presented': presented_at is not None, 'presented_revision': presented_at,
            'evidence_offer': offer}


def consent(snapshot, text):
    """Only bind a short answer to an actual active optional evidence offer."""
    current = state(snapshot.turns)
    if current['evidence_offer'] != 'offered':
        return None
    value = re.sub(r'[.!]+$', '', text.strip().casefold())
    if value in {'yes', 'yes please', 'sure', 'okay', 'ok', 'i would like to', 'please do'}:
        return 'accepted'
    if value in {'no', 'no thanks', 'skip', 'skip for now', 'cancel', 'not now'}:
        return 'declined'
    return None
