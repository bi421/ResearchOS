"""
Tests for the Phase 5.3a Evidence & Lineage storage foundation
(hash-contract hardened).

Covers:
    - ``EvidenceEnvelope`` immutability, determinism, and lineage verification.
    - Hash-contract hardening:
        * same payload + different artifact_type => different artifact_hash
        * version change affects lineage verification
        * tampered type/version fails verification
        * unsupported payload type rejected
    - ``EvidenceRepository`` append-only storage, lineage traversal, integrity.
    - Schema migration (SCHEMA_VERSION 3) creates the ``evidence`` and
      ``lineage`` tables.

Contract-preserving: no existing behavior is changed; these tests assert the
new additive evidence/lineage guarantees and the hardened hash contract.
"""

from __future__ import annotations

import pytest

from researchos.evidence.envelope import (
    ARTIFACT_TYPES,
    HASH_SCHEME_VERSION,
    EvidenceEnvelope,
    build_envelope,
    compute_artifact_hash,
)
from researchos.evidence.repository import EvidenceRepository
from researchos.storage.repository import SCHEMA_VERSION, ResearchRepository

# =============================================================================
# EvidenceEnvelope
# =============================================================================


class TestEvidenceEnvelope:
    def test_artifact_types_registered(self):
        assert "Dataset" in ARTIFACT_TYPES
        assert "Model" in ARTIFACT_TYPES
        assert len(ARTIFACT_TYPES) >= 7

    def test_build_envelope_hashes_deterministically(self):
        e1 = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        e2 = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        assert e1.artifact_hash == e2.artifact_hash
        assert e1.lineage_hash == e2.lineage_hash

    def test_different_payload_differs(self):
        e1 = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        e2 = build_envelope("Dataset", {"a": 2}, version="1.0.0")
        assert e1.artifact_hash != e2.artifact_hash

    def test_same_payload_different_type_differs(self):
        """Hardening #1: artifact identity must bind the artifact type."""
        ds = build_envelope("Dataset", {"sym": ["AAPL"]}, version="1.0.0")
        ft = build_envelope("Feature", {"sym": ["AAPL"]}, version="1.0.0")
        assert ds.artifact_hash != ft.artifact_hash
        assert ds.lineage_hash != ft.lineage_hash

    def test_parent_order_does_not_change_lineage_hash(self):
        p1 = build_envelope("Dataset", {"x": 1}, version="v")
        p2 = build_envelope("Dataset", {"x": 2}, version="v")
        a = build_envelope("Feature", {"y": 3}, parent_hashes=[p1.artifact_hash, p2.artifact_hash])
        b = build_envelope("Feature", {"y": 3}, parent_hashes=[p2.artifact_hash, p1.artifact_hash])
        assert a.lineage_hash == b.lineage_hash

    def test_verify_accepts_valid_envelope(self):
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        assert e.verify() is True

    def test_verify_detects_tampered_payload(self):
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        tampered = EvidenceEnvelope(
            artifact_type=e.artifact_type,
            artifact_hash=e.artifact_hash,
            payload={"tampered": True},
            parent_hashes=[],
            lineage_hash=e.lineage_hash,
        )
        assert tampered.verify() is False

    def test_verify_detects_tampered_version(self):
        """Hardening #2: version tampering must fail verification."""
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        tampered = EvidenceEnvelope(
            artifact_type=e.artifact_type,
            artifact_hash=e.artifact_hash,
            payload={"a": 1},
            version="999.0.0",
            parent_hashes=[],
            lineage_hash=e.lineage_hash,
        )
        assert tampered.verify() is False

    def test_verify_detects_tampered_type(self):
        """Hardening #2: artifact_type tampering must fail verification."""
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        tampered = EvidenceEnvelope(
            artifact_type="Experiment",
            artifact_hash=e.artifact_hash,
            payload={"a": 1},
            version=e.version,
            parent_hashes=[],
            lineage_hash=e.lineage_hash,
        )
        assert tampered.verify() is False

    def test_version_change_affects_lineage(self):
        """Hardening #2: version change alters the lineage signature."""
        v1 = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        v2 = build_envelope("Dataset", {"a": 1}, version="2.0.0")
        assert v1.lineage_hash != v2.lineage_hash
        assert v1.artifact_hash != v2.artifact_hash

    def test_legacy_verify_accepts_pre_hardening_scheme(self):
        """Backward compatibility: legacy scheme-1 lineage hash still verifies."""
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        # Build a legacy-format envelope exactly as the pre-hardening code did.
        from researchos.core.identity import deterministic_hash

        legacy = EvidenceEnvelope(
            artifact_type=e.artifact_type,
            artifact_hash=e.artifact_hash,
            payload=e.payload,
            version=e.version,
            parent_hashes=[],
            lineage_hash=deterministic_hash({"payload": e.payload, "parent_hashes": sorted([])}),
        )
        # New-scheme verify must reject the legacy hash...
        assert legacy.verify() is False
        # ...but legacy_verify must accept it (backward compatible).
        assert legacy.legacy_verify() is True

    def test_verify_accepts_empty_lineage_hash_legacy(self):
        e = EvidenceEnvelope(
            artifact_type="Dataset",
            artifact_hash="abc",
            payload={"a": 1},
            lineage_hash="",
        )
        assert e.verify() is True

    def test_invalid_artifact_type_rejected(self):
        with pytest.raises(ValueError):
            EvidenceEnvelope(artifact_type="Bogus", artifact_hash="abc")

    def test_missing_artifact_hash_rejected(self):
        with pytest.raises(ValueError):
            EvidenceEnvelope(artifact_type="Dataset", artifact_hash="")

    def test_serialization_round_trip(self):
        e = build_envelope(
            "Run",
            {"params": {"a": 1}},
            version="1.0.0",
            parent_hashes=["p1", "p2"],
        )
        restored = EvidenceEnvelope.from_dict(e.to_dict())
        assert restored.artifact_hash == e.artifact_hash
        assert restored.lineage_hash == e.lineage_hash
        assert restored.parent_hashes == e.parent_hashes
        assert restored.verify() is True

    def test_envelope_is_immutable(self):
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        # Frozen dataclass blocks attribute reassignment.
        with pytest.raises(Exception):
            e.artifact_hash = "changed"
        # parent_hashes are stored as an immutable tuple.
        assert isinstance(e.parent_hashes, tuple)

    def test_hash_scheme_version_marker(self):
        assert HASH_SCHEME_VERSION == "2"
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        assert e.verify() is True


# =============================================================================
# Payload contract (strict primitive validation)
# =============================================================================


class TestPayloadContract:
    def test_build_rejects_unsupported_object(self):
        """Hardening #3: unsupported payload objects are rejected."""
        with pytest.raises(TypeError):
            build_envelope("Dataset", {"dt": __import__("datetime").datetime.now()})

    def test_build_rejects_custom_object(self):
        class _Custom:
            pass

        with pytest.raises(TypeError):
            build_envelope("Dataset", {"obj": _Custom()})

    def test_envelope_constructor_rejects_unsupported_object(self):
        with pytest.raises(TypeError):
            EvidenceEnvelope(
                artifact_type="Dataset",
                artifact_hash="abc",
                payload={"bad": object()},
            )

    def test_nested_unsupported_object_rejected(self):
        with pytest.raises(TypeError):
            build_envelope("Dataset", {"outer": {"inner": {"x": object()}}})

    def test_non_string_dict_key_rejected(self):
        with pytest.raises(TypeError):
            build_envelope("Dataset", {1: "value"})

    def test_allowed_primitives_accepted(self):
        payload = {
            "str": "s",
            "int": 1,
            "float": 1.5,
            "bool": True,
            "none": None,
            "list": [1, "a", None, 2.5, True],
            "nested": {"k": [1, 2]},
        }
        e = build_envelope("Dataset", payload, version="1.0.0")
        assert e.verify() is True

    def test_compute_artifact_hash_rejects_unsupported(self):
        with pytest.raises(TypeError):
            compute_artifact_hash("Dataset", "1.0.0", {"x": object()})


# =============================================================================
# Schema migration
# =============================================================================


class TestSchemaMigration:
    def test_schema_version_is_3(self):
        assert SCHEMA_VERSION == 3

    def test_evidence_tables_created(self):
        repo = ResearchRepository(db_path=":memory:")
        conn = repo._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cursor.fetchall()}
        assert "evidence" in tables
        assert "lineage" in tables


# =============================================================================
# EvidenceRepository
# =============================================================================


class TestEvidenceRepository:
    def _make_repo(self) -> EvidenceRepository:
        return EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))

    def test_append_and_retrieve(self):
        ev = self._make_repo()
        e = build_envelope("Dataset", {"symbols": ["AAPL"]}, version="1.0.0")
        ev.append_artifact(e)
        fetched = ev.get_artifact(e.artifact_hash)
        assert fetched is not None
        assert fetched.artifact_type == "Dataset"
        assert fetched.payload == {"symbols": ["AAPL"]}
        assert fetched.verify() is True

    def test_get_missing_returns_none(self):
        ev = self._make_repo()
        assert ev.get_artifact("does-not-exist") is None

    def test_lineage_edges_are_recorded(self):
        ev = self._make_repo()
        ds = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        feat = build_envelope("Feature", {"b": 2}, version="1.0.0", parent_hashes=[ds.artifact_hash])
        ev.append_artifact(ds)
        ev.append_artifact(feat)
        assert ev.get_parents(feat.artifact_hash) == [ds.artifact_hash]
        assert ev.get_children(ds.artifact_hash) == [feat.artifact_hash]

    def test_explicit_edge_add(self):
        ev = self._make_repo()
        ev.add_lineage_edge("parent-hash", "child-hash", relation="produces")
        assert ev.get_children("parent-hash") == ["child-hash"]
        assert ev.get_parents("child-hash") == ["parent-hash"]

    def test_invalid_relation_rejected(self):
        ev = self._make_repo()
        with pytest.raises(ValueError):
            ev.add_lineage_edge("p", "c", relation="bogus")

    def test_append_is_deduplicating_not_updating(self):
        ev = self._make_repo()
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        ev.append_artifact(e)
        ev.append_artifact(e)  # identical -> no-op (INSERT OR IGNORE)
        assert ev.count_artifacts() == 1

    def test_append_rejects_tampered_envelope(self):
        ev = self._make_repo()
        e = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        tampered = EvidenceEnvelope(
            artifact_type=e.artifact_type,
            artifact_hash=e.artifact_hash,
            payload={"changed": True},
            parent_hashes=[],
            lineage_hash=e.lineage_hash,
        )
        with pytest.raises(ValueError):
            ev.append_artifact(tampered)

    def test_verify_evidence_true_when_consistent(self):
        ev = self._make_repo()
        ds = build_envelope("Dataset", {"a": 1}, version="1.0.0")
        feat = build_envelope("Feature", {"b": 2}, version="1.0.0", parent_hashes=[ds.artifact_hash])
        ev.append_artifact(ds)
        ev.append_artifact(feat)
        assert ev.verify_evidence() is True

    def test_counts(self):
        ev = self._make_repo()
        assert ev.count_artifacts() == 0
        assert ev.count_edges() == 0
        e1 = build_envelope("Dataset", {"a": 1})
        e2 = build_envelope("Feature", {"b": 2}, parent_hashes=[e1.artifact_hash])
        ev.append_artifact(e1)
        ev.append_artifact(e2)
        assert ev.count_artifacts() == 2
        assert ev.count_edges() == 1

    def test_round_trip_maintains_parent_hashes(self):
        ev = self._make_repo()
        p = build_envelope("Dataset", {"x": 1}, version="v")
        c = build_envelope("Feature", {"y": 2}, version="v", parent_hashes=[p.artifact_hash])
        ev.append_artifact(p)
        ev.append_artifact(c)
        fetched = ev.get_artifact(c.artifact_hash)
        assert fetched.parent_hashes == (p.artifact_hash,)
        assert fetched.verify() is True

    def test_append_distinct_types_no_collision(self):
        """Hardening #1: Dataset and Feature with same payload both stored."""
        ev = self._make_repo()
        ds = build_envelope("Dataset", {"v": 1}, version="1.0.0")
        ft = build_envelope("Feature", {"v": 1}, version="1.0.0")
        assert ds.artifact_hash != ft.artifact_hash
        ev.append_artifact(ds)
        ev.append_artifact(ft)
        assert ev.count_artifacts() == 2
        assert ev.get_artifact(ds.artifact_hash).artifact_type == "Dataset"
        assert ev.get_artifact(ft.artifact_hash).artifact_type == "Feature"
