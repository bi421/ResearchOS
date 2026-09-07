"""Tests for ExperimentRun evidence emission and Experiment → Run lineage."""
from __future__ import annotations

import datetime
import pytest

from researchos.evidence.envelope import HASH_SCHEME_VERSION, EvidenceEnvelope, build_envelope
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.run_emission import (
    EXPERIMENT_TO_RUN_RELATION, RUN_ARTIFACT_TYPE, RUN_EVIDENCE_VERSION,
    attach_experiment_parent, build_run_envelope, emit_run, emit_run_for_experiment, run_payload,
)
from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.result import ExperimentRun
from researchos.storage.repository import ResearchRepository


def _make_run(experiment_id="exp1", run_number=1, dataset=None, sim=None, params=None, duration=0.0, trace="", status="Completed") -> ExperimentRun:
    run = ExperimentRun(experiment_id=experiment_id, run_number=run_number,
        dataset_config=dataset or DatasetConfig(source="yahoo", symbols=["AAPL"]),
        simulation_config=sim or SimulationConfig(seed=42), parameters=params or {"lookback": 20})
    if status in ("Completed", "Running"):
        run.start(); run.complete(result_id="res-1", result_hash="h-1", duration_seconds=duration, trace=trace)
    return run


def _make_run_with_timing(duration: float = 0.0) -> ExperimentRun:
    run = _make_run(); seconds = int(duration)
    run.started_at = datetime.datetime(2020, 1, 1)
    run.completed_at = datetime.datetime(2020, 1, 1, 0, 0, min(seconds, 59))
    run.duration_seconds = duration
    return run


def _make_repo() -> EvidenceRepository:
    return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))


def _seed_parent(repo: EvidenceRepository, artifact_type: str = "Experiment") -> str:
    parent = build_envelope(artifact_type, {"fixture": artifact_type, "id": "parent"}, version="1.0.0")
    repo.append_artifact(parent)
    return parent.artifact_hash


class TestRunPayload:
    def test_payload_preserves_content(self):
        payload = run_payload(_make_run(), experiment_hash="exp-hash-1")
        assert payload["run_hash"] == _make_run().run_hash
        assert payload["experiment_id"] == "exp1" and payload["experiment_hash"] == "exp-hash-1"
        assert payload["dataset_config"]["source"] == "yahoo" and payload["simulation_config"]["seed"] == 42
        assert payload["parameters"] == {"lookback": 20}
    def test_payload_includes_backend_identity(self):
        assert run_payload(_make_run(), experiment_hash="exp-hash-1", backend_identity={"name":"PythonQuantBackend","version":"1.0.0"})["backend_identity"]["name"] == "PythonQuantBackend"
    def test_payload_excludes_timestamps_and_duration(self):
        p = run_payload(_make_run(duration=12.5), experiment_hash="exp-hash-1")
        assert all(k not in p for k in ("started_at","completed_at","duration_seconds","created_at"))
    def test_payload_does_not_mutate_run(self):
        run = _make_run(); h = run.run_hash; run_payload(run, experiment_hash="exp-hash-1"); assert run.run_hash == h

class TestBuildRunEnvelope:
    def test_same_run_same_artifact_hash(self):
        e1=build_run_envelope(_make_run(),experiment_hash="exp-hash-1"); e2=build_run_envelope(_make_run(),experiment_hash="exp-hash-1"); assert e1.artifact_hash==e2.artifact_hash and e1.lineage_hash==e2.lineage_hash
    def test_changed_params_different_artifact_hash(self):
        assert build_run_envelope(_make_run(params={"lookback":20}),experiment_hash="exp-hash-1").artifact_hash != build_run_envelope(_make_run(params={"lookback":30}),experiment_hash="exp-hash-1").artifact_hash
    def test_changed_dataset_config_different_artifact_hash(self):
        assert build_run_envelope(_make_run(dataset=DatasetConfig(source="yahoo",symbols=["AAPL"])),experiment_hash="exp-hash-1").artifact_hash != build_run_envelope(_make_run(dataset=DatasetConfig(source="google",symbols=["GOOG"])),experiment_hash="exp-hash-1").artifact_hash
    def test_changed_experiment_hash_different_artifact_hash(self):
        assert build_run_envelope(_make_run(),experiment_hash="exp-hash-1").artifact_hash != build_run_envelope(_make_run(),experiment_hash="exp-hash-2").artifact_hash
    def test_runtime_timing_does_not_affect_hash(self):
        assert build_run_envelope(_make_run_with_timing(1),experiment_hash="exp-hash-1").artifact_hash == build_run_envelope(_make_run_with_timing(99),experiment_hash="exp-hash-1").artifact_hash
    def test_artifact_type_is_run(self): assert build_run_envelope(_make_run(),experiment_hash="exp-hash-1").artifact_type==RUN_ARTIFACT_TYPE=="Run"
    def test_scheme_version_is_2(self): assert HASH_SCHEME_VERSION=="2" and build_run_envelope(_make_run(),experiment_hash="exp-hash-1").verify()
    def test_version_binds_into_identity(self): assert build_run_envelope(_make_run(),experiment_hash="exp-hash-1",version="1.0.0").artifact_hash != build_run_envelope(_make_run(),experiment_hash="exp-hash-1",version="2.0.0").artifact_hash
    def test_returns_immutable_envelope(self): assert isinstance(build_run_envelope(_make_run(),experiment_hash="exp-hash-1"),EvidenceEnvelope)

class TestExperimentLineage:
    def test_experiment_parent_preserved(self): assert "exp-hash-1" in build_run_envelope(_make_run(),experiment_hash="exp-hash-1",parent_hashes=["exp-hash-1"]).parent_hashes
    def test_attach_experiment_parent_adds_hash(self):
        base=build_run_envelope(_make_run(),experiment_hash="exp-hash-1"); linked=attach_experiment_parent(base,"exp-hash-1"); assert "exp-hash-1" in linked.parent_hashes and base.parent_hashes==()
    def test_relation_constant_is_executes(self): assert EXPERIMENT_TO_RUN_RELATION=="executes"

class TestEmitRun:
    def test_emit_and_retrieve(self):
        repo=_make_repo(); e=build_run_envelope(_make_run(),experiment_hash="exp-hash-1"); emit_run(e,repo); assert repo.get_artifact(e.artifact_hash).verify()
    def test_emit_returns_stored_envelope(self):
        repo=_make_repo(); e=build_run_envelope(_make_run(),experiment_hash="exp-hash-1"); assert emit_run(e,repo).artifact_hash==e.artifact_hash and repo.count_artifacts()==1
    def test_emit_rejects_non_run_type(self):
        repo=_make_repo();
        with pytest.raises(ValueError): emit_run(build_envelope("Feature",{"x":1}),repo)
    def test_emit_default_in_memory_repo(self):
        e=build_run_envelope(_make_run(),experiment_hash="exp-hash-1"); assert emit_run(e).artifact_hash==e.artifact_hash

class TestExperimentRunLineage:
    def test_lineage_edge_experiment_to_run(self):
        repo=_make_repo(); exp_hash=_seed_parent(repo); e=build_run_envelope(_make_run(),experiment_hash=exp_hash,parent_hashes=[exp_hash]); emit_run(e,repo); assert e.artifact_hash in repo.get_children(exp_hash) and exp_hash in repo.get_parents(e.artifact_hash) and repo.count_edges()==1
    def test_emit_run_for_experiment_links_lineage(self):
        repo=_make_repo(); exp_hash=_seed_parent(repo); stored=emit_run_for_experiment(_make_run(),exp_hash,repo); assert exp_hash in stored.parent_hashes and repo.count_edges()==1 and repo.get_children(exp_hash)==[stored.artifact_hash]

class TestProgressTracking:
    def test_acceptance_identical_runs_identical_hash(self): assert build_run_envelope(_make_run(),experiment_hash="exp-hash-1").artifact_hash==build_run_envelope(_make_run(),experiment_hash="exp-hash-1").artifact_hash
    def test_acceptance_changed_logical_input_diff_hash(self): assert build_run_envelope(_make_run(params={"lookback":20}),experiment_hash="exp-hash-1").artifact_hash!=build_run_envelope(_make_run(params={"lookback":30}),experiment_hash="exp-hash-1").artifact_hash
    def test_acceptance_runtime_timing_no_effect(self): assert build_run_envelope(_make_run_with_timing(1),experiment_hash="exp-hash-1").artifact_hash==build_run_envelope(_make_run_with_timing(500),experiment_hash="exp-hash-1").artifact_hash
    def test_acceptance_experiment_to_run_lineage(self):
        repo=_make_repo(); exp_hash=_seed_parent(repo); stored=emit_run_for_experiment(_make_run(),exp_hash,repo); assert repo.get_children(exp_hash)==[stored.artifact_hash]
    def test_acceptance_repository_retrieval(self):
        repo=_make_repo(); e=build_run_envelope(_make_run(),experiment_hash="exp-hash-1"); emit_run(e,repo); assert repo.get_artifact(e.artifact_hash) is not None
    def test_acceptance_version_constant(self): assert RUN_EVIDENCE_VERSION=="1.0.0"
