from __future__ import annotations

import pandas as pd

from researchos.data_engine.xauusd_gap_policy import classify_gap


def ts(value: str) -> pd.Timestamp:
    return pd.Timestamp(value, tz="UTC")


def test_friday_to_sunday_gap_is_weekend_candidate() -> None:
    assert classify_gap(ts("2025-01-03 23:58"), ts("2025-01-05 23:00")) == "weekend_overlap_candidate"


def test_friday_to_monday_gap_is_weekend_candidate() -> None:
    assert classify_gap(ts("2025-01-03 23:58"), ts("2025-01-06 01:00")) == "weekend_overlap_candidate"


def test_thursday_to_monday_gap_is_weekend_candidate() -> None:
    assert classify_gap(ts("2025-01-02 23:58"), ts("2025-01-06 01:00")) == "weekend_overlap_candidate"


def test_weekend_overlap_is_not_declared_valid() -> None:
    assert classify_gap(ts("2025-01-04 00:00"), ts("2025-01-06 01:00")) == "weekend_overlap_candidate"


def test_weekday_gap_is_suspicious() -> None:
    assert classify_gap(ts("2025-01-07 10:00"), ts("2025-01-07 12:00")) == "non_weekend_suspicious"
