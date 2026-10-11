"""Opt-in synthetic-only proposal capture; never imported by production."""
import json
import os
from pathlib import Path
from uuid import uuid4
from app.main import app
from app.services import understanding, case_agent

if os.environ.get('SMOKE_LIVE_AI') != '1':
    raise RuntimeError('Explicit synthetic live opt-in required')
original = understanding.get_provider


class DiagnosticProvider:
    def __init__(self, provider): self.provider = provider

    async def extract(self, message, context):
        output = await self.provider.extract(message, context)
        self.save('understanding', message, output)
        return output

    async def decide(self, context):
        output = await self.provider.decide(context)
        self.save('follow-up', json.loads(context)['current_message'], output)
        return output

    def save(self, stage, message, output):
        root = Path(__file__).parents[1] / 'tmp' / 'phase6-proposals'
        root.mkdir(parents=True, exist_ok=True)
        (root/f'{uuid4()}-{stage}.json').write_text(json.dumps(
            {'synthetic_message':message,'stage':stage,'output':output},ensure_ascii=False),encoding='utf-8')


def provider():
    value = original()
    return DiagnosticProvider(value) if value else None


understanding.get_provider = case_agent.get_provider = provider
