"""
Tests for Phase 5.3b.2 — Experiment Evidence Emission.

Covers:
    - ``build_experiment_envelope`` determinism and identity.
    - Payload projection from the existing ``Experiment`` contract:
      experiment_hash, hypothesis identity, dataset references,
      dataset_config snapshot, simulation_config snapshot, methodology/version.
    - Persistence + retrieval via ``EvidenceRepository``.
    - Dataset → Experiment lineage edge wiring.
    - Hash-scheme-2 marker and strict payload contract.

Verification requirements:
    - identical experiment → identical artifact_hash
    - changed config → different artifact_hash
    - dataset linkage preserved
    - artifact retrievable from EvidenceRepository
    - lineage edge Dataset -> Experiment works
"""

from __future__ import annotations

import pytest

from researchos.evidence.envelope import HASH_SCHEME_VERSION, EvidenceEnvelope
from researchos.evidence.experiment_emission import (
    EXPERIMENT_ARTIFACT_TYPE,
    EXPERIMENT_EVIDENCE_VERSION,
    attach_dataset_parent,
    build_experiment_envelope,
    emit_experiment,
    emit_experiment_with_dataset,
    experiment_payload,
)
from researchos.evidence.repository import EvidenceRepository
from researchos.experiments.contracts import (
    DatasetConfig,
    MetricDefinition,
    SimulationConfig,
)
from researchos.experiments.experiment import Experiment
from researchos.storage.repository import ResearchRepository


def _make_experiment(
    hypothesis_id="hyp1",
    name="Exp",
    dataset=None,
    sim=None,
    params=None,
    version="1.0.0",
    status=None,
) -> Experiment:
    dataset = dataset or DatasetConfig(source="yahoo", symbols=["AAPL"])
    sim = sim or SimulationConfig(seed=42)
    exp = Experiment(
        hypothesis_id=hypothesis_id,
        name=name,
        dataset_config=dataset,
        simulation_config=sim,
        metric_definitions=[MetricDefinition(name="sharpe", higher_is_better=True)],
        parameters=params or {"lookback": 20},
        version=version,
    )
    if status is not None:
        exp.mark_ready()
    return exp


def _make_repo() -> EvidenceRepository:
    return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))


class TestExperimentPayload:
    def test_payload_preserves_content(self):
        exp = _make_experiment()
        payload = experiment_payload(exp)
        assert payload["experiment_hash"] == exp.experiment_hash
        assert payload["hypothesis_id"] == "hyp1"
        assert payload["name"] == "Exp"
        assert payload["experiment_type"] == "Backtest"
        assert payload["dataset_config"]["source"] == "yahoo"
        assert payload["simulation_config"]["seed"] == 42
        assert payload["version"] == "1.0.0"
        assert payload["parameters"] == {"lookback": 20}

    def test_payload_excludes_created_at(self):
        exp = _make_experiment()
        payload = experiment_payload(exp)
        assert "created_at" not in payload

    def test_payload_does_not_mutate_experiment(self):
        exp = _make_experiment()
        before_hash = exp.experiment_hash
        before_cfg = exp.dataset_config.to_dict()
        experiment_payload(exp)
        assert exp.experiment_hash == before_hash
        assert exp.dataset_config.to_dict() == before_cfg


class TestBuildExperimentEnvelope:
    def test_same_experiment_same_artifact_hash(self):
        e1 = build_experiment_envelope(_make_experiment())
        e2 = build_experiment_envelope(_make_experiment())
        assert e1.artifact_hash == e2.artifact_hash
        assert e1.lineage_hash == e2.lineage_hash

    def test_changed_dataset_config_different_artifact_hash(self):
        d1 = DatasetConfig(source="yahoo", symbols=["AAPL"])
        d2 = DatasetConfig(source="google", symbols=["GOOG"])
        e1 = build_experiment_envelope(_make_experiment(dataset=d1))
        e2 = build_experiment_envelope(_make_experiment(dataset=d2))
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_sim_config_different_artifact_hash(self):
        s1 = SimulationConfig(seed=42)
        s2 = SimulationConfig(seed=999)
        e1 = build_experiment_envelope(_make_experiment(sim=s1))
        e2 = build_experiment_envelope(_make_experiment(sim=s2))
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_params_different_artifact_hash(self):
        e1 = build_experiment_envelope(_make_experiment(params={"lookback": 20}))
        e2 = build_experiment_envelope(_make_experiment(params={"lookback": 30}))
        assert e1.artifact_hash != e2.artifact_hash

    def test_artifact_type_is_experiment(self):
        e = build_experiment_envelope(_make_experiment())
        assert e.artifact_type == EXPERIMENT_ARTIFACT_TYPE == "Experiment"

    def test_scheme_version_is_2(self):
        assert HASH_SCHEME_VERSION == "2"
        e = build_experiment_envelope(_make_experiment())
        assert e.verify() is True

    def test_version_binds_into_identity(self):
        e1 = build_experiment_envelope(_make_experiment(version="1.0.0"))
        e2 = build_experiment_envelope(_make_experiment(version="2.0.0"))
        assert e1.artifact_hash != e2.artifact_hash

    def test_returns_immutable_envelope(self):
        e = build_experiment_envelope(_make_experiment())
        assert isinstance(e, EvidenceEnvelope)
        assert e.verify() is True


class TestDatasetLineage:
    def test_dataset_parent_preserved(self):
        exp = _make_experiment()
        e = build_experiment_envelope(exp, parent_hashes=["ds-hash-1"])
        assert "ds-hash-1" in e.parent_hashes

    def test_attach_dataset_parent_adds_hash(self):
        exp = _make_experiment()
        base = build_experiment_envelope(exp)
        linked = attach_dataset_parent(base, "ds-hash-1")
        assert "ds-hash-1" in linked.parent_hashes
        # Original envelope unchanged (immutability).
        assert base.parent_hashes == ()

    def test_dataset_parent_preserved_in_payload_linked(self):
        exp = _make_experiment(dataset=DatasetConfig(source="yahoo"))
        base = build_experiment_envelope(exp)
        linked = attach_dataset_parent(base, "ds-hash-1")
        assert linked.payload["dataset_config"]["source"] == "yahoo"
        assert linked.verify() is True


class TestEmitExperiment:
    def test_emit_and_retrieve(self):
        repo = _make_repo()
        e = build_experiment_envelope(_make_experiment())
        emit_experiment(e, repo)
        fetched = repo.get_artifact(e.artifact_hash)
        assert fetched is not None
        assert fetched.artifact_type == "Experiment"
        assert fetched.verify() is True

    def test_emit_returns_stored_envelope(self):
        repo = _make_repo()
        e = build_experiment_envelope(_make_experiment())
        stored = emit_experiment(e, repo)
        assert stored.artifact_hash == e.artifact_hash
        assert repo.count_artifacts() == 1

    def test_emit_rejects_non_experiment_type(self):
        repo = _make_repo()
        from researchos.evidence.envelope import build_envelope

        non_exp = build_envelope("Feature", {"x": 1})
        with pytest.raises(ValueError):
            emit_experiment(non_exp, repo)

    def test_emit_default_in_memory_repo(self):
        e = build_experiment_envelope(_make_experiment())
        stored = emit_experiment(e)
        assert stored.artifact_hash == e.artifact_hash


class TestDatasetExperimentLineage:
    def test_lineage_edge_dataset_to_experiment(self):
        repo = _make_repo()
        ds_hash = "dataset-hash-0001"
        e = build_experiment_envelope(_make_experiment(), parent_hashes=[ds_hash])
        emit_experiment(e, repo)
        children = repo.get_children(ds_hash)
        assert e.artifact_hash in children
        parents = repo.get_parents(e.artifact_hash)
        assert ds_hash in parents

    def test_emit_experiment_with_dataset_links_lineage(self):
        repo = _make_repo()
        ds_hash = "dataset-hash-0002"
        stored = emit_experiment_with_dataset(_make_experiment(), ds_hash, repo)
        assert ds_hash in stored.parent_hashes
        assert repo.count_edges() == 1
        assert repo.get_children(ds_hash) == [stored.artifact_hash]


class TestProgressTracking:
    """Track progress against the Phase 5.3b.2 acceptance criteria."""

    def _make_repo(self) -> EvidenceRepository:
        return _make_repo()

    def test_acceptance_identical_identical_hash(self):
        assert (
            build_experiment_envelope(_make_experiment()).artifact_hash
            == build_experiment_envelope(_make_experiment()).artifact_hash
        )

    def test_acceptance_changed_config_diff_hash(self):
        e1 = build_experiment_envelope(_make_experiment(sim=SimulationConfig(seed=1)))
        e2 = build_experiment_envelope(_make_experiment(sim=SimulationConfig(seed=2)))
        assert e1.artifact_hash != e2.artifact_hash

    def test_acceptance_dataset_linkage_preserved(self):
        exp = _make_experiment(dataset=DatasetConfig(source="yahoo"))
        e = build_experiment_envelope(exp, parent_hashes=["ds-hash-x"])
        assert "ds-hash-x" in e.parent_hashes
        assert e.payload["dataset_config"]["source"] == "yahoo"

    def test_acceptance_retrievable_from_repo(self):
        repo = _make_repo()
        e = build_experiment_envelope(_make_experiment())
        emit_experiment(e, repo)
        assert repo.get_artifact(e.artifact_hash) is not None

    def test_acceptance_dataset_to_experiment_edge(self):
        repo = _make_repo()
        ds_hash = "ds-hash-lineage"
        stored = emit_experiment_with_dataset(_make_experiment(), ds_hash, repo)
        assert repo.get_children(ds_hash) == [stored.artifact_hash]

    def test_acceptance_version_constant(self):
        assert EXPERIMENT_EVIDENCE_VERSION == "1.0.0"
