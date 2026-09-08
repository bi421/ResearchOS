"""Regression tests for statistical evidence and production gates."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from researchos.market_memory.event_schema import EventContext, EventOutcome, MarketEvent
from researchos.market_memory.production_gate import check_production_evidence_readiness
from researchos.market_memory.statistical_evidence import bonferroni_alpha, wilson_proportion_ci


def _event(i: int, outcome: float = 0.01, source: str = "real_mt5") -> MarketEvent:
    ts = datetime(2025, 1, 1 + i, tzinfo=timezone.utc)
    context = EventContext(event_id=f"e{i}", asset="XAUUSD", timeframe="D1", timestamp=ts)
    return MarketEvent(
        event_id=f"e{i}", asset="XAUUSD", timeframe="D1", event_type="sma_crossover",
        direction="bullish", timestamp=ts, event_price=2000.0, context=context,
        outcome=EventOutcome(event_id=f"e{i}", asset="XAUUSD", timeframe="D1", event_timestamp=ts, return_1d=outcome),
        dataset_source=source,
    )


def test_wilson_interval_is_bounded_and_deterministic():
    a = wilson_proportion_ci(7, 10)
    b = wilson_proportion_ci(7, 10)
    assert a == b
    assert 0.0 <= a.confidence_interval[0] <= a.probability <= a.confidence_interval[1] <= 1.0


def test_wilson_rejects_invalid_counts():
    with pytest.raises(ValueError):
        wilson_proportion_ci(11, 10)
    with pytest.raises(ValueError):
        wilson_proportion_ci(1, 0)


def test_bonferroni_alpha():
    assert bonferroni_alpha(0.05, 5) == pytest.approx(0.01)


def test_production_gate_accepts_real_provenance():
    result = check_production_evidence_readiness([_event(i) for i in range(100)], dataset_source="real_mt5", minimum_events=100)
    assert result.passed is True
    assert result.issues == ()


def test_production_gate_rejects_synthetic():
    result = check_production_evidence_readiness([_event(i, source="synthetic") for i in range(100)], dataset_source="synthetic")
    assert result.passed is False
    assert any("blocked evidence source" in issue for issue in result.issues)


def test_production_gate_rejects_missing_outcome():
    event = _event(0)
    broken = MarketEvent(
        event_id=event.event_id, asset=event.asset, timeframe=event.timeframe,
        event_type=event.event_type, direction=event.direction, timestamp=event.timestamp,
        event_price=event.event_price, context=event.context, outcome=None,
        dataset_source=event.dataset_source,
    )
    result = check_production_evidence_readiness([broken], dataset_source="real_mt5", minimum_events=1)
    assert result.passed is False
    assert any("missing outcome" in issue for issue in result.issues)
