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
    assert result.fit_mode == "fixed_matcher"


def test_fit_callback_receives_only_purged_training_data():
    events = _events(220)
    seen: list[tuple[datetime, ...]] = []

    def fit(train):
        seen.append(tuple(event.timestamp for event in train))
        return lambda e: False

    result = walk_forward_validate(
        events, lambda e: False, lambda e: e.value,
        initial_train_size=100, validation_size=40, test_size=40, step_size=40,
        min_test_events=20, purge_days=3, max_outcome_horizon_days=3,
        fit_callback=fit,
    )

    assert result.fit_mode == "train_only_fit"
    assert result.total_folds == 2
    for fold_index, timestamps in enumerate(seen):
        validation_start = events[100 + fold_index * 40].timestamp
        assert max(timestamps) < validation_start - timedelta(days=3)


def test_fit_callback_must_return_callable_matcher():
    with pytest.raises(TypeError, match="callable matcher"):
        walk_forward_validate(
            _events(220), lambda e: True, lambda e: e.value,
            initial_train_size=100, validation_size=40, test_size=40,
            fit_callback=lambda train: object(),
        )


def test_legacy_fixed_matcher_api_remains_compatible():
    result = walk_forward_validate(
        _events(220), lambda e: e.match, lambda e: e.value,
        initial_train_size=100, validation_size=40, test_size=40, step_size=40,
    )
    assert result.total_folds == 2
    assert result.fit_mode == "fixed_matcher"
