from __future__ import annotations

import pandas as pd

from scripts.audit_xauusd_m1_gaps import classify_gap


def ts(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="UTC")


def test_friday_to_sunday_gap_is_weekend_candidate() -> None:
    assert classify_gap(ts("2025-01-03 23:58"), ts("2025-01-05 23:00")) == "weekend_closure_candidate"


def test_weekend_overlap_is_not_declared_valid() -> None:
    assert classify_gap(ts("2025-01-04 00:00"), ts("2025-01-06 01:00")) == "weekend_overlap_candidate"


def test_weekday_gap_is_suspicious() -> None:
    assert classify_gap(ts("2025-01-07 10:00"), ts("2025-01-07 12:00")) == "non_weekend_suspicious"
