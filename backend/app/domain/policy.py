"""Evidence policy foundation, not OCR/content moderation or an extraction phase."""
from enum import Enum
import re
from pydantic import BaseModel, ConfigDict


class EvidenceContentKind(str, Enum):
    general_document = "general_document"
    credentials = "credentials"
    explicit_intimate_media = "explicit_intimate_media"
    child_sexual_abuse_material = "child_sexual_abuse_material"
    identity_document = "identity_document"


class EvidencePolicy(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str = "financial-safe-evidence-1"
    prohibited: tuple[EvidenceContentKind, ...] = tuple(k for k in EvidenceContentKind if k != EvidenceContentKind.general_document)
    prohibited_credentials: tuple[str, ...] = ("OTP", "PIN", "password", "full banking credentials")

    def check(self, kind: EvidenceContentKind, text: str = "") -> None:
        if kind in self.prohibited:
            raise ValueError("This content is prohibited by the case evidence policy. Do not upload it.")
        reject_sensitive_text(text)


POLICIES = {ident: EvidencePolicy() for ident in ("financial_scam_transfer", "unauthorized_financial_transaction", "financial_authorization_unknown")}


def reject_sensitive_text(text: str) -> None:
    labelled = r"\b(?:otp|pin|password|cvv|security code|banking credentials)\s*[:=]\s*\S+|\bcard\s*(?:number|no)\s*[:=]\s*[\d -]{13,25}"
    numeric_story = r"(?:\b(?:otp|pin|cvv|security code)\b|ఓటీపీ|పిన్|ओटीपी|पिन)\s*(?:(?:is|was|hai|number|code)\s*)?[:=]?\s*\d{3,8}\b"
    password_story = r"\bpassword\s+(?:is|was)\s+(?!(?:shared|exposed|compromised|stolen|unknown)\b)\S+"
    card_story = r"\bcard\s*(?:number|no)\s*(?:(?:is|was)\s*)?[:=]?\s*[\d -]{13,25}"
    if any(re.search(pattern, text, re.I) for pattern in (labelled, numeric_story, password_story, card_story)):
        raise ValueError("Remove access credentials or full card details before submitting. Never enter OTPs, PINs or passwords.")


def check_values(value: object) -> None:
    if isinstance(value, str):
        reject_sensitive_text(value)
    elif isinstance(value, dict):
        for item in value.values():
            check_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            check_values(item)
