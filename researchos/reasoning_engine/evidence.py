"""
Reasoning Engine -- evidence validation wrapper (Phase 4.5.2).

``EvidenceRecord`` is an immutable envelope around an :class:`ReasoningEvidence` that
reports whether the item is structurally ready for reasoning, and -- when it is
not -- the deterministic, human-readable reasons why.

Design rules (ResearchOS engineering standards):
    - frozen dataclass; immutable; hashable; deterministic.
    - stdlib only; no external dependencies.
    - No business logic beyond invariant enforcement.
    - ``validated`` is derived from ``validation_errors``: it is ``True`` exactly
      when there are no errors, guaranteeing the invariant can never be violated.

Based on Article X: Reasoning Engine -- Evidence Validation Layer.
"""

from __future__ import annotations

from dataclasses import dataclass

from researchos.reasoning_engine.contracts import ReasoningEvidence


@dataclass(frozen=True)
class EvidenceRecord:
    """
    An :class:`ReasoningEvidence` together with the outcome of validation.

    Attributes:
        evidence: The underlying, already-constructed evidence item.
        validated: ``True`` only when ``validation_errors`` is empty.
        validation_errors: Immutable tuple of human-readable validation failures.
    """

    evidence: ReasoningEvidence
    validated: bool = False
    validation_errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Canonicalise errors and derive ``validated`` from them."""
        object.__setattr__(
            self,
            "validation_errors",
            tuple(str(error) for error in self.validation_errors),
        )
        object.__setattr__(self, "validated", len(self.validation_errors) == 0)

    def to_dict(self) -> dict:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "evidence": self.evidence.to_dict(),
            "validated": self.validated,
            "validation_errors": list(self.validation_errors),
        }


__all__ = ["EvidenceRecord"]
