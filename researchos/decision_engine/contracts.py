"""
Contracts, enums, and dataclasses for the Decision Intelligence Engine.

Based on Article XVII: Object Model — Decision Engine Layer.

Defines the shared vocabulary used across all decision engine objects.

Every decision must be:
    - Deterministic: Same inputs → same outputs
    - Auditable: Full lifecycle tracking
    - Explainable: Every conclusion has a reasoning trace
    - Versioned: Calculation versions for reproducibility
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EvidenceSource(str, Enum):
    """Source modules that contribute evidence to a decision."""

    MARKET_MEMORY = "MarketMemory"
    EXPERIMENT = "Experiment"
    VALIDATION = "Validation"
    MACRO_INTELLIGENCE = "MacroIntelligence"
    RESEARCH_OBJECTS = "ResearchObjects"
    QUANT_ENGINE = "QuantEngine"


class ProbabilityDirection(str, Enum):
    """Direction that a single evidence item supports."""

    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class ProbabilityOutcome(str, Enum):
    """The directional probability outcomes."""

    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class CalculationMethod(str, Enum):
    """Methods for computing probabilities from evidence scores."""

    WEIGHTED_EVIDENCE = "WeightedEvidence"
    BAYESIAN = "Bayesian"
    HISTORICAL_FREQUENCY = "HistoricalFrequency"
    CONFIDENCE_ADJUSTED = "ConfidenceAdjusted"
    EVIDENCE_BALANCE = "EvidenceBalance"


class DecisionStatus(str, Enum):
    """Lifecycle status of a decision process."""

    PENDING = "Pending"
    EVIDENCE_COLLECTED = "EvidenceCollected"
    SCORED = "Scored"
    PROBABILITY_COMPUTED = "ProbabilityComputed"
    REASONED = "Reasoned"
    REPORT_GENERATED = "ReportGenerated"
    ARCHIVED = "Archived"


class DecisionVersion(str, Enum):
    """Explicit version identifier for decision methodology.

    When formulas change, a new version is added.
    Historical decisions remain reproducible under their original version.

    DECISION_V1: Initial release — WeightedEvidence scoring, weighted probability.
    """

    DECISION_V1 = "DECISION_V1"

    # Future versions:
    # DECISION_V2 = "DECISION_V2"


@dataclass
class EvidenceItem:
    """
    A single piece of evidence collected from any source module.

    All evidence items are weighted and combined deterministically.

    Attributes:
        source: Which module produced this evidence.
        source_id: Specific object ID that produced the evidence.
        direction: Direction the evidence supports (Bullish, Bearish, Neutral).
        strength: Evidence strength (0.0-1.0).
        weight: Configurable weight factor for this evidence type.
        confidence: Confidence in this specific evidence item (0.0-1.0).
        description: Human-readable explanation.
        supporting_ids: IDs of supporting objects (scenarios, experiments, etc.).
    """

    source: EvidenceSource
    source_id: str
    direction: ProbabilityOutcome
    strength: float
    weight: float
    confidence: float
    description: str
    supporting_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.value,
            "source_id": self.source_id,
            "direction": self.direction.value,
            "strength": self.strength,
            "weight": self.weight,
            "confidence": self.confidence,
            "description": self.description,
            "supporting_ids": list(self.supporting_ids),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceItem":
        return cls(
            source=EvidenceSource(data["source"]),
            source_id=data["source_id"],
            direction=ProbabilityOutcome(data["direction"]),
            strength=float(data["strength"]),
            weight=float(data["weight"]),
            confidence=float(data["confidence"]),
            description=data.get("description", ""),
            supporting_ids=list(data.get("supporting_ids", [])),
        )


@dataclass
class WeightConfiguration:
    """
    Configurable weights for evidence sources.

    Stored separately so future research can compare different weighting models.
    NOT hardcoded inside algorithms.

    Attributes:
        macro_weight: Weight for Macro Intelligence evidence.
        market_memory_weight: Weight for Market Memory evidence.
        experiment_weight: Weight for Experiment Results evidence.
        validation_weight: Weight for Validation evidence.
        quant_weight: Weight for Quant Statistics evidence.
        weighting_version: Version identifier for this weight configuration.
    """

    macro_weight: float = 0.25
    market_memory_weight: float = 0.25
    experiment_weight: float = 0.20
    validation_weight: float = 0.15
    quant_weight: float = 0.15
    weighting_version: str = "WEIGHT_V1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "macro_weight": self.macro_weight,
            "market_memory_weight": self.market_memory_weight,
            "experiment_weight": self.experiment_weight,
            "validation_weight": self.validation_weight,
            "quant_weight": self.quant_weight,
            "weighting_version": self.weighting_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeightConfiguration":
        return cls(
            macro_weight=float(data.get("macro_weight", 0.25)),
            market_memory_weight=float(data.get("market_memory_weight", 0.25)),
            experiment_weight=float(data.get("experiment_weight", 0.20)),
            validation_weight=float(data.get("validation_weight", 0.15)),
            quant_weight=float(data.get("quant_weight", 0.15)),
            weighting_version=str(data.get("weighting_version", "WEIGHT_V1")),
        )

    def total_weight(self) -> float:
        """Sum of all weights (should be 1.0)."""
        return (
            self.macro_weight
            + self.market_memory_weight
            + self.experiment_weight
            + self.validation_weight
            + self.quant_weight
        )
