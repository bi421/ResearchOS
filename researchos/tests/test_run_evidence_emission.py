"""
Tests for Phase 5.3b.3 — ExperimentRun Evidence Emission.

Covers:
    - ``build_run_envelope`` determinism and identity.
    - Payload projection from the ``ExperimentRun`` contract: run_hash,
      experiment_id, experiment_hash reference, parameters snapshot,
      dataset_config snapshot, simulation_config snapshot, backend identity
      metadata, deterministic run metadata.
    - Excludes wall-clock telemetry / runtime duration from identity.
    - Persistence + retrieval via ``EvidenceRepository``.
    - Experiment → Run lineage edge (relation "executes").

Verification requirements:
    - identical runs → identical artifact_hash
    - changed logical input → different artifact_hash
    - runtime timing does NOT affect hash
    - Experiment -> Run lineage works
    - repository retrieval works
"""

from __future__ import annotations

import datetime

import pytest

from researchos.evidence.envelope import HASH_SCHEME_VERSION, EvidenceEnvelope
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.run_emission import (
    EXPERIMENT_TO_RUN_RELATION,
    RUN_ARTIFACT_TYPE,
    RUN_EVIDENCE_VERSION,
    attach_experiment_parent,
    build_run_envelope,
    emit_run,
    emit_run_for_experiment,
    run_payload,
)
from researchos.experiments.contracts import (
    DatasetConfig,
    SimulationConfig,
)
from researchos.experiments.result import ExperimentRun
from researchos.storage.repository import ResearchRepository


def _make_run(
    experiment_id="exp1",
    run_number=1,
    dataset=None,
    sim=None,
    params=None,
    duration=0.0,
    trace="",
    status="Completed",
) -> ExperimentRun:
    dataset = dataset or DatasetConfig(source="yahoo", symbols=["AAPL"])
    sim = sim or SimulationConfig(seed=42)
    run = ExperimentRun(
        experiment_id=experiment_id,
        run_number=run_number,
        dataset_config=dataset,
        simulation_config=sim,
        parameters=params or {"lookback": 20},
    )
    if status in ("Completed", "Running"):
        run.start()
        run.complete(
            result_id="res-1",
            result_hash="h-1",
            duration_seconds=duration,
            trace=trace,
        )
    return run


def _make_run_with_timing(duration: float = 0.0) -> ExperimentRun:
    """Build a completed run, then mutate ONLY the observational timing
    attributes (started_at / completed_at / duration_seconds) directly so the
    deterministic ``run_hash`` is unchanged.  This isolates the runtime-timing
    independence of the evidence hash: the payload reads ``run_hash`` (a
    logical identity) and never the timing attributes.
    """
    run = _make_run()
    seconds = int(duration)
    run.started_at = datetime.datetime(2020, 1, 1)
    # Distinct completed_at timestamp and distinct duration_seconds.  Both are
    # observational and must not affect the evidence artifact_hash.
    run.completed_at = datetime.datetime(2020, 1, 1, 0, 0, min(seconds, 59))
    run.duration_seconds = duration
    return run


def _make_repo() -> EvidenceRepository:
    return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))


class TestRunPayload:
    def test_payload_preserves_content(self):
        run = _make_run()
        payload = run_payload(run, experiment_hash="exp-hash-1")
        assert payload["run_hash"] == run.run_hash
        assert payload["experiment_id"] == "exp1"
        assert payload["experiment_hash"] == "exp-hash-1"
        assert payload["dataset_config"]["source"] == "yahoo"
        assert payload["simulation_config"]["seed"] == 42
        assert payload["parameters"] == {"lookback": 20}

    def test_payload_includes_backend_identity(self):
        run = _make_run()
        payload = run_payload(
            run,
            experiment_hash="exp-hash-1",
            backend_identity={"name": "PythonQuantBackend", "version": "1.0.0"},
        )
        assert payload["backend_identity"] == {
            "name": "PythonQuantBackend",
            "version": "1.0.0",
        }

    def test_payload_excludes_timestamps_and_duration(self):
        run = _make_run(duration=12.5)
        payload = run_payload(run, experiment_hash="exp-hash-1")
        assert "started_at" not in payload
        assert "completed_at" not in payload
        assert "duration_seconds" not in payload
        assert "created_at" not in payload

    def test_payload_does_not_mutate_run(self):
        run = _make_run()
        before_hash = run.run_hash
        before_cfg = run.dataset_config.to_dict()
        run_payload(run, experiment_hash="exp-hash-1")
        assert run.run_hash == before_hash
        assert run.dataset_config.to_dict() == before_cfg


class TestBuildRunEnvelope:
    def test_same_run_same_artifact_hash(self):
        e1 = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        e2 = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        assert e1.artifact_hash == e2.artifact_hash
        assert e1.lineage_hash == e2.lineage_hash

    def test_changed_params_different_artifact_hash(self):
        r1 = _make_run(params={"lookback": 20})
        r2 = _make_run(params={"lookback": 30})
        e1 = build_run_envelope(r1, experiment_hash="exp-hash-1")
        e2 = build_run_envelope(r2, experiment_hash="exp-hash-1")
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_dataset_config_different_artifact_hash(self):
        d1 = DatasetConfig(source="yahoo", symbols=["AAPL"])
        d2 = DatasetConfig(source="google", symbols=["GOOG"])
        e1 = build_run_envelope(
            _make_run(dataset=d1), experiment_hash="exp-hash-1"
        )
        e2 = build_run_envelope(
            _make_run(dataset=d2), experiment_hash="exp-hash-1"
        )
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_experiment_hash_different_artifact_hash(self):
        e1 = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        e2 = build_run_envelope(_make_run(), experiment_hash="exp-hash-2")
        assert e1.artifact_hash != e2.artifact_hash

    def test_runtime_timing_does_not_affect_hash(self):
        # Same logical run, different runtime duration → same artifact hash.
        r1 = _make_run_with_timing(duration=1.0)
        r2 = _make_run_with_timing(duration=99.0)
        e1 = build_run_envelope(r1, experiment_hash="exp-hash-1")
        e2 = build_run_envelope(r2, experiment_hash="exp-hash-1")
        assert e1.artifact_hash == e2.artifact_hash

    def test_artifact_type_is_run(self):
        e = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        assert e.artifact_type == RUN_ARTIFACT_TYPE == "Run"

    def test_scheme_version_is_2(self):
        assert HASH_SCHEME_VERSION == "2"
        e = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        assert e.verify() is True

    def test_version_binds_into_identity(self):
        e1 = build_run_envelope(
            _make_run(), experiment_hash="exp-hash-1", version="1.0.0"
        )
        e2 = build_run_envelope(
            _make_run(), experiment_hash="exp-hash-1", version="2.0.0"
        )
        assert e1.artifact_hash != e2.artifact_hash

    def test_returns_immutable_envelope(self):
        e = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        assert isinstance(e, EvidenceEnvelope)
        assert e.verify() is True


class TestExperimentLineage:
    def test_experiment_parent_preserved(self):
        e = build_run_envelope(
            _make_run(), experiment_hash="exp-hash-1",
            parent_hashes=["exp-hash-1"],
        )
        assert "exp-hash-1" in e.parent_hashes

    def test_attach_experiment_parent_adds_hash(self):
        base = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        linked = attach_experiment_parent(base, "exp-hash-1")
        assert "exp-hash-1" in linked.parent_hashes
        # Original envelope unchanged (immutability).
        assert base.parent_hashes == ()

    def test_relation_constant_is_executes(self):
        assert EXPERIMENT_TO_RUN_RELATION == "executes"


class TestEmitRun:
    def test_emit_and_retrieve(self):
        repo = _make_repo()
        e = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        emit_run(e, repo)
        fetched = repo.get_artifact(e.artifact_hash)
        assert fetched is not None
        assert fetched.artifact_type == "Run"
        assert fetched.verify() is True

    def test_emit_returns_stored_envelope(self):
        repo = _make_repo()
        e = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        stored = emit_run(e, repo)
        assert stored.artifact_hash == e.artifact_hash
        assert repo.count_artifacts() == 1

    def test_emit_rejects_non_run_type(self):
        repo = _make_repo()
        from researchos.evidence.envelope import build_envelope

        non_run = build_envelope("Feature", {"x": 1})
        with pytest.raises(ValueError):
            emit_run(non_run, repo)

    def test_emit_default_in_memory_repo(self):
        e = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        stored = emit_run(e)
        assert stored.artifact_hash == e.artifact_hash


class TestExperimentRunLineage:
    def test_lineage_edge_experiment_to_run(self):
        repo = _make_repo()
        exp_hash = "exp-hash-0001"
        e = build_run_envelope(
            _make_run(), experiment_hash=exp_hash, parent_hashes=[exp_hash]
        )
        emit_run(e, repo)
        children = repo.get_children(exp_hash)
        assert e.artifact_hash in children
        parents = repo.get_parents(e.artifact_hash)
        assert exp_hash in parents
        # Relation "executes"
        assert repo.count_edges() == 1

    def test_emit_run_for_experiment_links_lineage(self):
        repo = _make_repo()
        exp_hash = "exp-hash-0002"
        stored = emit_run_for_experiment(_make_run(), exp_hash, repo)
        assert exp_hash in stored.parent_hashes
        assert repo.count_edges() == 1
        assert repo.get_children(exp_hash) == [stored.artifact_hash]


class TestProgressTracking:
    """Track progress against the Phase 5.3b.3 acceptance criteria."""

    def _make_repo(self) -> EvidenceRepository:
        return _make_repo()

    def test_acceptance_identical_runs_identical_hash(self):
        assert (
            build_run_envelope(
                _make_run(), experiment_hash="exp-hash-1"
            ).artifact_hash
            == build_run_envelope(
                _make_run(), experiment_hash="exp-hash-1"
            ).artifact_hash
        )

    def test_acceptance_changed_logical_input_diff_hash(self):
        e1 = build_run_envelope(
            _make_run(params={"lookback": 20}), experiment_hash="exp-hash-1"
        )
        e2 = build_run_envelope(
            _make_run(params={"lookback": 30}), experiment_hash="exp-hash-1"
        )
        assert e1.artifact_hash != e2.artifact_hash

    def test_acceptance_runtime_timing_no_effect(self):
        r1 = _make_run_with_timing(duration=1.0)
        r2 = _make_run_with_timing(duration=500.0)
        assert (
            build_run_envelope(r1, experiment_hash="exp-hash-1").artifact_hash
            == build_run_envelope(r2, experiment_hash="exp-hash-1").artifact_hash
        )

    def test_acceptance_experiment_to_run_lineage(self):
        repo = _make_repo()
        exp_hash = "exp-hash-lineage"
        stored = emit_run_for_experiment(_make_run(), exp_hash, repo)
        assert repo.get_children(exp_hash) == [stored.artifact_hash]

    def test_acceptance_repository_retrieval(self):
        repo = _make_repo()
        e = build_run_envelope(_make_run(), experiment_hash="exp-hash-1")
        emit_run(e, repo)
        assert repo.get_artifact(e.artifact_hash) is not None

    def test_acceptance_version_constant(self):
        assert RUN_EVIDENCE_VERSION == "1.0.0"
