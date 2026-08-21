"""
Tests for Phase 5.3b.4 — ExperimentResult Evidence Emission.

Covers:
    - ``build_result_envelope`` determinism and identity.
    - Payload projection from the ``ExperimentResult`` contract: result_hash,
      run_id, run_hash reference, experiment reference, metrics, statistics,
      performance metadata (deterministic fields only), result metadata,
      backend identity metadata.
    - Excludes timestamps / runtime telemetry / execution timing from identity.
    - Persistence + retrieval via ``EvidenceRepository``.
    - Run → Result lineage edge (relation "produces").

Verification requirements:
    - identical result → identical artifact_hash
    - changed metric → different artifact_hash
    - changed statistics → different artifact_hash
    - telemetry does NOT affect hash
    - Run -> Result lineage works
    - repository retrieval works
"""

from __future__ import annotations

import pytest

from researchos.evidence.envelope import HASH_SCHEME_VERSION, EvidenceEnvelope
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
    result = ExperimentResult(
        run_id=run_id,
        metrics=metrics or {"sharpe": 1.5, "sortino": 1.2},
        statistics=statistics or {"mean": 0.05, "std": 0.02},
        performance=performance or {"win_rate": 0.6},
        metadata=metadata or {"dataset_version": "abc123"},
        trace=trace,
    )
    return result


def _make_result_with_telemetry(time_ms: float = 0.0) -> ExperimentResult:
    """Build a result, then mutate ONLY the observational telemetry fields
    (backend_execution_time_ms / backend_execution_timestamp) directly.  These
    are not part of ``ExperimentResult._to_hashable_dict``, so the
    deterministic ``result_hash`` is unchanged.  This isolates the telemetry
    independence of the evidence hash: the payload reads ``result_hash`` (a
    content identity) and never the telemetry.
    """
    result = _make_result()
    result.backend_execution_time_ms = time_ms
    result.backend_execution_timestamp = f"2020-01-01T00:00:{int(time_ms) % 60:02d}"
    return result


def _make_repo() -> EvidenceRepository:
    return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))


class TestResultPayload:
    def test_payload_preserves_content(self):
        result = _make_result()
        payload = result_payload(result, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert payload["result_hash"] == result.result_hash
        assert payload["run_id"] == "run-1"
        assert payload["run_hash"] == "run-hash-1"
        assert payload["experiment_hash"] == "exp-hash-1"
        assert payload["metrics"] == {"sharpe": 1.5, "sortino": 1.2}
        assert payload["statistics"]["mean"] == 0.05
        assert payload["performance"]["win_rate"] == 0.6
        assert payload["metadata"]["dataset_version"] == "abc123"

    def test_payload_includes_backend_identity(self):
        result = _make_result()
        payload = result_payload(
            result,
            run_hash="run-hash-1",
            experiment_hash="exp-hash-1",
            backend_identity={"name": "PythonQuantBackend", "version": "1.0.0"},
        )
        assert payload["backend_identity"] == {
            "name": "PythonQuantBackend",
            "version": "1.0.0",
        }

    def test_payload_excludes_telemetry(self):
        result = _make_result_with_telemetry(time_ms=123.5)
        payload = result_payload(result, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert "backend_execution_time_ms" not in payload
        assert "backend_execution_timestamp" not in payload
        assert "created_at" not in payload

    def test_payload_does_not_mutate_result(self):
        result = _make_result()
        before_hash = result.result_hash
        result_payload(result, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert result.result_hash == before_hash


class TestBuildResultEnvelope:
    def test_same_result_same_artifact_hash(self):
        e1 = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        e2 = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert e1.artifact_hash == e2.artifact_hash
        assert e1.lineage_hash == e2.lineage_hash

    def test_changed_metric_different_artifact_hash(self):
        r1 = _make_result(metrics={"sharpe": 1.5})
        r2 = _make_result(metrics={"sharpe": 2.0})
        e1 = build_result_envelope(r1, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        e2 = build_result_envelope(r2, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_statistics_different_artifact_hash(self):
        r1 = _make_result(statistics={"mean": 0.05})
        r2 = _make_result(statistics={"mean": 0.10})
        e1 = build_result_envelope(r1, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        e2 = build_result_envelope(r2, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_run_hash_different_artifact_hash(self):
        e1 = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        e2 = build_result_envelope(_make_result(), run_hash="run-hash-2", experiment_hash="exp-hash-1")
        assert e1.artifact_hash != e2.artifact_hash

    def test_telemetry_does_not_affect_hash(self):
        # Same logical result, different telemetry → same artifact hash.
        r1 = _make_result_with_telemetry(time_ms=1.0)
        r2 = _make_result_with_telemetry(time_ms=999.0)
        e1 = build_result_envelope(r1, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        e2 = build_result_envelope(r2, run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert e1.artifact_hash == e2.artifact_hash

    def test_artifact_type_is_result(self):
        e = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert e.artifact_type == RESULT_ARTIFACT_TYPE == "Result"

    def test_scheme_version_is_2(self):
        assert HASH_SCHEME_VERSION == "2"
        e = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert e.verify() is True

    def test_version_binds_into_identity(self):
        e1 = build_result_envelope(
            _make_result(),
            run_hash="run-hash-1",
            experiment_hash="exp-hash-1",
            version="1.0.0",
        )
        e2 = build_result_envelope(
            _make_result(),
            run_hash="run-hash-1",
            experiment_hash="exp-hash-1",
            version="2.0.0",
        )
        assert e1.artifact_hash != e2.artifact_hash

    def test_returns_immutable_envelope(self):
        e = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        assert isinstance(e, EvidenceEnvelope)
        assert e.verify() is True


class TestRunLineage:
    def test_run_parent_preserved(self):
        e = build_result_envelope(
            _make_result(),
            run_hash="run-hash-1",
            experiment_hash="exp-hash-1",
            parent_hashes=["run-hash-1"],
        )
        assert "run-hash-1" in e.parent_hashes

    def test_attach_run_parent_adds_hash(self):
        base = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        linked = attach_run_parent(base, "run-hash-1")
        assert "run-hash-1" in linked.parent_hashes
        # Original envelope unchanged (immutability).
        assert base.parent_hashes == ()

    def test_relation_constant_is_produces(self):
        assert RUN_TO_RESULT_RELATION == "produces"


class TestEmitResult:
    def test_emit_and_retrieve(self):
        repo = _make_repo()
        e = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        emit_result(e, repo)
        fetched = repo.get_artifact(e.artifact_hash)
        assert fetched is not None
        assert fetched.artifact_type == "Result"
        assert fetched.verify() is True

    def test_emit_returns_stored_envelope(self):
        repo = _make_repo()
        e = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        stored = emit_result(e, repo)
        assert stored.artifact_hash == e.artifact_hash
        assert repo.count_artifacts() == 1

    def test_emit_rejects_non_result_type(self):
        repo = _make_repo()
        from researchos.evidence.envelope import build_envelope

        non_result = build_envelope("Feature", {"x": 1})
        with pytest.raises(ValueError):
            emit_result(non_result, repo)

    def test_emit_default_in_memory_repo(self):
        e = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        stored = emit_result(e)
        assert stored.artifact_hash == e.artifact_hash


class TestRunResultLineage:
    def test_lineage_edge_run_to_result(self):
        repo = _make_repo()
        run_hash = "run-hash-0001"
        e = build_result_envelope(
            _make_result(),
            run_hash=run_hash,
            experiment_hash="exp-hash-1",
            parent_hashes=[run_hash],
        )
        emit_result(e, repo)
        children = repo.get_children(run_hash)
        assert e.artifact_hash in children
        parents = repo.get_parents(e.artifact_hash)
        assert run_hash in parents
        # Relation "produces"
        assert repo.count_edges() == 1

    def test_emit_result_for_run_links_lineage(self):
        repo = _make_repo()
        run_hash = "run-hash-0002"
        stored = emit_result_for_run(_make_result(), run_hash, repo, experiment_hash="exp-hash-1")
        assert run_hash in stored.parent_hashes
        assert repo.count_edges() == 1
        assert repo.get_children(run_hash) == [stored.artifact_hash]


class TestProgressTracking:
    """Track progress against the Phase 5.3b.4 acceptance criteria."""

    def _make_repo(self) -> EvidenceRepository:
        return _make_repo()

    def test_acceptance_identical_result_identical_hash(self):
        assert (
            build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1").artifact_hash
            == build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1").artifact_hash
        )

    def test_acceptance_changed_metric_diff_hash(self):
        e1 = build_result_envelope(
            _make_result(metrics={"sharpe": 1.5}),
            run_hash="run-hash-1",
            experiment_hash="exp-hash-1",
        )
        e2 = build_result_envelope(
            _make_result(metrics={"sharpe": 2.0}),
            run_hash="run-hash-1",
            experiment_hash="exp-hash-1",
        )
        assert e1.artifact_hash != e2.artifact_hash

    def test_acceptance_changed_statistics_diff_hash(self):
        e1 = build_result_envelope(
            _make_result(statistics={"mean": 0.05}),
            run_hash="run-hash-1",
            experiment_hash="exp-hash-1",
        )
        e2 = build_result_envelope(
            _make_result(statistics={"mean": 0.10}),
            run_hash="run-hash-1",
            experiment_hash="exp-hash-1",
        )
        assert e1.artifact_hash != e2.artifact_hash

    def test_acceptance_telemetry_no_effect(self):
        r1 = _make_result_with_telemetry(time_ms=1.0)
        r2 = _make_result_with_telemetry(time_ms=500.0)
        assert (
            build_result_envelope(r1, run_hash="run-hash-1", experiment_hash="exp-hash-1").artifact_hash == build_result_envelope(r2, run_hash="run-hash-1", experiment_hash="exp-hash-1").artifact_hash
        )

    def test_acceptance_run_to_result_lineage(self):
        repo = _make_repo()
        run_hash = "run-hash-lineage"
        stored = emit_result_for_run(_make_result(), run_hash, repo, experiment_hash="exp-hash-1")
        assert repo.get_children(run_hash) == [stored.artifact_hash]

    def test_acceptance_repository_retrieval(self):
        repo = _make_repo()
        e = build_result_envelope(_make_result(), run_hash="run-hash-1", experiment_hash="exp-hash-1")
        emit_result(e, repo)
        assert repo.get_artifact(e.artifact_hash) is not None

    def test_acceptance_version_constant(self):
        assert RESULT_EVIDENCE_VERSION == "1.0.0"
