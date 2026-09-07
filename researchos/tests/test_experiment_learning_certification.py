import pytest

from researchos.evidence.envelope import build_envelope
from researchos.evidence.experiment_learning_certification import (
    certify_experiment_learning,
)
from researchos.evidence.repository import EvidenceRepository
from researchos.experiments.learning import ExperimentLearningRecord
from researchos.storage.repository import ResearchRepository


def _finding_repository(tmp_path, status="VALIDATED"):
    evidence_store = ResearchRepository(str(tmp_path / "evidence.db"))
    repository = EvidenceRepository(evidence_store)
    validation = build_envelope(
        artifact_type="Validation",
        payload={"validation_id": "validation-1", "status": "VALIDATED"},
        version="1.0.0",
        created_at="2026-09-07T00:00:00+00:00",
    )
    repository.append_artifact(validation)
    envelope = build_envelope(
        artifact_type="Finding",
        payload={"status": status, "validation_id": "validation-1"},
        version="1.0.0",
        created_at="2026-09-07T00:00:00+00:00",
        parent_hashes=(validation.artifact_hash,),
    )
    repository.append_artifact(envelope)
    return repository, envelope.artifact_hash


def test_experiment_learning_requires_validated_finding(tmp_path):
    evidence, finding_hash = _finding_repository(tmp_path)
    research = ResearchRepository(str(tmp_path / "research.db"))
    learning = ExperimentLearningRecord(
        experiment_id="experiment-1",
        validation_id="validation-1",
        hypothesis_id="hypothesis-1",
    )

    certification = certify_experiment_learning(
        learning,
        finding_hash,
        evidence,
        research,
    )

    assert certification.learning_id == learning.id
    assert certification.verify(evidence, research)
    assert research.load_by_id(learning.id)["object_type"] == "ExperimentLearningRecord"


def test_experiment_learning_rejects_non_validated_finding(tmp_path):
    evidence, finding_hash = _finding_repository(tmp_path, status="REJECTED")
    research = ResearchRepository(str(tmp_path / "research.db"))
    learning = ExperimentLearningRecord(
        experiment_id="experiment-1",
        validation_id="validation-1",
        hypothesis_id="hypothesis-1",
    )

    with pytest.raises(ValueError, match="VALIDATED"):
        certify_experiment_learning(learning, finding_hash, evidence, research)

    assert research.load_by_id(learning.id) is None


def test_experiment_learning_rejects_mismatched_validation(tmp_path):
    evidence, finding_hash = _finding_repository(tmp_path)
    research = ResearchRepository(str(tmp_path / "research.db"))
    learning = ExperimentLearningRecord(
        experiment_id="experiment-1",
        validation_id="validation-other",
        hypothesis_id="hypothesis-1",
    )

    with pytest.raises(ValueError, match="does not match Finding provenance"):
        certify_experiment_learning(learning, finding_hash, evidence, research)

    assert research.load_by_id(learning.id) is None
