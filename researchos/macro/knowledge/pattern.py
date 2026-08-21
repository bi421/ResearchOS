"""
ResearchOS Macro Intelligence Layer - Knowledge Pattern Detection

The PatternDetector uses deterministic rules ONLY (no machine learning).

It consumes frozen upstream outputs (regime classifications, transitions,
relationships, feature vectors) and emits knowledge-type pattern findings.

Supported patterns:

- REGIME_PERSISTENCE: regime persisted beyond threshold with high confidence
- REGIME_TRANSITION: transition detected with high confidence
- PERSISTENT_RELATIONSHIP: correlation stable over time
- CORRELATION_BREAK: structural break detected in a relationship
- ANOMALY: feature z-score beyond threshold
- REGIME_PATTERN: dominant regime pattern visible
- RISK_OFF_SAFE_HAVEN: risk-off conditions with safe-haven correlation
- TIGHTENING_VOLATILITY: tightening monetary conditions with elevated volatility
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from researchos.macro.knowledge.models import ALGORITHM_VERSION, KnowledgeType
from researchos.macro.knowledge.rules import (
    ANOMALY_MIN_CONFIDENCE,
    ANOMALY_MIN_ZSCORE,
    CORRELATION_BREAK_MIN_CONFIDENCE,
    KNOWLEDGE_RULES_VERSION,
    PERSISTENT_RELATIONSHIP_MIN_ABS_CORR,
    PERSISTENT_RELATIONSHIP_MIN_SAMPLE,
    PERSISTENT_RELATIONSHIP_MIN_STABILITY,
    REGIME_PATTERN_MIN_CONFIDENCE,
    REGIME_PERSISTENCE_MIN_CONFIDENCE,
    REGIME_PERSISTENCE_MIN_CONTINUATION,
    REGIME_PERSISTENCE_MIN_PERIODS,
    REGIME_TRANSITION_MIN_CONFIDENCE,
    RISK_OFF_MIN_ABS_SAFE_HAVEN_CORR,
    RISK_OFF_MIN_CONFIDENCE,
    TIGHTENING_VOL_MIN_CONFIDENCE,
    get_rule,
)


@dataclass(frozen=True)
class PatternFinding:
    """
    A deterministic pattern finding.

    This is an intermediate artifact between raw frozen inputs and a
    final KnowledgeObject. It carries a knowledge type, the statement,
    the confidence of the underlying detection, and the support signature.
    """

    pattern_type: KnowledgeType
    statement: str
    confidence: float
    rule_id: str
    rule_version: str = KNOWLEDGE_RULES_VERSION
    supporting_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "statement": self.statement,
            "confidence": self.confidence,
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "supporting_ids": sorted(self.supporting_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PatternFinding:
        return cls(
            pattern_type=KnowledgeType(data["pattern_type"]),
            statement=data["statement"],
            confidence=data["confidence"],
            rule_id=data["rule_id"],
            rule_version=data.get("rule_version", KNOWLEDGE_RULES_VERSION),
            supporting_ids=tuple(sorted(data.get("supporting_ids", []))),
        )


class PatternDetector:
    """
    Deterministic, rule-based pattern detector.

    Stateless and pure. No machine learning, no randomness, no hidden state.
    """

    def __init__(self) -> None:
        self._version = ALGORITHM_VERSION

    @property
    def version(self) -> str:
        return self._version

    # =========================================================================
    # Regime persistence
    # =========================================================================

    def detect_regime_persistence(
        self,
        persistence_periods: int,
        regime_confidence: float,
        continuation_probability: float,
        regime_name: str,
    ) -> PatternFinding | None:
        """
        Detect REGIME_PERSISTENCE pattern.

        Rule (KNOW-001):
        IF regime persists > REGIME_PERSISTENCE_MIN_PERIODS
        AND confidence > REGIME_PERSISTENCE_MIN_CONFIDENCE
        AND continuation probability > REGIME_PERSISTENCE_MIN_CONTINUATION
        THEN REGIME_PERSISTENCE
        """
        if persistence_periods < REGIME_PERSISTENCE_MIN_PERIODS:
            return None
        if regime_confidence < REGIME_PERSISTENCE_MIN_CONFIDENCE:
            return None
        if continuation_probability < REGIME_PERSISTENCE_MIN_CONTINUATION:
            return None

        statement = (
            f"{regime_name} regime persistence detected with "
            f"{regime_confidence:.2f} confidence over {persistence_periods} periods "
            f"(continuation probability {continuation_probability:.2f})."
        )
        return PatternFinding(
            pattern_type=KnowledgeType.REGIME_PERSISTENCE,
            statement=statement,
            confidence=round(regime_confidence, 4),
            rule_id=get_rule("REGIME_PERSISTENCE").rule_id,
            supporting_ids=(regime_name,),
        )

    # =========================================================================
    # Regime transition
    # =========================================================================

    def detect_regime_transition(
        self,
        transition_detected: bool,
        transition_confidence: float,
        previous_regime: str,
        current_regime: str,
    ) -> PatternFinding | None:
        """
        Detect REGIME_TRANSITION pattern.

        Rule (KNOW-002):
        IF transition detected
        AND transition confidence >= REGIME_TRANSITION_MIN_CONFIDENCE
        THEN REGIME_TRANSITION
        """
        if not transition_detected:
            return None
        if transition_confidence < REGIME_TRANSITION_MIN_CONFIDENCE:
            return None

        statement = f"Regime transition detected from {previous_regime} to {current_regime} with {transition_confidence:.2f} confidence."
        return PatternFinding(
            pattern_type=KnowledgeType.REGIME_TRANSITION,
            statement=statement,
            confidence=round(transition_confidence, 4),
            rule_id=get_rule("REGIME_TRANSITION").rule_id,
            supporting_ids=(previous_regime, current_regime),
        )

    # =========================================================================
    # Persistent relationship
    # =========================================================================

    def detect_persistent_relationship(
        self,
        rolling_stability: float | None,
        overall_correlation: float | None,
        sample_size: int,
        series_a: str,
        series_b: str,
    ) -> PatternFinding | None:
        """
        Detect PERSISTENT_RELATIONSHIP pattern.

        Rule (KNOW-003):
        IF correlation is stable over time (rolling std <= threshold)
        AND |overall correlation| >= threshold
        AND sample size >= threshold
        THEN PERSISTENT_RELATIONSHIP
        """
        if rolling_stability is None or overall_correlation is None:
            return None
        if rolling_stability > PERSISTENT_RELATIONSHIP_MIN_STABILITY:
            return None
        if abs(overall_correlation) < PERSISTENT_RELATIONSHIP_MIN_ABS_CORR:
            return None
        if sample_size < PERSISTENT_RELATIONSHIP_MIN_SAMPLE:
            return None

        statement = (
            f"Persistent relationship detected between {series_a} and {series_b}: "
            f"correlation {overall_correlation:.2f} stable over time "
            f"(rolling std {rolling_stability:.4f})."
        )
        confidence = round(
            min(1.0, abs(overall_correlation) + (1.0 - rolling_stability)),
            4,
        )
        return PatternFinding(
            pattern_type=KnowledgeType.PERSISTENT_RELATIONSHIP,
            statement=statement,
            confidence=confidence,
            rule_id=get_rule("PERSISTENT_RELATIONSHIP").rule_id,
            supporting_ids=(series_a, series_b),
        )

    # =========================================================================
    # Correlation break
    # =========================================================================

    def detect_correlation_break(
        self,
        breaks: list[Any],
        series_a: str,
        series_b: str,
    ) -> PatternFinding | None:
        """
        Detect CORRELATION_BREAK pattern.

        Rule (KNOW-004):
        IF any structural break detected
        AND break confidence >= CORRELATION_BREAK_MIN_CONFIDENCE
        THEN CORRELATION_BREAK
        """
        if not breaks:
            return None

        highest = None
        for b in breaks:
            conf = float(getattr(b, "confidence", 0.0) or 0.0)
            if conf >= CORRELATION_BREAK_MIN_CONFIDENCE:
                if highest is None or conf > highest:
                    highest = conf

        if highest is None:
            return None

        break_type = getattr(breaks[0], "break_type", "structural_break")
        statement = f"Correlation break detected between {series_a} and {series_b} (type: {break_type}) with {highest:.2f} confidence."
        return PatternFinding(
            pattern_type=KnowledgeType.CORRELATION_BREAK,
            statement=statement,
            confidence=round(highest, 4),
            rule_id=get_rule("CORRELATION_BREAK").rule_id,
            supporting_ids=(series_a, series_b),
        )

    # =========================================================================
    # Anomaly
    # =========================================================================

    def detect_anomaly(
        self,
        features: dict[str, Any],
    ) -> PatternFinding | None:
        """
        Detect ANOMALY pattern from feature z-scores.

        Rule (KNOW-005):
        IF |z_score| >= ANOMALY_MIN_ZSCORE
        AND feature confidence >= ANOMALY_MIN_CONFIDENCE
        THEN ANOMALY
        """
        best = None
        best_score = -1.0
        best_conf = 0.0

        # Accept either FeatureValue objects or raw dicts
        for feature_id, fv in features.items():
            if hasattr(fv, "to_dict"):
                data = fv.to_dict()
            elif isinstance(fv, dict):
                data = fv
            else:
                continue

            # A feature may carry a z_score or we use the value magnitude
            z_score = data.get("z_score")
            if z_score is None:
                value = data.get("value")
                if value is None:
                    continue
                z_score = abs(float(value))
            else:
                z_score = abs(float(z_score))

            quality = float(data.get("quality_score", 1.0) or 1.0)

            if z_score >= ANOMALY_MIN_ZSCORE and quality >= ANOMALY_MIN_CONFIDENCE:
                if z_score > best_score:
                    best_score = z_score
                    best = feature_id
                    best_conf = quality

        if best is None:
            return None

        statement = f"Anomaly detected in feature {best}: z-score magnitude {best_score:.2f} beyond threshold {ANOMALY_MIN_ZSCORE}."
        return PatternFinding(
            pattern_type=KnowledgeType.ANOMALY,
            statement=statement,
            confidence=round(best_conf, 4),
            rule_id=get_rule("ANOMALY").rule_id,
            supporting_ids=(best,),
        )

    # =========================================================================
    # Regime pattern
    # =========================================================================

    def detect_regime_pattern(
        self,
        dominant_regime: str,
        regime_confidence: float,
        regime_description: str = "",
    ) -> PatternFinding | None:
        """
        Detect REGIME_PATTERN pattern.

        Rule (KNOW-006):
        IF a dominant regime is observed
        AND regime confidence >= REGIME_PATTERN_MIN_CONFIDENCE
        THEN REGIME_PATTERN
        """
        if not dominant_regime:
            return None
        if regime_confidence < REGIME_PATTERN_MIN_CONFIDENCE:
            return None

        suffix = f" ({regime_description})" if regime_description else ""
        statement = f"Regime pattern detected: dominant regime is {dominant_regime}{suffix} with {regime_confidence:.2f} confidence."
        return PatternFinding(
            pattern_type=KnowledgeType.REGIME_PATTERN,
            statement=statement,
            confidence=round(regime_confidence, 4),
            rule_id=get_rule("REGIME_PATTERN").rule_id,
            supporting_ids=(dominant_regime,),
        )

    # =========================================================================
    # Risk-off / safe haven
    # =========================================================================

    def detect_risk_off_safe_haven(
        self,
        risk_regime: str,
        risk_confidence: float,
        safe_haven_correlations: dict[str, float] | None = None,
    ) -> PatternFinding | None:
        """
        Detect RISK_OFF_SAFE_HAVEN pattern.

        Rule (KNOW-007):
        IF risk regime is risk-off
        AND risk confidence >= RISK_OFF_MIN_CONFIDENCE
        AND |safe-haven correlation| >= RISK_OFF_MIN_ABS_SAFE_HAVEN_CORR
        THEN RISK_OFF_SAFE_HAVEN
        """
        if risk_regime.lower() not in ("risk_off", "risk-off", "crisis"):
            return None
        if risk_confidence < RISK_OFF_MIN_CONFIDENCE:
            return None

        safe_haven_correlations = safe_haven_correlations or {}
        best_pair = None
        best_abs = 0.0

        for pair, corr in safe_haven_correlations.items():
            abs_corr = abs(float(corr))
            if abs_corr >= RISK_OFF_MIN_ABS_SAFE_HAVEN_CORR and abs_corr > best_abs:
                best_abs = abs_corr
                best_pair = pair

        if best_pair is None:
            return None

        statement = (
            f"Risk-off conditions detected (regime {risk_regime}, confidence "
            f"{risk_confidence:.2f}) with safe-haven relationship {best_pair} "
            f"(|correlation| {best_abs:.2f})."
        )
        return PatternFinding(
            pattern_type=KnowledgeType.RISK_OFF_SAFE_HAVEN,
            statement=statement,
            confidence=round(risk_confidence, 4),
            rule_id=get_rule("RISK_OFF_SAFE_HAVEN").rule_id,
            supporting_ids=(risk_regime, best_pair),
        )

    # =========================================================================
    # Tightening volatility
    # =========================================================================

    def detect_tightening_volatility(
        self,
        monetary_regime: str,
        monetary_confidence: float,
        volatility_elevated: bool,
    ) -> PatternFinding | None:
        """
        Detect TIGHTENING_VOLATILITY pattern.

        Rule (KNOW-008):
        IF monetary regime is tightening/hawkish
        AND volatility is elevated
        AND monetary confidence >= TIGHTENING_VOL_MIN_CONFIDENCE
        THEN TIGHTENING_VOLATILITY
        """
        tightening = monetary_regime.lower() in (
            "tightening",
            "hawkish",
            "hawkish_restrictive",
            "fed_hawkish",
        )
        if not tightening:
            return None
        if not volatility_elevated:
            return None
        if monetary_confidence < TIGHTENING_VOL_MIN_CONFIDENCE:
            return None

        statement = (
            f"Tightening volatility conditions detected: monetary regime "
            f"{monetary_regime} (confidence {monetary_confidence:.2f}) with "
            f"elevated volatility."
        )
        return PatternFinding(
            pattern_type=KnowledgeType.TIGHTENING_VOLATILITY,
            statement=statement,
            confidence=round(monetary_confidence, 4),
            rule_id=get_rule("TIGHTENING_VOLATILITY").rule_id,
            supporting_ids=(monetary_regime, "elevated_volatility"),
        )

    # =========================================================================
    # Orchestration
    # =========================================================================

    def detect_all(
        self,
        *,
        persistence_periods: int = 0,
        regime_confidence: float = 0.0,
        continuation_probability: float = 0.0,
        regime_name: str = "",
        transition_detected: bool = False,
        transition_confidence: float = 0.0,
        previous_regime: str = "",
        current_regime: str = "",
        rolling_stability: float | None = None,
        overall_correlation: float | None = None,
        relationship_sample_size: int = 0,
        series_a: str = "",
        series_b: str = "",
        breaks: list[Any] | None = None,
        features: dict[str, Any] | None = None,
        dominant_regime: str = "",
        regime_description: str = "",
        risk_regime: str = "",
        risk_confidence: float = 0.0,
        safe_haven_correlations: dict[str, float] | None = None,
        monetary_regime: str = "",
        monetary_confidence: float = 0.0,
        volatility_elevated: bool = False,
    ) -> list[PatternFinding]:
        """
        Run all deterministic pattern detectors.

        Returns:
            List of PatternFindings (possibly empty).
        """
        findings: list[PatternFinding] = []

        finding = self.detect_regime_persistence(persistence_periods, regime_confidence, continuation_probability, regime_name)
        if finding:
            findings.append(finding)

        finding = self.detect_regime_transition(transition_detected, transition_confidence, previous_regime, current_regime)
        if finding:
            findings.append(finding)

        finding = self.detect_persistent_relationship(rolling_stability, overall_correlation, relationship_sample_size, series_a, series_b)
        if finding:
            findings.append(finding)

        finding = self.detect_correlation_break(breaks or [], series_a, series_b)
        if finding:
            findings.append(finding)

        finding = self.detect_anomaly(features or {})
        if finding:
            findings.append(finding)

        finding = self.detect_regime_pattern(dominant_regime, regime_confidence, regime_description)
        if finding:
            findings.append(finding)

        finding = self.detect_risk_off_safe_haven(risk_regime, risk_confidence, safe_haven_correlations)
        if finding:
            findings.append(finding)

        finding = self.detect_tightening_volatility(monetary_regime, monetary_confidence, volatility_elevated)
        if finding:
            findings.append(finding)

        # Deterministic ordering by knowledge type value
        return sorted(findings, key=lambda f: f.pattern_type.value)
