from __future__ import annotations

from researchos.evidence import EvidenceRepository
from researchos.experiments.certified_runner import EvidenceAwareExperimentRunner
from researchos.experiments.contracts import DatasetConfig, MetricDefinition, SimulationConfig
from researchos.experiments.experiment import Experiment


def _experiment() -> Experiment:
    experiment = Experiment(
        hypothesis_id="hyp-certification",
        name="certification-test",
        dataset_config=DatasetConfig(source="synthetic", symbols=["XAUUSD"]),
        simulation_config=SimulationConfig(seed=42),
        metric_definitions=[MetricDefinition(name="sharpe", higher_is_better=True)],
        parameters={"lookback": 20},
    )
    experiment.mark_ready()
    return experiment


def _price_dataset(length: int = 20, base: float = 100.0) -> list[dict[str, float]]:
    return [
        {
            "open": base + i,
            "high": base + i + 1.0,
            "low": base + i - 0.5,
            "close": base + i + 0.25,
            "volume": 1000.0 + i * 10.0,
        }
        for i in range(length)
    ]


def test_evidence_aware_runner_certifies_runtime_chain():
    experiment = _experiment()
    repository = EvidenceRepository()
    runner = EvidenceAwareExperimentRunner(evidence_repository=repository)

    run, result = runner.run(experiment, _price_dataset())

    certification = runner.last_certification
    assert certification is not None
    assert certification.run.payload["run_hash"] == run.run_hash
    assert certification.result.payload["result_hash"] == result.result_hash
    assert repository.count_artifacts() == 3
    assert repository.count_edges() == 2
    assert certification.verify(repository)
