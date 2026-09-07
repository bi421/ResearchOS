from __future__ import annotations

import json

import pytest

from researchos.evidence.envelope import build_envelope
from researchos.evidence.repository import EvidenceRepository
from researchos.storage.repository import ResearchRepository


def _make_repo() -> tuple[ResearchRepository, EvidenceRepository]:
    repository = ResearchRepository(db_path=":memory:")
    return repository, EvidenceRepository(repository=repository)


def test_append_is_atomic_when_generic_mirror_conflicts() -> None:
    repository, evidence = _make_repo()
    envelope = build_envelope("Dataset", {"a": 1}, version="1.0.0")

    with repository._transaction() as cursor:
        cursor.execute(
            "INSERT INTO objects (id, object_type, created_at, data) VALUES (?, ?, ?, ?)",
            (
                envelope.artifact_hash,
                "Knowledge",
                envelope.created_at,
                json.dumps({"object_type": "Knowledge", "id": envelope.artifact_hash}),
            ),
        )

    with pytest.raises(ValueError, match="conflicting content"):
        evidence.append_artifact(envelope)

    assert evidence.count_artifacts() == 0
    assert repository.load_by_id(envelope.artifact_hash)["object_type"] == "Knowledge"


def test_append_commit_contains_evidence_mirror_and_lineage() -> None:
    repository, evidence = _make_repo()
    parent = build_envelope("Dataset", {"x": 1}, version="1.0.0")
    child = build_envelope(
        "Feature",
        {"y": 2},
        version="1.0.0",
        parent_hashes=[parent.artifact_hash],
    )

    evidence.append_artifact(parent)
    evidence.append_artifact(child)

    assert evidence.count_artifacts() == 2
    assert evidence.count_edges() == 1
    mirrored = repository.load_by_id(child.artifact_hash)
    assert mirrored is not None
    assert mirrored["object_type"] == "EvidenceEnvelope"
    assert mirrored["artifact_hash"] == child.artifact_hash
    assert evidence.verify_evidence() is True
