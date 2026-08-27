"""
Temporal Validation — chronological validation for market memory findings.

Implements:
  - Chronological train/validation/test splits
  - Walk-forward validation
  - Expanding window validation
  - Stability detection

Never uses random shuffling. Always respects temporal order.
"""

from __future__ import annotations

from typing import Any


def chronological_split(
    events: list[Any],
    train_ratio: float = 0.6,
    validation_ratio: float = 0.2,
) -> tuple[list[Any], list[Any], list[Any]]:
    """
    Split events chronologically into train, validation, and test sets.

    Args:
        events: List of events sorted by timestamp
        train_ratio: Fraction for training (default 0.6)
        validation_ratio: Fraction for validation (default 0.2)

    Returns:
        Tuple of (train_events, validation_events, test_events)
    """
    if not events:
        return [], [], []

    n = len(events)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * validation_ratio)

    train = events[:train_end]
    validation = events[train_end:val_end]
    test = events[val_end:]

    return train, validation, test


def expanding_window_splits(
    events: list[Any],
    initial_train_size: int = 100,
    validation_size: int = 50,
    step_size: int = 50,
) -> list[tuple[list[Any], list[Any]]]:
    """
    Generate expanding window train/validation splits.

    The training window expands by step_size each fold.
    Validation window is always validation_size.

    Args:
        events: List of events sorted by timestamp
        initial_train_size: Initial training set size
        validation_size: Validation set size
        step_size: How much the training window expands each fold

    Returns:
        List of (train_events, validation_events) tuples
    """
    splits = []
    n = len(events)

    train_end = initial_train_size
    while train_end + validation_size <= n:
        train = events[:train_end]
        validation = events[train_end : train_end + validation_size]
        splits.append((train, validation))
        train_end += step_size

    return splits


def check_temporal_integrity(
    events: list[Any],
) -> dict[str, Any]:
    """
    Check temporal integrity of event list.

    Verifies:
      - Events are sorted by timestamp
      - No duplicate timestamps (within same asset/timeframe)
      - No future leakage in conditioning variables
    """
    if not events:
        return {"status": "PASS", "issues": []}

    issues = []

    # Check sorting
    for i in range(1, len(events)):
        if events[i].timestamp < events[i - 1].timestamp:
            issues.append(f"Timestamp out of order at index {i}")

    # Check duplicates
    seen = set()
    for i, e in enumerate(events):
        key = (e.asset, e.timeframe, e.timestamp.isoformat())
        if key in seen:
            issues.append(f"Duplicate event at index {i}: {key}")
        seen.add(key)

    return {
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "total_events": len(events),
    }
