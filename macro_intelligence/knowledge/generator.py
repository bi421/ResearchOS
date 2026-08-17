"""
ResearchOS Macro Intelligence Layer - Knowledge Generator Pipeline

The KnowledgeGenerator orchestrates the deterministic pipeline that
converts frozen upstream outputs into immutable KnowledgeObjects.

Pipeline (dependency direction, never bypassed):

    contracts -> evidence -> features -> statistics -> relationships
        -> regime intelligence -> knowledge generation -> macro context

The generator consumes ONLY frozen outputs. It never recomputes statistics,
relationships, or regime classification. It never mutates upstream inputs.

Architecture invariants:
- MIL-KNOW-001: Knowledge objects are immutable
- MIL-KNOW-002: Complete provenance is preserved
- MIL-KNOW-003: Same inputs produce identical knowledge
- MIL-KNOW-004: Knowledge generation is deterministic
- MIL-KNOW-005: Algorithm versions are permanent
- MIL-KNOW-006: Never mutates source evidence
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from macro_intelligence.knowledge.confidence import (
    ConfidenceCalculator,
    ConfidenceComponents,
)
from macro_intelligence.knowledge.evidence_link import EvidenceLinker
from macro_intelligence.knowledge.models import (
    ALGORITHM_VERSION,
    KnowledgeObject,
    KnowledgeProvenance,
)
from macro_intelligence.knowledge.pattern import PatternDetector, PatternFinding
from macro_intelligence.knowledge.rules import get_rules_version


@dataclass(frozen=True)
class KnowledgeInputs:
    """
    Frozen set of upstream inputs consumed by the generator.

    The generator only reads these stable identifiers and scalar signals.
    It never mutates the upstream objects they reference.
    """

    # Supporting evidence identifiers
    evidence_ids: tuple[str, ...] = field(default_factory=tuple)

    # Supporting feature vector identifiers
    feature_vector_ids: tuple[str, ...] = field(default_factory=tuple)

    # Supporting relationship identifiers
    relationship_ids: tuple[str, ...] = field(default_factory=tuple)

    # Regime classification identifier
    regime_classification_id: str = ""

    # Regime transition identifier
    transition_id: str = ""

    # Regime context label
    regime_context: str = ""

    # --- Scalar signals (frozen outputs from upstream layers) ---
    persistence_periods: int = 0
    regime_confidence: float = 0.0
    continuation_probability: float = 0.0
    regime_name: str = ""
    transition_detected: bool = False
    transition_confidence: float = 0.0
    previous_regime: str = ""
    current_regime: str = ""
    rolling_stability: float | None = None
    overall_correlation: float | None = None
    relationship_sample_size: int = 0
    series_a: str = ""
    series_b: str = ""
    breaks: tuple[Any, ...] = field(default_factory=tuple)
    features: dict[str, Any] = field(default_factory=dict)
    dominant_regime: str = ""
    regime_description: str = ""
    risk_regime: str = ""
    risk_confidence: float = 0.0
    safe_haven_correlations: dict[str, float] = field(default_factory=dict)
    monetary_regime: str = ""
    monetary_confidence: float = 0.0
    volatility_elevated: bool = False

    # --- Confidence components (optional, from upstream quality) ---
    evidence_quality: float | None = None
    feature_quality: float | None = None
    relationship_stability_quality: float | None = None
    regime_confidence_quality: float | None = None
    historical_consistency: float | None = None


class KnowledgeGenerator:
    """
    Deterministic pipeline orchestrator for knowledge generation.

    Stateless and pure with respect to its dependencies. It composes the
    PatternDetector, ConfidenceCalculator, and EvidenceLinker, then emits
    immutable KnowledgeObjects.
    """

    def __init__(self) -> None:
        self._version = ALGORITHM_VERSION
        self._rules_version = get_rules_version()
        self._detector = PatternDetector()
        self._confidence = ConfidenceCalculator()
        self._linker = EvidenceLinker()

    @property
    def version(self) -> str:
        return self._version

    @property
    def rules_version(self) -> str:
        return self._rules_version

    def _generate_id(self, rule_id: str, inputs: KnowledgeInputs) -> str:
        """Deterministic knowledge id derived from stable inputs."""
        semantic = {
            "rule_id": rule_id,
            "evidence_ids": sorted(inputs.evidence_ids),
            "feature_vector_ids": sorted(inputs.feature_vector_ids),
            "relationship_ids": sorted(inputs.relationship_ids),
            "regime_classification_id": inputs.regime_classification_id,
            "transition_id": inputs.transition_id,
            "regime_context": inputs.regime_context,
        }
        canonical = __import__("json").dumps(semantic, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
        return f"KN_{rule_id}_{digest}"

    def _build_confidence(self, inputs: KnowledgeInputs) -> float:
        """Compute deterministic confidence from frozen components."""
        components = ConfidenceComponents(
            evidence_quality=inputs.evidence_quality,
            feature_quality=inputs.feature_quality,
            relationship_stability=inputs.relationship_stability_quality,
            regime_confidence=inputs.regime_confidence_quality,
            historical_consistency=inputs.historical_consistency,
        )
        return self._confidence.compute(components)

    def _build_provenance(self, inputs: KnowledgeInputs) -> KnowledgeProvenance:
        return self._linker.build_provenance(
            evidence_ids=list(inputs.evidence_ids),
            feature_vector_ids=list(inputs.feature_vector_ids),
            relationship_ids=list(inputs.relationship_ids),
            regime_classification_id=inputs.regime_classification_id,
            transition_id=inputs.transition_id,
            rules_version=self._rules_version,
        )

    def _to_object(
        self,
        finding: PatternFinding,
        inputs: KnowledgeInputs,
        confidence: float,
        provenance: KnowledgeProvenance,
    ) -> KnowledgeObject:
        """Build an immutable KnowledgeObject from a pattern finding."""
        return KnowledgeObject(
            knowledge_id=self._generate_id(finding.rule_id, inputs),
            knowledge_type=finding.pattern_type,
            statement=finding.statement,
            confidence=confidence,
            supporting_evidence=inputs.evidence_ids,
            supporting_features=inputs.feature_vector_ids,
            supporting_relationships=inputs.relationship_ids,
            regime_context=inputs.regime_context,
            algorithm_version=ALGORITHM_VERSION,
            provenance=provenance,
        )

    def generate(self, inputs: KnowledgeInputs) -> list[KnowledgeObject]:
        """
        Generate all deterministic knowledge objects from the given inputs.

        Consumes ONLY frozen upstream outputs; never mutates them.

        Returns:
            A list of immutable KnowledgeObjects (possibly empty).
        """
        findings = self._detector.detect_all(
            persistence_periods=inputs.persistence_periods,
            regime_confidence=inputs.regime_confidence,
            continuation_probability=inputs.continuation_probability,
            regime_name=inputs.regime_name,
            transition_detected=inputs.transition_detected,
            transition_confidence=inputs.transition_confidence,
            previous_regime=inputs.previous_regime,
            current_regime=inputs.current_regime,
            rolling_stability=inputs.rolling_stability,
            overall_correlation=inputs.overall_correlation,
            relationship_sample_size=inputs.relationship_sample_size,
            series_a=inputs.series_a,
            series_b=inputs.series_b,
            breaks=list(inputs.breaks),
            features=inputs.features,
            dominant_regime=inputs.dominant_regime,
            regime_description=inputs.regime_description,
            risk_regime=inputs.risk_regime,
            risk_confidence=inputs.risk_confidence,
            safe_haven_correlations=inputs.safe_haven_correlations,
            monetary_regime=inputs.monetary_regime,
            monetary_confidence=inputs.monetary_confidence,
            volatility_elevated=inputs.volatility_elevated,
        )

        confidence = self._build_confidence(inputs)
        provenance = self._build_provenance(inputs)

        objects = [self._to_object(finding, inputs, confidence, provenance) for finding in findings]

        # Deterministic ordering by knowledge type value
        return sorted(objects, key=lambda o: o.knowledge_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self._version,
            "rules_version": self._rules_version,
            "pattern_detector_version": self._detector.version,
            "confidence_calculator_version": self._confidence.version,
            "evidence_linker_version": self._linker.version,
        }
