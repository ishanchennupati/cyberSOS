"""Opt-in synthetic browser diagnostic; never imported by the application."""
import json
import os
from pathlib import Path
from app.main import app
from app.services import case_agent

if os.environ.get('SMOKE_LIVE_AI') != '1':
    raise RuntimeError('Synthetic live harness opt-in required')

original = case_agent.get_provider


class DiagnosticProvider:
    def __init__(self, provider): self.provider = provider

    async def decide(self, context):
        output = await self.provider.decide(context)
        target = Path(__file__).parents[1] / 'tmp/phase4-last-proposal.json'
        target.parent.mkdir(exist_ok=True)
        target.write_text(output, encoding='utf-8')
        return output


def get_provider():
    provider = original()
    return DiagnosticProvider(provider) if provider else None


case_agent.get_provider = get_provider
