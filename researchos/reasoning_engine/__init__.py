"""
ResearchOS Reasoning Engine.

The Reasoning Engine transforms verified evidence into structured reasoning
(facts, hypotheses, and reasoning chains). It does NOT generate unsupported
conclusions, does NOT use LLMs or embeddings, does NOT consult vector databases,
and does NOT make autonomous decisions or perform trading logic.

Phase 4.5.1 exposes only the immutable domain contracts (Contracts Layer).
Reasoning algorithms are intentionally deferred to later phases.

Based on Article X: Reasoning Engine.
"""

from researchos.reasoning_engine.contracts import (
    EvidenceItem,
    EvidenceType,
    Fact,
    Hypothesis,
)

__version__ = "1.0.0"
__status__ = "Phase 4.5.1 - Reasoning Engine Contracts Foundation"

__all__ = [
    "EvidenceType",
    "EvidenceItem",
    "Fact",
    "Hypothesis",
]
