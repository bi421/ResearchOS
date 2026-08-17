"""
Tests for Phase 5.3b.1 — Dataset Evidence Emission.

Covers:
    - ``build_dataset_envelope`` determinism and identity.
    - Dataset payload projection from the frozen ``ResearchDataset`` contract.
    - Persistence + retrieval via ``EvidenceRepository``.
    - Lineage metadata (parent hashes) support.
    - Hash-scheme-2 marker and strict payload contract.

Verification requirements:
    - same dataset → same artifact_hash
    - changed dataset → different artifact_hash
    - artifact can be retrieved from EvidenceRepository
    - existing dataset behavior preserved (no mutation)
"""

from __future__ import annotations

import pytest

from researchos.evidence.dataset_emission import (
    DATASET_ARTIFACT_TYPE,
    DATASET_EVIDENCE_VERSION,
    build_dataset_envelope,
    emit_dataset,
    make_dataset_envelope_from_payload,
    research_dataset_payload,
)
from researchos.evidence.envelope import HASH_SCHEME_VERSION, EvidenceEnvelope
from researchos.evidence.repository import EvidenceRepository
from researchos.quant_engine.machine_learning.dataset_contracts import (
    ResearchDataset,
)
from researchos.storage.repository import ResearchRepository


def _make_dataset(
    feature_names=("a", "b"),
    features=None,
    labels=None,
    metadata=None,
    version="1.0.0",
    label_name="target",
) -> ResearchDataset:
    features = features or [
        (1.0, 2.0),
        (3.0, 4.0),
        (5.0, 6.0),
    ]
    labels = labels or [0.0, 1.0, 0.0]
    metadata = metadata or {"source": "yahoo", "periods": 3}
    return ResearchDataset(
        feature_names=tuple(feature_names),
        features=tuple(tuple(r) for r in features),
        labels=tuple(labels),
        metadata=dict(metadata),
        sample_count=len(labels),
        feature_count=len(feature_names),
        label_name=label_name,
        version=version,
        created_at=None,
    )


class TestDatasetPayload:
    def test_payload_projection_preserves_content(self):
        ds = _make_dataset()
        payload = research_dataset_payload(ds)
        assert payload["feature_names"] == ["a", "b"]
        assert payload["features"] == [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        assert payload["labels"] == [0.0, 1.0, 0.0]
        assert payload["sample_count"] == 3
        assert payload["feature_count"] == 2
        assert payload["label_name"] == "target"
        assert payload["metadata"]["source"] == "yahoo"

    def test_payload_excludes_created_at(self):
        ds = _make_dataset()
        payload = research_dataset_payload(ds)
        assert "created_at" not in payload

    def test_payload_does_not_mutate_dataset(self):
        ds = _make_dataset()
        before_names = ds.feature_names
        before_features = ds.features
        before_labels = ds.labels
        research_dataset_payload(ds)
        assert ds.feature_names == before_names
        assert ds.features == before_features
        assert ds.labels == before_labels


class TestBuildDatasetEnvelope:
    def test_same_dataset_same_artifact_hash(self):
        ds = _make_dataset()
        e1 = build_dataset_envelope(ds, version="1.0.0")
        e2 = build_dataset_envelope(ds, version="1.0.0")
        assert e1.artifact_hash == e2.artifact_hash
        assert e1.lineage_hash == e2.lineage_hash

    def test_changed_dataset_different_artifact_hash(self):
        d1 = _make_dataset(labels=[0.0, 1.0, 0.0])
        d2 = _make_dataset(labels=[1.0, 0.0, 1.0])
        e1 = build_dataset_envelope(d1)
        e2 = build_dataset_envelope(d2)
        assert e1.artifact_hash != e2.artifact_hash

    def test_changed_metadata_different_artifact_hash(self):
        d1 = _make_dataset(metadata={"source": "yahoo"})
        d2 = _make_dataset(metadata={"source": "google"})
        assert build_dataset_envelope(d1).artifact_hash != build_dataset_envelope(d2).artifact_hash

    def test_artifact_type_is_dataset(self):
        e = build_dataset_envelope(_make_dataset())
        assert e.artifact_type == DATASET_ARTIFACT_TYPE == "Dataset"

    def test_scheme_version_is_2(self):
        assert HASH_SCHEME_VERSION == "2"
        e = build_dataset_envelope(_make_dataset())
        assert e.verify() is True

    def test_parent_hashes_are_supported(self):
        e = build_dataset_envelope(
            _make_dataset(),
            parent_hashes=["parent-a", "parent-b"],
        )
        assert set(e.parent_hashes) == {"parent-a", "parent-b"}
        assert e.verify() is True

    def test_parent_order_does_not_change_hash(self):
        a = build_dataset_envelope(_make_dataset(), parent_hashes=["x", "y"])
        b = build_dataset_envelope(_make_dataset(), parent_hashes=["y", "x"])
        assert a.lineage_hash == b.lineage_hash

    def test_version_binds_into_identity(self):
        e1 = build_dataset_envelope(_make_dataset(), version="1.0.0")
        e2 = build_dataset_envelope(_make_dataset(), version="2.0.0")
        assert e1.artifact_hash != e2.artifact_hash

    def test_returns_immutable_envelope(self):
        e = build_dataset_envelope(_make_dataset())
        assert isinstance(e, EvidenceEnvelope)
        assert e.verify() is True


class TestMakeDatasetEnvelopeFromPayload:
    def test_from_payload_matches_build(self):
        ds = _make_dataset()
        payload = research_dataset_payload(ds)
        from_payload = make_dataset_envelope_from_payload(payload, version="1.0.0")
        from_ds = build_dataset_envelope(ds, version="1.0.0")
        assert from_payload.artifact_hash == from_ds.artifact_hash
        assert from_payload.lineage_hash == from_ds.lineage_hash


class TestEmitDataset:
    def _make_repo(self) -> EvidenceRepository:
        return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))

    def test_emit_and_retrieve(self):
        repo = self._make_repo()
        e = build_dataset_envelope(_make_dataset())
        emit_dataset(e, repo)
        fetched = repo.get_artifact(e.artifact_hash)
        assert fetched is not None
        assert fetched.artifact_type == "Dataset"
        assert fetched.verify() is True

    def test_emit_returns_stored_envelope(self):
        repo = self._make_repo()
        e = build_dataset_envelope(_make_dataset())
        stored = emit_dataset(e, repo)
        assert stored.artifact_hash == e.artifact_hash
        assert repo.count_artifacts() == 1

    def test_emit_rejects_non_dataset_type(self):
        repo = self._make_repo()
        from researchos.evidence.envelope import build_envelope

        non_dataset = build_envelope("Feature", {"x": 1})
        with pytest.raises(ValueError):
            emit_dataset(non_dataset, repo)

    def test_emit_rejects_tampered_envelope(self):
        repo = self._make_repo()
        e = build_dataset_envelope(_make_dataset())
        tampered = EvidenceEnvelope(
            artifact_type=e.artifact_type,
            artifact_hash=e.artifact_hash,
            payload={"tampered": True},
            parent_hashes=[],
            lineage_hash=e.lineage_hash,
        )
        with pytest.raises(ValueError):
            emit_dataset(tampered, repo)

    def test_emit_default_in_memory_repo(self):
        e = build_dataset_envelope(_make_dataset())
        stored = emit_dataset(e)
        assert stored.artifact_hash == e.artifact_hash


class TestProgressTracking:
    """Track progress against the Phase 5.3b.1 acceptance criteria."""

    def _make_repo(self) -> EvidenceRepository:
        return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))

    def test_acceptance_same_dataset_same_hash(self):
        assert (
            build_dataset_envelope(_make_dataset()).artifact_hash
            == build_dataset_envelope(_make_dataset()).artifact_hash
        )

    def test_acceptance_changed_dataset_diff_hash(self):
        assert (
            build_dataset_envelope(_make_dataset(labels=[0, 1, 0])).artifact_hash
            != build_dataset_envelope(_make_dataset(labels=[1, 0, 1])).artifact_hash
        )

    def test_acceptance_retrievable_from_repo(self):
        repo = self._make_repo()
        e = build_dataset_envelope(_make_dataset())
        emit_dataset(e, repo)
        assert repo.get_artifact(e.artifact_hash) is not None

    def test_acceptance_version_constant(self):
        assert DATASET_EVIDENCE_VERSION == "1.0.0"
