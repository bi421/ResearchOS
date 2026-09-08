from datetime import datetime, timedelta, timezone

import pytest

from researchos.market_memory.label_dependence import audit_label_overlap


class Event:
    def __init__(self, timestamp: datetime) -> None:
        self.timestamp = timestamp


def test_overlap_audit_counts_intersecting_windows() -> None:
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    events = [Event(t0), Event(t0 + timedelta(hours=12)), Event(t0 + timedelta(days=2))]
    audit = audit_label_overlap(
        events,
        lambda event: event.timestamp + timedelta(days=1),
    )
    assert audit.overlap_pairs == 1
    assert audit.max_concurrent_labels == 2
    assert audit.passed


def test_overlap_audit_does_not_count_shared_boundary() -> None:
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    events = [Event(t0), Event(t0 + timedelta(days=1))]
    audit = audit_label_overlap(events, lambda event: event.timestamp + timedelta(days=1))
    assert audit.overlap_pairs == 0
    assert audit.max_concurrent_labels == 1


def test_overlap_audit_requires_realized_end() -> None:
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    audit = audit_label_overlap([Event(t0)], lambda _event: None)
    assert audit.missing_realized_end == 1
    assert not audit.passed


def test_overlap_audit_rejects_invalid_interval() -> None:
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="must be after"):
        audit_label_overlap([Event(t0)], lambda event: event.timestamp)
