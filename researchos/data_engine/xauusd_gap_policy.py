from __future__ import annotations

import pandas as pd


def classify_gap(start: pd.Timestamp, end: pd.Timestamp) -> str:
    """Classify a temporal gap conservatively.

    A weekend overlap is only a candidate classification. It is not evidence
    that the broker was closed. Holidays, maintenance windows, and intraday
    session breaks require an explicit broker session calendar before a gap
    can be accepted as valid market closure.
    """
    days = pd.date_range(start.normalize(), end.normalize(), freq="D")
    if any(day.weekday() >= 5 for day in days):
        return "weekend_overlap_candidate"
    return "non_weekend_suspicious"
