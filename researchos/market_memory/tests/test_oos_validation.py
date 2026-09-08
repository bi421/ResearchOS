"""Regression tests for walk-forward OOS validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from researchos.market_memory.oos_validation import walk_forward_validate


@dataclass(frozen=True)
class E:
    timestamp: datetime
    value: float
    match: bool = True


def _events(n: int = 300, value: float = 0.01) -> list[E]:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return [E(start + timedelta(days=i), value) for i in range(n)]


def test_walk_forward_is_chronological_and_validates_stable_condition():
    result = walk_forward_validate(
        _events(), lambda e: e.match, lambda e: e.value,
        initial_train_size=100, validation_size=50, test_size=50, step_size=50,
        min_test_events=20,
    )
    assert result.total_folds == 3
    assert result.status == "VALIDATED"
    assert result.stable is True
    assert all(f.test_events >= 20 for f in result.folds)


def test_walk_forward_rejects_duplicate_or_reordered_timestamps():
    events = _events(120)
    events[5] = E(events[4].timestamp, 0.01)
    with pytest.raises(ValueError, match="strictly increasing"):
        walk_forward_validate(
            events, lambda e: True, lambda e: e.value,
            initial_train_size=40, validation_size=20, test_size=20,
        )


def test_walk_forward_is_inconclusive_with_small_oos_samples():
    result = walk_forward_validate(
        _events(), lambda e: e.match, lambda e: e.value,
        initial_train_size=100, validation_size=50, test_size=50, step_size=50,
        min_test_events=60,
    )
    assert result.status == "INCONCLUSIVE"
    assert result.stable is False
