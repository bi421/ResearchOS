from datetime import datetime, timedelta, timezone

import polars as pl
import pytest

from researchos.market_memory.event_schema import EventContext, EventType, MarketEvent
from researchos.market_memory.outcome_engine import compute_forward_outcomes


def _event(direction: str) -> MarketEvent:
    ts = datetime(2021, 1, 1, tzinfo=timezone.utc)
    context = EventContext(
        event_id=f"{direction}-1",
        asset="XAUUSD",
        timeframe="D1",
        timestamp=ts,
        event_price=100.0,
    )
    return MarketEvent(
        event_id=f"{direction}-1",
        asset="XAUUSD",
        timeframe="D1",
        event_type=EventType.SMA_CROSSOVER.value,
        direction=direction,
        timestamp=ts,
        event_price=100.0,
        context=context,
    )


def _prices(close: float, high: float, low: float) -> pl.DataFrame:
    ts = datetime(2021, 1, 1, tzinfo=timezone.utc)
    return pl.DataFrame(
        {
            "timestamp": [ts, ts + timedelta(days=1)],
            "open": [100.0, close],
            "high": [101.0, high],
            "low": [99.0, low],
            "close": [100.0, close],
        }
    )


def test_bearish_positive_move_is_a_miss() -> None:
    result = compute_forward_outcomes(
        [_event("bearish")], _prices(close=101.0, high=102.0, low=100.0)
    )[0].outcome
    assert result is not None
    assert result.return_1d == pytest.approx(0.01)
    assert result.hit_threshold_1d is False
    assert result.mfe_1d == pytest.approx(0.0)
    assert result.mae_1d == pytest.approx(-0.02)


def test_bearish_negative_move_is_a_hit() -> None:
    result = compute_forward_outcomes(
        [_event("bearish")], _prices(close=99.0, high=100.0, low=98.0)
    )[0].outcome
    assert result is not None
    assert result.return_1d == pytest.approx(-0.01)
    assert result.hit_threshold_1d is False
    assert result.mfe_1d == pytest.approx(0.02)
    assert result.mae_1d == pytest.approx(0.0)


def test_directional_threshold_can_be_positive_for_bearish_event() -> None:
    result = compute_forward_outcomes(
        [_event("bearish")], _prices(close=99.0, high=100.0, low=98.0), threshold=0.005
    )[0].outcome
    assert result is not None
    assert result.hit_threshold_1d is True
