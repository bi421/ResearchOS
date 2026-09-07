from __future__ import annotations

import pytest

from researchos.evidence import EvidenceRepository, build_envelope
from researchos.knowledge import KnowledgeQuery, KnowledgeRetrieval
from researchos.objects.knowledge import Knowledge
from researchos.storage.repository import ResearchRepository


@pytest.fixture
def repo() -> ResearchRepository:
    return ResearchRepository(db_path=":memory:")


def _seed_chain(repo: ResearchRepository) -> tuple[str, str]:
    evidence = EvidenceRepository(repo)
    dataset = evidence.append_artifact(build_envelope("Dataset", {"id": "dataset-1"}))
    experiment = evidence.append_artifact(
        build_envelope(
            "Experiment",
            {"id": "experiment-1"},
            parent_hashes=[dataset.artifact_hash],
        )
    )
    run = evidence.append_artifact(
        build_envelope(
            "Run",
            {"id": "run-1"},
            parent_hashes=[experiment.artifact_hash],
        )
    )
    result = evidence.append_artifact(
        build_envelope(
            "Result",
            {"id": "result-1"},
            parent_hashes=[run.artifact_hash],
        )
    )
    validation = evidence.append_artifact(
        build_envelope(
            "Validation",
            {"id": "validation-1", "status": "VALIDATED"},
            parent_hashes=[result.artifact_hash],
        )
    )
    finding = evidence.append_artifact(
        build_envelope(
            "Finding",
            {"id": "finding-1", "status": "VALIDATED", "validation_id": "validation-1"},
            parent_hashes=[validation.artifact_hash],
        )
    )
    return finding.artifact_hash, dataset.artifact_hash


def test_query_is_exact_deterministic_and_filters_unvalidated(repo: ResearchRepository):
    finding_hash, _ = _seed_chain(repo)
    validated = Knowledge(
        type="Event_Impact",
        subject="XAUUSD",
        predicate="response",
        object="higher",
        confidence=0.8,
        source_references=[finding_hash],
    )
    unvalidated = Knowledge(
        type="Event_Impact",
        subject="XAUUSD",
        predicate="response",
        object="lower",
        confidence=0.9,
        source_references=[],
    )
    repo.save_object(validated)
    repo.save_object(unvalidated)

    retrieval = KnowledgeRetrieval(repo, EvidenceRepository(repo))
    first = retrieval.query(KnowledgeQuery(subject="XAUUSD", min_confidence=0.7))
    second = retrieval.query(KnowledgeQuery(subject="XAUUSD", min_confidence=0.7))

    assert [item.id for item in first] == [validated.id]
    assert [item.id for item in first] == [item.id for item in second]


def test_retrieve_returns_complete_upstream_provenance(repo: ResearchRepository):
    finding_hash, dataset_hash = _seed_chain(repo)
    knowledge = Knowledge(
        type="Event_Impact",
        subject="XAUUSD",
        predicate="response",
        object="higher",
        confidence=0.8,
        source_references=[finding_hash],
    )
    repo.save_object(knowledge)

    retrieval = KnowledgeRetrieval(repo, EvidenceRepository(repo))
    result = retrieval.retrieve()[0]

    assert result.knowledge.id == knowledge.id
    assert [node.artifact_type for node in result.provenance] == [
        "Finding",
        "Validation",
        "Result",
        "Run",
        "Experiment",
        "Dataset",
    ]
    assert result.provenance[-1].artifact_hash == dataset_hash


def test_traverse_rejects_missing_or_nonvalidated_provenance(repo: ResearchRepository):
    evidence = EvidenceRepository(repo)
    finding = evidence.append_artifact(
        build_envelope("Finding", {"id": "finding-1", "status": "EXPLORATORY"})
    )
    knowledge = Knowledge(
        type="Event_Impact",
        subject="XAUUSD",
        predicate="response",
        object="higher",
        source_references=[finding.artifact_hash],
    )
    repo.save_object(knowledge)

    retrieval = KnowledgeRetrieval(repo, evidence)
    assert retrieval.query() == []
    with pytest.raises(ValueError, match="no validated Finding provenance"):
        retrieval.traverse(knowledge.id)


def test_query_does_not_mutate_knowledge(repo: ResearchRepository):
    finding_hash, _ = _seed_chain(repo)
    knowledge = Knowledge(
        type="Event_Impact",
        subject="XAUUSD",
        predicate="response",
        object="higher",
        confidence=0.8,
        source_references=[finding_hash],
    )
    repo.save_object(knowledge)
    before = knowledge.to_dict()

    KnowledgeRetrieval(repo, EvidenceRepository(repo)).retrieve()

    assert knowledge.to_dict() == before
