"""
ResearchOS Macro Intelligence Layer - Knowledge Generation Package

The Knowledge Layer is the final interpretation layer inside the Macro
Intelligence Layer. It converts previously computed information into
structured, explainable, deterministic knowledge objects.

Dependency direction (never bypassed):

    contracts -> evidence -> features -> statistics -> relationships
        -> regime intelligence -> knowledge generation -> macro context

Architecture invariants:
- MIL-KNOW-001: Knowledge objects are immutable
- MIL-KNOW-002: Every knowledge object preserves complete provenance
- MIL-KNOW-003: Same inputs produce identical knowledge
- MIL-KNOW-004: Knowledge generation is deterministic
- MIL-KNOW-005: Algorithm versions are permanent
- MIL-KNOW-006: Source evidence and features are never mutated
"""

from __future__ import annotations

from researchos.macro.knowledge.confidence import (
    CONFIDENCE_WEIGHTS,
    CONFIDENCE_WEIGHTS_VERSION,
    ConfidenceCalculator,
    ConfidenceComponents,
)
from researchos.macro.knowledge.context import MacroContextBuilder
from researchos.macro.knowledge.evidence_link import (
    EvidenceLink,
    EvidenceLinker,
)
from researchos.macro.knowledge.generator import (
    KnowledgeGenerator,
    KnowledgeInputs,
)
from researchos.macro.knowledge.models import (
    ALGORITHM_VERSION,
    KnowledgeObject,
    KnowledgeProvenance,
    KnowledgeType,
    MacroContext,
)
from researchos.macro.knowledge.pattern import (
    PatternDetector,
    PatternFinding,
)
from researchos.macro.knowledge.rules import (
    KNOWLEDGE_RULES_VERSION,
    RULES,
    KnowledgeRule,
    get_rule,
    get_rules_version,
)

__all__ = [
    # Models
    "ALGORITHM_VERSION",
    "KnowledgeType",
    "KnowledgeProvenance",
    "KnowledgeObject",
    "MacroContext",
    # Rules
    "KNOWLEDGE_RULES_VERSION",
    "KnowledgeRule",
    "RULES",
    "get_rule",
    "get_rules_version",
    # Evidence linking
    "EvidenceLink",
    "EvidenceLinker",
    # Pattern detection
    "PatternFinding",
    "PatternDetector",
    # Confidence
    "CONFIDENCE_WEIGHTS_VERSION",
    "CONFIDENCE_WEIGHTS",
    "ConfidenceComponents",
    "ConfidenceCalculator",
    # Generator
    "KnowledgeInputs",
    "KnowledgeGenerator",
    # Context builder
    "MacroContextBuilder",
]
