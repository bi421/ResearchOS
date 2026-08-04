"""
ResearchOS Macro Intelligence Layer - Knowledge Confidence Calculation

The ConfidenceCalculator is a deterministic, weighted aggregation of
frozen upstream quality signals. It never uses randomness.

Component weights (deterministic, versioned):

    Evidence quality             30%
    Feature quality              20%
    Relationship stability       20%
    Regime confidence            20%
    Historical consistency       10%

Output is a single float in [0.0, 1.0].

Architecture invariants:
- MIL-KNOW-004: Knowledge generation is deterministic
- MIL-KNOW-005: Algorithm versions are permanent
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from macro_intelligence.knowledge.models import ALGORITHM_VERSION


# =============================================================================
# Deterministic component weights
# =============================================================================

# Versioned weight set (immutable). Future changes create a new version set.
CONFIDENCE_WEIGHTS_VERSION = "know-conf/v1.0.0"

CONFIDENCE_WEIGHTS: dict[str, float] = {
    "evidence_quality": 0.30,
    "feature_quality": 0.20,
    "relationship_stability": 0.20,
    "regime_confidence": 0.20,
    "historical_consistency": 0.10,
}


@dataclass(frozen=True)
class ConfidenceComponents:
    """
    Immutable record of the raw component scores used by the calculator.

    Each component is an optional float in [0.0, 1.0]. Missing components
    contribute 0.0 to the weighted sum.
    """

    evidence_quality: float | None = None
    feature_quality: float | None = None
    relationship_stability: float | None = None
    regime_confidence: float | None = None
    historical_consistency: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_quality": self.evidence_quality,
            "feature_quality": self.feature_quality,
            "relationship_stability": self.relationship_stability,
            "regime_confidence": self.regime_confidence,
            "historical_consistency": self.historical_consistency,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConfidenceComponents:
        return cls(
            evidence_quality=data.get("evidence_quality"),
            feature_quality=data.get("feature_quality"),
            relationship_stability=data.get("relationship_stability"),
            regime_confidence=data.get("regime_confidence"),
            historical_consistency=data.get("historical_consistency"),
        )


class ConfidenceCalculator:
    """
    Deterministic confidence calculator.

    Stateless and pure: same inputs always produce the same output.
    """

    def __init__(self) -> None:
        self._version = ALGORITHM_VERSION
        self._weights_version = CONFIDENCE_WEIGHTS_VERSION
        self._weights = dict(CONFIDENCE_WEIGHTS)

    @property
    def version(self) -> str:
        return self._version

    @property
    def weights_version(self) -> str:
        return self._weights_version

    @property
    def weights(self) -> dict[str, float]:
        return dict(self._weights)

    def _clamp(self, value: float | None) -> float:
        """Clamp a component to [0.0, 1.0]; missing -> 0.0."""
        if value is None:
            return 0.0
        return max(0.0, min(1.0, float(value)))

    def compute(
        self,
        components: ConfidenceComponents,
    ) -> float:
        """
        Compute the deterministic weighted confidence.

        Args:
            components: The frozen component scores.

        Returns:
            A float in [0.0, 1.0].
        """
        contribution = (
            self._weights["evidence_quality"] * self._clamp(components.evidence_quality)
            + self._weights["feature_quality"] * self._clamp(components.feature_quality)
            + self._weights["relationship_stability"]
            * self._clamp(components.relationship_stability)
            + self._weights["regime_confidence"] * self._clamp(components.regime_confidence)
            + self._weights["historical_consistency"]
            * self._clamp(components.historical_consistency)
        )
        return round(contribution, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self._version,
            "weights_version": self._weights_version,
            "weights": dict(sorted(self._weights.items())),
        }
