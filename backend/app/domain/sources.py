"""Single runtime registry; source snapshots travel with historical plans."""
from datetime import date
from types import MappingProxyType
from app.domain.response import OfficialSource

SOURCES = MappingProxyType({s.id: s for s in (
    OfficialSource(id="NCRP-SAFE-RECORDS", authority="I4C / Ministry of Home Affairs",
        display_name="Cybercrime reporting and safe records", official_url="https://cybercrime.gov.in/Webform/FAQ.aspx",
        purpose="Cybercrime and platform reporting", supported_guidance=("Citizens may report cybercrime on NCRP. Social media services offer reporting or flagging of objectionable content.",),
        reviewed_on=date(2026, 10, 7), notes="FAQ reviewed; no universal anonymous reporting claim. Preserve safer non-explicit records only."),
    OfficialSource(id="GOOGLE-ACCOUNT", authority="Google",
        display_name="Secure a hacked or compromised Google Account", official_url="https://support.google.com/accounts/answer/6294825",
        purpose="Google account recovery", supported_guidance=("Google provides account recovery and security review for a hacked or compromised Google Account.",),
        reviewed_on=date(2026, 10, 7), notes="Platform-specific guidance, not a guarantee or permission to enter credentials in CyberSOS."),
    OfficialSource(id="MHA-1930", authority="Ministry of Home Affairs / PIB",
        display_name="Financial cyber fraud reporting", official_url="https://www.pib.gov.in/PressReleasePage.aspx?PRID=1814120&lang=2&reg=48",
        purpose="Financial fraud reporting", supported_guidance=("1930 assists reporting financial cyber incidents.",),
        reviewed_on=date(2026, 10, 1), notes="Primary-source indexed text reviewed. No recovery or response-time claim."),
    OfficialSource(id="NCRP-REPORT", authority="I4C / Ministry of Home Affairs",
        display_name="National Cybercrime Reporting Portal", official_url="https://cybercrime.gov.in",
        purpose="External citizen reporting", supported_guidance=("Citizens may report cybercrime at NCRP.",),
        reviewed_on=date(2026, 10, 1), notes="PIB primary-source reporting description reviewed; user submits independently."),
    OfficialSource(id="NPCI-BANK", authority="National Payments Corporation of India",
        display_name="Fraud transaction complaints", official_url="https://www.npci.org.in/register-a-complaint",
        purpose="Bank reporting", supported_guidance=("Fraudulent/unidentified/unauthorized transaction complaints should be raised with the respective bank.",),
        reviewed_on=date(2026, 10, 1), notes="Indexed primary-source text reviewed; no stop/reversal guarantee."),
    OfficialSource(id="RBI-UNAUTHORIZED", authority="Reserve Bank of India",
        display_name="Reporting unauthorized electronic banking transactions", official_url="https://rbi.org.in/commonman/Upload/English/Notification/PDFs/NOTI1506072017.PDF",
        purpose="Unauthorized transaction reporting", supported_guidance=("Notify the bank promptly about an unauthorized electronic banking transaction.",),
        reviewed_on=date(2026, 10, 1), notes="Primary-source notification reviewed for reporting only; no liability/refund rule implemented. Not used for approved scam transfers."),
    OfficialSource(id="INDIA-EMERGENCY", authority="Government of India / ERSS",
        display_name="Official emergency information", official_url="https://112.gov.in",
        purpose="Existing legacy safety handoff", supported_guidance=("112 is India's emergency reporting number.",),
        reviewed_on=date(2026, 10, 1), notes="MHA ERSS primary-source indexed text reviewed: https://www.mha.gov.in/en/commoncontent/emergency-response-support-system-erss . No response-time guarantee; no financial-playbook action uses this entry."),
)})


def source(source_id: str) -> OfficialSource:
    return SOURCES[source_id]
