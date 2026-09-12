from __future__ import annotations

from types import SimpleNamespace

import pytest

from researchos.evidence.envelope import build_envelope
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.runtime_certification import certify_runtime


def _dataset(source: str = "real_market") -> SimpleNamespace:
    return SimpleNamespace(
        feature_names=["x"],
        features=[[0.1], [0.2]],
        labels=[0.0, 1.0],
        metadata={"data_classification": source},
        sample_count=2,
        feature_count=1,
        label_name="outcome",
        version="1.0.0",
        source=source,
    )


def _experiment(source: str = "real_market") -> SimpleNamespace:
    return SimpleNamespace(
        experiment_hash="experiment-definition-hash",
        hypothesis_id="hypothesis-1",
        name="Certification test",
        description="Runtime certification",
        experiment_type="backtest",
        dataset_config=SimpleNamespace(
            source=source,
            parameters={"data_classification": source},
            to_dict=lambda: {"source": source},
        ),
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
        dataset_config=SimpleNamespace(to_dict=lambda: {"source": "real_market"}),
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


def test_certify_runtime_creates_and_verifies_four_node_chain() -> None:
    repo = EvidenceRepository()
    certification = certify_runtime(
        _experiment(),
        _run(),
        _result(),
        repo,
        dataset=_dataset(),
        backend_identity={"name": "python", "version": "1"},
    )

    assert certification.verify(repo)
    assert repo.count_artifacts() == 4
    assert repo.count_edges() == 3
    assert repo.get_children(certification.dataset_hash) == [certification.experiment_hash]
    assert repo.get_children(certification.experiment_hash) == [certification.run_hash]
    assert repo.get_children(certification.run_hash) == [certification.result_hash]


def test_certify_runtime_requires_dataset_parent() -> None:
    repo = EvidenceRepository()
    with pytest.raises(ValueError, match="requires a Dataset evidence parent"):
        certify_runtime(_experiment(), _run(), _result(), repo)


def test_certify_runtime_rejects_fixture_before_any_write() -> None:
    repo = EvidenceRepository()
    with pytest.raises(ValueError, match="cannot be certified"):
        certify_runtime(
            _experiment("fixture"),
            _run(),
            _result(),
            repo,
            dataset=_dataset("fixture"),
        )
    assert repo.count_artifacts() == 0
    assert repo.count_edges() == 0


def test_certify_runtime_rejects_synthetic_dataset_before_any_write() -> None:
    repo = EvidenceRepository()
    with pytest.raises(ValueError, match="cannot be certified"):
        certify_runtime(
            _experiment(),
            _run(),
            _result(),
            repo,
            dataset=_dataset("synthetic"),
        )
    assert repo.count_artifacts() == 0


def test_certify_runtime_accepts_existing_dataset_parent() -> None:
    repo = EvidenceRepository()
    dataset = build_envelope("Dataset", {"name": "real-market"})
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


def test_artifact_identity_excludes_created_at() -> None:
    first = build_envelope("Dataset", {"name": "real-market"}, created_at="2026-01-01T00:00:00Z")
    second = build_envelope("Dataset", {"name": "real-market"}, created_at="2036-01-01T00:00:00Z")
    assert first.artifact_hash == second.artifact_hash
    assert first.lineage_hash == second.lineage_hash
