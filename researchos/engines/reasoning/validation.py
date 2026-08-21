"""
Reasoning Engine -- deterministic evidence validation (Phase 4.5.2).

``EvidenceValidator`` determines whether an :class:`ReasoningEvidence` is
structurally ready for reasoning. It does NOT judge truth, does NOT verify
external data sources, and performs no filesystem or network access.

Validation rules (checked in fixed order so error output is deterministic):

    1. reliability_score >= 0.5
    2. content_hash length >= 8
    3. source must contain meaningful text (non-empty once stripped)
    4. id must be non-empty (non-empty once stripped)

Rules 3 and 4 are defensive invariants: the Phase 4.5.1 ``ReasoningEvidence``
contract already guarantees non-empty ``id``, ``source`` and ``content_hash``,
so these checks can never fail for a contract-valid item.  They exist so that the
validator's contract document stays self-describing and so that a future, more
lenient evidence item would still be gated.

The output is an immutable, hashable :class:`EvidenceRecord`.

Based on Article X: Reasoning Engine -- Evidence Validation Layer.
"""

from __future__ import annotations

from researchos.engines.reasoning.contracts import ReasoningEvidence
from researchos.engines.reasoning.evidence import EvidenceRecord


class EvidenceValidator:
    """
    Deterministic, stateless validator for :class:`ReasoningEvidence` objects.

    The same ``ReasoningEvidence`` always yields the same ``EvidenceRecord``.
    """

    MIN_RELIABILITY_SCORE: float = 0.5
    MIN_CONTENT_HASH_LENGTH: int = 8

    def validate(self, evidence: ReasoningEvidence) -> EvidenceRecord:
        """
        Validate a single evidence item.

        Returns an :class:`EvidenceRecord` whose ``validated`` flag is ``True``
        only when every rule passes.  All failing-rule messages are collected
        (never short-circuited) and reported in a deterministic order.
        """
        errors: list[str] = []

        # Rule 1
        if evidence.reliability_score < self.MIN_RELIABILITY_SCORE:
            errors.append("reliability_score below threshold")

        # Rule 2
        if len(evidence.content_hash) < self.MIN_CONTENT_HASH_LENGTH:
            errors.append("content_hash too short")

        # Rule 3 (defensive -- guaranteed by the ReasoningEvidence contract)
        if not evidence.source.strip():
            errors.append("source must contain meaningful text")

        # Rule 4 (defensive -- guaranteed by the ReasoningEvidence contract)
        if not evidence.id.strip():
            errors.append("id must be non-empty")

        return EvidenceRecord(
            evidence=evidence,
            validation_errors=tuple(errors),
        )


__all__ = ["EvidenceValidator"]
