"""Derived case-only context. No global cache, provider calls or fact mutation."""
import re

STOP = frozenset('the a an is are was were i you me my to of and or what did do have it this that about can how with'.split())


def terms(text):
    return set(re.findall(r'[\w]+', text.casefold())) - STOP


def exchange(turn):
    changes = turn.fact_changes or {}
    pending = getattr(turn, 'pending_question', None)
    if hasattr(pending, 'model_dump'): pending = pending.model_dump(mode='json')
    return {'source_turn': str(turn.id), 'revision': turn.revision,
        'user': turn.text[:800],
        'assistant': ' '.join(filter(None, [changes.get('acknowledgement', ''),
            (changes.get('next_move') or {}).get('message', ''),
            (pending or {}).get('question', '') if not changes.get('next_move') else '']))[:900]}


def recall(turns, message, budget=6000):
    """Recent exchanges plus relevant older history, bounded by serialized characters."""
    query = terms(message)
    recent, older = list(turns[-6:]), list(turns[:-6])
    ranked = sorted(older, key=lambda t: (len(query & terms(t.text)), t.revision), reverse=True)
    selected = []
    for turn in ranked:
        if not query & terms(turn.text):
            continue
        item = exchange(turn)
        size = len(str(item))
        if size <= budget:
            selected.append(item)
            budget -= size
        if len(selected) == 4:
            break
    return {'recent': [exchange(t) for t in recent],
        'older': sorted(selected, key=lambda item: item['revision'])}


def derive_memory(facts, turns, conflicts, message=''):
    """Rebuild from canonical truth at each revision; history is recall, not evidence."""
    values = facts.model_dump(mode='json')
    provenance = {p.field: p for p in facts.provenance}
    summary = {}
    for field, value in values.items():
        if field in {'provenance', 'fact_schema_version', 'kind', 'detected_language'} or value in (None, 'unknown', []):
            continue
        origin = provenance.get(field)
        summary[field] = {'value': value, 'source_turn': str(origin.source_turn) if origin and origin.source_turn else None,
            'origin': origin.origin if origin else 'canonical', 'verified': bool(origin and origin.verified)}
    declined, explanations = set(), set()
    paused = False
    for turn in turns:
        changes = turn.fact_changes
        intents = changes.get('understanding', {}).get('intents', [])
        if 'pause' in intents: paused = True
        if 'resume' in intents: paused = False
        if changes.get('answered_unknown'):
            declined.add(changes['answered_unknown'])
        for update in changes.get('updates', []):
            declined.discard(update['field'])
            if update['field'] in {'occurred_at','time_window'}: declined.difference_update({'occurred_at','time_window'})
        move = changes.get('next_move') or {}
        if move.get('action_id'):
            explanations.add(move['action_id'])
    recalled = recall(turns, message)
    return {'revision': turns[-1].revision if turns else 0, 'facts': summary,
        'open_issues': list(conflicts), 'declined_fields': sorted(declined),
        'explained_actions': sorted(explanations), 'older_recall': recalled['older'], 'questions_paused': paused,
        'authority': 'derived; canonical facts supersede all historical claims'}
