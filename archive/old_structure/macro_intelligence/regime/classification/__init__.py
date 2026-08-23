"""
ResearchOS Macro Intelligence Layer - Regime Classification Package

Provides deterministic regime classification from detection outputs.

All classifiers are:
- Pure functions (no mutable state)
- Deterministic (same input always produces same output)
- Stateless (no caches, no randomness)
- Rule-based (explainable, auditable)

Architecture invariants:
- MIL-REG-009: Classification is deterministic
- MIL-REG-010: Every classification has explainable rules
- MIL-REG-011: Classification preserves detector provenance
- MIL-REG-012: Rules are versioned and immutable
"""

from __future__ import annotations

from macro_intelligence.regime.classification.classifier import RegimeClassifier
from macro_intelligence.regime.classification.models import (
    ClassificationEvidence,
    ClassificationRule,
    RegimeClassification,
)
from macro_intelligence.regime.classification.rules import (
    ALL_RULES,
    GROWTH_INFLATION_RULES,
    LIQUIDITY_RULES,
    MONETARY_RULES,
    RISK_RULES,
    RULES_VERSION,
)
from macro_intelligence.regime.classification.taxonomy import (
    LIQUIDITY_REGIME_PRIORITY,
    MACRO_REGIME_PRIORITY,
    MONETARY_REGIME_PRIORITY,
    RISK_REGIME_PRIORITY,
    LiquidityRegime,
    MacroRegime,
    MonetaryRegime,
    RiskRegime,
)

__all__ = [
    # Taxonomy
    "MacroRegime",
    "LiquidityRegime",
    "RiskRegime",
    "MonetaryRegime",
    "MACRO_REGIME_PRIORITY",
    "LIQUIDITY_REGIME_PRIORITY",
    "RISK_REGIME_PRIORITY",
    "MONETARY_REGIME_PRIORITY",
    # Models
    "ClassificationRule",
    "ClassificationEvidence",
    "RegimeClassification",
    # Classifier
    "RegimeClassifier",
    # Rules
    "RULES_VERSION",
    "ALL_RULES",
    "GROWTH_INFLATION_RULES",
    "LIQUIDITY_RULES",
    "RISK_RULES",
    "MONETARY_RULES",
]
