from __future__ import annotations

import pytest

from researchos.evidence import EvidenceRepository
from researchos.experiments.certified_runner import EvidenceAwareExperimentRunner
from researchos.experiments.contracts import DatasetConfig, MetricDefinition, SimulationConfig
from researchos.experiments.experiment import Experiment
from researchos.quant_engine.machine_learning.dataset_contracts import ResearchDataset


def _experiment(source: str = "real_market") -> Experiment:
    experiment = Experiment(
        hypothesis_id="hyp-certification",
        name="certification-test",
        dataset_config=DatasetConfig(
            source=source,
            symbols=["XAUUSD"],
            parameters={"data_classification": source},
        ),
        simulation_config=SimulationConfig(seed=42),
        metric_definitions=[MetricDefinition(name="sharpe", higher_is_better=True)],
        parameters={"lookback": 20},
    )
    experiment.mark_ready()
    return experiment


def _price_dataset(length: int = 20, base: float = 100.0) -> ResearchDataset:
    features = tuple((base + i, base + i + 0.25) for i in range(length))
    labels = tuple(float(1 if i % 2 == 0 else -1) for i in range(length))
    return ResearchDataset(
        feature_names=("open", "close"),
        features=features,
        labels=labels,
        metadata={"data_classification": "real_market", "source": "real_market"},
        sample_count=length,
        feature_count=2,
        label_name="outcome",
        version="1.0.0",
    )


def test_evidence_aware_runner_certifies_runtime_chain():
    experiment = _experiment()
    repository = EvidenceRepository()
    runner = EvidenceAwareExperimentRunner(evidence_repository=repository)

    run, result = runner.run(experiment, _price_dataset())

    certification = runner.last_certification
    assert certification is not None
    assert certification.run.payload["run_hash"] == run.run_hash
    assert certification.result.payload["result_hash"] == result.result_hash
    assert repository.count_artifacts() == 4
    assert repository.count_edges() == 3
    assert certification.verify(repository)


def test_evidence_certification_rejects_synthetic_source_before_write():
    experiment = _experiment(source="synthetic")
    repository = EvidenceRepository()
    runner = EvidenceAwareExperimentRunner(evidence_repository=repository)

    with pytest.raises(ValueError, match="cannot be certified as research evidence"):
        runner.run(experiment, _price_dataset())

    assert repository.count_artifacts() == 0
    assert repository.count_edges() == 0


def test_evidence_certification_rejects_explicit_synthetic_classification():
    experiment = _experiment()
    experiment.dataset_config.parameters["data_classification"] = "synthetic"
    repository = EvidenceRepository()
    runner = EvidenceAwareExperimentRunner(evidence_repository=repository)

    with pytest.raises(ValueError, match="cannot be certified as research evidence"):
        runner.run(experiment, _price_dataset())

    assert repository.count_artifacts() == 0
    assert repository.count_edges() == 0
