"""
Dataset-contract normalization — the ONLY data-parsing point in the compute layer.

Every ``QuantComputationInterface`` backend (Python reference and C++ adapter)
normalizes a raw dataset contract into a deterministic close-price series using
this single shared function, so Python vs C++ backends can never diverge on
dataset parsing.

Supported dataset contracts:
    - ``List[float]``: used directly as the price series.
    - ``HistoricalDataset``: ``close`` prices from Candle records.
    - ``List[Candle]``: ``close`` prices from candle objects.
    - ``List[dict]`` with ``close`` key: close prices from dict records.
    - ``None``: deterministic synthetic prices (252 periods) for testing/demo.

This is a COMPUTATION LAYER helper — NOT trading or execution logic.
"""

from __future__ import annotations

from typing import Any, List


def extract_prices(dataset: Any) -> List[float]:
    """Normalize a dataset contract into a deterministic close-price series.

    Args:
        dataset: The dataset contract to normalize.

    Returns:
        List of float prices (oldest to newest).
    """
    if dataset is None:
        # Deterministic default prices for testing when no dataset provided.
        base = 100.0
        return [base * (1.0 + 0.0001 * i) for i in range(252)]

    if isinstance(dataset, list):
        if not dataset:
            return [100.0]
        # List of Candle objects (duck-typed via 'close' attribute).
        if hasattr(dataset[0], "close"):
            return [float(c.close) for c in dataset]
        # List of floats — use directly.
        if isinstance(dataset[0], (int, float)):
            return [float(p) for p in dataset]
        # List of dicts with a 'close' key.
        if isinstance(dataset[0], dict) and "close" in dataset[0]:
            return [float(d["close"]) for d in dataset]

    # HistoricalDataset via duck typing (records + symbol).
    if hasattr(dataset, "records") and hasattr(dataset, "symbol"):
        records = dataset.records
        if records and hasattr(records[0], "close"):
            return [float(r.close) for r in records]

    # Any iterable of Candle-like objects.
    if hasattr(dataset, "__iter__"):
        try:
            items = list(dataset)
            if items and hasattr(items[0], "close"):
                return [float(c.close) for c in items]
        except (TypeError, IndexError):
            pass

    # Fallback: deterministic default.
    return [100.0]


__all__ = ["extract_prices"]
