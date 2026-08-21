"""
Confidence objects — probability estimates with uncertainty bounds.

Based on Article XVII: Object Model — Confidence Layer.
Based on Article XVI: Scientific Reasoning Framework — Confidence Framework.

Confidence is derived from 5 sources and adjusted by penalties and boosters.
"""

from __future__ import annotations

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage

# Confidence source weights (Article XVI, Section 6.1)
CONF_EVIDENCE_STRENGTH = 0.30
CONF_COHERENCE = 0.25
CONF_HISTORICAL_PRECEDENT = 0.20
CONF_MODEL_UNCERTAINTY = 0.15
CONF_RECENCY = 0.10

# Calibration parameters (Article XVI, Section 6.4)
CALIBRATION_BIN_WIDTH = 0.1
CALIBRATION_THRESHOLD = 0.05


class Confidence(BaseObject):
    """
    A probability estimate with uncertainty bounds.

    Based on Article XVII: Object Model — Confidence.

    Confidence is derived from 5 sources:
        1. Evidence Strength (0.30)
        2. Coherence (0.25)
        3. Historical Precedent (0.20)
        4. Model Uncertainty (0.15)
        5. Recency (0.10)

    Attributes:
        target_id: ID of the object being assessed
        target_type: Type of the target object
        value: The confidence estimate (0.0-1.0)
        calibrated_value: After calibration
        lower_bound: Confidence interval lower bound
        upper_bound: Confidence interval upper bound
        standard_error: Statistical measure of variability
        evidence_strength: Factor 1 (weight 0.30)
        coherence: Factor 2 (weight 0.25)
        historical_precedent: Factor 3 (weight 0.20)
        model_uncertainty: Factor 4 (weight 0.15)
        recency: Factor 5 (weight 0.10)
        penalties: Applied penalties
        boosters: Applied boosters
        calibration_bin: Bin identifier (e.g., "0.7-0.8")
        calibration_adjustment: Adjustment applied
    """

    def __init__(
        self,
        target_id: str,
        target_type: str,
        evidence_strength: float = 0.0,
        coherence: float = 0.0,
        historical_precedent: float = 0.0,
        model_uncertainty: float = 0.0,
        recency: float = 0.0,
        penalties: list[str] | None = None,
        boosters: list[str] | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"Confidence|{target_id}|{target_type}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.target_id = target_id
        self.target_type = target_type
        self.evidence_strength = evidence_strength
        self.coherence = coherence
        self.historical_precedent = historical_precedent
        self.model_uncertainty = model_uncertainty
        self.recency = recency
        self.penalties: list[str] = penalties or []
        self.boosters: list[str] = boosters or []

        # Compute confidence value
        self.value = self._compute_value()
        self.calibrated_value = self.value
        self.lower_bound = max(0.0, self.value - 0.1)
        self.upper_bound = min(1.0, self.value + 0.1)
        self.standard_error = 0.05
        self.calibration_bin = self._compute_calibration_bin()
        self.calibration_adjustment = 0.0

        self.lifecycle.transition(
            LifecycleStage.CALIBRATED,
            reason="Confidence computed and calibrated",
        )

    def _compute_value(self) -> float:
        """
        Compute confidence from 5 sources.

        Value = Evidence_Strength × 0.30 + Coherence × 0.25 +
                Historical_Precedent × 0.20 + Model_Uncertainty × 0.15 +
                Recency × 0.10
        """
        value = (
            self.evidence_strength * CONF_EVIDENCE_STRENGTH
            + self.coherence * CONF_COHERENCE
            + self.historical_precedent * CONF_HISTORICAL_PRECEDENT
            + self.model_uncertainty * CONF_MODEL_UNCERTAINTY
            + self.recency * CONF_RECENCY
        )
        return min(1.0, max(0.0, value))

    def _compute_calibration_bin(self) -> str:
        """Compute the calibration bin for this confidence value."""
        bin_lower = int(self.value / CALIBRATION_BIN_WIDTH) * CALIBRATION_BIN_WIDTH
        bin_upper = bin_lower + CALIBRATION_BIN_WIDTH
        return f"{bin_lower:.1f}-{bin_upper:.1f}"

    def apply_calibration(self, observed_frequency: float) -> None:
        """
        Apply calibration adjustment based on observed frequency.

        If observed frequency differs from bin midpoint by more than
        the calibration threshold, an adjustment is applied.
        """
        bin_midpoint = float(self.calibration_bin.split("-")[0]) + CALIBRATION_BIN_WIDTH / 2
        difference = observed_frequency - bin_midpoint

        if abs(difference) > CALIBRATION_THRESHOLD:
            self.calibration_adjustment = difference
            self.calibrated_value = min(1.0, max(0.0, self.value + difference))
            self.lifecycle.transition(
                LifecycleStage.UPDATED,
                reason=f"Calibration applied: adjustment={difference:.4f}",
            )

    def apply_penalty(self, penalty: str, amount: float = 0.0) -> None:
        """Apply a confidence penalty."""
        self.penalties.append(penalty)
        self.value = max(0.0, self.value - amount)
        self.calibrated_value = self.value

    def apply_booster(self, booster: str, amount: float = 0.0) -> None:
        """Apply a confidence booster."""
        self.boosters.append(booster)
        self.value = min(1.0, self.value + amount)
        self.calibrated_value = self.value

    def _to_hashable_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "evidence_strength": self.evidence_strength,
            "coherence": self.coherence,
            "historical_precedent": self.historical_precedent,
            "model_uncertainty": self.model_uncertainty,
            "recency": self.recency,
            "penalties": sorted(self.penalties),
            "boosters": sorted(self.boosters),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "target_id": self.target_id,
                "target_type": self.target_type,
                "value": self.value,
                "calibrated_value": self.calibrated_value,
                "lower_bound": self.lower_bound,
                "upper_bound": self.upper_bound,
                "standard_error": self.standard_error,
                "evidence_strength": self.evidence_strength,
                "coherence": self.coherence,
                "historical_precedent": self.historical_precedent,
                "model_uncertainty": self.model_uncertainty,
                "recency": self.recency,
                "penalties": self.penalties,
                "boosters": self.boosters,
                "calibration_bin": self.calibration_bin,
                "calibration_adjustment": self.calibration_adjustment,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> Confidence:
        obj = super().from_dict(data)
        obj.target_id = data["target_id"]
        obj.target_type = data["target_type"]
        obj.evidence_strength = data.get("evidence_strength", 0.0)
        obj.coherence = data.get("coherence", 0.0)
        obj.historical_precedent = data.get("historical_precedent", 0.0)
        obj.model_uncertainty = data.get("model_uncertainty", 0.0)
        obj.recency = data.get("recency", 0.0)
        obj.penalties = list(data.get("penalties", []))
        obj.boosters = list(data.get("boosters", []))
        obj.value = data.get("value", obj._compute_value())
        obj.calibrated_value = data.get("calibrated_value", obj.value)
        obj.lower_bound = data.get("lower_bound", max(0.0, obj.value - 0.1))
        obj.upper_bound = data.get("upper_bound", min(1.0, obj.value + 0.1))
        obj.standard_error = data.get("standard_error", 0.05)
        obj.calibration_bin = data.get("calibration_bin", obj._compute_calibration_bin())
        obj.calibration_adjustment = data.get("calibration_adjustment", 0.0)
        return obj


class ConfidenceReport(BaseObject):
    """
    A collection of all confidence estimates for a research cycle.

    Based on Article XVII: Object Model — ConfidenceReport.
    """

    def __init__(
        self,
        research_id: str,
        confidences: list[Confidence] | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"ConfidenceReport|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)
        self.research_id = research_id
        self.confidences: list[Confidence] = confidences or []
        self._confidence_ids: list[str] = []

    @property
    def overall_confidence(self) -> float:
        """Average of all confidence values."""
        if not self.confidences:
            return 0.0
        return sum(c.value for c in self.confidences) / len(self.confidences)

    def add_confidence(self, confidence: Confidence) -> None:
        """Add a confidence estimate to the report."""
        self.confidences.append(confidence)

    def get_by_target(self, target_id: str) -> Confidence | None:
        """Get confidence for a specific target."""
        for c in self.confidences:
            if c.target_id == target_id:
                return c
        return None

    @property
    def confidence_ids(self) -> list[str]:
        if self.confidences:
            return [c.id for c in self.confidences]
        return self._confidence_ids

    @confidence_ids.setter
    def confidence_ids(self, value: list[str]) -> None:
        self._confidence_ids = value

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "confidence_ids": self.confidence_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> ConfidenceReport:
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.confidences = []
        obj._confidence_ids = list(data.get("confidence_ids", []))
        return obj

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "confidence_ids": sorted(self.confidence_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }
