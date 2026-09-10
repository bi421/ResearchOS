from __future__ import annotations

from datetime import date, timedelta

from researchos.experiments.phase52_rebuild.context_features import (
    build_context_feature_dataset,
)
from researchos.experiments.phase52_rebuild.daily_dataset import DailyObservation
from researchos.experiments.phase52_rebuild.feature_contract import Phase52FeatureContract


def _obs(day_index: int, close: float) -> DailyObservation:
    day = date(2020, 1, 1) + timedelta(days=day_index)
    iso = day.isoformat()
    return DailyObservation(
        day=iso,
        timestamp=f"{iso}T00:00:00Z",
        open=close - 0.5,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        tick_volume=100.0 + day_index,
        spread=1.0,
        real_volume=0.0,
        dxy=100.0 + day_index * 0.01,
        us10y=1.0 + day_index * 0.001,
        vix=20.0 + day_index * 0.01,
        m1_rows=1440,
    )


def _contract() -> Phase52FeatureContract:
    return Phase52FeatureContract(
        warmup=60,
        horizon=5,
        train_size=5,
        validation_size=5,
    )


def test_context_initializes_features_without_being_emitted() -> None:
    context = tuple(_obs(i, 100.0 + i * 0.1) for i in range(60))
    research = tuple(_obs(60 + i, 106.0 + i * 0.2) for i in range(10))

    dataset, audit = build_context_feature_dataset(
        context, research, "PRICE_ONLY", _contract()
    )

    assert audit.invariant_ok
    assert audit.context_rows == 60
    assert audit.research_rows == 10
    assert audit.emitted_rows == 5
    assert dataset.source_days == tuple(o.day for o in research[:5])
    assert dataset.metadata["context_is_feature_state_only"] is True
    assert dataset.metadata["context_rows_emitted"] is False


def test_future_research_changes_only_future_features() -> None:
    context = tuple(_obs(i, 100.0 + i * 0.1) for i in range(60))
    research = tuple(_obs(60 + i, 106.0 + i * 0.2) for i in range(10))
    changed = research[:-1] + (_obs(69, 999.0),)

    first, _ = build_context_feature_dataset(
        context, research, "PRICE_ONLY", _contract()
    )
    second, _ = build_context_feature_dataset(
        context, changed, "PRICE_ONLY", _contract()
    )

    assert first.rows[:-1] == second.rows[:-1]
    assert first.source_days[:-1] == second.source_days[:-1]


def test_context_must_end_before_research() -> None:
    context = tuple(_obs(i, 100.0 + i) for i in range(60))
    research = (context[-1],) + tuple(_obs(61 + i, 200.0 + i) for i in range(5))

    try:
        build_context_feature_dataset(context, research, "PRICE_ONLY", _contract())
    except ValueError as exc:
        assert "context must end strictly before research starts" in str(exc)
    else:
        raise AssertionError("expected overlapping context/research boundary to fail")


def test_insufficient_context_is_blocked() -> None:
    context = tuple(_obs(i, 100.0 + i) for i in range(59))
    research = tuple(_obs(59 + i, 200.0 + i) for i in range(6))

    try:
        build_context_feature_dataset(context, research, "PRICE_ONLY", _contract())
    except ValueError as exc:
        assert "warm-up rows are required" in str(exc)
    else:
        raise AssertionError("expected insufficient context to fail")
