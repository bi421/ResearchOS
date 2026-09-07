"""End-to-end contract for the canonical evidence lineage chain.

This test intentionally uses the evidence layer directly so it verifies the
storage/lineage contract independently of higher-level experiment fixtures.
The chain mirrors the canonical ResearchOS flow:

    Dataset -> Experiment -> Run -> Result -> Validation -> Finding

and then extends the same graph with a Model artifact to prove that every
canonical evidence type can participate in a closed, verifiable graph.
"""

from __future__ import annotations

import pytest

from researchos.evidence.envelope import build_envelope
from researchos.evidence.repository import EvidenceRepository
from researchos.storage.repository import ResearchRepository


def test_canonical_evidence_chain_is_closed_and_verifiable() -> None:
    repo = EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))

    dataset = build_envelope("Dataset", {"symbol": "XAUUSD", "rows": 100})
    experiment = build_envelope(
        "Experiment",
        {"name": "xauusd-direction-study", "version": "1"},
        parent_hashes=[dataset.artifact_hash],
    )
    run = build_envelope(
        "Run",
        {"run_id": "run-001", "seed": 42},
        parent_hashes=[experiment.artifact_hash],
    )
    result = build_envelope(
        "Result",
        {"accuracy": 0.61, "sample_count": 100},
        parent_hashes=[run.artifact_hash],
    )
    validation = build_envelope(
        "Validation",
        {"status": "validated", "method": "walk_forward"},
        parent_hashes=[result.artifact_hash],
    )
    finding = build_envelope(
        "Finding",
        {"status": "validated", "statement": "historical relationship"},
        parent_hashes=[validation.artifact_hash],
    )
    model = build_envelope(
        "Model",
        {"kind": "research-model", "version": "1"},
        parent_hashes=[finding.artifact_hash],
    )

    for artifact in (
        dataset,
        experiment,
        run,
        result,
        validation,
        finding,
        model,
    ):
        repo.append_artifact(artifact)

    assert repo.count_artifacts() == 7
    assert repo.count_edges() == 6
    assert repo.get_children(dataset.artifact_hash) == [experiment.artifact_hash]
    assert repo.get_children(experiment.artifact_hash) == [run.artifact_hash]
    assert repo.get_children(run.artifact_hash) == [result.artifact_hash]
    assert repo.get_children(result.artifact_hash) == [validation.artifact_hash]
    assert repo.get_children(validation.artifact_hash) == [finding.artifact_hash]
    assert repo.get_children(finding.artifact_hash) == [model.artifact_hash]
    assert repo.verify_evidence() is True


def test_canonical_chain_rejects_missing_upstream_evidence() -> None:
    repo = EvidenceRepository(repository=ResearchRepository(db_path=":memory:"))
    orphan_run = build_envelope(
        "Run",
        {"run_id": "orphan"},
        parent_hashes=["missing-experiment"],
    )

    with pytest.raises(ValueError, match="parent evidence missing-experiment does not exist"):
        repo.append_artifact(orphan_run)

    assert repo.count_artifacts() == 0
    assert repo.count_edges() == 0
