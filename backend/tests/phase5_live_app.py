"""Synthetic opt-in diagnostic delegates every AI call to the real provider."""
import json
import os
from pathlib import Path
from app.main import app
from app.services import understanding, case_agent

if os.environ.get('SMOKE_LIVE_AI') != '1':
    raise RuntimeError('Synthetic live opt-in required')
original = understanding.get_provider


class DiagnosticProvider:
    def __init__(self, provider):
        self.provider = provider

    async def extract(self, message, context):
        output = await self.provider.extract(message, context)
        self.save('understanding', output)
        return output

    async def decide(self, context):
        output = await self.provider.decide(context)
        self.save('follow-up', output)
        return output

    def save(self, stage, output):
        root = Path(__file__).parents[1] / 'tmp'
        root.mkdir(exist_ok=True)
        (root/f'phase5-last-{stage}.json').write_text(output, encoding='utf-8')


def get_provider():
    provider = original()
    return DiagnosticProvider(provider) if provider else None


understanding.get_provider = case_agent.get_provider = get_provider
