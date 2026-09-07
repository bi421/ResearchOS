from __future__ import annotations

from researchos.evidence import EvidenceRepository
from researchos.experiments.certified_runner import EvidenceAwareExperimentRunner


def _experiment():
    from researchos.experiments.experiment import Experiment

    return Experiment.create(
        name="certification-test",
        description="runtime evidence certification",
    )


def test_evidence_aware_runner_certifies_runtime_chain():
    experiment = _experiment()
    experiment.mark_ready()
    repository = EvidenceRepository()
    runner = EvidenceAwareExperimentRunner(evidence_repository=repository)

    run, result = runner.run(experiment, [])

    certification = runner.last_certification
    assert certification is not None
    assert certification.run.payload["run_hash"] == run.run_hash
    assert certification.result.payload["result_hash"] == result.result_hash
    assert repository.count_artifacts() == 3
    assert repository.count_edges() == 2
    assert certification.verify(repository)
