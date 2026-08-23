"""
ResearchOS Macro Intelligence Layer - Macro Context Builder

The MacroContextBuilder aggregates deterministic knowledge objects into an
immutable MacroContext (a synthesis view for downstream consumption).

This is NOT a trading decision. It is a structured, explainable collection
of knowledge artifacts plus the regime context they describe.

Architecture invariants:
- MIL-KNOW-003: Same inputs produce identical context
- MIL-KNOW-004: Context generation is deterministic
- MIL-KNOW-005: Algorithm versions are permanent
"""

from __future__ import annotations

import hashlib
from typing import Any

from macro_intelligence.knowledge.models import (
    ALGORITHM_VERSION,
    KnowledgeObject,
    MacroContext,
)


class MacroContextBuilder:
    """
    Deterministic builder of macro context from knowledge objects.

    Stateless and pure. It never mutates the knowledge objects it receives.
    """

    def __init__(self) -> None:
        self._version = ALGORITHM_VERSION

    @property
    def version(self) -> str:
        return self._version

    def _generate_context_id(
        self,
        regime_context: str,
        knowledge_objects: tuple[KnowledgeObject, ...],
    ) -> str:
        """Deterministic context id from stable inputs."""
        semantic = {
            "regime_context": regime_context,
            "knowledge_hashes": sorted(k.compute_hash() for k in knowledge_objects),
            "algorithm_version": ALGORITHM_VERSION,
        }
        canonical = __import__("json").dumps(semantic, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        return f"CTX_{digest}"

    def build(
        self,
        knowledge_objects: list[KnowledgeObject],
        regime_context: str = "",
    ) -> MacroContext:
        """
        Build an immutable MacroContext from knowledge objects.

        Args:
            knowledge_objects: Deterministic knowledge objects (not mutated).
            regime_context: Regime context label (identifier).

        Returns:
            An immutable MacroContext.
        """
        # Deterministic ordering
        ordered = tuple(sorted(knowledge_objects, key=lambda k: k.knowledge_id))
        context_id = self._generate_context_id(regime_context, ordered)
        return MacroContext(
            context_id=context_id,
            regime_context=regime_context,
            knowledge_objects=ordered,
            algorithm_version=ALGORITHM_VERSION,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self._version,
        }
