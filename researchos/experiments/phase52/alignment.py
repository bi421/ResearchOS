from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def validate_exact_timestamp_alignment(
    target_timestamps: Sequence[object],
    factor_timestamps: Sequence[object],
    factor_name: str,
) -> None:
    """Require a one-to-one, order-preserving UTC timestamp match.

    No date truncation, interpolation, forward-fill, resampling, or repair is
    performed. Any duplicate, missing, extra, reordered, or differently timed
    observation blocks empirical execution.
    """
    target = pd.DatetimeIndex(pd.to_datetime(list(target_timestamps), utc=True, errors="coerce"))
    factor = pd.DatetimeIndex(pd.to_datetime(list(factor_timestamps), utc=True, errors="coerce"))

    if target.isna().any() or factor.isna().any():
        raise ValueError(f"{factor_name}: invalid timestamp")
    if target.has_duplicates:
        raise ValueError("XAUUSD: duplicate timestamps")
    if factor.has_duplicates:
        raise ValueError(f"{factor_name}: duplicate timestamps")
    if len(target) != len(factor):
        raise ValueError(f"{factor_name}: timestamp length mismatch")
    if not target.equals(factor):
        mismatch = next((i for i, (a, b) in enumerate(zip(target, factor)) if a != b), None)
        if mismatch is None:
            mismatch = min(len(target), len(factor))
        raise ValueError(f"{factor_name}: exact timestamp mismatch at index {mismatch}")


__all__ = ["validate_exact_timestamp_alignment"]
