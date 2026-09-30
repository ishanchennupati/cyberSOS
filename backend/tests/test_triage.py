from datetime import datetime, timedelta, timezone

import pytest

from app.models.incident import Urgency
from app.services.incident_service import LARGE_AMOUNT_THRESHOLD, compute_urgency

NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=timezone.utc)
SMALL = 1_000.0
LARGE = LARGE_AMOUNT_THRESHOLD
JUST_UNDER_LARGE = LARGE_AMOUNT_THRESHOLD - 0.01


def _ago(**kwargs: float) -> datetime:
    return NOW - timedelta(**kwargs)


@pytest.mark.parametrize(
    ("elapsed_kwargs", "expected"),
    [
        ({"seconds": 0}, Urgency.critical),
        ({"minutes": 59, "seconds": 59}, Urgency.critical),
        ({"hours": 1}, Urgency.critical),
        ({"hours": 1, "microseconds": 1}, Urgency.critical),
        ({"hours": 23, "minutes": 59}, Urgency.critical),
        ({"hours": 24}, Urgency.high),
        ({"hours": 24, "microseconds": 1}, Urgency.high),
        ({"days": 2, "hours": 23}, Urgency.high),
        ({"days": 3}, Urgency.medium),
        ({"days": 3, "microseconds": 1}, Urgency.medium),
        ({"days": 29, "hours": 23}, Urgency.low),
        ({"days": 30}, Urgency.low),
        ({"days": 30, "microseconds": 1}, Urgency.low),
        ({"days": 90}, Urgency.low),
    ],
)
def test_time_boundaries_small_amount(elapsed_kwargs: dict, expected: Urgency) -> None:
    assert compute_urgency(_ago(**elapsed_kwargs), SMALL, now=NOW) == expected


def test_future_occurred_at_is_critical() -> None:
    future = NOW + timedelta(minutes=5)
    assert compute_urgency(future, SMALL, now=NOW) == Urgency.critical


def test_naive_datetime_treated_as_utc() -> None:
    naive = datetime(2026, 8, 24, 11, 0, 0)  # exactly 1 hour before NOW
    assert compute_urgency(naive, SMALL, now=NOW) == Urgency.critical


@pytest.mark.parametrize(
    ("elapsed_kwargs", "base", "bumped"),
    [
        ({"hours": 1}, Urgency.critical, Urgency.critical),
        ({"hours": 24}, Urgency.high, Urgency.critical),
        ({"days": 3}, Urgency.medium, Urgency.high),
        ({"days": 30}, Urgency.low, Urgency.medium),
        ({"days": 45}, Urgency.low, Urgency.medium_low),
    ],
)
def test_large_amount_does_not_bump_priority(
    elapsed_kwargs: dict, base: Urgency, bumped: Urgency
) -> None:
    occurred = _ago(**elapsed_kwargs)
    assert compute_urgency(occurred, JUST_UNDER_LARGE, now=NOW) == base
    assert compute_urgency(occurred, LARGE, now=NOW) == base
    assert compute_urgency(occurred, LARGE + 1, now=NOW) == base


def test_none_amount_does_not_bump() -> None:
    occurred = _ago(days=45)
    assert compute_urgency(occurred, None, now=NOW) == Urgency.low
