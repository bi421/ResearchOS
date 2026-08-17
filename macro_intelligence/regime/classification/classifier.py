"""
ResearchOS Macro Intelligence Layer - Regime Classifier

Main classification engine that transforms RegimeAssessment outputs
into unified MacroRegime classifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from macro_intelligence.regime.classification.models import (
    ClassificationEvidence,
    ClassificationRule,
    RegimeClassification,
)
from macro_intelligence.regime.classification.rules import (
    ALL_RULES,
    RULES_VERSION,
)
from macro_intelligence.regime.classification.taxonomy import (
    MacroRegime,
)
from macro_intelligence.regime.detection.models import RegimeAssessment
from macro_intelligence.statistics.provenance import content_hash


class RegimeClassifier:
    """
    Deterministic regime classification engine.

    Transforms RegimeAssessment outputs into unified
    MacroRegime classifications using rule-based logic.
    """

    def __init__(self):
        self._version = RULES_VERSION
        self._rules = ALL_RULES

    @property
    def version(self) -> str:
        return self._version

    def classify_growth_inflation(
        self,
        inflation_signal: str,
        growth_signal: str,
        inflation_confidence: float,
        growth_confidence: float,
    ) -> tuple[str, float, str]:
        """
        Classify growth/inflation regime.

        Returns:
            (regime, confidence, explanation)
        """
        for rule in self._rules["growth_inflation"]:
            if rule.matches({"inflation": inflation_signal, "growth": growth_signal}):
                # Confidence is weighted average of detector confidences
                confidence = round((inflation_confidence + growth_confidence) / 2, 2)
                # Minimum confidence floor
                confidence = max(confidence, 0.5)
                explanation = self._build_gi_explanation(inflation_signal, growth_signal, rule)
                return rule.result_regime, confidence, explanation

        # Default: stable/slowdown
        return "disinflation", 0.5, "Default classification: no matching rules"

    def classify_liquidity(
        self,
        liquidity_signal: str,
        liquidity_confidence: float,
    ) -> tuple[str, float, str]:
        """
        Classify liquidity regime.

        Returns:
            (regime, confidence, explanation)
        """
        for rule in self._rules["liquidity"]:
            if rule.matches({"liquidity": liquidity_signal}):
                return rule.result_regime, liquidity_confidence, rule.description

        return "liquidity_neutral", 0.5, "Default liquidity: neutral"

    def classify_risk(
        self,
        risk_signal: str,
        risk_confidence: float,
    ) -> tuple[str, float, str]:
        """
        Classify risk regime.

        Returns:
            (regime, confidence, explanation)
        """
        for rule in self._rules["risk"]:
            if rule.matches({"risk": risk_signal}):
                return rule.result_regime, risk_confidence, rule.description

        return "risk_off", 0.5, "Default risk: risk_off"

    def classify_monetary(
        self,
        monetary_signal: str,
        monetary_confidence: float,
    ) -> tuple[str, float, str]:
        """
        Classify monetary regime.

        Returns:
            (regime, confidence, explanation)
        """
        for rule in self._rules["monetary"]:
            if rule.matches({"monetary": monetary_signal}):
                return rule.result_regime, monetary_confidence, rule.description

        return "fed_neutral", 0.5, "Default monetary: neutral"

    def classify_macro_regime(
        self,
        assessment: RegimeAssessment,
        classification_id: str | None = None,
    ) -> RegimeClassification:
        """
        Full macro regime classification from a RegimeAssessment.

        Args:
            assessment: RegimeAssessment from detection engine
            classification_id: Optional custom ID (auto-generated if None)

        Returns:
            RegimeClassification with all signals
        """
        # Classify each dimension
        gi_regime, gi_confidence, gi_explanation = self.classify_growth_inflation(
            assessment.inflation_signal.signal,
            assessment.growth_signal.signal,
            assessment.inflation_signal.confidence,
            assessment.growth_signal.confidence,
        )

        liq_regime, liq_confidence, liq_explanation = self.classify_liquidity(
            assessment.liquidity_signal.signal,
            assessment.liquidity_signal.confidence,
        )

        risk_regime, risk_confidence, risk_explanation = self.classify_risk(
            assessment.risk_signal.signal,
            assessment.risk_signal.confidence,
        )

        mon_regime, mon_confidence, mon_explanation = self.classify_monetary(
            assessment.monetary_signal.signal,
            assessment.monetary_signal.confidence,
        )

        emp_regime, emp_confidence, emp_explanation = self.classify_employment(
            assessment.employment_signal.signal,
            assessment.employment_signal.confidence,
        )

        # Determine primary regime from GI classification
        primary_regime = self._map_macro_regime(gi_regime)

        # Build secondary regimes
        secondary_regimes = {
            "liquidity": liq_regime,
            "risk": risk_regime,
            "monetary": mon_regime,
            "employment": emp_regime,
        }

        # Compute overall confidence
        overall_confidence = round(
            (gi_confidence + liq_confidence + risk_confidence + mon_confidence + emp_confidence)
            / 5,
            2,
        )

        confidence_breakdown = {
            "growth_inflation": gi_confidence,
            "liquidity": liq_confidence,
            "risk": risk_confidence,
            "monetary": mon_confidence,
            "employment": emp_confidence,
        }

        # Build evidence
        evidence = ClassificationEvidence(
            matching_rule_id="GI-" + gi_regime.upper()[:3]
            if gi_regime != "disinflation"
            else "GI-005",
            matching_rule_version=RULES_VERSION,
            signal_evidence={
                "inflation": assessment.inflation_signal.signal,
                "growth": assessment.growth_signal.signal,
                "liquidity": assessment.liquidity_signal.signal,
                "risk": assessment.risk_signal.signal,
                "monetary": assessment.monetary_signal.signal,
                "employment": assessment.employment_signal.signal,
            },
            explanation=gi_explanation,
            detector_provenance={
                "inflation": assessment.inflation_signal.algorithm_version,
                "growth": assessment.growth_signal.algorithm_version,
                "liquidity": assessment.liquidity_signal.algorithm_version,
                "risk": assessment.risk_signal.algorithm_version,
                "monetary": assessment.monetary_signal.algorithm_version,
                "employment": assessment.employment_signal.algorithm_version,
            },
        )

        # Generate explanation
        explanation = self._generate_full_explanation(
            gi_regime,
            liq_regime,
            risk_regime,
            mon_regime,
            emp_regime,
            gi_explanation,
            liq_explanation,
            risk_explanation,
            mon_explanation,
            emp_explanation,
        )

        # Generate classification ID if not provided.
        # Content-derived deterministic ID: identical scientific inputs
        # produce an identical classification_id (no wall-clock time).
        if classification_id is None:
            classification_id = "CL-" + content_hash(
                {
                    "gi": gi_regime,
                    "liq": liq_regime,
                    "risk": risk_regime,
                    "mon": mon_regime,
                    "emp": emp_regime,
                    "confidence": overall_confidence,
                }
            )

        return RegimeClassification(
            classification_id=classification_id,
            algorithm_version=self._version,
            primary_regime=primary_regime,
            secondary_regimes=secondary_regimes,
            confidence=overall_confidence,
            confidence_breakdown=confidence_breakdown,
            evidence=evidence,
            classification_time=datetime.now(timezone.utc),
            rule_applied=gi_regime,
            explanation=explanation,
        )

    def classify_employment(
        self,
        employment_signal: str,
        employment_confidence: float,
    ) -> tuple[str, float, str]:
        """Classify employment regime."""
        employment_map = {
            "strong": "employment_strong",
            "normal": "employment_normal",
            "weakening": "employment_weakening",
            "stressed": "employment_stressed",
        }
        regime = employment_map.get(employment_signal, "employment_normal")
        return regime, employment_confidence, f"Employment: {employment_signal}"

    def _map_macro_regime(self, gi_regime: str) -> MacroRegime:
        """Map growth/inflation regime to MacroRegime enum."""
        mapping = {
            "goldilocks": MacroRegime.GOLDILOCKS,
            "inflationary_growth": MacroRegime.INFLATIONARY_GROWTH,
            "stagflation": MacroRegime.STAGFLATION,
            "disinflation": MacroRegime.DISINFLATION,
            "deflationary_slowdown": MacroRegime.DEFLATIONARY_SLOWDOWN,
            "recession": MacroRegime.RECESSION,
        }
        return mapping.get(gi_regime, MacroRegime.DISINFLATION)

    def _build_gi_explanation(
        self,
        inflation: str,
        growth: str,
        rule: ClassificationRule,
    ) -> str:
        """Build explanation for growth/inflation classification."""
        return f"{rule.description}. Inflation: {inflation}, Growth: {growth}"

    def _generate_full_explanation(
        self,
        gi_regime: str,
        liq_regime: str,
        risk_regime: str,
        mon_regime: str,
        emp_regime: str,
        gi_explanation: str,
        liq_explanation: str,
        risk_explanation: str,
        mon_explanation: str,
        emp_explanation: str,
    ) -> str:
        """Generate full classification explanation."""
        parts = [gi_explanation]
        if liq_regime != "liquidity_neutral":
            parts.append(liq_explanation)
        if risk_regime != "risk_off":
            parts.append(risk_explanation)
        if mon_regime != "fed_neutral":
            parts.append(mon_explanation)
        if emp_regime not in ("employment_normal", "employment_strong"):
            parts.append(emp_explanation)
        return "; ".join(parts)

    def get_rule_by_id(self, rule_id: str) -> ClassificationRule | None:
        """Get a specific rule by ID."""
        for category, rules in self._rules.items():
            for rule in rules:
                if rule.rule_id == rule_id:
                    return rule
        return None

    def get_all_rules(self) -> list[ClassificationRule]:
        """Get all classification rules."""
        return [rule for rules in self._rules.values() for rule in rules]

    def to_dict(self) -> dict[str, Any]:
        """Return classifier metadata."""
        return {
            "version": self._version,
            "categories": list(self._rules.keys()),
            "total_rules": sum(len(rules) for rules in self._rules.values()),
        }
