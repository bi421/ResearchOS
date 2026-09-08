"""Content identity for Phase 5.2 empirical inputs.

The provenance digest is intentionally separate from the result reproducibility
hash.  It fingerprints the actual ordered observations used by the experiment,
including UTC timestamps, so changing a value, timestamp, factor, or order
changes the empirical input identity.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from researchos.experiments.phase51.contracts import reproducibility_hash

HASH_ALGORITHM = "sha256"


def _utc_timestamp(value: object) -> str:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.isoformat()


def _series_records(
    timestamps: Sequence[object],
    values: Sequence[Any],
) -> list[dict[str, Any]]:
    if len(timestamps) != len(values):
        raise ValueError("provenance: timestamp/value length mismatch")
    return [
        {"timestamp": _utc_timestamp(ts), "value": value}
        for ts, value in zip(timestamps, values)
    ]


def hash_series(
    timestamps: Sequence[object],
    values: Sequence[Any],
) -> str:
    """Hash an ordered timestamp/value series with timestamps in the identity."""
    return reproducibility_hash(_series_records(timestamps, values))


def build_input_provenance(
    timestamps: Sequence[object],
    close: Sequence[Any],
    high: Sequence[Any],
    low: Sequence[Any],
    volume: Sequence[Any],
    macro_timestamps: dict[str, Sequence[object]],
    macro_factor_series: dict[str, Sequence[Any]],
    required_macro_symbols: Sequence[str],
) -> dict[str, Any]:
    """Build deterministic identity hashes for all Phase 5.2 empirical inputs."""
    price_records = [
        {
            "timestamp": _utc_timestamp(ts),
            "close": c,
            "high": h,
            "low": l,
            "volume": v,
        }
        for ts, c, h, l, v in zip(timestamps, close, high, low, volume)
    ]
    price_hash = reproducibility_hash(price_records)
    macro_hashes = {
        symbol: hash_series(macro_timestamps[symbol], macro_factor_series[symbol])
        for symbol in required_macro_symbols
    }
    combined_hash = reproducibility_hash(
        {
            "price": price_hash,
            "macro": macro_hashes,
            "required_macro_symbols": list(required_macro_symbols),
        }
    )
    return {
        "hash_algorithm": HASH_ALGORITHM,
        "price_input_hash": price_hash,
        "macro_input_hashes": macro_hashes,
        "combined_input_hash": combined_hash,
    }


__all__ = ["HASH_ALGORITHM", "hash_series", "build_input_provenance"]
