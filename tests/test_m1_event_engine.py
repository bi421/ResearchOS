from datetime import datetime, timezone

import polars as pl
import pytest

from researchos.market_memory.m1_event_engine import extract_xauusd_m1_sma_crossover_events


def _frame() -> pl.DataFrame:
    ts = [datetime(2026, 1, 1, 0, i, tzinfo=timezone.utc) for i in range(12)]
    close = [100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 96.0, 97.0, 98.0, 99.0, 101.0, 103.0]
    return pl.DataFrame(
        {
            "timestamp": ts,
            "open": close,
            "high": [x + 0.5 for x in close],
            "low": [x - 0.5 for x in close],
            "close": close,
            "tick_volume": [100] * len(close),
        }
    )


def test_m1_engine_is_deterministic_and_uses_m1_contract() -> None:
    df = _frame()
    a = extract_xauusd_m1_sma_crossover_events(df, fast_period=2, slow_period=3)
    b = extract_xauusd_m1_sma_crossover_events(df, fast_period=2, slow_period=3)
    assert a == b
    assert a
    assert all(event.timeframe == "M1" for event in a)
    assert all(event.context.timeframe == "M1" for event in a)
    assert all("M1_SMA2/3_crossover" == event.computation_method for event in a)


def test_m1_engine_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="df missing columns"):
        extract_xauusd_m1_sma_crossover_events(_frame().drop("close"))


def test_m1_engine_does_not_accept_invalid_period_order() -> None:
    with pytest.raises(ValueError, match="fast_period < slow_period"):
        extract_xauusd_m1_sma_crossover_events(_frame(), fast_period=3, slow_period=2)
