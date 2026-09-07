"""Tests for Validation evidence emission and Result → Validation lineage."""
from __future__ import annotations

import pytest

from researchos.evidence.envelope import HASH_SCHEME_VERSION, EvidenceEnvelope, build_envelope
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.validation_emission import (
    RESULT_TO_VALIDATION_RELATION,
    VALIDATION_ARTIFACT_TYPE,
    VALIDATION_EVIDENCE_VERSION,
    attach_result_parent,
    build_validation_envelope,
    emit_validation,
    emit_validation_for_result,
    validation_hash,
    validation_payload,
)
from researchos.quant_engine.validation.contracts import FoldResult, ValidationResult
from researchos.storage.repository import ResearchRepository


def _make_fold(fold_id: int, metric: float = 0.85) -> FoldResult:
    return FoldResult(
        fold_id=fold_id,
        train_range=(0, 80),
        validation_range=(80, 100),
        metrics={"accuracy": metric, "loss": 1.0 - metric},
        sample_count=20,
    )


def _make_validation(
    fold_count: int = 3, metric: float = 0.85, metadata: dict | None = None
) -> ValidationResult:
    return ValidationResult(
        train_size=80,
        validation_size=20,
        test_size=0,
        fold_count=fold_count,
        fold_results=tuple(_make_fold(i + 1, metric) for i in range(fold_count)),
        metrics={"mean_accuracy": metric},
        metadata=metadata or {"method": "walk_forward"},
    )


def _make_repo() -> EvidenceRepository:
    return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))


def _seed_result(repo: EvidenceRepository) -> str:
    parent = build_envelope(
        "Result", {"fixture": "Result", "id": "parent"}, version="1.0.0"
    )
    repo.append_artifact(parent)
    return parent.artifact_hash


class TestValidationPayload:
    def test_payload_preserves_content(self):
        payload = validation_payload(
            _make_validation(), result_hash="result-hash-1", run_hash="run-hash-1"
        )
        assert payload["validation_hash"] == validation_hash(_make_validation())
        assert payload["result_hash"] == "result-hash-1"
        assert payload["run_hash"] == "run-hash-1"
        assert payload["metrics"] == {"mean_accuracy": 0.85}
        assert payload["parameters"]["train_size"] == 80
        assert payload["parameters"]["validation_size"] == 20
        assert payload["statistics"]["fold_count"] == 3
        assert payload["metadata"]["method"] == "walk_forward"

    def test_payload_includes_evaluation_config(self):
        payload = validation_payload(
            _make_validation(),
            result_hash="result-hash-1",
            evaluation_config={"metric": "accuracy", "top_k": 5},
        )
        assert payload["evaluation_config"] == {"metric": "accuracy", "top_k": 5}

    def test_payload_excludes_telemetry(self):
        payload = validation_payload(_make_validation(), result_hash="result-hash-1")
        assert "created_at" not in payload
        assert "duration_seconds" not in payload
        assert "execution_time_ms" not in payload
        assert "timestamp" not in payload

    def test_payload_does_not_mutate_validation(self):
        v = _make_validation()
        before = v.to_dict()
        validation_payload(v, result_hash="result-hash-1")
        assert v.to_dict() == before

    def test_payload_is_primitives_only(self):
        def _assert_primitives(value):
            if isinstance(value, dict):
                for k, val in value.items():
                    assert isinstance(k, str)
                    _assert_primitives(val)
            elif isinstance(value, list):
                for item in value:
                    _assert_primitives(item)
            else:
                assert value is None or isinstance(value, (str, int, float, bool)), (
                    f"non-primitive: {value!r}"
                )

        _assert_primitives(
            validation_payload(_make_validation(), result_hash="result-hash-1")
        )


class TestBuildValidationEnvelope:
    def test_same_validation_same_artifact_hash(self):
        e1 = build_validation_envelope(
            _make_validation(), result_hash="result-hash-1", run_hash="run-hash-1"
        )
        e2 = build_validation_envelope(
            _make_validation(), result_hash="result-hash-1", run_hash="run-hash-1"
        )
        assert e1.artifact_hash == e2.artifact_hash
        assert e1.lineage_hash == e2.lineage_hash

    def test_changed_metric_different_artifact_hash(self):
        e1 = build_validation_envelope(_make_validation(metric=0.85), result_hash="result-hash-1")
        e2 = build_validation_envelope(_make_validation(metric=0.90), result_hash="result-hash-1")
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_configuration_different_artifact_hash(self):
        e1 = build_validation_envelope(_make_validation(fold_count=3), result_hash="result-hash-1")
        e2 = build_validation_envelope(_make_validation(fold_count=5), result_hash="result-hash-1")
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_evaluation_config_different_artifact_hash(self):
        e1 = build_validation_envelope(
            _make_validation(),
            result_hash="result-hash-1",
            evaluation_config={"metric": "accuracy"},
        )
        e2 = build_validation_envelope(
            _make_validation(),
            result_hash="result-hash-1",
            evaluation_config={"metric": "precision"},
        )
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_result_hash_different_artifact_hash(self):
        e1 = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        e2 = build_validation_envelope(_make_validation(), result_hash="result-hash-2")
        assert e1.artifact_hash != e2.artifact_hash

    def test_timestamps_do_not_affect_hash(self):
        e1 = build_validation_envelope(
            _make_validation(),
            result_hash="result-hash-1",
            created_at="2020-01-01T00:00:00Z",
        )
        e2 = build_validation_envelope(
            _make_validation(),
            result_hash="result-hash-1",
            created_at="2024-12-31T23:59:59Z",
        )
        assert e1.artifact_hash == e2.artifact_hash

    def test_artifact_type_is_validation(self):
        assert (
            build_validation_envelope(_make_validation(), result_hash="result-hash-1").artifact_type
            == VALIDATION_ARTIFACT_TYPE
            == "Validation"
        )

    def test_scheme_version_is_2(self):
        assert HASH_SCHEME_VERSION == "2"
        assert build_validation_envelope(
            _make_validation(), result_hash="result-hash-1"
        ).verify() is True

    def test_version_binds_into_identity(self):
        e1 = build_validation_envelope(
            _make_validation(), result_hash="result-hash-1", version="1.0.0"
        )
        e2 = build_validation_envelope(
            _make_validation(), result_hash="result-hash-1", version="2.0.0"
        )
        assert e1.artifact_hash != e2.artifact_hash

    def test_returns_immutable_envelope(self):
        assert isinstance(
            build_validation_envelope(_make_validation(), result_hash="result-hash-1"),
            EvidenceEnvelope,
        )


class TestResultLineage:
    def test_result_parent_preserved(self):
        envelope = build_validation_envelope(
            _make_validation(),
            result_hash="result-hash-1",
            parent_hashes=["result-hash-1"],
        )
        assert "result-hash-1" in envelope.parent_hashes

    def test_attach_result_parent_adds_hash(self):
        base = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        linked = attach_result_parent(base, "result-hash-1")
        assert "result-hash-1" in linked.parent_hashes
        assert base.parent_hashes == ()

    def test_relation_constant_is_validates(self):
        assert RESULT_TO_VALIDATION_RELATION == "validates"


class TestEmitValidation:
    def test_emit_and_retrieve(self):
        repo = _make_repo()
        e = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        emit_validation(e, repo)
        fetched = repo.get_artifact(e.artifact_hash)
        assert fetched is not None
        assert fetched.artifact_type == "Validation"
        assert fetched.verify() is True

    def test_emit_returns_stored_envelope(self):
        repo = _make_repo()
        e = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        stored = emit_validation(e, repo)
        assert stored.artifact_hash == e.artifact_hash
        assert repo.count_artifacts() == 1

    def test_emit_rejects_non_validation_type(self):
        repo = _make_repo()
        non_validation = build_envelope("Feature", {"x": 1})
        with pytest.raises(ValueError):
            emit_validation(non_validation, repo)

    def test_emit_rejects_tampered_envelope(self):
        repo = _make_repo()
        e = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        tampered = EvidenceEnvelope(
            artifact_type=e.artifact_type,
            artifact_hash=e.artifact_hash,
            payload={"validation_hash": "tampered"},
            version=e.version,
            created_at=e.created_at,
            parent_hashes=e.parent_hashes,
            lineage_hash=e.lineage_hash,
        )
        with pytest.raises(ValueError):
            emit_validation(tampered, repo)

    def test_emit_default_in_memory_repo(self):
        e = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        assert emit_validation(e).artifact_hash == e.artifact_hash


class TestResultValidationLineage:
    def test_lineage_edge_result_to_validation(self):
        repo = _make_repo()
        result_hash = _seed_result(repo)
        e = build_validation_envelope(
            _make_validation(), result_hash=result_hash, parent_hashes=[result_hash]
        )
        emit_validation(e, repo)
        assert result_hash in repo.get_parents(e.artifact_hash)
        assert e.artifact_hash in repo.get_children(result_hash)
        assert repo.count_edges() == 1

    def test_emit_validation_for_result_links_lineage(self):
        repo = _make_repo()
        result_hash = _seed_result(repo)
        stored = emit_validation_for_result(_make_validation(), result_hash, repo)
        assert result_hash in stored.parent_hashes
        assert repo.count_edges() == 1
        assert repo.get_children(result_hash) == [stored.artifact_hash]


class TestProgressTracking:
    def test_acceptance_identical_validation_identical_hash(self):
        e1 = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        e2 = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        assert e1.artifact_hash == e2.artifact_hash

    def test_acceptance_changed_metric_diff_hash(self):
        e1 = build_validation_envelope(_make_validation(metric=0.85), result_hash="result-hash-1")
        e2 = build_validation_envelope(_make_validation(metric=0.90), result_hash="result-hash-1")
        assert e1.artifact_hash != e2.artifact_hash

    def test_acceptance_changed_config_diff_hash(self):
        e1 = build_validation_envelope(_make_validation(fold_count=3), result_hash="result-hash-1")
        e2 = build_validation_envelope(_make_validation(fold_count=5), result_hash="result-hash-1")
        assert e1.artifact_hash != e2.artifact_hash

    def test_acceptance_timestamps_no_effect(self):
        e1 = build_validation_envelope(
            _make_validation(),
            result_hash="result-hash-1",
            created_at="2020-01-01T00:00:00Z",
        )
        e2 = build_validation_envelope(
            _make_validation(),
            result_hash="result-hash-1",
            created_at="2024-01-01T00:00:00Z",
        )
        assert e1.artifact_hash == e2.artifact_hash

    def test_acceptance_result_to_validation_lineage(self):
        repo = _make_repo()
        result_hash = _seed_result(repo)
        stored = emit_validation_for_result(_make_validation(), result_hash, repo)
        assert repo.get_children(result_hash) == [stored.artifact_hash]

    def test_acceptance_repository_retrieval(self):
        repo = _make_repo()
        e = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        emit_validation(e, repo)
        assert repo.get_artifact(e.artifact_hash) is not None

    def test_acceptance_tampered_rejected(self):
        repo = _make_repo()
        e = build_validation_envelope(_make_validation(), result_hash="result-hash-1")
        tampered = EvidenceEnvelope(
            artifact_type=e.artifact_type,
            artifact_hash=e.artifact_hash,
            payload={"validation_hash": "bad"},
            version=e.version,
            created_at=e.created_at,
            parent_hashes=e.parent_hashes,
            lineage_hash=e.lineage_hash,
        )
        with pytest.raises(ValueError):
            emit_validation(tampered, repo)

    def test_acceptance_payload_primitive_only(self):
        payload = validation_payload(_make_validation(), result_hash="result-hash-1")

        def _assert_primitives(value):
            if isinstance(value, dict):
                for k, val in value.items():
                    assert isinstance(k, str)
                    _assert_primitives(val)
            elif isinstance(value, list):
                for item in value:
                    _assert_primitives(item)
            else:
                assert value is None or isinstance(value, (str, int, float, bool))

        _assert_primitives(payload)

    def test_acceptance_scheme_version_2(self):
        assert HASH_SCHEME_VERSION == "2"

    def test_acceptance_version_constant(self):
        assert VALIDATION_EVIDENCE_VERSION == "1.0.0"
