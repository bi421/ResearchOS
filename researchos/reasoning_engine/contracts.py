"""
Reasoning Engine — immutable domain contracts (Phase 4.5.1).

These are the frozen, validated dataclasses that define the Reasoning Engine's
shared vocabulary.  The Reasoning Engine transforms verified evidence into
structured reasoning (facts, hypotheses, and reasoning chains).

Design rules (ResearchOS engineering standards):
    - frozen dataclasses; immutable, hashable, deterministic.
    - stdlib only; no external dependencies.
    - No business logic inside contracts -- only invariant validation.
    - Range and emptiness invariants are enforced at construction time.

Based on Article X: Reasoning Engine -- contracts layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Tuple

# --------------------------------------------------------------------------- #
# Enumerations
# --------------------------------------------------------------------------- #


class EvidenceType(str, Enum):
    """
    Categories of evidence that may feed the reasoning pipeline.

    Based on Article X: Reasoning Engine -- Evidence Layer.
    """

    DATASET = "dataset"
    MEASUREMENT = "measurement"
    OBSERVATION = "observation"
    DOCUMENT = "document"


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class ReasoningContractError(Exception):
    """Base class for all reasoning-engine contract errors."""


class InvalidIdentifierError(ReasoningContractError):
    """Raised when a required identifier or text field is empty or malformed."""


class InvalidReliabilityScoreError(ReasoningContractError):
    """Raised when a reliability/confidence score falls outside [0.0, 1.0]."""


class InvalidEvidenceTypeError(ReasoningContractError):
    """Raised when an evidence type is not a recognised EvidenceType member."""


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #


def _require_nonempty(value: Any, name: str) -> str:
    """Validate that *value* is a non-empty string (whitespace-only is rejected)."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidIdentifierError(f"{name} must be a non-empty string")
    return value.strip()


def _require_score(value: Any, name: str) -> float:
    """Validate that *value* is a number within the closed interval [0.0, 1.0]."""
    if not isinstance(value, (int, float)):
        raise InvalidReliabilityScoreError(f"{name} must be a number, got {type(value).__name__}")
    score = float(value)
    if score < 0.0 or score > 1.0:
        raise InvalidReliabilityScoreError(f"{name} must be in the range [0.0, 1.0], got {score}")
    return score


def _require_evidence_type(value: Any) -> EvidenceType:
    """Coerce *value* into an :class:`EvidenceType` from an enum member or string."""
    if isinstance(value, EvidenceType):
        return value
    if isinstance(value, str):
        try:
            return EvidenceType(value)
        except ValueError:
            valid = ", ".join(member.value for member in EvidenceType)
            raise InvalidEvidenceTypeError(
                f"evidence_type {value!r} is not a valid EvidenceType; allowed values: {valid}"
            ) from None
    raise InvalidEvidenceTypeError(
        f"evidence_type must be an EvidenceType or str, got {type(value).__name__}"
    )


def _require_str_tuple(value: Any, name: str) -> Tuple[str, ...]:
    """Normalise a sequence of identifiers into an immutable tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    raise InvalidIdentifierError(
        f"{name} must be a list or tuple of strings, got {type(value).__name__}"
    )


# --------------------------------------------------------------------------- #
# ReasoningEvidence (canonical) — alias: EvidenceItem
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ReasoningEvidence:
    """
    A single piece of verified evidence that feeds into reasoning.

    Based on Article X: Reasoning Engine -- evidence contract.

    Attributes:
        id: Unique evidence identifier.
        source: Origin system or dataset that produced the evidence.
        evidence_type: Categorical type of the evidence.
        content_hash: Deterministic hash of the underlying content.
        reliability_score: Trustworthiness of the evidence in [0.0, 1.0].
    """

    id: str
    source: str
    evidence_type: EvidenceType
    content_hash: str
    reliability_score: float

    def __post_init__(self) -> None:
        """Enforce construction-time invariants on an otherwise immutable object."""
        object.__setattr__(self, "id", _require_nonempty(self.id, "id"))
        object.__setattr__(self, "source", _require_nonempty(self.source, "source"))
        object.__setattr__(
            self,
            "content_hash",
            _require_nonempty(self.content_hash, "content_hash"),
        )
        object.__setattr__(
            self,
            "evidence_type",
            _require_evidence_type(self.evidence_type),
        )
        object.__setattr__(
            self,
            "reliability_score",
            _require_score(self.reliability_score, "reliability_score"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "evidence_type": self.evidence_type.value,
            "content_hash": self.content_hash,
            "reliability_score": self.reliability_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningEvidence":
        """Reconstruct a :class:`ReasoningEvidence` from a ``to_dict()`` mapping."""
        return cls(
            id=str(data["id"]),
            source=str(data["source"]),
            evidence_type=data["evidence_type"],
            content_hash=str(data["content_hash"]),
            reliability_score=float(data["reliability_score"]),
        )


# Deprecated compatibility alias — canonical name is ``ReasoningEvidence``
# (renamed 2026-08-17 to end the collision with
# ``researchos.decision_engine.contracts.EvidenceItem``; the schemas are
# different bounded contexts and are NOT unified — see
# docs/architecture/OWNERSHIP.md).
EvidenceItem = ReasoningEvidence


# --------------------------------------------------------------------------- #
# Fact
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Fact:
    """
    A verified statement grounded in one or more pieces of evidence.

    Based on Article X: Reasoning Engine -- Fact contract.

    Attributes:
        statement: The asserted factual statement.
        evidence_ids: Immutable tuple of :class:`ReasoningEvidence` ids supporting the fact.
    """

    statement: str
    evidence_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        """Enforce construction-time invariants."""
        object.__setattr__(
            self,
            "statement",
            _require_nonempty(self.statement, "statement"),
        )
        object.__setattr__(
            self,
            "evidence_ids",
            _require_str_tuple(self.evidence_ids, "evidence_ids"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "statement": self.statement,
            "evidence_ids": list(self.evidence_ids),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Fact":
        """Reconstruct a :class:`Fact` from a ``to_dict()`` mapping."""
        return cls(
            statement=str(data["statement"]),
            evidence_ids=tuple(data.get("evidence_ids", [])),
        )


# --------------------------------------------------------------------------- #
# Hypothesis
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Hypothesis:
    """
    A testable prediction that may be supported by one or more facts.

    Based on Article X: Reasoning Engine -- Hypothesis contract.

    Attributes:
        statement: The testable prediction statement.
        supporting_facts: Immutable tuple of :class:`Fact` ids that support it.
        confidence: Confidence in the hypothesis in [0.0, 1.0].
    """

    statement: str
    supporting_facts: Tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        """Enforce construction-time invariants."""
        object.__setattr__(
            self,
            "statement",
            _require_nonempty(self.statement, "statement"),
        )
        object.__setattr__(
            self,
            "supporting_facts",
            _require_str_tuple(self.supporting_facts, "supporting_facts"),
        )
        object.__setattr__(
            self,
            "confidence",
            _require_score(self.confidence, "confidence"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "statement": self.statement,
            "supporting_facts": list(self.supporting_facts),
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hypothesis":
        """Reconstruct a :class:`Hypothesis` from a ``to_dict()`` mapping."""
        return cls(
            statement=str(data["statement"]),
            supporting_facts=tuple(data.get("supporting_facts", [])),
            confidence=float(data["confidence"]),
        )


__all__ = [
    "EvidenceType",
    "ReasoningEvidence",
    "EvidenceItem",
    "Fact",
    "Hypothesis",
    "ReasoningContractError",
    "InvalidIdentifierError",
    "InvalidReliabilityScoreError",
    "InvalidEvidenceTypeError",
]
