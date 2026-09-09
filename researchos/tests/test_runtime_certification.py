from __future__ import annotations

from types import SimpleNamespace

import pytest

from researchos.evidence.envelope import build_envelope
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.runtime_certification import certify_runtime


def _experiment(source: str = "mt5") -> SimpleNamespace:
    return SimpleNamespace(
        experiment_hash="experiment-definition-hash",
        hypothesis_id="hypothesis-1",
        name="Certification test",
        description="Runtime certification",
        experiment_type="backtest",
        dataset_config=SimpleNamespace(to_dict=lambda: {"source": source}),
        simulation_config=SimpleNamespace(to_dict=lambda: {"seed": 42}),
        metric_definitions=[],
        parameters={"window": 20},
        version="1.0.0",
        tags=["test"],
        experiment_trace="",
        status="Ready",
        ontology_tags=[],
    )


def _run() -> SimpleNamespace:
    return SimpleNamespace(
        run_hash="run-definition-hash",
        experiment_id="experiment-1",
        run_number=1,
        dataset_config=SimpleNamespace(to_dict=lambda: {"source": "mt5"}),
        simulation_config=SimpleNamespace(to_dict=lambda: {"seed": 42}),
        parameters={},
        status="Completed",
        trace="completed",
        tags=[],
        ontology_tags=[],
    )


def _result() -> SimpleNamespace:
    return SimpleNamespace(
        result_hash="result-definition-hash",
        run_id="run-1",
        metrics={"return": 0.12},
        statistics={"sample_size": 100},
        performance={},
        metadata={"deterministic": True},
        trace="completed",
        ontology_tags=[],
    )


def test_certify_runtime_creates_and_verifies_three_node_chain() -> None:
    repo = EvidenceRepository()
    certification = certify_runtime(
        _experiment(),
        _run(),
        _result(),
        repo,
        backend_identity={"name": "python", "version": "1"},
    )

    assert certification.verify(repo)
    assert repo.count_artifacts() == 3
    assert repo.count_edges() == 2
    assert repo.get_children(certification.experiment_hash) == [certification.run_hash]
    assert repo.get_children(certification.run_hash) == [certification.result_hash]


def test_certify_runtime_rejects_synthetic_source_before_writes() -> None:
    repo = EvidenceRepository()
    with pytest.raises(ValueError, match="Synthetic"):
        certify_runtime(_experiment("fixture"), _run(), _result(), repo)
    assert repo.count_artifacts() == 0
    assert repo.count_edges() == 0


def test_certify_runtime_requires_existing_dataset_parent() -> None:
    repo = EvidenceRepository()
    with pytest.raises(ValueError, match="does not exist"):
        certify_runtime(
            _experiment(),
            _run(),
            _result(),
            repo,
            dataset_hash="missing-dataset",
        )


def test_certify_runtime_accepts_existing_dataset_parent() -> None:
    repo = EvidenceRepository()
    dataset = build_envelope("Dataset", {"name": "fixture"})
    repo.append_artifact(dataset)

    certification = certify_runtime(
        _experiment(),
        _run(),
        _result(),
        repo,
        dataset_hash=dataset.artifact_hash,
    )

    assert certification.verify(repo)
    assert repo.count_artifacts() == 4
    assert repo.count_edges() == 3
    assert certification.experiment_hash in repo.get_children(dataset.artifact_hash)
