from __future__ import annotations

from datetime import datetime, timedelta, timezone

from researchos.market_memory.event_schema import EventOutcome, EventType
from researchos.market_memory.self_audit import run_self_audit
from researchos.market_memory.tests.test_market_memory_v1 import _make_minimal_event


def _with_realized_end(event_id: str, start: datetime, end: datetime):
    event = _make_minimal_event(event_id, "bullish", start)
    outcome = EventOutcome(
        event_id=event_id,
        asset="XAUUSD",
        timeframe="D1",
        event_timestamp=start,
        return_1d=0.01,
        direction_1d="up",
        data_availability={"realized_end_1d": end.isoformat()},
    )
    return event.__class__(
        event_id=event.event_id,
        asset=event.asset,
        timeframe=event.timeframe,
        event_type=EventType.SMA_CROSSOVER.value,
        direction=event.direction,
        timestamp=event.timestamp,
        event_price=event.event_price,
        context=event.context,
        outcome=outcome,
    )


def test_self_audit_uses_realized_label_overlap():
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    events = [
        _with_realized_end("e1", t0, t0 + timedelta(days=2)),
        _with_realized_end("e2", t0 + timedelta(days=1), t0 + timedelta(days=3)),
        _with_realized_end("e3", t0 + timedelta(days=3), t0 + timedelta(days=4)),
    ]

    audit = run_self_audit(
        events,
        label_end_getter=lambda event: datetime.fromisoformat(
            event.outcome.data_availability["realized_end_1d"]
        ),
        multiple_testing_corrected=True,
    )

    assert audit.overlapping_windows == 1
    assert audit.multiple_testing_risk is False
    assert audit.overall_status == "WARNING"


def test_self_audit_reports_missing_realized_end():
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    event = _with_realized_end("e1", t0, t0 + timedelta(days=1))
    event = event.__class__(
        event_id=event.event_id,
        asset=event.asset,
        timeframe=event.timeframe,
        event_type=event.event_type,
        direction=event.direction,
        timestamp=event.timestamp,
        event_price=event.event_price,
        context=event.context,
        outcome=EventOutcome(
            event_id=event.event_id,
            asset=event.asset,
            timeframe=event.timeframe,
            event_timestamp=event.timestamp,
            return_1d=0.01,
        ),
    )

    audit = run_self_audit(
        [event],
        label_end_getter=lambda e: None,
        multiple_testing_corrected=True,
    )

    assert audit.overlapping_windows == 0
    assert any("Missing realized label end timestamps" in item for item in audit.missing_provenance)
    assert audit.overall_status == "WARNING"
