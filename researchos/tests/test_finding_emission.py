from __future__ import annotations

import pytest

from researchos.evidence import (
    EvidenceRepository,
    build_result_envelope,
    certify_finding,
    certify_validation,
    emit_result,
)
from researchos.market_memory.evidence import create_evidence_record
from researchos.quant_engine.validation.contracts import FoldResult, ValidationResult


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


def _seed_result(repository: EvidenceRepository) -> str:
    result = build_result_envelope(
        {"result": "validated-test-result"},
        version="1.0.0",
        created_at="2026-01-01T00:00:00+00:00",
    )
    emit_result(result, repository)
    return result.artifact_hash


def _seed_validation(repository: EvidenceRepository):
    return certify_validation(_validation(), _seed_result(repository), repository)


def test_finding_requires_existing_validation_and_preserves_lineage() -> None:
    repository = EvidenceRepository()
    validation = _seed_validation(repository)
    finding = certify_finding(_finding(), validation.validation_hash, repository)

    assert finding.artifact_type == "Finding"
    assert finding.parent_hashes == (validation.validation_hash,)
    assert repository.get_parents(finding.artifact_hash) == [validation.validation_hash]
    assert repository.get_children(validation.validation_hash) == [finding.artifact_hash]
    assert repository.verify_evidence()


def test_finding_rejects_missing_validation() -> None:
    repository = EvidenceRepository()
    with pytest.raises(ValueError, match="Validation artifact"):
        certify_finding(_finding(), "missing-validation", repository)


def test_finding_identity_excludes_observational_creation_time() -> None:
    repository = EvidenceRepository()
    validation = _seed_validation(repository)
    finding = _finding()

    first = certify_finding(
        finding,
        validation.validation_hash,
        repository,
        created_at="2026-01-01T00:00:00+00:00",
    )
    second = certify_finding(
        finding,
        validation.validation_hash,
        repository,
        created_at="2027-01-01T00:00:00+00:00",
    )

    assert first.artifact_hash == second.artifact_hash
    assert repository.count_artifacts() == 3
