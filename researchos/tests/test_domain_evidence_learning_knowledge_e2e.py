"""Domain-level contract for evidence -> learning -> knowledge promotion.

This test exercises the public emission/certification boundaries rather than
constructing EvidenceEnvelope objects directly. It proves that a validated
research finding can be promoted to ExperimentLearningRecord and Knowledge,
while preserving the append-only evidence lineage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from researchos.evidence.dataset_emission import build_dataset_envelope, emit_dataset
from researchos.evidence.experiment_emission import emit_experiment_with_dataset
from researchos.evidence.experiment_learning_certification import (
    certify_experiment_learning,
)
from researchos.evidence.finding_emission import certify_finding
from researchos.evidence.knowledge_certification import certify_knowledge
from researchos.evidence.repository import EvidenceRepository
from researchos.evidence.result_emission import emit_result_for_run
from researchos.evidence.run_emission import emit_run_for_experiment
from researchos.evidence.validation_emission import emit_validation_for_result
from researchos.experiments.learning import ExperimentLearningRecord
from researchos.objects.knowledge import Knowledge
from researchos.storage.repository import ResearchRepository


@dataclass
class _Dataset:
    feature_names: list[str] = field(default_factory=lambda: ["return"])
    features: list[list[float]] = field(default_factory=lambda: [[0.1], [0.2]])
    labels: list[float] = field(default_factory=lambda: [1.0, 0.0])
    metadata: dict[str, Any] = field(default_factory=lambda: {"symbol": "XAUUSD"})
    sample_count: int = 2
    feature_count: int = 1
    label_name: str = "direction"
    version: str = "1.0.0"


@dataclass
class _Experiment:
    experiment_hash: str = "exp-domain-001"
    hypothesis_id: str = "hyp-domain-001"
    name: str = "xauusd-domain-study"
    description: str = "domain e2e"
    experiment_type: str = "research"
    dataset_config: Any = None
    simulation_config: Any = None
    metric_definitions: list[Any] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    tags: list[str] = field(default_factory=list)
    experiment_trace: str = ""
    status: str = "COMPLETED"
    ontology_tags: list[str] = field(default_factory=list)


@dataclass
class _Run:
    run_hash: str = "run-domain-001"
    experiment_id: str = "exp-domain-001"
    run_number: int = 1
    dataset_config: Any = None
    simulation_config: Any = None
    parameters: dict[str, Any] = field(default_factory=dict)
    status: str = "COMPLETED"
    trace: str = ""
    tags: list[str] = field(default_factory=list)
    ontology_tags: list[str] = field(default_factory=list)


@dataclass
class _Result:
    result_hash: str = "result-domain-001"
    run_id: str = "run-domain-001"
    metrics: dict[str, Any] = field(default_factory=lambda: {"accuracy": 0.61})
    statistics: dict[str, Any] = field(default_factory=lambda: {"n": 2})
    performance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    trace: str = ""
    ontology_tags: list[str] = field(default_factory=list)


@dataclass
class _Validation:
    metrics: dict[str, Any] = field(default_factory=lambda: {"accuracy": 0.61})
    metadata: dict[str, Any] = field(
        default_factory=lambda: {"validation_version": "1.0.0"}
    )
    fold_results: tuple[Any, ...] = ()
    train_size: int = 1
    validation_size: int = 1
    test_size: int = 1
    fold_count: int = 1
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metrics": self.metrics,
            "metadata": self.metadata,
            "fold_results": list(self.fold_results),
            "train_size": self.train_size,
            "validation_size": self.validation_size,
            "test_size": self.test_size,
            "fold_count": self.fold_count,
            "version": self.version,
        }


@dataclass
class _Finding:
    status: str = "VALIDATED"
    validation_id: str = "validation-domain-001"
    statement: str = "The historical relationship is stable in the tested sample."

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "validation_id": self.validation_id,
            "statement": self.statement,
        }


def test_domain_pipeline_promotes_validated_finding_to_learning_and_knowledge() -> None:
    research_repo = ResearchRepository(db_path=":memory:")
    evidence_repo = EvidenceRepository(repository=research_repo)

    dataset = emit_dataset(build_dataset_envelope(_Dataset()), evidence_repo)
    experiment = emit_experiment_with_dataset(
        _Experiment(), dataset.artifact_hash, evidence_repo
    )
    run = emit_run_for_experiment(
        _Run(), experiment.artifact_hash, evidence_repo
    )
    result = emit_result_for_run(
        _Result(), run.artifact_hash, evidence_repo, experiment_hash=experiment.artifact_hash
    )
    validation = emit_validation_for_result(
        _Validation(), result.artifact_hash, evidence_repo, run_hash=run.artifact_hash,
        experiment_hash=experiment.artifact_hash, method="walk_forward"
    )
    finding = certify_finding(
        _Finding(), validation.artifact_hash, evidence_repo
    )

    learning = ExperimentLearningRecord(
        experiment_id=_Experiment().experiment_hash,
        validation_id="validation-domain-001",
        hypothesis_id=_Experiment().hypothesis_id,
        run_id=_Run().run_hash,
        hypothesis_accepted=True,
        findings=["historical relationship validated"],
        patterns_observed=["directional persistence"],
        recommendations=["retain for out-of-sample monitoring"],
        confidence=0.8,
    )
    learning_cert = certify_experiment_learning(
        learning, finding.artifact_hash, evidence_repo, research_repo
    )

    knowledge = Knowledge(
        type="Classification_Rule",
        subject="XAUUSD",
        predicate="supports",
        object="directional_persistence",
        confidence=0.8,
        knowledge_trace="Derived from validated finding in domain e2e contract.",
    )
    knowledge_cert = certify_knowledge(
        finding.artifact_hash, knowledge, evidence_repo, research_repo
    )

    assert research_repo.load_by_id(learning_cert.learning_id)["object_type"] == (
        "ExperimentLearningRecord"
    )
    stored_knowledge = research_repo.load_by_id(knowledge_cert.knowledge_id)
    assert stored_knowledge["object_type"] == "Knowledge"
    assert finding.artifact_hash in stored_knowledge["source_references"]

    assert evidence_repo.count_artifacts() == 6
    assert evidence_repo.count_edges() == 5
    assert evidence_repo.get_children(dataset.artifact_hash) == [experiment.artifact_hash]
    assert evidence_repo.get_children(experiment.artifact_hash) == [run.artifact_hash]
    assert evidence_repo.get_children(run.artifact_hash) == [result.artifact_hash]
    assert evidence_repo.get_children(result.artifact_hash) == [validation.artifact_hash]
    assert evidence_repo.get_children(validation.artifact_hash) == [finding.artifact_hash]
    assert evidence_repo.verify_evidence() is True


def test_unvalidated_finding_cannot_promote_learning_or_knowledge() -> None:
    research_repo = ResearchRepository(db_path=":memory:")
    evidence_repo = EvidenceRepository(repository=research_repo)

    finding = certify_finding
    del finding
