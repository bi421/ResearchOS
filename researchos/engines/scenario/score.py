"""
EvidenceScore — normalized intermediate score between evidence and probability.

Based on Article XVII: Object Model — Decision Engine Layer.

Purpose:
    EvidenceScore normalizes and combines raw evidence items into
    structured scores before probability calculation. This intermediate
    object ensures:
        - All evidence is normalized to a common scale
        - Source-specific scores are tracked separately
        - Score computation is deterministic and auditable
        - Future engines can replace scoring without changing probability

Design:
    EvidenceScore is a BaseObject with full lifecycle, serialization,
    and hash support. It is the REQUIRED intermediate step in the
    decision pipeline.

Pipeline:
    DecisionContext → EvidenceAggregator → EvidenceScore →
    ProbabilityAssessment → DecisionReasoner → DecisionReport
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import deterministic_hash, generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.engines.scenario.contracts import (
    DecisionEvidenceItem,
    EvidenceSource,
    WeightConfiguration,
)


class EvidenceScore(BaseObject):
    """
    Normalized and combined evidence scores for all sources.

    This is the intermediate output between evidence aggregation
    and probability calculation. It separates:
        - Raw evidence (collected items)
        - Normalized scores (per source and direction)
        - Combined scores (aggregated across sources)

    Attributes:
        context_id: Link to the DecisionContext.
        total_score: Overall evidence score (-1.0 to 1.0), negative = bearish, positive = bullish.
        bullish_score: Aggregate bullish evidence score (0.0-1.0).
        bearish_score: Aggregate bearish evidence score (0.0-1.0).
        neutral_score: Aggregate neutral evidence score (0.0-1.0).
        macro_score: Score from macro intelligence (0.0-1.0).
        historical_score: Score from market memory (0.0-1.0).
        experiment_score: Score from experiment results (0.0-1.0).
        validation_score: Score from validation (0.0-1.0).
        market_memory_score: Score from market memory matches (0.0-1.0).
        quant_score: Score from quant engine (0.0-1.0).
        confidence_score: Overall confidence in the evidence (0.0-1.0).
        uncertainty_score: Measure of disagreement between sources (0.0-1.0).
        evidence_count: Total number of evidence items aggregated.
        evidence_items: The raw evidence items (for audit trail).
        weighting_version: Version of weight configuration used.
        scoring_version: Version of scoring methodology.
    """

    def __init__(
        self,
        context_id: str,
        total_score: float = 0.0,
        bullish_score: float = 0.0,
        bearish_score: float = 0.0,
        neutral_score: float = 0.0,
        macro_score: float = 0.0,
        historical_score: float = 0.0,
        experiment_score: float = 0.0,
        validation_score: float = 0.0,
        market_memory_score: float = 0.0,
        quant_score: float = 0.0,
        confidence_score: float = 0.0,
        uncertainty_score: float = 0.0,
        evidence_count: int = 0,
        evidence_items: Optional[List[DecisionEvidenceItem]] = None,
        weighting_version: str = "WEIGHT_V1",
        scoring_version: str = "SCORE_V1",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"EvidenceScore|{context_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.context_id = context_id
        self.total_score = total_score
        self.bullish_score = bullish_score
        self.bearish_score = bearish_score
        self.neutral_score = neutral_score
        self.macro_score = macro_score
        self.historical_score = historical_score
        self.experiment_score = experiment_score
        self.validation_score = validation_score
        self.market_memory_score = market_memory_score
        self.quant_score = quant_score
        self.confidence_score = confidence_score
        self.uncertainty_score = uncertainty_score
        self.evidence_count = evidence_count
        self.evidence_items: List[DecisionEvidenceItem] = evidence_items or []
        self.weighting_version = weighting_version
        self.scoring_version = scoring_version
        self._score_hash: str = ""

        self._update_hash()

        self.lifecycle.transition(
            LifecycleStage.CALIBRATED,
            reason=f"Evidence score computed: {self.evidence_count} items, total={total_score:.4f}",
        )

    @property
    def score_hash(self) -> str:
        """Get the deterministic hash of this score."""
        if not self._score_hash:
            self._update_hash()
        return self._score_hash

    def _update_hash(self) -> None:
        """Compute the deterministic hash."""
        content = self._to_hashable_dict()
        self._score_hash = deterministic_hash(content)

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "total_score": self.total_score,
            "bullish_score": self.bullish_score,
            "bearish_score": self.bearish_score,
            "neutral_score": self.neutral_score,
            "macro_score": self.macro_score,
            "historical_score": self.historical_score,
            "experiment_score": self.experiment_score,
            "validation_score": self.validation_score,
            "market_memory_score": self.market_memory_score,
            "quant_score": self.quant_score,
            "confidence_score": self.confidence_score,
            "uncertainty_score": self.uncertainty_score,
            "evidence_count": self.evidence_count,
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "weighting_version": self.weighting_version,
            "scoring_version": self.scoring_version,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "context_id": self.context_id,
                "total_score": self.total_score,
                "bullish_score": self.bullish_score,
                "bearish_score": self.bearish_score,
                "neutral_score": self.neutral_score,
                "macro_score": self.macro_score,
                "historical_score": self.historical_score,
                "experiment_score": self.experiment_score,
                "validation_score": self.validation_score,
                "market_memory_score": self.market_memory_score,
                "quant_score": self.quant_score,
                "confidence_score": self.confidence_score,
                "uncertainty_score": self.uncertainty_score,
                "evidence_count": self.evidence_count,
                "evidence_items": [e.to_dict() for e in self.evidence_items],
                "weighting_version": self.weighting_version,
                "scoring_version": self.scoring_version,
                "score_hash": self._score_hash,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceScore":
        obj = super().from_dict(data)
        obj.context_id = data["context_id"]
        obj.total_score = float(data.get("total_score", 0.0))
        obj.bullish_score = float(data.get("bullish_score", 0.0))
        obj.bearish_score = float(data.get("bearish_score", 0.0))
        obj.neutral_score = float(data.get("neutral_score", 0.0))
        obj.macro_score = float(data.get("macro_score", 0.0))
        obj.historical_score = float(data.get("historical_score", 0.0))
        obj.experiment_score = float(data.get("experiment_score", 0.0))
        obj.validation_score = float(data.get("validation_score", 0.0))
        obj.market_memory_score = float(data.get("market_memory_score", 0.0))
        obj.quant_score = float(data.get("quant_score", 0.0))
        obj.confidence_score = float(data.get("confidence_score", 0.0))
        obj.uncertainty_score = float(data.get("uncertainty_score", 0.0))
        obj.evidence_count = int(data.get("evidence_count", 0))
        obj.evidence_items = [
            DecisionEvidenceItem.from_dict(e) for e in data.get("evidence_items", [])
        ]
        obj.weighting_version = data.get("weighting_version", "WEIGHT_V1")
        obj.scoring_version = data.get("scoring_version", "SCORE_V1")
        obj._score_hash = data.get("score_hash", "")
        return obj


def compute_evidence_score(
    context_id: str,
    evidence_items: List[DecisionEvidenceItem],
    weight_config: WeightConfiguration,
    scoring_version: str = "SCORE_V1",
) -> EvidenceScore:
    """
    Compute normalized EvidenceScore from raw evidence items.

    Deterministic: Same items + weights → same score.

    Args:
        context_id: Link to the DecisionContext.
        evidence_items: Raw evidence items from EvidenceAggregator.
        weight_config: Weight configuration for scoring.
        scoring_version: Version identifier for scoring methodology.

    Returns:
        Computed EvidenceScore with all fields populated.
    """
    if not evidence_items:
        return EvidenceScore(
            context_id=context_id,
            evidence_count=0,
            uncertainty_score=1.0,
            weighting_version=weight_config.weighting_version,
            scoring_version=scoring_version,
        )

    # Separate evidence by source and direction
    source_scores: Dict[str, Dict[str, float]] = {}
    source_confidences: Dict[str, float] = {}
    total_items = len(evidence_items)

    # Map source types to weight config attributes
    source_weight_map = {
        EvidenceSource.MARKET_MEMORY.value: weight_config.market_memory_weight,
        EvidenceSource.MACRO_INTELLIGENCE.value: weight_config.macro_weight,
        EvidenceSource.EXPERIMENT.value: weight_config.experiment_weight,
        EvidenceSource.VALIDATION.value: weight_config.validation_weight,
        EvidenceSource.QUANT_ENGINE.value: weight_config.quant_weight,
        EvidenceSource.RESEARCH_OBJECTS.value: weight_config.quant_weight,  # fallback
    }

    for item in evidence_items:
        source_key = item.source.value
        if source_key not in source_scores:
            source_scores[source_key] = {"Bullish": 0.0, "Bearish": 0.0, "Neutral": 0.0}
            source_confidences[source_key] = 0.0

        # Apply both item-level weight and source-level config weight
        source_weight = source_weight_map.get(source_key, 0.2)
        strength = item.strength * item.weight * source_weight
        source_scores[source_key][item.direction.value] += strength
        source_confidences[source_key] = max(source_confidences[source_key], item.confidence)

    # Compute per-direction aggregate scores
    bullish_total = sum(s.get("Bullish", 0.0) for s in source_scores.values())
    bearish_total = sum(s.get("Bearish", 0.0) for s in source_scores.values())
    neutral_total = sum(s.get("Neutral", 0.0) for s in source_scores.values())

    # Normalize directional scores to 0.0-1.0 range
    max_directional = max(bullish_total, bearish_total, neutral_total, 0.001)
    bullish_norm = bullish_total / max_directional
    bearish_norm = bearish_total / max_directional
    neutral_norm = neutral_total / max_directional

    # Total score: -1.0 (strong bearish) to +1.0 (strong bullish)
    total_score = bullish_total - bearish_total
    total_score = max(-1.0, min(1.0, total_score))

    # Per-source scores
    mm_key = EvidenceSource.MARKET_MEMORY.value
    macro_key = EvidenceSource.MACRO_INTELLIGENCE.value
    exp_key = EvidenceSource.EXPERIMENT.value
    val_key = EvidenceSource.VALIDATION.value
    quant_key = EvidenceSource.QUANT_ENGINE.value

    market_memory_score = (
        max(
            source_scores.get(mm_key, {}).get("Bullish", 0.0),
            source_scores.get(mm_key, {}).get("Bearish", 0.0),
            source_scores.get(mm_key, {}).get("Neutral", 0.0),
        )
        if mm_key in source_scores
        else 0.0
    )

    historical_score = market_memory_score  # Same source
    macro_score = (
        max(
            source_scores.get(macro_key, {}).get("Bullish", 0.0),
            source_scores.get(macro_key, {}).get("Bearish", 0.0),
            source_scores.get(macro_key, {}).get("Neutral", 0.0),
        )
        if macro_key in source_scores
        else 0.0
    )

    experiment_score = (
        max(
            source_scores.get(exp_key, {}).get("Bullish", 0.0),
            source_scores.get(exp_key, {}).get("Bearish", 0.0),
            source_scores.get(exp_key, {}).get("Neutral", 0.0),
        )
        if exp_key in source_scores
        else 0.0
    )

    validation_score = (
        max(
            source_scores.get(val_key, {}).get("Bullish", 0.0),
            source_scores.get(val_key, {}).get("Bearish", 0.0),
            source_scores.get(val_key, {}).get("Neutral", 0.0),
        )
        if val_key in source_scores
        else 0.0
    )

    quant_score = (
        max(
            source_scores.get(quant_key, {}).get("Bullish", 0.0),
            source_scores.get(quant_key, {}).get("Bearish", 0.0),
            source_scores.get(quant_key, {}).get("Neutral", 0.0),
        )
        if quant_key in source_scores
        else 0.0
    )

    # Confidence score: average of source confidences
    confidence_score = (
        sum(source_confidences.values()) / len(source_confidences) if source_confidences else 0.0
    )

    # Uncertainty score: disagreement between sources
    # Higher when sources disagree on direction
    directional_agreement = max(bullish_norm, bearish_norm, neutral_norm)
    uncertainty_score = 1.0 - directional_agreement

    return EvidenceScore(
        context_id=context_id,
        total_score=total_score,
        bullish_score=bullish_norm,
        bearish_score=bearish_norm,
        neutral_score=neutral_norm,
        macro_score=macro_score,
        historical_score=historical_score,
        experiment_score=experiment_score,
        validation_score=validation_score,
        market_memory_score=market_memory_score,
        quant_score=quant_score,
        confidence_score=confidence_score,
        uncertainty_score=uncertainty_score,
        evidence_count=total_items,
        evidence_items=evidence_items,
        weighting_version=weight_config.weighting_version,
        scoring_version=scoring_version,
    )
