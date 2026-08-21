"""
ResearchOS Macro Intelligence Layer - Regime Detector

Main orchestrator for all regime detection algorithms.
Provides the unified RegimeDetector interface.

Algorithm version: det-orch/v2.0.0
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macro_intelligence.regime.detection.employment_detector import detect_employment
from macro_intelligence.regime.detection.growth_detector import detect_growth
from macro_intelligence.regime.detection.inflation_detector import detect_inflation
from macro_intelligence.regime.detection.liquidity_detector import detect_liquidity
from macro_intelligence.regime.detection.models import (
    DetectionEvidence,
    FeatureVector,
    RegimeAssessment,
)
from macro_intelligence.regime.detection.monetary_detector import detect_monetary
from macro_intelligence.regime.detection.risk_detector import detect_risk

ORCHESTRATOR_VERSION = "det-orch/v2.0.0"


class RegimeDetector:
    """
    Unified regime detection orchestrator.

    Accepts FeatureVectors and produces RegimeAssessments.
    All detection is deterministic, stateless, and pure.
    """

    def __init__(self):
        self._version = ORCHESTRATOR_VERSION

    @property
    def version(self) -> str:
        return self._version

    def detect_inflation(self, features: FeatureVector) -> DetectionEvidence:
        """
        Detect inflation regime.

        Args:
            features: FeatureVector with inflation data.

        Returns:
            DetectionEvidence with inflation signal.
        """
        return detect_inflation(features)

    def detect_growth(self, features: FeatureVector) -> DetectionEvidence:
        """
        Detect growth regime.

        Args:
            features: FeatureVector with growth data.

        Returns:
            DetectionEvidence with growth signal.
        """
        return detect_growth(features)

    def detect_monetary(self, features: FeatureVector) -> DetectionEvidence:
        """
        Detect monetary regime.

        Args:
            features: FeatureVector with monetary data.

        Returns:
            DetectionEvidence with monetary signal.
        """
        return detect_monetary(features)

    def detect_liquidity(self, features: FeatureVector) -> DetectionEvidence:
        """
        Detect liquidity regime.

        Args:
            features: FeatureVector with liquidity data.

        Returns:
            DetectionEvidence with liquidity signal.
        """
        return detect_liquidity(features)

    def detect_employment(self, features: FeatureVector) -> DetectionEvidence:
        """
        Detect employment regime.

        Args:
            features: FeatureVector with employment data.

        Returns:
            DetectionEvidence with employment signal.
        """
        return detect_employment(features)

    def detect_risk(self, features: FeatureVector) -> DetectionEvidence:
        """
        Detect risk regime.

        Args:
            features: FeatureVector with risk data.

        Returns:
            DetectionEvidence with risk signal.
        """
        return detect_risk(features)

    def detect_all(self, features: FeatureVector) -> RegimeAssessment:
        """
        Run all detectors and produce a unified regime assessment.

        Args:
            features: FeatureVector with all macro data.

        Returns:
            RegimeAssessment with all signals and overall confidence.
        """
        inflation = self.detect_inflation(features)
        growth = self.detect_growth(features)
        monetary = self.detect_monetary(features)
        liquidity = self.detect_liquidity(features)
        employment = self.detect_employment(features)
        risk = self.detect_risk(features)

        # Compute overall confidence as weighted average
        confidences = [
            inflation.confidence,
            growth.confidence,
            monetary.confidence,
            liquidity.confidence,
            employment.confidence,
            risk.confidence,
        ]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        overall_confidence = round(overall_confidence, 2)

        # Determine dominant regime from risk and growth signals
        dominant_regime = self._determine_dominant_regime(growth.signal, risk.signal, inflation.signal)

        # Generate regime description
        regime_description = self._generate_regime_description(
            inflation.signal,
            growth.signal,
            monetary.signal,
            liquidity.signal,
            employment.signal,
            risk.signal,
        )

        # Collect all evidence refs
        all_evidence_refs = (
            inflation.evidence_refs
            + growth.evidence_refs
            + monetary.evidence_refs
            + liquidity.evidence_refs
            + employment.evidence_refs
            + risk.evidence_refs
        )

        return RegimeAssessment(
            assessment_time=datetime.now(timezone.utc),
            algorithm_version=ORCHESTRATOR_VERSION,
            inflation_signal=inflation,
            growth_signal=growth,
            monetary_signal=monetary,
            liquidity_signal=liquidity,
            employment_signal=employment,
            risk_signal=risk,
            overall_confidence=overall_confidence,
            dominant_regime=dominant_regime,
            regime_description=regime_description,
            evidence_refs=list(set(all_evidence_refs)),
        )

    def _determine_dominant_regime(self, growth: str, risk: str, inflation: str) -> str | None:
        """Determine dominant regime from key signals."""
        # Priority: risk > growth > inflation
        if risk != "neutral":
            return risk
        if growth != "neutral":
            return growth
        if inflation != "neutral":
            return inflation
        return None

    def _generate_regime_description(
        self,
        inflation: str,
        growth: str,
        monetary: str,
        liquidity: str,
        employment: str,
        risk: str,
    ) -> str:
        """Generate human-readable regime description."""
        parts = []

        # Inflation context
        if inflation != "neutral":
            parts.append(f"inflation {inflation}")

        # Growth context
        if growth != "neutral":
            parts.append(f"growth {growth}")

        # Monetary context
        if monetary != "neutral":
            parts.append(f"monetary {monetary}")

        # Risk context
        if risk != "neutral":
            parts.append(f"risk {risk}")

        if parts:
            return " and ".join(parts)
        return "All regimes neutral - insufficient data"

    def to_dict(self) -> dict[str, Any]:
        """Return detector metadata."""
        return {
            "version": self._version,
            "detectors": [
                "inflation_detector",
                "growth_detector",
                "monetary_detector",
                "liquidity_detector",
                "employment_detector",
                "risk_detector",
            ],
        }
