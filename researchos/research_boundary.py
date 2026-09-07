"""API-first boundary for deterministic research runs."""

from __future__ import annotations

from dataclasses import dataclass

from researchos.data_engine.boundary import ValidatedDatasetRef

RESEARCH_BOUNDARY_SCHEMA_VERSION = "research-boundary.v1"


@dataclass(frozen=True)
class ResearchInput:
    """Explicit research input contract.

    A research run can only identify its dataset through the validated data
    boundary. This prevents research code from bypassing data validation.
    """

    schema_version: str
    research_id: str
    question: str
    methodology_version: str
    dataset: ValidatedDatasetRef

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_BOUNDARY_SCHEMA_VERSION:
            raise ValueError("unsupported research boundary schema version")
        if not self.research_id or not self.question:
            raise ValueError("research_id and question are required")
        if not self.methodology_version:
            raise ValueError("methodology_version is required")
        if not self.dataset.is_valid:
            raise ValueError("research input requires a valid validated-dataset reference")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "research_id": self.research_id,
            "question": self.question,
            "methodology_version": self.methodology_version,
            "dataset": self.dataset.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ResearchInput:
        return cls(
            schema_version=str(data["schema_version"]),
            research_id=str(data["research_id"]),
            question=str(data["question"]),
            methodology_version=str(data["methodology_version"]),
            dataset=ValidatedDatasetRef.from_dict(dict(data["dataset"])),
        )


@dataclass(frozen=True)
class ResearchEvidenceLink:
    """Immutable lineage from research to its evidence/probability output."""

    schema_version: str
    research_id: str
    dataset_id: str
    dataset_content_hash: str
    dataset_hash: str
    evidence_collection_id: str
    assessment_hash: str
    methodology_version: str

    def __post_init__(self) -> None:
        if self.schema_version != RESEARCH_BOUNDARY_SCHEMA_VERSION:
            raise ValueError("unsupported research boundary schema version")
        for name, value in (
            ("research_id", self.research_id),
            ("dataset_id", self.dataset_id),
            ("dataset_content_hash", self.dataset_content_hash),
            ("dataset_hash", self.dataset_hash),
            ("evidence_collection_id", self.evidence_collection_id),
            ("assessment_hash", self.assessment_hash),
            ("methodology_version", self.methodology_version),
        ):
            if not value:
                raise ValueError(f"{name} is required")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "research_id": self.research_id,
            "dataset_id": self.dataset_id,
            "dataset_content_hash": self.dataset_content_hash,
            "dataset_hash": self.dataset_hash,
            "evidence_collection_id": self.evidence_collection_id,
            "assessment_hash": self.assessment_hash,
            "methodology_version": self.methodology_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ResearchEvidenceLink:
        return cls(
            schema_version=str(data["schema_version"]),
            research_id=str(data["research_id"]),
            dataset_id=str(data["dataset_id"]),
            dataset_content_hash=str(data["dataset_content_hash"]),
            dataset_hash=str(data["dataset_hash"]),
            evidence_collection_id=str(data["evidence_collection_id"]),
            assessment_hash=str(data["assessment_hash"]),
            methodology_version=str(data["methodology_version"]),
        )
