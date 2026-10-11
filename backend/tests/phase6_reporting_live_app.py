"""Synthetic browser acceptance: fake intake, independently live narrative stage."""
import json
import os
from pathlib import Path
from uuid import uuid4
from tests.phase6_reporting_smoke_app import app
from app.services import ai_provider, reporting_narrative

if os.environ.get('SMOKE_LIVE_AI') != '1':
    raise RuntimeError('Explicit synthetic live drafting opt-in required')


class LiveDraftProvider:
    name = 'gemini'

    async def draft(self, encoded):
        provider = ai_provider.get_provider()
        if provider is None:
            raise RuntimeError('Configured live provider unavailable')
        output = await provider.draft(encoded)
        root = Path(__file__).parents[1] / 'tmp' / 'phase6-live-drafts'
        root.mkdir(parents=True, exist_ok=True)
        (root / f'{uuid4()}.json').write_text(json.dumps(
            {'synthetic_packet':json.loads(encoded), 'proposal':json.loads(output)},
            ensure_ascii=False), encoding='utf-8')
        return output


reporting_narrative.get_provider = lambda: LiveDraftProvider()
