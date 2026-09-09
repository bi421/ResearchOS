"""Canonical bridge from validated Market Memory evidence to Decision Engine."""

from __future__ import annotations

import ast

from researchos.decision_engine.contracts import DecisionEvidenceItem, EvidenceSource, ProbabilityOutcome
from researchos.decision_engine.evidence import EvidenceCollection
from researchos.decision_engine.probability import ProbabilityAssessment, ProbabilityCalculator
from researchos.market_memory.event_schema import EvidenceRecord, EvidenceStatus, MarketMemoryReport


def _condition_direction(condition_definition: str) -> ProbabilityOutcome:
    """Read an explicit directional condition; unknown conditions are neutral."""
    try:
        value = ast.literal_eval(condition_definition)
    except (ValueError, SyntaxError):
        return ProbabilityOutcome.NEUTRAL
    if not isinstance(value, dict):
        return ProbabilityOutcome.NEUTRAL
    direction = str(value.get("direction", "")).strip().lower()
    if direction == "bullish":
        return ProbabilityOutcome.BULLISH
    if direction == "bearish":
        return ProbabilityOutcome.BEARISH
    return ProbabilityOutcome.NEUTRAL


def _confidence(record: EvidenceRecord, direction: ProbabilityOutcome) -> float:
    """Convert validated empirical outcome probability into directional confidence."""
    probability = record.result.get("raw_probability")
    if not isinstance(probability, (int, float)) or not 0.0 <= float(probability) <= 1.0:
        return 0.0
    p = float(probability)
    if direction is ProbabilityOutcome.BULLISH:
        return p
    if direction is ProbabilityOutcome.BEARISH:
        return 1.0 - p
    return 1.0 - abs(p - 0.5) * 2.0


def _provenance(record: EvidenceRecord) -> dict[str, object]:
    """Extract the immutable Market Memory provenance envelope without mutation."""
    value = record.uncertainty.get("provenance", {})
    return dict(value) if isinstance(value, dict) else {}


def evidence_record_to_decision_item(record: EvidenceRecord) -> DecisionEvidenceItem | None:
    """Convert one validated Market Memory finding into canonical decision evidence."""
    if record.status != EvidenceStatus.VALIDATED.value:
        return None

    direction = _condition_direction(record.condition_definition)
    confidence = _confidence(record, direction)
    return DecisionEvidenceItem(
        source=EvidenceSource.MARKET_MEMORY,
        source_id=record.finding_id,
        direction=direction,
        strength=confidence,
        weight=1.0,
        confidence=confidence,
        description=(
            f"Validated Market Memory finding: {record.finding_name}; "
            f"empirical probability={record.result.get('raw_probability', 'unavailable')}"
        ),
        supporting_ids=[record.finding_id],
        provenance=_provenance(record),
    )


def market_memory_to_decision_evidence(
    report: MarketMemoryReport,
    *,
    directional_only: bool = True,
) -> list[DecisionEvidenceItem]:
    """Bridge a MarketMemoryReport into canonical DecisionEvidenceItem objects."""
    items: list[DecisionEvidenceItem] = []
    for record in report.evidence_records:
        item = evidence_record_to_decision_item(record)
        if item is None:
            continue
        if directional_only and item.direction is ProbabilityOutcome.NEUTRAL:
            continue
        items.append(item)
    return items


def market_memory_to_probability(
    report: MarketMemoryReport,
    *,
    decision_context_id: str,
) -> ProbabilityAssessment:
    """Compute the canonical ProbabilityAssessment directly from Market Memory."""
    items = market_memory_to_decision_evidence(report, directional_only=True)
    collection = EvidenceCollection(decision_context_id=decision_context_id, items=items)
    return ProbabilityCalculator().calculate(collection)


__all__ = ["evidence_record_to_decision_item", "market_memory_to_decision_evidence", "market_memory_to_probability"]
