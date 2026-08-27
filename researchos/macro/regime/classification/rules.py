"""
ResearchOS Macro Intelligence Layer - Classification Rules

Immutable, versioned rules for regime classification.
All rules are defined as frozen ClassificationRule instances.
"""

from __future__ import annotations

from researchos.macro.regime.classification.models import ClassificationRule

# =============================================================================
# Algorithm version
# =============================================================================

RULES_VERSION = "cls-rules/v3.0.0"

# =============================================================================
# Growth/Inflation Classification Rules
# =============================================================================

GROWTH_INFLATION_RULES: list[ClassificationRule] = [
    # RECESSION: High inflation + Contraction
    ClassificationRule(
        rule_id="GI-001",
        rule_version=RULES_VERSION,
        conditions={"inflation": "high", "growth": "contraction"},
        result_regime="recession",
        description="High inflation with economic contraction",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    # DEFLATIONARY_SLOWDOWN: Deflationary + Slowdown
    ClassificationRule(
        rule_id="GI-002",
        rule_version=RULES_VERSION,
        conditions={"inflation": "deflationary", "growth": "slowdown"},
        result_regime="deflationary_slowdown",
        description="Deflationary pressures with economic slowdown",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    # STAGFLATION: Rising/High inflation + Slowdown/Contraction
    ClassificationRule(
        rule_id="GI-003",
        rule_version=RULES_VERSION,
        conditions={"inflation": "rising", "growth": "slowdown"},
        result_regime="stagflation",
        description="Rising inflation with economic slowdown",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="GI-004",
        rule_version=RULES_VERSION,
        conditions={"inflation": "high", "growth": "slowdown"},
        result_regime="stagflation",
        description="High inflation with economic slowdown",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    # DISINFLATION: Falling inflation + Weak growth
    ClassificationRule(
        rule_id="GI-005",
        rule_version=RULES_VERSION,
        conditions={"inflation": "falling", "growth": "slowdown"},
        result_regime="disinflation",
        description="Falling inflation with economic slowdown",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="GI-006",
        rule_version=RULES_VERSION,
        conditions={"inflation": "falling", "growth": "contraction"},
        result_regime="disinflation",
        description="Falling inflation with economic contraction",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    # INFLATIONARY_GROWTH: Rising/High inflation + Expansion
    ClassificationRule(
        rule_id="GI-007",
        rule_version=RULES_VERSION,
        conditions={"inflation": "rising", "growth": "expansion"},
        result_regime="inflationary_growth",
        description="Rising inflation with economic expansion",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="GI-008",
        rule_version=RULES_VERSION,
        conditions={"inflation": "high", "growth": "expansion"},
        result_regime="inflationary_growth",
        description="High inflation with economic expansion",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="GI-009",
        rule_version=RULES_VERSION,
        conditions={"inflation": "rising", "growth": "recovery"},
        result_regime="inflationary_growth",
        description="Rising inflation with economic recovery",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    # GOLDILOCKS: Stable/Low inflation + Expansion/Recovery
    ClassificationRule(
        rule_id="GI-010",
        rule_version=RULES_VERSION,
        conditions={"inflation": "stable", "growth": "expansion"},
        result_regime="goldilocks",
        description="Stable inflation with economic expansion",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="GI-011",
        rule_version=RULES_VERSION,
        conditions={"inflation": "low", "growth": "expansion"},
        result_regime="goldilocks",
        description="Low inflation with economic expansion",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="GI-012",
        rule_version=RULES_VERSION,
        conditions={"inflation": "stable", "growth": "recovery"},
        result_regime="goldilocks",
        description="Stable inflation with economic recovery",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="GI-013",
        rule_version=RULES_VERSION,
        conditions={"inflation": "low", "growth": "recovery"},
        result_regime="goldilocks",
        description="Low inflation with economic recovery",
        provenance="MIL-REG-009: Deterministic classification",
    ),
]

# =============================================================================
# Liquidity Classification Rules
# =============================================================================

LIQUIDITY_RULES: list[ClassificationRule] = [
    ClassificationRule(
        rule_id="LIQ-001",
        rule_version=RULES_VERSION,
        conditions={"liquidity": "expanding"},
        result_regime="liquidity_expansion",
        description="Liquidity conditions expanding",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="LIQ-002",
        rule_version=RULES_VERSION,
        conditions={"liquidity": "contracting"},
        result_regime="liquidity_contraction",
        description="Liquidity conditions contracting",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="LIQ-003",
        rule_version=RULES_VERSION,
        conditions={"liquidity": "neutral"},
        result_regime="liquidity_neutral",
        description="Liquidity conditions neutral",
        provenance="MIL-REG-009: Deterministic classification",
    ),
]

# =============================================================================
# Risk Classification Rules
# =============================================================================

RISK_RULES: list[ClassificationRule] = [
    ClassificationRule(
        rule_id="RISK-001",
        rule_version=RULES_VERSION,
        conditions={"risk": "crisis"},
        result_regime="crisis",
        description="Financial crisis conditions",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="RISK-002",
        rule_version=RULES_VERSION,
        conditions={"risk": "risk_off"},
        result_regime="risk_off",
        description="Risk-off market conditions",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="RISK-003",
        rule_version=RULES_VERSION,
        conditions={"risk": "risk_on"},
        result_regime="risk_on",
        description="Risk-on market conditions",
        provenance="MIL-REG-009: Deterministic classification",
    ),
]

# =============================================================================
# Monetary Classification Rules
# =============================================================================

MONETARY_RULES: list[ClassificationRule] = [
    ClassificationRule(
        rule_id="MON-001",
        rule_version=RULES_VERSION,
        conditions={"monetary": "hawkish"},
        result_regime="fed_hawkish",
        description="Hawkish monetary policy",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="MON-002",
        rule_version=RULES_VERSION,
        conditions={"monetary": "dovish"},
        result_regime="fed_dovish",
        description="Dovish monetary policy",
        provenance="MIL-REG-009: Deterministic classification",
    ),
    ClassificationRule(
        rule_id="MON-003",
        rule_version=RULES_VERSION,
        conditions={"monetary": "neutral"},
        result_regime="fed_neutral",
        description="Neutral monetary policy",
        provenance="MIL-REG-009: Deterministic classification",
    ),
]

# =============================================================================
# All rules indexed by category
# =============================================================================

ALL_RULES: dict[str, list[ClassificationRule]] = {
    "growth_inflation": GROWTH_INFLATION_RULES,
    "liquidity": LIQUIDITY_RULES,
    "risk": RISK_RULES,
    "monetary": MONETARY_RULES,
}
