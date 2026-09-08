"""Production readiness gates for Market Memory evidence generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from researchos.market_memory.event_schema import MarketEvent
from researchos.market_memory.temporal_validation import check_temporal_integrity


@dataclass(frozen=True)
class ProductionGateResult:
    """Deterministic gate result; failures must block evidence publication."""

    passed: bool
    issues: tuple[str, ...]
    checked_events: int
    source: str


def check_production_evidence_readiness(
    events: Sequence[MarketEvent],
    *,
    dataset_source: str,
    minimum_events: int = 100,
) -> ProductionGateResult:
    """Validate prerequisites before a research result is treated as evidence.

    Synthetic/demo/mock/fixture sources are never eligible. Event timestamps,
    outcomes, and provenance must be present and temporally coherent.
    """
    issues: list[str] = []
    source = dataset_source.strip().lower()
    blocked_sources = {"synthetic", "demo", "mock", "fixture"}
    if source in blocked_sources:
        issues.append(f"blocked evidence source: {source}")
    if not dataset_source.strip():
        issues.append("dataset_source is required")
    if len(events) < minimum_events:
        issues.append(f"insufficient events: {len(events)} < {minimum_events}")

    temporal = check_temporal_integrity(list(events))
    if temporal["status"] != "PASS":
        issues.extend(str(issue) for issue in temporal["issues"])

    for event in events:
        if event.outcome is None:
            issues.append(f"missing outcome: {event.event_id}")
            continue
        if event.outcome.event_id != event.event_id:
            issues.append(f"outcome/event identity mismatch: {event.event_id}")
        if event.outcome.event_timestamp != event.timestamp:
            issues.append(f"outcome timestamp mismatch: {event.event_id}")
        if not event.dataset_source:
            issues.append(f"missing event provenance: {event.event_id}")

    return ProductionGateResult(
        passed=not issues,
        issues=tuple(issues),
        checked_events=len(events),
        source=dataset_source,
    )


__all__ = ["ProductionGateResult", "check_production_evidence_readiness"]
