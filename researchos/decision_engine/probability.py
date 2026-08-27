"""
Phase 7.3 — Probability Assessment Layer
========================================

Aggregates existing DecisionEvidenceItem fields into deterministic probability estimates.

IMPORTANT — This layer is NOT allowed to contain:
    - trading strategy
    - BUY/SELL logic
    - machine learning / neural networks
    - LLM reasoning
    - hidden weighting
    - hardcoded market rules

It is ONLY responsible for aggregating existing evidence into probability
estimates.

Pipeline:
    DecisionContext -> EvidenceAggregator -> EvidenceCollection
    -> ProbabilityCalculator -> ProbabilityAssessment -> ProbabilityValidator

Computation (pure aggregation, no hidden weights, no source priority):
    For each DecisionEvidenceItem read:
        item.confidence
        item.weight
        item.direction    # ProbabilityOutcome ("Bullish" | "Bearish" | "Neutral")

    contribution = confidence * weight

    bullish_weight = sum(contributions for bullish evidence)
    bearish_weight = sum(contributions for bearish evidence)
    neutral_weight = sum(contributions for neutral evidence)

    Normalize so that  bullish + bearish + neutral == 1.0

    confidence         = average(item.confidence)
    evidence_strength  = average(item.confidence * item.weight)
    sample_size        = len(items)
    historical_consistency = max(bullish, bearish, neutral probabilities)
    uncertainty        = 1.0 - historical_consistency
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import deterministic_hash, generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now
from researchos.decision_engine.contracts import (
    CalculationMethod,
    DecisionEvidenceItem,
    ProbabilityOutcome,
)
from researchos.decision_engine.evidence import EvidenceCollection

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Version identifier for the probability calculation methodology.
CALCULATION_VERSION = "PROBABILITY_V1"

#: Tolerance used when verifying that probabilities sum to 1.0.
FLOAT_TOLERANCE = 1e-9

#: Canonical direction strings (all lowercase).
_DIRECTION_BULLISH = "bullish"
_DIRECTION_BEARISH = "bearish"
_DIRECTION_NEUTRAL = "neutral"

#: Uniform fallback used when total weight is zero (no directional signal).
_UNIFORM_PROBABILITY = 1.0 / 3.0


def _normalize_direction(direction: Any) -> str:
    """Normalise a raw direction value to a lowercase canonical string.

    Any value that is not recognisably ``bullish`` or ``bearish`` collapses to
    ``neutral`` so that unknown directions never bias the result.
    """
    return str(direction).strip().lower()


# ---------------------------------------------------------------------------
# ProbabilityAssessment
# ---------------------------------------------------------------------------


class ProbabilityAssessment(BaseObject):
    """
    Deterministic probability assessment derived from evidence items.

    The three directional probabilities (bullish, bearish, neutral) always sum
    to 1.0 (within floating-point tolerance).

    Attributes:
        decision_context_id: ID of the DecisionContext that originated the
            evidence collection.
        evidence_collection_id: ID of the EvidenceCollection this assessment
            is based on.
        bullish_probability: Estimated probability of a bullish outcome
            (0.0-1.0).
        bearish_probability: Estimated probability of a bearish outcome
            (0.0-1.0).
        neutral_probability: Estimated probability of a neutral outcome
            (0.0-1.0).
        confidence: Average confidence across evidence items (0.0-1.0).
        uncertainty: 1.0 - historical_consistency (0.0-1.0).
        evidence_strength: Average of (confidence * weight) across items.
        historical_consistency: The strongest directional probability
            ``max(bullish, bearish, neutral)``.
        sample_size: Number of evidence items aggregated.
        calculation_method: Method used to compute probabilities.
        calculation_version: Version identifier for the methodology.
        limitations: Deterministic list of assessment caveats.
        timestamp: When the assessment was computed (UTC).
    """

    def __init__(
        self,
        decision_context_id: str,
        evidence_collection_id: str,
        bullish_probability: float = 0.0,
        bearish_probability: float = 0.0,
        neutral_probability: float = 0.0,
        confidence: float = 0.0,
        uncertainty: float = 0.0,
        evidence_strength: float = 0.0,
        historical_consistency: float = 0.0,
        sample_size: int = 0,
        calculation_method: CalculationMethod = CalculationMethod.WEIGHTED_EVIDENCE,
        calculation_version: str = CALCULATION_VERSION,
        limitations: list[str] | None = None,
        timestamp: datetime | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"ProbabilityAssessment|{decision_context_id}|{evidence_collection_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.decision_context_id = decision_context_id
        self.evidence_collection_id = evidence_collection_id
        self.bullish_probability = float(bullish_probability)
        self.bearish_probability = float(bearish_probability)
        self.neutral_probability = float(neutral_probability)
        self.confidence = float(confidence)
        self.uncertainty = float(uncertainty)
        self.evidence_strength = float(evidence_strength)
        self.historical_consistency = float(historical_consistency)
        self.sample_size = int(sample_size)
        self.calculation_method = calculation_method
        self.calculation_version = calculation_version
        self.limitations: list[str] = list(limitations) if limitations else []
        self.timestamp = timestamp or utc_now()

        self._assessment_hash: str = ""
        self._update_hash()

        self.lifecycle.transition(
            LifecycleStage.ANALYZED,
            reason=(f"Probability assessed: B={self.bullish_probability:.4f}, Be={self.bearish_probability:.4f}, N={self.neutral_probability:.4f}, confidence={self.confidence:.4f}, sample_size={self.sample_size}"),
        )

    # ------------------------------------------------------------------
    # Deterministic hashing
    # ------------------------------------------------------------------

    @property
    def assessment_hash(self) -> str:
        """Get the deterministic hash of this assessment."""
        if not self._assessment_hash:
            self._update_hash()
        return self._assessment_hash

    def _update_hash(self) -> None:
        """Compute the deterministic hash from content."""
        self._assessment_hash = deterministic_hash(self._to_hashable_dict())

    def _to_hashable_dict(self) -> dict[str, Any]:
        """Return a deterministic, order-independent representation.

        ``timestamp`` is deliberately excluded so that the hash reflects only
        the *computed content* (probabilities, confidence, etc.) and remains
        stable regardless of when the assessment was produced.  ``id``,
        ``created_at`` and ``lifecycle`` are metadata excluded by BaseObject.
        """
        return {
            "decision_context_id": self.decision_context_id,
            "evidence_collection_id": self.evidence_collection_id,
            "bullish_probability": self.bullish_probability,
            "bearish_probability": self.bearish_probability,
            "neutral_probability": self.neutral_probability,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence_strength": self.evidence_strength,
            "historical_consistency": self.historical_consistency,
            "sample_size": self.sample_size,
            "calculation_method": self.calculation_method.value,
            "calculation_version": self.calculation_version,
            "limitations": sorted(self.limitations),
            "ontology_tags": sorted(self.ontology_tags),
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a dictionary representation."""
        base = super().to_dict()
        base.update(
            {
                "decision_context_id": self.decision_context_id,
                "evidence_collection_id": self.evidence_collection_id,
                "bullish_probability": self.bullish_probability,
                "bearish_probability": self.bearish_probability,
                "neutral_probability": self.neutral_probability,
                "confidence": self.confidence,
                "uncertainty": self.uncertainty,
                "evidence_strength": self.evidence_strength,
                "historical_consistency": self.historical_consistency,
                "sample_size": self.sample_size,
                "calculation_method": self.calculation_method.value,
                "calculation_version": self.calculation_version,
                "limitations": self.limitations,
                "timestamp": self.timestamp.isoformat(),
                "assessment_hash": self._assessment_hash,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProbabilityAssessment:
        """Restore a ProbabilityAssessment from saved state."""
        obj = super().from_dict(data)  # type: ignore[assignment]
        obj.decision_context_id = data["decision_context_id"]
        obj.evidence_collection_id = data["evidence_collection_id"]
        obj.bullish_probability = float(data.get("bullish_probability", 0.0))
        obj.bearish_probability = float(data.get("bearish_probability", 0.0))
        obj.neutral_probability = float(data.get("neutral_probability", 0.0))
        obj.confidence = float(data.get("confidence", 0.0))
        obj.uncertainty = float(data.get("uncertainty", 0.0))
        obj.evidence_strength = float(data.get("evidence_strength", 0.0))
        obj.historical_consistency = float(data.get("historical_consistency", 0.0))
        obj.sample_size = int(data.get("sample_size", 0))
        obj.calculation_method = CalculationMethod(data.get("calculation_method", CalculationMethod.WEIGHTED_EVIDENCE.value))
        obj.calculation_version = data.get("calculation_version", CALCULATION_VERSION)
        obj.limitations = list(data.get("limitations", []))
        ts = data.get("timestamp")
        obj.timestamp = parse_timestamp(ts) if ts else utc_now()
        obj._assessment_hash = data.get("assessment_hash", "")
        return obj


# ---------------------------------------------------------------------------
# ProbabilityCalculator
# ---------------------------------------------------------------------------


class ProbabilityCalculator:
    """
    Stateless calculator that aggregates DecisionEvidenceItem fields into a
    ProbabilityAssessment.

    The calculator performs **pure aggregation** — it reads only the existing
    fields of each DecisionEvidenceItem (``confidence``, ``weight``, ``direction``)
    and applies a single normalisation pass.  There are:

        * no hidden weights,
        * no source priority,
        * no trading logic,
        * no machine learning,
        * no Bayesian inference,
        * no hardcoded market rules.

    The same EvidenceCollection always yields the same ProbabilityAssessment.
    """

    def __init__(self, calculation_version: str = CALCULATION_VERSION):
        self.calculation_version = calculation_version

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(self, collection: EvidenceCollection) -> ProbabilityAssessment:
        """Compute a deterministic ProbabilityAssessment from a collection.

        Args:
            collection: The EvidenceCollection to aggregate.

        Returns:
            A ProbabilityAssessment whose probabilities sum to 1.0.
        """
        return self._aggregate(
            decision_context_id=collection.decision_context_id,
            evidence_collection_id=collection.id,
            items=collection.items,
            timestamp=collection.collection_timestamp,
        )

    def compute(
        self,
        decision_context_id: str,
        evidence_collection_id: str,
        items: list[DecisionEvidenceItem],
        timestamp: datetime | None = None,
    ) -> ProbabilityAssessment:
        """Compute a ProbabilityAssessment from raw components.

        This is the low-level entry point used by :meth:`calculate` and is
        convenient for tests that build item lists directly.
        """
        return self._aggregate(
            decision_context_id=decision_context_id,
            evidence_collection_id=evidence_collection_id,
            items=items,
            timestamp=timestamp,
        )

    # ------------------------------------------------------------------
    # Internal aggregation
    # ------------------------------------------------------------------

    def _aggregate(
        self,
        decision_context_id: str,
        evidence_collection_id: str,
        items: list[DecisionEvidenceItem],
        timestamp: datetime | None = None,
    ) -> ProbabilityAssessment:
        bullish_weight = 0.0
        bearish_weight = 0.0
        neutral_weight = 0.0

        confidences: list[float] = []
        weighted_contributions: list[float] = []

        for item in items:
            confidence = float(item.confidence)
            weight = float(item.weight)
            contribution = confidence * weight

            confidences.append(confidence)
            weighted_contributions.append(contribution)

            raw_direction = item.direction.value if isinstance(item.direction, ProbabilityOutcome) else item.direction
            direction = _normalize_direction(raw_direction)
            if direction == _DIRECTION_BULLISH:
                bullish_weight += contribution
            elif direction == _DIRECTION_BEARISH:
                bearish_weight += contribution
            else:
                neutral_weight += contribution

        total = bullish_weight + bearish_weight + neutral_weight

        if total > 0:
            bullish_probability = bullish_weight / total
            bearish_probability = bearish_weight / total
            neutral_probability = neutral_weight / total
        else:
            # No directional signal at all — use a uniform fallback so that the
            # probabilities still sum to 1.0.
            bullish_probability = _UNIFORM_PROBABILITY
            bearish_probability = _UNIFORM_PROBABILITY
            neutral_probability = _UNIFORM_PROBABILITY

        # Correct floating-point drift so the three probabilities sum to
        # exactly 1.0.
        neutral_probability = 1.0 - bullish_probability - bearish_probability

        confidence = sum(confidences) / len(confidences) if confidences else 0.0
        evidence_strength = sum(weighted_contributions) / len(weighted_contributions) if weighted_contributions else 0.0
        sample_size = len(items)
        historical_consistency = max(bullish_probability, bearish_probability, neutral_probability)
        uncertainty = 1.0 - historical_consistency

        limitations = self._derive_limitations(
            items=items,
            sample_size=sample_size,
            total=total,
            confidence=confidence,
            uncertainty=uncertainty,
        )

        return ProbabilityAssessment(
            decision_context_id=decision_context_id,
            evidence_collection_id=evidence_collection_id,
            bullish_probability=bullish_probability,
            bearish_probability=bearish_probability,
            neutral_probability=neutral_probability,
            confidence=confidence,
            uncertainty=uncertainty,
            evidence_strength=evidence_strength,
            historical_consistency=historical_consistency,
            sample_size=sample_size,
            calculation_method=CalculationMethod.WEIGHTED_EVIDENCE,
            calculation_version=self.calculation_version,
            limitations=limitations,
            timestamp=timestamp,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_limitations(
        items: list[DecisionEvidenceItem],
        sample_size: int,
        total: float,
        confidence: float,
        uncertainty: float,
    ) -> list[str]:
        """Produce a deterministic, data-driven list of caveats."""
        limitations: list[str] = []

        if sample_size == 0:
            limitations.append("No evidence items available for probability assessment")
            return limitations

        if sample_size < 3:
            limitations.append(f"Low evidence sample size: {sample_size} items")

        if total == 0:
            limitations.append("All evidence items have zero effective weight (confidence * weight = 0)")

        if confidence == 0.0:
            limitations.append("No confident evidence; all items have zero confidence")

        if uncertainty > 0.6:
            limitations.append("High uncertainty: evidence directions are widely dispersed")

        return limitations


# ---------------------------------------------------------------------------
# ProbabilityValidator
# ---------------------------------------------------------------------------


class ProbabilityValidator:
    """
    Validates the invariants of a :class:`ProbabilityAssessment`.

    Rules:
        1. probabilities sum to 1.0 (within tolerance)
        2. each probability is in [0.0, 1.0]
        3. confidence is in [0.0, 1.0]
        4. uncertainty is in [0.0, 1.0]
        5. sample_size >= 0
        6. decision_context_id and evidence_collection_id are non-empty
        7. the stored assessment hash matches the recomputed hash

    Usage::

        validator = ProbabilityValidator()
        errors = validator.validate(assessment)
        if errors:
            for error in errors:
                print(f"Validation error: {error}")
    """

    TOLERANCE = FLOAT_TOLERANCE

    def validate(self, assessment: ProbabilityAssessment) -> list[str]:
        """Validate a ProbabilityAssessment.

        Returns:
            A list of error strings.  An empty list means the assessment is
            valid.
        """
        errors: list[str] = []

        errors.extend(self._check_probability_sum(assessment))
        errors.extend(self._check_probability_ranges(assessment))
        errors.extend(self._check_confidence_range(assessment))
        errors.extend(self._check_uncertainty_range(assessment))
        errors.extend(self._check_evidence_strength(assessment))
        errors.extend(self._check_historical_consistency(assessment))
        errors.extend(self._check_sample_size(assessment))
        errors.extend(self._check_references(assessment))
        errors.extend(self._check_hash(assessment))

        return errors

    def is_valid(self, assessment: ProbabilityAssessment) -> bool:
        """Quick boolean check."""
        return len(self.validate(assessment)) == 0

    # ------------------------------------------------------------------
    # Individual rules
    # ------------------------------------------------------------------

    def _check_probability_sum(self, assessment: ProbabilityAssessment) -> list[str]:
        total = assessment.bullish_probability + assessment.bearish_probability + assessment.neutral_probability
        if not isinstance(total, (int, float)) or abs(total - 1.0) > self.TOLERANCE:
            return [f"Probabilities must sum to 1.0 (±{self.TOLERANCE}), got {total}"]
        return []

    def _check_probability_ranges(self, assessment: ProbabilityAssessment) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("bullish_probability", assessment.bullish_probability),
            ("bearish_probability", assessment.bearish_probability),
            ("neutral_probability", assessment.neutral_probability),
        ):
            if not self._in_unit_interval(value):
                errors.append(f"{name} must be in [0.0, 1.0], got {value}")
        return errors

    def _check_confidence_range(self, assessment: ProbabilityAssessment) -> list[str]:
        if not self._in_unit_interval(assessment.confidence):
            return [f"confidence must be in [0.0, 1.0], got {assessment.confidence}"]
        return []

    def _check_uncertainty_range(self, assessment: ProbabilityAssessment) -> list[str]:
        if not self._in_unit_interval(assessment.uncertainty):
            return [f"uncertainty must be in [0.0, 1.0], got {assessment.uncertainty}"]
        return []

    def _check_evidence_strength(self, assessment: ProbabilityAssessment) -> list[str]:
        if not self._in_unit_interval(assessment.evidence_strength):
            return [f"evidence_strength must be in [0.0, 1.0], got {assessment.evidence_strength}"]
        return []

    def _check_historical_consistency(self, assessment: ProbabilityAssessment) -> list[str]:
        if not self._in_unit_interval(assessment.historical_consistency):
            return [f"historical_consistency must be in [0.0, 1.0], got {assessment.historical_consistency}"]
        return []

    def _check_sample_size(self, assessment: ProbabilityAssessment) -> list[str]:
        if assessment.sample_size < 0:
            return [f"sample_size must be >= 0, got {assessment.sample_size}"]
        return []

    def _check_references(self, assessment: ProbabilityAssessment) -> list[str]:
        errors: list[str] = []
        if not assessment.decision_context_id:
            errors.append("decision_context_id is empty")
        if not assessment.evidence_collection_id:
            errors.append("evidence_collection_id is empty")
        return errors

    def _check_hash(self, assessment: ProbabilityAssessment) -> list[str]:
        errors: list[str] = []
        if not assessment.assessment_hash:
            errors.append("assessment_hash is empty")
        elif assessment.assessment_hash != assessment.compute_hash():
            errors.append("assessment_hash does not match the recomputed hash (content has changed or hash is stale)")
        return errors

    @staticmethod
    def _in_unit_interval(value: Any) -> bool:
        return isinstance(value, (int, float)) and value >= 0.0 and value <= 1.0
