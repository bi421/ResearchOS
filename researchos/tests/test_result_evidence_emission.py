"""Tests for ExperimentResult evidence emission and Run → Result lineage."""
from __future__ import annotations

import pytest

from researchos.evidence.envelope import HASH_SCHEME_VERSION, EvidenceEnvelope, build_envelope
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.result_emission import (
    RESULT_ARTIFACT_TYPE,
    RESULT_EVIDENCE_VERSION,
    RUN_TO_RESULT_RELATION,
    attach_run_parent,
    build_result_envelope,
    emit_result,
    emit_result_for_run,
    result_payload,
)
from researchos.experiments.result import ExperimentResult
from researchos.storage.repository import ResearchRepository


def _make_result(
    run_id="run-1",
    metrics=None,
    statistics=None,
    performance=None,
    metadata=None,
    trace="",
) -> ExperimentResult:
    return ExperimentResult(
        run_id=run_id,
        metrics=metrics or {"sharpe": 1.5, "sortino": 1.2},
        statistics=statistics or {"mean": 0.05, "std": 0.02},
        performance=performance or {"win_rate": 0.6},
        metadata=metadata or {"dataset_version": "abc123"},
        trace=trace,
    )


def _make_result_with_telemetry(time_ms=0.0):
    result = _make_result()
    result.backend_execution_time_ms = time_ms
    result.backend_execution_timestamp = (
        f"2020-01-01T00:00:{int(time_ms) % 60:02d}"
    )
    return result


def _make_repo():
    return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))


def _seed_parent(repo, artifact_type="Run"):
    parent = build_envelope(
        artifact_type,
        {"fixture": artifact_type, "id": "parent"},
        version="1.0.0",
    )
    repo.append_artifact(parent)
    return parent.artifact_hash


class TestResultPayload:
    def test_payload_preserves_content(self):
        p = result_payload(
            _make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1"
        )
        assert p["result_hash"] == _make_result().result_hash
        assert p["run_id"] == "run-1"
        assert p["run_hash"] == "run-hash-1"
        assert p["experiment_hash"] == "exp-hash-1"
        assert p["metrics"]["sharpe"] == 1.5
        assert p["statistics"]["mean"] == 0.05
        assert p["performance"]["win_rate"] == 0.6

    def test_payload_includes_backend_identity(self):
        payload = result_payload(
            _make_result(),
            run_hash="r",
            experiment_hash="e",
            backend_identity={"name": "PythonQuantBackend", "version": "1.0.0"},
        )
        assert payload["backend_identity"]["name"] == "PythonQuantBackend"

    def test_payload_excludes_telemetry(self):
        payload = result_payload(
            _make_result_with_telemetry(123.5), run_hash="r", experiment_hash="e"
        )
        assert all(
            k not in payload
            for k in (
                "backend_execution_time_ms",
                "backend_execution_timestamp",
                "created_at",
            )
        )

    def test_payload_does_not_mutate_result(self):
        r = _make_result()
        h = r.result_hash
        result_payload(r, run_hash="r", experiment_hash="e")
        assert r.result_hash == h


class TestBuildResultEnvelope:
    def test_same_result_same_artifact_hash(self):
        a = build_result_envelope(
            _make_result(), run_hash="r", experiment_hash="e"
        )
        b = build_result_envelope(
            _make_result(), run_hash="r", experiment_hash="e"
        )
        assert a.artifact_hash == b.artifact_hash
        assert a.lineage_hash == b.lineage_hash

    def test_changed_metric_different_artifact_hash(self):
        assert (
            build_result_envelope(
                _make_result(metrics={"sharpe": 1.5}),
                run_hash="r",
                experiment_hash="e",
            ).artifact_hash
            != build_result_envelope(
                _make_result(metrics={"sharpe": 2}),
                run_hash="r",
                experiment_hash="e",
            ).artifact_hash
        )

    def test_changed_statistics_different_artifact_hash(self):
        assert (
            build_result_envelope(
                _make_result(statistics={"mean": 0.05}),
                run_hash="r",
                experiment_hash="e",
            ).artifact_hash
            != build_result_envelope(
                _make_result(statistics={"mean": 0.1}),
                run_hash="r",
                experiment_hash="e",
            ).artifact_hash
        )

    def test_changed_run_hash_different_artifact_hash(self):
        assert (
            build_result_envelope(
                _make_result(), run_hash="r1", experiment_hash="e"
            ).artifact_hash
            != build_result_envelope(
                _make_result(), run_hash="r2", experiment_hash="e"
            ).artifact_hash
        )

    def test_telemetry_does_not_affect_hash(self):
        assert (
            build_result_envelope(
                _make_result_with_telemetry(1), run_hash="r", experiment_hash="e"
            ).artifact_hash
            == build_result_envelope(
                _make_result_with_telemetry(999), run_hash="r", experiment_hash="e"
            ).artifact_hash
        )

    def test_artifact_type_is_result(self):
        assert (
            build_result_envelope(
                _make_result(), run_hash="r", experiment_hash="e"
            ).artifact_type
            == RESULT_ARTIFACT_TYPE
            == "Result"
        )

    def test_scheme_version_is_2(self):
        assert HASH_SCHEME_VERSION == "2"
        assert build_result_envelope(
            _make_result(), run_hash="r", experiment_hash="e"
        ).verify()

    def test_version_binds_into_identity(self):
        assert (
            build_result_envelope(
                _make_result(),
                run_hash="r",
                experiment_hash="e",
                version="1.0.0",
            ).artifact_hash
            != build_result_envelope(
                _make_result(),
                run_hash="r",
                experiment_hash="e",
                version="2.0.0",
            ).artifact_hash
        )

    def test_returns_immutable_envelope(self):
        assert isinstance(
            build_result_envelope(_make_result(), run_hash="r", experiment_hash="e"),
            EvidenceEnvelope,
        )


class TestRunLineage:
    def test_run_parent_preserved(self):
        envelope = build_result_envelope(
            _make_result(),
            run_hash="run-hash-1",
            experiment_hash="e",
            parent_hashes=["run-hash-1"],
        )
        assert "run-hash-1" in envelope.parent_hashes

    def test_attach_run_parent_adds_hash(self):
        base = build_result_envelope(
            _make_result(), run_hash="r", experiment_hash="e"
        )
        linked = attach_run_parent(base, "r")
        assert "r" in linked.parent_hashes
        assert base.parent_hashes == ()

    def test_relation_constant_is_produces(self):
        assert RUN_TO_RESULT_RELATION == "produces"


class TestEmitResult:
    def test_emit_and_retrieve(self):
        repo = _make_repo()
        e = build_result_envelope(_make_result(), run_hash="r", experiment_hash="e")
        emit_result(e, repo)
        assert repo.get_artifact(e.artifact_hash).verify()

    def test_emit_returns_stored_envelope(self):
        repo = _make_repo()
        e = build_result_envelope(_make_result(), run_hash="r", experiment_hash="e")
        stored = emit_result(e, repo)
        assert stored.artifact_hash == e.artifact_hash
        assert repo.count_artifacts() == 1

    def test_emit_rejects_non_result_type(self):
        with pytest.raises(ValueError):
            emit_result(build_envelope("Feature", {"x": 1}), _make_repo())

    def test_emit_default_in_memory_repo(self):
        e = build_result_envelope(_make_result(), run_hash="r", experiment_hash="e")
        assert emit_result(e).artifact_hash == e.artifact_hash


class TestRunResultLineage:
    def test_lineage_edge_run_to_result(self):
        repo = _make_repo()
        run_hash = _seed_parent(repo)
        e = build_result_envelope(
            _make_result(),
            run_hash=run_hash,
            experiment_hash="e",
            parent_hashes=[run_hash],
        )
        emit_result(e, repo)
        assert e.artifact_hash in repo.get_children(run_hash)
        assert run_hash in repo.get_parents(e.artifact_hash)
        assert repo.count_edges() == 1

    def test_emit_result_for_run_links_lineage(self):
        repo = _make_repo()
        run_hash = _seed_parent(repo)
        stored = emit_result_for_run(
            _make_result(), run_hash, repo, experiment_hash="e"
        )
        assert run_hash in stored.parent_hashes
        assert repo.count_edges() == 1
        assert repo.get_children(run_hash) == [stored.artifact_hash]


class TestProgressTracking:
    def test_acceptance_identical_result_identical_hash(self):
        assert (
            build_result_envelope(
                _make_result(), run_hash="r", experiment_hash="e"
            ).artifact_hash
            == build_result_envelope(
                _make_result(), run_hash="r", experiment_hash="e"
            ).artifact_hash
        )

    def test_acceptance_changed_metric_diff_hash(self):
        assert (
            build_result_envelope(
                _make_result(metrics={"sharpe": 1.5}),
                run_hash="r",
                experiment_hash="e",
            ).artifact_hash
            != build_result_envelope(
                _make_result(metrics={"sharpe": 2}),
                run_hash="r",
                experiment_hash="e",
            ).artifact_hash
        )

    def test_acceptance_changed_statistics_diff_hash(self):
        assert (
            build_result_envelope(
                _make_result(statistics={"mean": 0.05}),
                run_hash="r",
                experiment_hash="e",
            ).artifact_hash
            != build_result_envelope(
                _make_result(statistics={"mean": 0.1}),
                run_hash="r",
                experiment_hash="e",
            ).artifact_hash
        )

    def test_acceptance_telemetry_no_effect(self):
        assert (
            build_result_envelope(
                _make_result_with_telemetry(1), run_hash="r", experiment_hash="e"
            ).artifact_hash
            == build_result_envelope(
                _make_result_with_telemetry(500), run_hash="r", experiment_hash="e"
            ).artifact_hash
        )

    def test_acceptance_run_to_result_lineage(self):
        repo = _make_repo()
        run_hash = _seed_parent(repo)
        stored = emit_result_for_run(
            _make_result(), run_hash, repo, experiment_hash="e"
        )
        assert repo.get_children(run_hash) == [stored.artifact_hash]

    def test_acceptance_repository_retrieval(self):
        repo = _make_repo()
        e = build_result_envelope(_make_result(), run_hash="r", experiment_hash="e")
        emit_result(e, repo)
        assert repo.get_artifact(e.artifact_hash) is not None

    def test_acceptance_version_constant(self):
        assert RESULT_EVIDENCE_VERSION == "1.0.0"
