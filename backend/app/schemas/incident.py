import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.incident import (
    IncidentStatus,
    IncidentType,
    OtherCrimeSubCategory,
    PaymentMethod,
    Urgency,
)


def validate_other_crime_details(
    sub_category: OtherCrimeSubCategory | None,
    details: dict[str, object] | None,
) -> None:
    if sub_category is None:
        raise ValueError("Other cyber crime reports require a sub-category.")
    values = details or {}

    def required(key: str) -> bool:
        value = values.get(key)
        return isinstance(value, str) and bool(value.strip())

    for key in ("incident_date_time", "occurred_on"):
        if not required(key):
            raise ValueError(f"Other cyber crime reports require {key}.")
    if sub_category == OtherCrimeSubCategory.online_social_media:
        if not required("social_media_sub_category"):
            raise ValueError("Online social media reports require a sub-category.")
        if values.get("social_media_sub_category") in {"Impersonating Email", "Intimidating Email"}:
            for key in ("service_provider", "full_header_of_email"):
                if not required(key):
                    raise ValueError(f"Email reports require {key}.")
    if sub_category in {OtherCrimeSubCategory.ransomware, OtherCrimeSubCategory.cryptocurrency} and not required("bitcoin_details"):
        raise ValueError("This report requires Bitcoin address/details.")
    if sub_category == OtherCrimeSubCategory.hacking:
        hacking_sub = values.get("hacking_sub_category")
        if not isinstance(hacking_sub, str) or not hacking_sub.strip():
            raise ValueError("Hacking reports require a sub-category.")
        if hacking_sub == "Unauthorized Access/Data Breach" and not required("mode_of_communication"):
            raise ValueError("Unauthorized access reports require a mode of communication.")
        if hacking_sub == "Website Related/Defacement":
            for key in ("website_domain_name", "other_additional_details"):
                if not required(key):
                    raise ValueError(f"Website defacement reports require {key}.")
    if sub_category == OtherCrimeSubCategory.online_trafficking and not required("social_media_used"):
        raise ValueError("Online trafficking reports require social media used.")
    if sub_category == OtherCrimeSubCategory.online_gambling:
        if not required("gambling_related_with"):
            raise ValueError("Online gambling reports require what the gambling is related with.")
        if values.get("lost_money") is True:
            for key in ("transaction_id", "transaction_date_time", "bank_name_paid_from", "account_no_paid_from", "amount_paid", "bank_account_paid_to", "merchant_gateway_details"):
                if not required(key):
                    raise ValueError("Money-loss gambling reports require transaction details.")
    if sub_category == OtherCrimeSubCategory.any_other and not required("other_crime_details"):
        raise ValueError("Any other cyber crime reports require crime details.")


class IncidentCreate(BaseModel):
    incident_type: IncidentType = IncidentType.financial_fraud
    incident_subtype: str | None = None
    affected_person_type: str | None = None
    platform: str | None = None
    account_type: str | None = None
    immediate_danger: bool | None = None
    threat_or_blackmail: bool | None = None
    content_still_online: bool | None = None
    account_access: str | None = None
    attacker_active: bool | None = None
    sensitive_information_exposed: bool | None = None
    evidence_types: list[str] | None = None
    other_crime_sub_category: OtherCrimeSubCategory | None = None
    payment_method: PaymentMethod = PaymentMethod.unknown
    amount: float | None = Field(default=None, ge=0)
    incident_time: datetime | None = None
    details: dict[str, object] | None = None

    @model_validator(mode="after")
    def validate_category_payload(self) -> "IncidentCreate":
        if self.incident_type == IncidentType.other_cyber_crime and not self.incident_subtype:
            validate_other_crime_details(self.other_crime_sub_category, self.details)
        return self


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_type: IncidentType
    payment_method: PaymentMethod
    amount: float | None
    incident_time: datetime | None
    occurred_at: datetime | None = None
    transaction_id: str | None = None
    incident_subtype: str | None = None
    affected_person_type: str | None = None
    platform: str | None = None
    account_type: str | None = None
    immediate_danger: bool | None = None
    threat_or_blackmail: bool | None = None
    content_still_online: bool | None = None
    account_access: str | None = None
    attacker_active: bool | None = None
    sensitive_information_exposed: bool | None = None
    evidence_types: list[str] | None = None
    other_crime_sub_category: OtherCrimeSubCategory | None = None
    details: dict[str, object] | None = None
    urgency: Urgency
    urgency_score: int | None = None
    urgency_computed_at: datetime | None = None
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime

    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, value: object) -> float | None:
        if value is None:
            return None
        return float(value)


class TriageRequest(BaseModel):
    incident_type: IncidentType
    incident_subtype: str | None = None
    affected_person_type: str | None = None
    platform: str | None = None
    account_type: str | None = None
    immediate_danger: bool | None = None
    threat_or_blackmail: bool | None = None
    content_still_online: bool | None = None
    account_access: str | None = None
    attacker_active: bool | None = None
    sensitive_information_exposed: bool | None = None
    evidence_types: list[str] | None = None
    occurred_at: datetime
    amount: float | None = Field(default=None, ge=0)
    payment_method: PaymentMethod = PaymentMethod.unknown
    transaction_id: str | None = Field(default=None, max_length=128)
    other_crime_sub_category: OtherCrimeSubCategory | None = None
    details: dict[str, object] | None = None

    @field_validator("transaction_id", mode="before")
    @classmethod
    def empty_txn_id_as_none(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return str(value).strip()

    @model_validator(mode="after")
    def validate_category_payload(self) -> "TriageRequest":
        if self.incident_type == IncidentType.financial_fraud:
            if self.amount is None or self.amount <= 0:
                raise ValueError("Financial fraud reports require an amount greater than zero.")
            if self.payment_method == PaymentMethod.unknown:
                raise ValueError("Financial fraud reports require a payment method.")
        if self.incident_type == IncidentType.other_cyber_crime and self.other_crime_sub_category is None and not self.incident_subtype:
            raise ValueError("Other cyber crime reports require a sub-category.")
        if self.incident_type == IncidentType.other_cyber_crime and not self.incident_subtype:
            validate_other_crime_details(self.other_crime_sub_category, self.details)
        return self


class IncidentDetailsUpdate(BaseModel):
    other_crime_sub_category: OtherCrimeSubCategory | None = None
    details: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_details(self) -> "IncidentDetailsUpdate":
        validate_other_crime_details(self.other_crime_sub_category, self.details)
        return self


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    original_filename: str
    content_type: str | None
    size_bytes: int
    created_at: datetime


class ActionItem(BaseModel):
    id: str
    title: str
    why: str
    phone: str | None = None
    url: str | None = None
    url_label: str | None = None


class ComplaintDraft(BaseModel):
    body: str


class ActionPlanResponse(BaseModel):
    urgency: Urgency
    urgency_label: str
    core_message: str
    large_amount: bool
    actions: list[ActionItem]
    complaint_draft: ComplaintDraft
