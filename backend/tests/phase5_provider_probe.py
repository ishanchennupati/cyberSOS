"""Opt-in free-tier synthetic extraction probe. No DB or original mutation."""
import json
import os
from pathlib import Path
from time import perf_counter
from app.core.config import get_settings
from app.services.evidence_intelligence import analyze_bytes
from tests.phase5_fixtures import image_bytes


def main():
    if os.environ.get('PHASE5_LIVE') != '1':
        raise SystemExit('Explicit synthetic live opt-in required')
    settings = get_settings()
    print(json.dumps(dict(provider=settings.UNDERSTANDING_PROVIDER, model=settings.UNDERSTANDING_MODEL,
        key_configured=bool(settings.GEMINI_API_KEY))), flush=True)
    started = perf_counter()
    try:
        result = analyze_bytes(image_bytes(), 'image/png')
        record = dict(status='analyzed', duration_ms=round((perf_counter()-started)*1000),
            result=result.model_dump(mode='json'))
    except Exception as exc:
        from app.services.case_agent import failure_category
        record = dict(status='failed', category=failure_category(exc), error_type=type(exc).__name__,
            http_status=getattr(exc,'code',None), duration_ms=round((perf_counter()-started)*1000))
    target = Path(__file__).parents[1] / 'tmp/phase5-probe.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=True), flush=True)
    return 0 if record['status'] == 'analyzed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
