from datetime import datetime, timezone

import polars as pl
import pytest

from researchos.market_memory.event_schema import EventContext, MarketEvent
from researchos.market_memory.oos_validation import assert_label_boundaries
from researchos.market_memory.outcome_engine import compute_forward_outcomes


def _event(timestamp: datetime, event_id: str = "e1") -> MarketEvent:
    context = EventContext(
        event_id=event_id,
        asset="XAUUSD",
        timeframe="M1",
        timestamp=timestamp,
        event_price=100.0,
    )
    return MarketEvent(
        event_id=event_id,
        asset="XAUUSD",
        timeframe="M1",
        event_type="sma_crossover",
        direction="bullish",
        timestamp=timestamp,
        event_price=100.0,
        context=context,
    )


def test_outcome_records_actual_future_observation_timestamp() -> None:
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = datetime(2025, 1, 2, 0, 7, tzinfo=timezone.utc)
    events = [_event(t0)]
    prices = pl.DataFrame(
        {
            "timestamp": [t0, t1],
            "open": [100.0, 101.0],
            "high": [100.5, 102.0],
            "low": [99.5, 100.5],
            "close": [100.0, 101.0],
        }
    )

    result = compute_forward_outcomes(events, prices, horizons=[1])[0]

    assert result.outcome is not None
    assert result.outcome.data_availability["realized_end_1d"] == t1.isoformat()


def test_label_boundary_audit_fails_closed_when_realized_end_is_missing() -> None:
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    v0 = datetime(2025, 1, 3, tzinfo=timezone.utc)
    test0 = datetime(2025, 1, 5, tzinfo=timezone.utc)
    train = [_event(t0)]
    validation = [_event(v0, "e2")]
    test = [_event(test0, "e3")]

    def missing_end(_event: object) -> datetime | None:
        return None

    with pytest.raises(ValueError, match="requires realized end timestamp"):
        assert_label_boundaries(train, validation, test, missing_end)
