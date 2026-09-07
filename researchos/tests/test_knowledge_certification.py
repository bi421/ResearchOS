from __future__ import annotations

import pytest

from researchos.evidence import (
    EvidenceRepository,
    KnowledgeCertification,
    build_result_envelope,
    certify_finding,
    certify_knowledge,
    emit_result,
)
from researchos.evidence.validation_certification import certify_validation
from researchos.market_memory.evidence import create_evidence_record
from researchos.objects.knowledge import Knowledge
from researchos.quant_engine.validation.contracts import FoldResult, ValidationResult
from researchos.storage.repository import ResearchRepository


def _validation() -> ValidationResult:
    return ValidationResult(
        train_size=10,
        validation_size=5,
        test_size=5,
        fold_count=1,
        fold_results=(FoldResult(1, (0, 9), (10, 14), {"accuracy": 0.8}, 5),),
        metrics={"mean_accuracy": 0.8},
        metadata={"method": "walk_forward"},
    )


def _finding():
    return create_evidence_record(
        finding_name="bullish_crossover",
        dataset_id="xauusd-test",
        dataset_version="sha256:test",
        event_definition="SMA20 crosses above SMA100",
        condition_definition="bullish crossover",
        sample_size=100,
        time_range=("2024-01-01", "2024-06-30"),
        computation_method="deterministic conditional analysis",
        code_module="researchos.market_memory",
        statistical_method="bootstrap",
        result={"probability_1d": 0.61},
        uncertainty={"ci95": [0.55, 0.67]},
        validation_method="walk_forward",
        status="VALIDATED",
    )


def _seed_finding() -> tuple[EvidenceRepository, str]:
    repository = EvidenceRepository()
    result = build_result_envelope(
        {"result": "validated-test-result"},
        version="1.0.0",
        created_at="2026-01-01T00:00:00+00:00",
    )
    emit_result(result, repository)
    validation = certify_validation(_validation(), result.artifact_hash, repository)
    finding = certify_finding(_finding(), validation.validation_hash, repository)
    return repository, finding.artifact_hash


def _knowledge() -> Knowledge:
    return Knowledge(
        type="Event_Impact",
        subject="XAUUSD",
        predicate="has_observed_probability",
        object="bullish crossover -> 1d positive return",
        confidence=0.61,
        knowledge_trace="Derived from validated historical finding",
    )


def test_validated_finding_enters_durable_knowledge_memory() -> None:
    evidence_repository, finding_hash = _seed_finding()

    with ResearchRepository(":memory:") as research_repository:
        certification = certify_knowledge(
            finding_hash,
            _knowledge(),
            evidence_repository,
            research_repository,
        )

        assert isinstance(certification, KnowledgeCertification)
        assert certification.finding_hash == finding_hash
        assert certification.knowledge.source_references == [finding_hash]
        assert research_repository.load_by_id(certification.knowledge_id) is not None
        assert certification.verify(evidence_repository, research_repository)


def test_knowledge_rejects_missing_finding() -> None:
    evidence_repository = EvidenceRepository()

    with ResearchRepository(":memory:") as research_repository:
        with pytest.raises(ValueError, match="Finding artifact not found"):
            certify_knowledge(
                "missing-finding",
                _knowledge(),
                evidence_repository,
                research_repository,
            )


def test_knowledge_rejects_non_finding_source() -> None:
    evidence_repository = EvidenceRepository()
    result = build_result_envelope(
        {"result": "not-a-finding"},
        version="1.0.0",
        created_at="2026-01-01T00:00:00+00:00",
    )
    emit_result(result, evidence_repository)

    with ResearchRepository(":memory:") as research_repository:
        with pytest.raises(ValueError, match="must be a Finding artifact"):
            certify_knowledge(
                result.artifact_hash,
                _knowledge(),
                evidence_repository,
                research_repository,
            )
