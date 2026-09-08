from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from researchos.market_memory.oos_validation import walk_forward_validate


def _events(days: int = 12):
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return [
        SimpleNamespace(timestamp=start + timedelta(days=i), value=1.0 if i % 2 == 0 else -1.0)
        for i in range(days)
    ]


def _all(event):
    return True


def _value(event):
    return event.value


def test_walk_forward_purges_labels_crossing_boundaries():
    result = walk_forward_validate(
        _events(),
        _all,
        _value,
        initial_train_size=3,
        validation_size=2,
        test_size=2,
        step_size=2,
        min_test_events=1,
        purge_days=1,
    )

    first = result.folds[0]
    assert first.train_events == 2
    assert first.validation_events == 1
    assert first.test_events == 2
    assert result.purge_days == 1
    assert result.embargo_days == 0


def test_walk_forward_embargo_removes_early_test_observations():
    result = walk_forward_validate(
        _events(),
        _all,
        _value,
        initial_train_size=3,
        validation_size=2,
        test_size=2,
        step_size=2,
        min_test_events=1,
        purge_days=1,
        embargo_days=1,
    )

    assert result.folds[0].test_events == 1
    assert result.embargo_days == 1


def test_negative_purge_or_embargo_is_rejected():
    with pytest.raises(ValueError, match="purge_days and embargo_days"):
        walk_forward_validate(
            _events(),
            _all,
            _value,
            initial_train_size=3,
            validation_size=2,
            test_size=2,
            purge_days=-1,
        )
