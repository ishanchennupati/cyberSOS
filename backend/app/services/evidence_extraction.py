"""
EvidenceExtractionService — Section 9/30.

The rest of the app talks only to `extract_evidence(...)`. Which provider
actually runs is chosen by EXTRACTION_PROVIDER, so swapping providers later
never touches the route or the frontend. Every provider returns the same
ExtractedFinancialData shape, with unknown fields left as null — providers
must never guess.

Providers:
  * heuristic  — regex/text based, zero external dependencies, always
                 available. Handles PDF and TXT (via pypdf text extraction).
                 Cannot read text out of images (no OCR dependency bundled).
  * anthropic  — optional. Uses the Claude API (vision) to read screenshots
                 and PDFs when ANTHROPIC_API_KEY is configured. Falls back
                 to "failed" cleanly if the key/package isn't available.

If extraction fails for any reason, callers get ExtractionStatus.failed and
a safe message — the citizen can always fall back to manual entry.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

from app.core.config import get_settings
from app.models.evidence import EvidenceType, ExtractionStatus
from app.schemas.evidence import ExtractedFinancialData, ExtractionResult


FIELDS = tuple(ExtractedFinancialData.model_fields.keys())


class ExtractionProvider(ABC):
    name: str = "base"

    @abstractmethod
    def extract(
        self,
        *,
        file_bytes: bytes,
        mime_type: str,
        filename: str,
        evidence_type: EvidenceType,
    ) -> ExtractedFinancialData | None:
        """Return extracted fields, or None if this provider cannot handle
        the file at all (caller will report extraction as failed)."""


# --- Heuristic provider -----------------------------------------------------

_AMOUNT_RE = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
_UPI_RE = re.compile(r"\b[\w.\-]{2,256}@[a-zA-Z]{2,64}\b")
_EMAIL_RE = re.compile(r"\b[\w.\-]+@[\w\-]+\.[a-zA-Z]{2,}\b")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+91[\-\s]?)?[6-9]\d{9}(?!\d)")
_URL_RE = re.compile(r"https?://[^\s)>\]]+")
_TXN_RE = re.compile(
    r"(?:UTR|txn(?:\s*id)?|transaction\s*id|ref(?:erence)?\s*(?:no\.?|id)?)"
    r"[:\s#]*([A-Za-z0-9]{6,25})",
    re.IGNORECASE,
)
_DATE_RE = re.compile(
    r"\b(\d{1,2}[\/\-\.](?:\d{1,2}|[A-Za-z]{3,9})[\/\-\.]\d{2,4})\b"
)
_TIME_RE = re.compile(r"\b(\d{1,2}:\d{2}(?::\d{2})?\s?(?:AM|PM|am|pm)?)\b")

_BANK_HINTS = (
    "sbi", "hdfc", "icici", "axis", "kotak", "pnb", "bank of baroda", "canara",
    "union bank", "indian bank", "yes bank", "idfc", "bob",
)
_WALLET_HINTS = ("paytm", "phonepe", "amazon pay", "mobikwik", "freecharge")


def _extract_text(file_bytes: bytes, mime_type: str) -> str | None:
    if mime_type == "text/plain":
        try:
            return file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return None
    if mime_type == "application/pdf":
        try:
            from pypdf import PdfReader
            from io import BytesIO

            reader = PdfReader(BytesIO(file_bytes))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return None
    return None


class HeuristicExtractionProvider(ExtractionProvider):
    name = "heuristic"

    def extract(
        self,
        *,
        file_bytes: bytes,
        mime_type: str,
        filename: str,
        evidence_type: EvidenceType,
    ) -> ExtractedFinancialData | None:
        text = _extract_text(file_bytes, mime_type)
        if text is None:
            # Images: this provider has no OCR. Caller reports "failed".
            return None

        lowered = text.lower()
        data = ExtractedFinancialData()

        amount_match = _AMOUNT_RE.search(text)
        if amount_match:
            try:
                data.amount = float(amount_match.group(1).replace(",", ""))
            except ValueError:
                pass

        txn_match = _TXN_RE.search(text)
        if txn_match:
            data.transaction_id = txn_match.group(1)

        upi_match = _UPI_RE.search(text)
        if upi_match:
            data.upi_id = upi_match.group(0)

        email_match = _EMAIL_RE.search(text)
        if email_match:
            data.email = email_match.group(0)

        phone_match = _PHONE_RE.search(text)
        if phone_match:
            data.phone_number = phone_match.group(0)

        url_match = _URL_RE.search(text)
        if url_match:
            data.website_url = url_match.group(0)

        date_match = _DATE_RE.search(text)
        if date_match:
            data.date = date_match.group(1)

        time_match = _TIME_RE.search(text)
        if time_match:
            data.time = time_match.group(1)

        for hint in _BANK_HINTS:
            if hint in lowered:
                data.bank = hint.upper() if len(hint) <= 4 else hint.title()
                break

        for hint in _WALLET_HINTS:
            if hint in lowered:
                data.wallet = hint.title()
                break

        if "upi" in lowered:
            data.payment_method = "UPI"
        elif "credit card" in lowered:
            data.payment_method = "Credit card"
        elif "debit card" in lowered:
            data.payment_method = "Debit card"
        elif "net banking" in lowered or "netbanking" in lowered:
            data.payment_method = "Net banking"

        return data


# --- Optional Anthropic (Claude vision) provider -----------------------------


class AnthropicExtractionProvider(ExtractionProvider):
    name = "anthropic"

    _PROMPT = (
        "You are extracting structured fields from a piece of evidence for a "
        "citizen's cybercrime/financial-fraud report. Look at the attached "
        "file and return ONLY a JSON object with exactly these keys: "
        + ", ".join(FIELDS)
        + ". Use null for any field you cannot find with confidence. Never "
        "guess or invent a value. Return raw JSON only, no markdown fences, "
        "no commentary."
    )

    def extract(
        self,
        *,
        file_bytes: bytes,
        mime_type: str,
        filename: str,
        evidence_type: EvidenceType,
    ) -> ExtractedFinancialData | None:
        settings = get_settings()
        if not settings.ANTHROPIC_API_KEY or not settings.ANTHROPIC_MODEL:
            return None
        if mime_type not in ("image/png", "image/jpeg", "application/pdf"):
            return None

        try:
            import base64

            import anthropic
        except ImportError:
            return None

        try:
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            encoded = base64.standard_b64encode(file_bytes).decode("utf-8")
            block_type = "document" if mime_type == "application/pdf" else "image"
            message = client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": block_type,
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": encoded,
                                },
                            },
                            {"type": "text", "text": self._PROMPT},
                        ],
                    }
                ],
            )
            text_out = "".join(
                block.text for block in message.content if getattr(block, "type", "") == "text"
            )
            cleaned = text_out.strip().strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
            parsed = json.loads(cleaned)
            return ExtractedFinancialData(**{k: parsed.get(k) for k in FIELDS})
        except Exception:
            return None


_PROVIDERS: dict[str, type[ExtractionProvider]] = {
    "heuristic": HeuristicExtractionProvider,
    "anthropic": AnthropicExtractionProvider,
}


def get_extraction_provider() -> ExtractionProvider:
    settings = get_settings()
    provider_cls = _PROVIDERS.get(settings.EXTRACTION_PROVIDER, HeuristicExtractionProvider)
    return provider_cls()


def extract_evidence(
    *,
    file_bytes: bytes,
    mime_type: str,
    filename: str,
    evidence_type: EvidenceType,
) -> ExtractionResult:
    """
    Never raises. Always returns a well-formed ExtractionResult so the
    caller can persist extraction_status + extracted_data unconditionally.
    """
    provider = get_extraction_provider()
    try:
        data = provider.extract(
            file_bytes=file_bytes,
            mime_type=mime_type,
            filename=filename,
            evidence_type=evidence_type,
        )
    except Exception:
        data = None

    if data is None:
        return ExtractionResult(
            status=ExtractionStatus.failed,
            data=None,
            message="Extraction unavailable. You can enter these details manually.",
            provider=provider.name,
        )

    return ExtractionResult(
        status=ExtractionStatus.completed, data=data, message=None, provider=provider.name
    )
