"""Small replaceable lexical retrieval over reviewed claims, never citizen uploads."""
from math import log
from datetime import date
from app.domain.sources import SOURCES
from app.services.case_memory import terms


def collection():
    return [{'id': source.id + ':1', 'source_id': source.id, 'version': '1',
        'jurisdiction': 'IN', 'reviewed_on': source.reviewed_on.isoformat(),
        'review_due': '2027-01-01', 'withdrawn': False,
        'title': source.display_name, 'authority':source.authority, 'url': source.official_url,
        'text': ' '.join(source.supported_guidance)} for source in SOURCES.values()]


def retrieve(query, *, documents=None, limit=3):
    """Rank supporting documents by inverse-document-frequency token overlap.

    Supplied adapter documents must match the reviewed registry snapshot exactly.
    This trust check prevents a poisoned index from expanding reviewed claims.
    """
    query_terms = terms(query)
    trusted = {item['id']: item for item in collection()}
    candidates = []
    for item in collection() if documents is None else documents:
        reference = trusted.get(item.get('id'))
        if not reference or item != reference or item['withdrawn'] or date.fromisoformat(item['review_due']) < date.today():
            continue
        candidates.append(item)
    tokens = [terms(item['title'] + ' ' + item['text']) for item in candidates]
    ranked = []
    for item, token_set in zip(candidates, tokens):
        overlap = query_terms & token_set
        score = sum(log(1 + len(candidates) / sum(token in other for other in tokens)) for token in overlap)
        if score >= 1:
            ranked.append((score, item))
    return [dict(item) for _, item in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:limit]]


def relevant_knowledge(message):
    # Retrieval is useful for external questions; never establishes case facts.
    if '?' not in message and not terms(message) & {'explain', 'meaning', 'portal', 'helpline', '1930'}:
        return []
    return retrieve(message)
