from datetime import datetime, timedelta, timezone

import polars as pl

from researchos.market_memory.event_schema import MarketEvent
from researchos.market_memory.m1_outcome_contract import M1OutcomeContract
from researchos.market_memory.outcome_engine import compute_forward_outcomes


def _event(direction: str) -> MarketEvent:
    from researchos.market_memory.event_schema import EventContext, EventType
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ctx = EventContext(
        event_id="m1", asset="XAUUSD", timeframe="M1", timestamp=t,
        event_price=100.0, open_price=100.0, high_price=101.0, low_price=99.0,
        close_price=100.0, tick_volume=100, sma_fast=101.0, sma_slow=100.0,
        atr=1.0, rsi=50.0, macd_line=0.0, macd_signal=0.0, macd_histogram=0.0,
        market_regime="Ranging", volatility_state="Low", day_of_week=3,
        session="Asian", preceding_return_1d=0.0, preceding_return_3d=0.0,
        preceding_return_5d=0.0,
    )
    return MarketEvent(
        event_id="m1", asset="XAUUSD", timeframe="M1",
        event_type=EventType.SMA_CROSSOVER.value, direction=direction,
        timestamp=t, event_price=100.0, context=ctx,
        dataset_source="xauusd_m1_mt5", computation_method="M1_SMA20/100_crossover", seed=42,
    )


def test_m1_contract_and_outcome_engine_agree_on_direction() -> None:
    contract = M1OutcomeContract(horizon_days=1, threshold_return=0.01)
    event = _event("bearish")
    t = event.timestamp
    df = pl.DataFrame({
        "timestamp": [t, t + timedelta(days=1)],
        "open": [100.0, 98.0], "high": [100.0, 99.0],
        "low": [100.0, 97.0], "close": [100.0, 98.0],
    })
    outcome = compute_forward_outcomes([event], df, horizons=[contract.horizon_days], threshold=contract.threshold_return)[0].outcome
    assert outcome is not None
    assert getattr(outcome, contract.label_name) is True
    assert outcome.direction_1d == "down"
