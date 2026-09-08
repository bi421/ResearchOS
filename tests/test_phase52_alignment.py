from __future__ import annotations

import pandas as pd
import pytest

from researchos.experiments.phase52.alignment import validate_exact_timestamp_alignment


def ts(*values: str) -> list[pd.Timestamp]:
    return [pd.Timestamp(value, tz="UTC") for value in values]


def test_exact_timestamp_alignment_passes() -> None:
    values = ts("2025-01-02 00:00", "2025-01-03 00:00")
    validate_exact_timestamp_alignment(values, values, "DXY")


def test_shifted_timestamp_blocks() -> None:
    with pytest.raises(ValueError, match="exact timestamp mismatch"):
        validate_exact_timestamp_alignment(
            ts("2025-01-02 00:00", "2025-01-03 00:00"),
            ts("2025-01-02 00:00", "2025-01-03 00:01"),
            "DXY",
        )


def test_missing_timestamp_blocks() -> None:
    with pytest.raises(ValueError, match="timestamp length mismatch"):
        validate_exact_timestamp_alignment(
            ts("2025-01-02 00:00", "2025-01-03 00:00"),
            ts("2025-01-02 00:00"),
            "US10Y",
        )


def test_duplicate_timestamp_blocks() -> None:
    with pytest.raises(ValueError, match="duplicate timestamps"):
        validate_exact_timestamp_alignment(
            ts("2025-01-02 00:00", "2025-01-03 00:00"),
            ts("2025-01-02 00:00", "2025-01-02 00:00"),
            "VIX",
        )


def test_reordered_timestamp_blocks() -> None:
    with pytest.raises(ValueError, match="exact timestamp mismatch"):
        validate_exact_timestamp_alignment(
            ts("2025-01-02 00:00", "2025-01-03 00:00"),
            ts("2025-01-03 00:00", "2025-01-02 00:00"),
            "DXY",
        )
