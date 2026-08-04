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

from macro_intelligence.relationships.models import (
    ALGORITHM_VERSION,
    RelationshipType,
    RelationshipStrength,
    LagType,
    BreakType,
    CorrelationResult,
    RollingCorrelationResult,
    LagRelationship,
    RegimeRelationship,
    StructuralBreak,
    RelationshipResult,
)
from macro_intelligence.relationships.correlation import (
    pearson_correlation,
    spearman_correlation,
    classify_relationship,
    compute_rolling_correlation,
    approximate_p_value,
)
from macro_intelligence.relationships.rolling import compute_rolling, analyze_relationship_stability
from macro_intelligence.relationships.lag_analysis import find_optimal_lag, detect_reaction_delay
from macro_intelligence.relationships.regime_relationship import (
    compute_regime_correlation,
    compute_all_regime_correlations,
)
from macro_intelligence.relationships.break_detection import (
    detect_structural_breaks,
    compare_correlation_windows,
)
from macro_intelligence.relationships.engine import RelationshipEngine

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
