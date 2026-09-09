from __future__ import annotations

from researchos.decision_engine.contracts import ProbabilityOutcome
from researchos.market_memory.decision_adapter import market_memory_to_decision_evidence
from researchos.market_memory.event_schema import EvidenceRecord, EvidenceStatus, MarketMemoryReport


def _record(name: str, condition: str, probability: float, status: str = EvidenceStatus.VALIDATED.value, uncertainty: dict | None = None) -> EvidenceRecord:
    return EvidenceRecord(
        finding_id=f"EVIDENCE|{name}",
        finding_name=name,
        dataset_id="xauusd-d1",
        dataset_version="v1",
        event_definition="SMA20/100 crossover",
        condition_definition=condition,
        sample_size=1000,
        time_range=("2021-01-01T00:00:00+00:00", "2025-12-31T00:00:00+00:00"),
        computation_method="forward_return_analysis",
        code_module="test",
        statistical_method="wilson",
        result={"raw_probability": probability},
        uncertainty=uncertainty or {},
        status=status,
    )


def _report(*records: EvidenceRecord) -> MarketMemoryReport:
    return MarketMemoryReport(
        report_id="MMR|XAUUSD|D1|test",
        asset="XAUUSD",
        timeframe="D1",
        event_type="sma_crossover",
        evidence_records=list(records),
    )


def test_validated_directional_market_memory_reaches_decision_evidence() -> None:
    report = _report(
        _record("bullish_crossover", "{'direction':'bullish'}", 0.70),
        _record("bearish_crossover", "{'direction':'bearish'}", 0.30),
    )
    items = market_memory_to_decision_evidence(report)
    assert len(items) == 2
    assert {item.direction for item in items} == {ProbabilityOutcome.BULLISH, ProbabilityOutcome.BEARISH}
    bullish = next(i for i in items if i.direction is ProbabilityOutcome.BULLISH)
    bearish = next(i for i in items if i.direction is ProbabilityOutcome.BEARISH)
    assert bullish.confidence == 0.70
    assert bearish.confidence == 0.70
    assert all(item.weight == 1.0 for item in items)


def test_nonvalidated_and_neutral_findings_do_not_enter_directional_bridge() -> None:
    report = _report(
        _record("bullish_crossover", "{'direction':'bullish'}", 0.70, EvidenceStatus.UNVALIDATED.value),
        _record("all_crossovers", "{}", 0.55, EvidenceStatus.VALIDATED.value),
    )
    assert market_memory_to_decision_evidence(report) == []


def test_market_memory_provenance_is_preserved_in_decision_evidence() -> None:
    provenance = {
        "algorithm": "sha256",
        "evidence_computation_digest": "digest-123",
        "dataset_version_bound": "canonical-dataset-hash",
        "dataset_identity": {
            "dataset_id": "xauusd-d1",
            "dataset_content_hash": "content-123",
            "dataset_hash": "canonical-dataset-hash",
        },
    }
    item = market_memory_to_decision_evidence(
        _report(_record("bullish_crossover", "{'direction':'bullish'}", 0.70, uncertainty={"provenance": provenance}))
    )[0]
    assert item.provenance == provenance
    assert item.to_dict()["provenance"] == provenance
    restored = type(item).from_dict(item.to_dict())
    assert restored.provenance == provenance


def test_probability_calculator_consumes_market_memory_items() -> None:
    report = _report(
        _record("bullish_crossover", "{'direction':'bullish'}", 0.80),
        _record("bearish_crossover", "{'direction':'bearish'}", 0.40),
    )
    items = market_memory_to_decision_evidence(report)
    from researchos.decision_engine.evidence import EvidenceCollection
    from researchos.decision_engine.probability import ProbabilityCalculator
    collection = EvidenceCollection(decision_context_id="ctx-1", items=items)
    assessment = ProbabilityCalculator().calculate(collection)
    assert assessment.bullish_probability > assessment.bearish_probability
    assert assessment.bullish_probability + assessment.bearish_probability + assessment.neutral_probability == 1.0
