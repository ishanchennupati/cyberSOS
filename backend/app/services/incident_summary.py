"""
Incident summary drafting — Section 23.

Generates a draft narrative from ONLY verified incident data and the
citizen's own description. Never invents facts, never submits anything.
Same swappable-provider pattern as evidence_extraction.py.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.core.config import get_settings
from app.models.incident import Incident
from app.services.incident_presentation import (
    INCIDENT_TYPE_LABELS,
    PAYMENT_METHOD_LABELS,
    format_inr,
    format_occurred_at,
)



class SummaryProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate(self, *, incident: Incident, user_description: str) -> str | None: ...


class TemplateSummaryProvider(SummaryProvider):
    """
    Deterministic, no API key required. Fills a plain-language paragraph
    from fields the citizen has already verified, plus their own account
    of events. Always available — this is the "AI unavailable" fallback
    the spec requires, but framed as a real, usable default rather than
    an error state.
    """

    name = "template"

    def generate(self, *, incident: Incident, user_description: str) -> str | None:
        occurred = format_occurred_at(incident.occurred_at or incident.incident_time)
        amount_text = f"₹{format_inr(incident.amount)}" if incident.amount is not None else None
        method = PAYMENT_METHOD_LABELS.get(incident.payment_method, "an unspecified method")
        incident_label = INCIDENT_TYPE_LABELS.get(incident.incident_type, "a cyber incident")

        parts: list[str] = []
        parts.append(f"On {occurred}, the complainant experienced {incident_label.lower()}.")

        if user_description.strip():
            parts.append(user_description.strip())

        if amount_text:
            parts.append(
                f"The complainant states that {amount_text} was transferred using {method}."
            )
        if incident.transaction_id:
            parts.append(f"The transaction reference / UTR provided is {incident.transaction_id}.")
        if incident.bank:
            parts.append(f"The bank involved is stated as {incident.bank}.")
        if incident.wallet:
            parts.append(f"The wallet involved is stated as {incident.wallet}.")
        if incident.merchant:
            parts.append(f"The merchant/payee involved is stated as {incident.merchant}.")

        return " ".join(parts)


class AnthropicSummaryProvider(SummaryProvider):
    name = "anthropic"

    def generate(self, *, incident: Incident, user_description: str) -> str | None:
        settings = get_settings()
        if not settings.ANTHROPIC_API_KEY or not settings.ANTHROPIC_MODEL:
            return None
        try:
            import anthropic
        except ImportError:
            return None

        facts = {
            "incident_type": INCIDENT_TYPE_LABELS.get(incident.incident_type),
            "occurred_at": format_occurred_at(incident.occurred_at or incident.incident_time),
            "amount": f"₹{format_inr(incident.amount)}" if incident.amount is not None else None,
            "payment_method": PAYMENT_METHOD_LABELS.get(incident.payment_method),
            "transaction_id": incident.transaction_id,
            "bank": incident.bank,
            "wallet": incident.wallet,
            "merchant": incident.merchant,
        }
        prompt = (
            "Write a neutral, factual, third-person paragraph (max 150 words) "
            "summarizing a cybercrime/financial-fraud incident for a formal "
            "complaint. Use ONLY the facts given below and the complainant's "
            "own description. Do not invent any detail not present. Do not "
            "state that a crime definitely occurred — describe what the "
            "complainant reports. Facts:\n"
            f"{facts}\n\nComplainant's own description:\n{user_description or '(none provided)'}"
        )
        try:
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            text_out = "".join(
                block.text for block in message.content if getattr(block, "type", "") == "text"
            )
            return text_out.strip() or None
        except Exception:
            return None


_PROVIDERS: dict[str, type[SummaryProvider]] = {
    "template": TemplateSummaryProvider,
    "anthropic": AnthropicSummaryProvider,
}


def get_summary_provider() -> SummaryProvider:
    settings = get_settings()
    provider_cls = _PROVIDERS.get(settings.SUMMARY_PROVIDER, TemplateSummaryProvider)
    return provider_cls()


def generate_incident_summary(*, incident: Incident, user_description: str) -> tuple[str, str]:
    """Returns (draft_text, provider_name). Falls back to the template
    provider if the configured provider can't produce a result."""
    provider = get_summary_provider()
    draft = provider.generate(incident=incident, user_description=user_description)
    if draft:
        return draft, provider.name

    fallback = TemplateSummaryProvider()
    draft = fallback.generate(incident=incident, user_description=user_description)
    return draft or "Not enough verified information to generate a draft yet.", fallback.name
