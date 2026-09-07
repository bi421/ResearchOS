from __future__ import annotations

import pytest

from researchos.evidence import (
    EvidenceRepository,
    build_envelope,
    certify_experiment_learning,
    certify_knowledge,
)
from researchos.experiments.learning import ExperimentLearningRecord
from researchos.knowledge import KnowledgeQuery, KnowledgeRetrieval
from researchos.objects.knowledge import Knowledge
from researchos.storage.repository import ResearchRepository


@pytest.fixture
def repo() -> ResearchRepository:
    return ResearchRepository(db_path=":memory:")


def test_golden_path_dataset_to_knowledge_retrieval(repo: ResearchRepository):
    """Protect the complete evidence -> learning -> knowledge -> retrieval path."""
    evidence = EvidenceRepository(repo)

    dataset = evidence.append_artifact(
        build_envelope("Dataset", {"id": "golden-dataset", "symbol": "XAUUSD"})
    )
    experiment = evidence.append_artifact(
        build_envelope(
            "Experiment",
            {"id": "golden-experiment", "symbol": "XAUUSD"},
            parent_hashes=[dataset.artifact_hash],
        )
    )
    run = evidence.append_artifact(
        build_envelope(
            "Run",
            {"id": "golden-run"},
            parent_hashes=[experiment.artifact_hash],
        )
    )
    result = evidence.append_artifact(
        build_envelope(
            "Result",
            {"id": "golden-result", "metric": 0.61},
            parent_hashes=[run.artifact_hash],
        )
    )
    validation = evidence.append_artifact(
        build_envelope(
            "Validation",
            {"id": "golden-validation", "status": "VALIDATED"},
            parent_hashes=[result.artifact_hash],
        )
    )
    finding = evidence.append_artifact(
        build_envelope(
            "Finding",
            {
                "id": "golden-finding",
                "status": "VALIDATED",
                "validation_id": "golden-validation",
                "conclusion": "defined outcome has measurable historical evidence",
            },
            parent_hashes=[validation.artifact_hash],
        )

    learning = ExperimentLearningRecord(
        experiment_id="golden-experiment",
        validation_id="golden-validation",
        hypothesis_id="golden-hypothesis",
        run_id="golden-run",
        hypothesis_accepted=True,
        findings=["validated finding persisted"],
        patterns_observed=["historical response pattern"],
        recommendations=["retain for future research"],
        confidence=0.8,
    )
    learning_certification = certify_experiment_learning(
        learning=learning,
        finding_hash=finding.artifact_hash,
        evidence_repository=evidence,
        research_repository=repo,
    )

    knowledge = Knowledge(
        type="Event_Impact",
        subject="XAUUSD",
        predicate="response",
        object="higher",
        confidence=0.8,
        source_references=[finding.artifact_hash],
        knowledge_trace="golden path certification",
    )
    knowledge_certification = certify_knowledge(
        finding_hash=finding.artifact_hash,
        knowledge=knowledge,
        evidence_repository=evidence,
        research_repository=repo,
    )

    retrieval = KnowledgeRetrieval(repo, evidence)
    results = retrieval.query_knowledge(
        subject="XAUUSD",
        predicate="response",
        object="higher",
    )
    traced = retrieval.retrieve(KnowledgeQuery(subject="XAUUSD"))[0]

    assert learning_certification.verify(evidence, repo)
    assert knowledge_certification.verify(evidence, repo)
    assert results == [knowledge_certification.knowledge]
    assert [node.artifact_type for node in traced.provenance] == [
        "Finding",
        "Validation",
        "Result",
        "Run",
        "Experiment",
        "Dataset",
    ]
    assert traced.provenance[-1].artifact_hash == dataset.artifact_hash
    assert evidence.verify_evidence() is True
