"""
Research Evaluation Engine — immutable contracts (Q16).

Evaluates historical research runs stored by PipelineRepository.

Design rules:
    - frozen dataclasses; immutable; hashable; deterministic.
    - stdlib only; no randomness.
    - metadata uses MappingProxyType.
    - No modifications to any locked module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

EVALUATION_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# error hierarchy
# ---------------------------------------------------------------------------


class EvaluationError(Exception):
    """Base class for all evaluation-layer errors."""


class InvalidEvaluationError(EvaluationError):
    """Raised when an evaluation score or report is malformed."""


class PipelineEvaluationError(EvaluationError):
    """Raised when a pipeline cannot be evaluated (missing, etc.)."""


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _freeze(value: Any) -> Any:
    """Recursively convert a mapping/list value into a hashable form."""
    if isinstance(value, Mapping):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _as_immutable_mapping(value: Any) -> MappingProxyType:
    """Normalise a metadata value to an immutable mapping."""
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    raise InvalidEvaluationError(f"metadata must be a mapping, got {type(value).__name__}")


def _validate_identifier(value: Any, name: str) -> str:
    """Ensure a required identifier is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidEvaluationError(f"{name} must be a non-empty string")
    return value.strip()


def _grade(overall: float) -> str:
    """Deterministic letter grade from an overall score in [0, 1]."""
    if overall >= 0.95:
        return "A+"
    if overall >= 0.85:
        return "A"
    if overall >= 0.75:
        return "B+"
    if overall >= 0.65:
        return "B"
    if overall >= 0.55:
        return "C+"
    if overall >= 0.45:
        return "C"
    if overall >= 0.35:
        return "D+"
    if overall >= 0.25:
        return "D"
    return "F"


# ---------------------------------------------------------------------------
# EvaluationScore
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationScore:
    """Immutable, hashable, serializable evaluation score.

    Attributes:
        pipeline_id: The pipeline being evaluated.
        reproducibility_score: Same-input → same-output consistency [0, 1].
        stability_score: Variance of repeated research outcomes [0, 1].
        evidence_score: Quality of supporting evidence [0, 1].
        overall_score: Weighted deterministic aggregation [0, 1].
        grade: Letter grade derived from overall_score.
        metadata: Immutable mapping of extra evaluation metadata.
    """

    pipeline_id: str
    reproducibility_score: float
    stability_score: float
    evidence_score: float
    overall_score: float
    grade: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate identifiers and freeze metadata."""
        object.__setattr__(
            self,
            "pipeline_id",
            _validate_identifier(self.pipeline_id, "pipeline_id"),
        )
        for name in (
            "reproducibility_score",
            "stability_score",
            "evidence_score",
            "overall_score",
        ):
            value = getattr(self, name)
            if not isinstance(value, (int, float)):
                raise InvalidEvaluationError(f"{name} must be a number")
            clamped = max(0.0, min(1.0, float(value)))
            object.__setattr__(self, name, clamped)
        if not isinstance(self.grade, str) or not self.grade:
            raise InvalidEvaluationError("grade must be a non-empty string")
        object.__setattr__(self, "metadata", _as_immutable_mapping(self.metadata))

    def __hash__(self) -> int:
        return hash(
            (
                self.pipeline_id,
                self.reproducibility_score,
                self.stability_score,
                self.evidence_score,
                self.overall_score,
                self.grade,
                _freeze(self.metadata),
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "reproducibility_score": self.reproducibility_score,
            "stability_score": self.stability_score,
            "evidence_score": self.evidence_score,
            "overall_score": self.overall_score,
            "grade": self.grade,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvaluationScore:
        """Reconstruct an ``EvaluationScore`` from a ``to_dict()`` mapping.

        Raises:
            InvalidEvaluationError: If the payload is malformed.
        """
        try:
            return cls(
                pipeline_id=str(data["pipeline_id"]),
                reproducibility_score=float(data["reproducibility_score"]),
                stability_score=float(data["stability_score"]),
                evidence_score=float(data["evidence_score"]),
                overall_score=float(data["overall_score"]),
                grade=str(data["grade"]),
                metadata=dict(data.get("metadata", {})),
            )
        except KeyError as exc:
            raise InvalidEvaluationError(f"missing key: {exc.args[0]}") from None
        except (TypeError, ValueError) as exc:
            raise InvalidEvaluationError(f"invalid evaluation score: {exc}") from None


# ---------------------------------------------------------------------------
# EvaluationReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvaluationReport:
    """Immutable, hashable, serializable evaluation report.

    Attributes:
        evaluation_id: Deterministic content-derived identifier.
        pipeline_id: The pipeline being evaluated.
        score: The ``EvaluationScore``.
        created_at: Deterministic timestamp string (default ``""``).
        version: Evaluation schema version.
    """

    evaluation_id: str
    pipeline_id: str
    score: EvaluationScore
    created_at: str
    version: str

    def __post_init__(self) -> None:
        """Validate identifiers."""
        object.__setattr__(
            self,
            "evaluation_id",
            _validate_identifier(self.evaluation_id, "evaluation_id"),
        )
        object.__setattr__(
            self,
            "pipeline_id",
            _validate_identifier(self.pipeline_id, "pipeline_id"),
        )
        if not isinstance(self.score, EvaluationScore):
            raise InvalidEvaluationError("score must be an EvaluationScore")
        object.__setattr__(self, "created_at", str(self.created_at))
        object.__setattr__(
            self,
            "version",
            _validate_identifier(self.version, "version"),
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.evaluation_id,
                self.pipeline_id,
                hash(self.score),
                self.created_at,
                self.version,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "evaluation_id": self.evaluation_id,
            "pipeline_id": self.pipeline_id,
            "score": self.score.to_dict(),
            "created_at": self.created_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EvaluationReport:
        """Reconstruct an ``EvaluationReport`` from a ``to_dict()`` mapping.

        Raises:
            InvalidEvaluationError: If the payload is malformed.
        """
        try:
            score_data = data["score"]
            if not isinstance(score_data, Mapping):
                raise InvalidEvaluationError("score must be a mapping")
            return cls(
                evaluation_id=str(data["evaluation_id"]),
                pipeline_id=str(data["pipeline_id"]),
                score=EvaluationScore.from_dict(score_data),
                created_at=str(data.get("created_at", "")),
                version=str(data["version"]),
            )
        except KeyError as exc:
            raise InvalidEvaluationError(f"missing key: {exc.args[0]}") from None
        except EvaluationError:
            raise
        except (TypeError, ValueError) as exc:
            raise InvalidEvaluationError(f"invalid evaluation report: {exc}") from None


__all__ = [
    "EVALUATION_VERSION",
    "EvaluationError",
    "EvaluationReport",
    "EvaluationScore",
    "InvalidEvaluationError",
    "PipelineEvaluationError",
]
