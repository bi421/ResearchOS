from __future__ import annotations

import pytest

from researchos.evidence import EvidenceRepository, ValidationCertification, certify_runtime, certify_validation
from researchos.experiments.experiment import Experiment
from researchos.quant_engine.validation.contracts import FoldResult, ValidationResult


def _experiment() -> Experiment:
    experiment = Experiment.create(
        name="validation-certification-test",
        description="Result to Validation evidence boundary",
    )
    experiment.mark_ready()
    return experiment


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


def test_validation_certification_extends_runtime_chain() -> None:
    repository = EvidenceRepository()
    experiment = _experiment()
    run, result = __import__("researchos.experiments.runner", fromlist=["BaseExperimentRunner"]).BaseExperimentRunner().run(
        experiment,
        [],
    )
    runtime = certify_runtime(experiment, run, result, repository)

    certification = certify_validation(
        _validation(),
        runtime.result_hash,
        repository,
        run_hash=runtime.run_hash,
        experiment_hash=runtime.experiment_hash,
        method="walk_forward",
    )

    assert isinstance(certification, ValidationCertification)
    assert certification.verify(repository)
    assert repository.count_artifacts() == 4
    assert repository.count_edges() == 3
    assert certification.validation.parent_hashes == (runtime.result_hash,)


def test_validation_certification_rejects_missing_result() -> None:
    repository = EvidenceRepository()
    with pytest.raises(ValueError, match="does not exist"):
        certify_validation(_validation(), "missing-result", repository)
