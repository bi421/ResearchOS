"""
ResearchOS Macro Intelligence Layer - Knowledge Generation Rules

Immutable, versioned deterministic rules for knowledge generation.

Rules are permanent. Future changes create a new version (e.g.
know-rules/v1.1.0) rather than modifying existing rules.

Architecture invariants:
- MIL-KNOW-005: Algorithm versions are permanent
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# =============================================================================
# Rules version
# =============================================================================

KNOWLEDGE_RULES_VERSION = "know-rules/v1.0.0"


# =============================================================================
# Threshold constants
# =============================================================================

# Regime persistence detection
REGIME_PERSISTENCE_MIN_PERIODS = 8
REGIME_PERSISTENCE_MIN_CONFIDENCE = 0.60
REGIME_PERSISTENCE_MIN_CONTINUATION = 0.55

# Regime transition detection
REGIME_TRANSITION_MIN_CONFIDENCE = 0.60

# Persistent relationship detection
PERSISTENT_RELATIONSHIP_MIN_STABILITY = 0.15  # lower rolling std = more stable
PERSISTENT_RELATIONSHIP_MIN_ABS_CORR = 0.40
PERSISTENT_RELATIONSHIP_MIN_SAMPLE = 20

# Correlation break detection
CORRELATION_BREAK_MIN_CONFIDENCE = 0.50

# Anomaly detection
ANOMALY_MIN_ZSCORE = 2.0
ANOMALY_MIN_CONFIDENCE = 0.60

# Regime pattern detection
REGIME_PATTERN_MIN_CONFIDENCE = 0.60

# Risk-off / safe-haven detection
RISK_OFF_MIN_CONFIDENCE = 0.60
RISK_OFF_MIN_ABS_SAFE_HAVEN_CORR = 0.40

# Tightening volatility detection
TIGHTENING_VOL_MIN_CONFIDENCE = 0.60


# =============================================================================
# Rule record
# =============================================================================


@dataclass(frozen=True)
class KnowledgeRule:
    """
    A single immutable knowledge generation rule.

    Each rule is a versioned, deterministic predicate that maps a set of
    observed (frozen) inputs to a boolean decision.
    """

    rule_id: str
    rule_version: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "description": self.description,
            "parameters": dict(sorted(self.parameters.items())),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeRule:
        return cls(
            rule_id=data["rule_id"],
            rule_version=data["rule_version"],
            description=data["description"],
            parameters=data.get("parameters", {}),
        )

    def compute_hash(self) -> str:
        import hashlib
        import json

        hash_data = {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "parameters": dict(sorted(self.parameters.items())),
        }
        canonical = json.dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# =============================================================================
# Rule registry
# =============================================================================

RULES: dict[str, KnowledgeRule] = {
    "REGIME_PERSISTENCE": KnowledgeRule(
        rule_id="KNOW-001",
        rule_version=KNOWLEDGE_RULES_VERSION,
        description=("IF regime persists for at least REGIME_PERSISTENCE_MIN_PERIODS AND regime confidence >= REGIME_PERSISTENCE_MIN_CONFIDENCE AND continuation probability >= REGIME_PERSISTENCE_MIN_CONTINUATION THEN REGIME_PERSISTENCE knowledge"),
        parameters={
            "min_periods": REGIME_PERSISTENCE_MIN_PERIODS,
            "min_confidence": REGIME_PERSISTENCE_MIN_CONFIDENCE,
            "min_continuation": REGIME_PERSISTENCE_MIN_CONTINUATION,
        },
    ),
    "REGIME_TRANSITION": KnowledgeRule(
        rule_id="KNOW-002",
        rule_version=KNOWLEDGE_RULES_VERSION,
        description=("IF transition detected AND transition confidence >= REGIME_TRANSITION_MIN_CONFIDENCE THEN REGIME_TRANSITION knowledge"),
        parameters={
            "min_confidence": REGIME_TRANSITION_MIN_CONFIDENCE,
        },
    ),
    "PERSISTENT_RELATIONSHIP": KnowledgeRule(
        rule_id="KNOW-003",
        rule_version=KNOWLEDGE_RULES_VERSION,
        description=("IF correlation stability (rolling std) <= PERSISTENT_RELATIONSHIP_MIN_STABILITY AND abs(overall correlation) >= PERSISTENT_RELATIONSHIP_MIN_ABS_CORR AND sample size >= PERSISTENT_RELATIONSHIP_MIN_SAMPLE THEN PERSISTENT_RELATIONSHIP knowledge"),
        parameters={
            "min_stability": PERSISTENT_RELATIONSHIP_MIN_STABILITY,
            "min_abs_corr": PERSISTENT_RELATIONSHIP_MIN_ABS_CORR,
            "min_sample": PERSISTENT_RELATIONSHIP_MIN_SAMPLE,
        },
    ),
    "CORRELATION_BREAK": KnowledgeRule(
        rule_id="KNOW-004",
        rule_version=KNOWLEDGE_RULES_VERSION,
        description=("IF any structural break detected AND break confidence >= CORRELATION_BREAK_MIN_CONFIDENCE THEN CORRELATION_BREAK knowledge"),
        parameters={
            "min_confidence": CORRELATION_BREAK_MIN_CONFIDENCE,
        },
    ),
    "ANOMALY": KnowledgeRule(
        rule_id="KNOW-005",
        rule_version=KNOWLEDGE_RULES_VERSION,
        description=("IF a feature z-score magnitude >= ANOMALY_MIN_ZSCORE AND feature confidence >= ANOMALY_MIN_CONFIDENCE THEN ANOMALY knowledge"),
        parameters={
            "min_zscore": ANOMALY_MIN_ZSCORE,
            "min_confidence": ANOMALY_MIN_CONFIDENCE,
        },
    ),
    "REGIME_PATTERN": KnowledgeRule(
        rule_id="KNOW-006",
        rule_version=KNOWLEDGE_RULES_VERSION,
        description=("IF a dominant regime pattern is observed AND regime confidence >= REGIME_PATTERN_MIN_CONFIDENCE THEN REGIME_PATTERN knowledge"),
        parameters={
            "min_confidence": REGIME_PATTERN_MIN_CONFIDENCE,
        },
    ),
    "RISK_OFF_SAFE_HAVEN": KnowledgeRule(
        rule_id="KNOW-007",
        rule_version=KNOWLEDGE_RULES_VERSION,
        description=("IF risk regime is risk-off AND risk confidence >= RISK_OFF_MIN_CONFIDENCE AND abs(safe-haven correlation) >= RISK_OFF_MIN_ABS_SAFE_HAVEN_CORR THEN RISK_OFF_SAFE_HAVEN knowledge"),
        parameters={
            "min_confidence": RISK_OFF_MIN_CONFIDENCE,
            "min_abs_safe_haven_corr": RISK_OFF_MIN_ABS_SAFE_HAVEN_CORR,
        },
    ),
    "TIGHTENING_VOLATILITY": KnowledgeRule(
        rule_id="KNOW-008",
        rule_version=KNOWLEDGE_RULES_VERSION,
        description=("IF monetary regime is tightening AND volatility is elevated AND tightening confidence >= TIGHTENING_VOL_MIN_CONFIDENCE THEN TIGHTENING_VOLATILITY knowledge"),
        parameters={
            "min_confidence": TIGHTENING_VOL_MIN_CONFIDENCE,
        },
    ),
}


def get_rule(knowledge_type: str) -> KnowledgeRule | None:
    """Return the immutable rule for a knowledge type, or None."""
    return RULES.get(knowledge_type)


def get_rules_version() -> str:
    """Return the current immutable rules version."""
    return KNOWLEDGE_RULES_VERSION
