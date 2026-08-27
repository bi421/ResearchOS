"""
ResearchOS Macro Intelligence Layer - Relationship Engine Package

Provides deterministic historical relationship analysis between macro variables.

All relationship computations are:
- Pure functions (no mutable state)
- Deterministic (same input always produces same output)
- Stateless (no caches, no randomness)
- Provenance-preserving (output includes evidence references)

Architecture invariants:
- MIL-REL-001: Same input produces identical relationship output
- MIL-REL-002: Relationship objects are immutable
- MIL-REL-003: All relationships preserve provenance
- MIL-REL-004: Algorithms are versioned
- MIL-REL-005: No dependency on ResearchOS V1
- MIL-REL-006: Historical reconstruction is deterministic
"""

from __future__ import annotations

from researchos.macro.relationships.break_detection import (
    compare_correlation_windows,
    detect_structural_breaks,
)
from researchos.macro.relationships.correlation import (
    approximate_p_value,
    classify_relationship,
    compute_rolling_correlation,
    pearson_correlation,
    spearman_correlation,
)
from researchos.macro.relationships.engine import RelationshipEngine
from researchos.macro.relationships.lag_analysis import detect_reaction_delay, find_optimal_lag
from researchos.macro.relationships.models import (
    ALGORITHM_VERSION,
    BreakType,
    CorrelationResult,
    LagRelationship,
    LagType,
    RegimeRelationship,
    RelationshipResult,
    RelationshipStrength,
    RelationshipType,
    RollingCorrelationResult,
    StructuralBreak,
)
from researchos.macro.relationships.regime_relationship import (
    compute_all_regime_correlations,
    compute_regime_correlation,
)
from researchos.macro.relationships.rolling import analyze_relationship_stability, compute_rolling

__all__ = [
    # Models
    "ALGORITHM_VERSION",
    "RelationshipType",
    "RelationshipStrength",
    "LagType",
    "BreakType",
    "CorrelationResult",
    "RollingCorrelationResult",
    "LagRelationship",
    "RegimeRelationship",
    "StructuralBreak",
    "RelationshipResult",
    # Correlation
    "pearson_correlation",
    "spearman_correlation",
    "classify_relationship",
    "compute_rolling_correlation",
    "approximate_p_value",
    # Rolling
    "compute_rolling",
    "analyze_relationship_stability",
    # Lag analysis
    "find_optimal_lag",
    "detect_reaction_delay",
    # Regime relationships
    "compute_regime_correlation",
    "compute_all_regime_correlations",
    # Break detection
    "detect_structural_breaks",
    "compare_correlation_windows",
    # Engine
    "RelationshipEngine",
]
