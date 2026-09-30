from datetime import timedelta
from decimal import Decimal

from app.models.incident import IncidentType, Urgency

AGE_BUCKETS = {
    "under_24_hours": timedelta(hours=24),
    "24_to_72_hours": timedelta(hours=72),
    "72_hours_to_7_days": timedelta(days=7),
}
AMOUNT_THRESHOLDS = {
    "moderate": Decimal("10000"),
    "high": Decimal("50000"),
    "very_high": Decimal("100000"),
}
PRIORITY_TIERS = (
    Urgency.critical,
    Urgency.high,
    Urgency.medium,
    Urgency.medium_low,
    Urgency.standard,
    Urgency.low,
)
SUPPORTED_INCIDENT_TYPES = (IncidentType.financial_fraud,)