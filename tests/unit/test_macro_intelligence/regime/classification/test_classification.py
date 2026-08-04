"""
ResearchOS Macro Intelligence Layer - Regime Classification Tests
Tests for deterministic regime classification engine.
"""

import pytest
from datetime import datetime, timezone

UTC = timezone.utc


def _make_test_assessment(**kwargs):
    """Module-level helper to create a RegimeAssessment with default values."""
    from macro_intelligence.regime.detection.models import RegimeAssessment, DetectionEvidence

    defaults = {
        "assessment_time": datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        "algorithm_version": "det-orch/v2.0.0",
        "inflation_signal": DetectionEvidence(
            detector_name="inflation_detector",
            signal="stable",
            confidence=0.8,
            algorithm_version="infl-det/v2.0.0",
        ),
        "growth_signal": DetectionEvidence(
            detector_name="growth_detector",
            signal="expansion",
            confidence=0.85,
            algorithm_version="grw-det/v2.0.0",
        ),
        "monetary_signal": DetectionEvidence(
            detector_name="monetary_detector",
            signal="neutral",
            confidence=0.7,
            algorithm_version="mon-det/v2.0.0",
        ),
        "liquidity_signal": DetectionEvidence(
            detector_name="liquidity_detector",
            signal="expanding",
            confidence=0.75,
            algorithm_version="liq-det/v2.0.0",
        ),
        "employment_signal": DetectionEvidence(
            detector_name="employment_detector",
            signal="strong",
            confidence=0.9,
            algorithm_version="emp-det/v2.0.0",
        ),
        "risk_signal": DetectionEvidence(
            detector_name="risk_detector",
            signal="normal",
            confidence=0.65,
            algorithm_version="risk-det/v2.0.0",
        ),
        "overall_confidence": 0.78,
    }
    defaults.update(kwargs)
    return RegimeAssessment(**defaults)


# =============================================================================
# Taxonomy tests
# =============================================================================


class TestTaxonomy:
    """Tests for regime taxonomy enums."""

    def test_macro_regime_values(self):
        """Test all macro regimes have correct values."""
        from macro_intelligence.regime.classification import MacroRegime

        assert MacroRegime.GOLDILOCKS.value == "goldilocks"
        assert MacroRegime.INFLATIONARY_GROWTH.value == "inflationary_growth"
        assert MacroRegime.STAGFLATION.value == "stagflation"
        assert MacroRegime.DISINFLATION.value == "disinflation"
        assert MacroRegime.DEFLATIONARY_SLOWDOWN.value == "deflationary_slowdown"
        assert MacroRegime.RECESSION.value == "recession"

    def test_liquidity_regime_values(self):
        """Test all liquidity regimes."""
        from macro_intelligence.regime.classification import LiquidityRegime

        assert LiquidityRegime.LIQUIDITY_EXPANSION.value == "liquidity_expansion"
        assert LiquidityRegime.LIQUIDITY_NEUTRAL.value == "liquidity_neutral"
        assert LiquidityRegime.LIQUIDITY_CONTRACTION.value == "liquidity_contraction"

    def test_risk_regime_values(self):
        """Test all risk regimes."""
        from macro_intelligence.regime.classification import RiskRegime

        assert RiskRegime.RISK_ON.value == "risk_on"
        assert RiskRegime.RISK_OFF.value == "risk_off"
        assert RiskRegime.CRISIS.value == "crisis"

    def test_monetary_regime_values(self):
        """Test all monetary regimes."""
        from macro_intelligence.regime.classification import MonetaryRegime

        assert MonetaryRegime.FED_HAWKISH.value == "fed_hawkish"
        assert MonetaryRegime.FED_NEUTRAL.value == "fed_neutral"
        assert MonetaryRegime.FED_DOVISH.value == "fed_dovish"

    def test_priority_orderings(self):
        """Test priority orderings are defined."""
        from macro_intelligence.regime.classification import (
            MACRO_REGIME_PRIORITY,
            LIQUIDITY_REGIME_PRIORITY,
            RISK_REGIME_PRIORITY,
            MONETARY_REGIME_PRIORITY,
        )

        assert len(MACRO_REGIME_PRIORITY) == 6
        assert len(LIQUIDITY_REGIME_PRIORITY) == 3
        assert len(RISK_REGIME_PRIORITY) == 3
        assert len(MONETARY_REGIME_PRIORITY) == 3


# =============================================================================
# ClassificationRule tests
# =============================================================================


class TestClassificationRule:
    """Tests for ClassificationRule model."""

    def test_create_rule(self):
        """Test creating a classification rule."""
        from macro_intelligence.regime.classification import ClassificationRule

        rule = ClassificationRule(
            rule_id="TEST-001",
            rule_version="cls-rules/v1.0.0",
            conditions={"inflation": "stable", "growth": "expansion"},
            result_regime="goldilocks",
            description="Goldilocks regime",
            provenance="test",
        )

        assert rule.rule_id == "TEST-001"
        assert rule.result_regime == "goldilocks"
        assert rule.matches({"inflation": "stable", "growth": "expansion"}) is True
        assert rule.matches({"inflation": "high", "growth": "contraction"}) is False

    def test_rule_to_dict(self):
        """Test rule serialization."""
        from macro_intelligence.regime.classification import ClassificationRule

        rule = ClassificationRule(
            rule_id="TEST-001",
            rule_version="v1",
            conditions={"a": "1", "b": "2"},
            result_regime="test",
            description="Test rule",
        )

        data = rule.to_dict()
        assert data["rule_id"] == "TEST-001"
        assert data["result_regime"] == "test"

    def test_rule_from_dict(self):
        """Test rule deserialization."""
        from macro_intelligence.regime.classification import ClassificationRule

        data = {
            "rule_id": "TEST-001",
            "rule_version": "v1",
            "conditions": {"inflation": "stable", "growth": "expansion"},
            "result_regime": "goldilocks",
            "description": "Test",
        }

        rule = ClassificationRule.from_dict(data)
        assert rule.rule_id == "TEST-001"
        assert rule.matches({"inflation": "stable", "growth": "expansion"}) is True

    def test_rule_immutability(self):
        """Test that rules are immutable."""
        from macro_intelligence.regime.classification import ClassificationRule

        rule = ClassificationRule(
            rule_id="TEST-001",
            rule_version="v1",
            conditions={"a": "1"},
            result_regime="test",
            description="Test",
        )

        with pytest.raises(AttributeError):
            rule.rule_id = "MODIFIED"

    def test_rule_hash_deterministic(self):
        """Test rule hash determinism."""
        from macro_intelligence.regime.classification import ClassificationRule

        r1 = ClassificationRule(
            rule_id="TEST-001",
            rule_version="v1",
            conditions={"a": "1", "b": "2"},
            result_regime="test",
            description="Test",
        )
        r2 = ClassificationRule(
            rule_id="TEST-001",
            rule_version="v1",
            conditions={"a": "1", "b": "2"},
            result_regime="test",
            description="Test",
        )

        assert r1.compute_hash() == r2.compute_hash()

    def test_rule_matches_partial(self):
        """Test rule matching with partial conditions."""
        from macro_intelligence.regime.classification import ClassificationRule

        rule = ClassificationRule(
            rule_id="TEST-001",
            rule_version="v1",
            conditions={"inflation": "stable"},
            result_regime="test",
            description="Test",
        )

        assert rule.matches({"inflation": "stable", "growth": "expansion"}) is True
        assert rule.matches({"inflation": "high", "growth": "expansion"}) is False


# =============================================================================
# ClassificationEvidence tests
# =============================================================================


class TestClassificationEvidence:
    """Tests for ClassificationEvidence model."""

    def test_create_evidence(self):
        """Test creating classification evidence."""
        from macro_intelligence.regime.classification import ClassificationEvidence

        evidence = ClassificationEvidence(
            matching_rule_id="GI-010",
            matching_rule_version="cls-rules/v3.0.0",
            signal_evidence={"inflation": "stable", "growth": "expansion"},
            explanation="Goldilocks regime",
            detector_provenance={"inflation": "infl-det/v2.0.0"},
        )

        assert evidence.matching_rule_id == "GI-010"
        assert evidence.explanation == "Goldilocks regime"

    def test_evidence_to_dict(self):
        """Test evidence serialization."""
        from macro_intelligence.regime.classification import ClassificationEvidence

        evidence = ClassificationEvidence(
            matching_rule_id="GI-010",
            matching_rule_version="v1",
            signal_evidence={"a": "1"},
        )

        data = evidence.to_dict()
        assert data["matching_rule_id"] == "GI-010"

    def test_evidence_roundtrip(self):
        """Test evidence serialization roundtrip."""
        from macro_intelligence.regime.classification import ClassificationEvidence

        original = ClassificationEvidence(
            matching_rule_id="GI-010",
            matching_rule_version="v1",
            signal_evidence={"inflation": "stable", "growth": "expansion"},
            explanation="Test",
            detector_provenance={"infl": "v1"},
        )

        data = original.to_dict()
        restored = ClassificationEvidence.from_dict(data)

        assert restored.matching_rule_id == original.matching_rule_id
        assert restored.signal_evidence == original.signal_evidence

    def test_evidence_immutability(self):
        """Test evidence immutability."""
        from macro_intelligence.regime.classification import ClassificationEvidence

        evidence = ClassificationEvidence(
            matching_rule_id="GI-010",
            matching_rule_version="v1",
            signal_evidence={"a": "1"},
        )

        with pytest.raises(AttributeError):
            evidence.matching_rule_id = "MODIFIED"


# =============================================================================
# RegimeClassification model tests
# =============================================================================


class TestRegimeClassification:
    """Tests for RegimeClassification model."""

    def test_create_classification(self):
        """Test creating a RegimeClassification."""
        from macro_intelligence.regime.classification import (
            ClassificationEvidence,
            MacroRegime,
            RegimeClassification,
        )

        classification = RegimeClassification(
            classification_id="CL-001",
            algorithm_version="cls-rules/v3.0.0",
            primary_regime=MacroRegime.GOLDILOCKS,
            secondary_regimes={"liquidity": "liquidity_expansion"},
            confidence=0.85,
            confidence_breakdown={"gi": 0.9},
            evidence=ClassificationEvidence(
                matching_rule_id="GI-010",
                matching_rule_version="v3.0.0",
                signal_evidence={"inflation": "stable", "growth": "expansion"},
                explanation="Goldilocks",
            ),
            classification_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            rule_applied="goldilocks",
            explanation="Stable inflation with expansion",
        )

        assert classification.primary_regime == MacroRegime.GOLDILOCKS
        assert classification.confidence == 0.85
        assert classification.classification_id == "CL-001"

    def test_classification_to_dict(self):
        """Test classification serialization."""
        from macro_intelligence.regime.classification import (
            ClassificationEvidence,
            MacroRegime,
            RegimeClassification,
        )

        classification = RegimeClassification(
            classification_id="CL-001",
            algorithm_version="v1",
            primary_regime=MacroRegime.GOLDILOCKS,
            confidence=0.8,
            evidence=ClassificationEvidence(
                matching_rule_id="GI-010",
                matching_rule_version="v1",
                signal_evidence={"inflation": "stable"},
            ),
            classification_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        data = classification.to_dict()
        assert data["primary_regime"] == "goldilocks"
        assert data["confidence"] == 0.8

    def test_classification_from_dict(self):
        """Test classification deserialization."""
        from macro_intelligence.regime.classification import RegimeClassification

        data = {
            "classification_id": "CL-001",
            "algorithm_version": "v1",
            "primary_regime": "goldilocks",
            "secondary_regimes": {},
            "confidence": 0.8,
            "confidence_breakdown": {},
            "evidence": {
                "matching_rule_id": "GI-010",
                "matching_rule_version": "v1",
                "signal_evidence": {"inflation": "stable"},
                "explanation": "Test",
                "detector_provenance": {},
            },
            "classification_time": "2026-08-03T12:00:00+00:00",
            "rule_applied": "goldilocks",
            "explanation": "Test",
        }

        classification = RegimeClassification.from_dict(data)
        assert classification.primary_regime.value == "goldilocks"

    def test_classification_roundtrip(self):
        """Test classification JSON roundtrip."""
        from macro_intelligence.regime.classification import (
            ClassificationEvidence,
            MacroRegime,
            RegimeClassification,
        )

        original = RegimeClassification(
            classification_id="CL-001",
            algorithm_version="v1",
            primary_regime=MacroRegime.GOLDILOCKS,
            confidence=0.85,
            evidence=ClassificationEvidence(
                matching_rule_id="GI-010",
                matching_rule_version="v1",
                signal_evidence={"inflation": "stable", "growth": "expansion"},
            ),
            classification_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        json_str = original.to_json()
        restored = RegimeClassification.from_json(json_str)

        assert restored.classification_id == original.classification_id
        assert restored.primary_regime == original.primary_regime
        assert restored.confidence == original.confidence
        assert restored.to_json() == json_str

    def test_classification_hash_deterministic(self):
        """Test classification hash determinism."""
        from macro_intelligence.regime.classification import (
            ClassificationEvidence,
            MacroRegime,
            RegimeClassification,
        )

        c1 = RegimeClassification(
            classification_id="CL-001",
            algorithm_version="v1",
            primary_regime=MacroRegime.GOLDILOCKS,
            confidence=0.85,
            evidence=ClassificationEvidence(
                matching_rule_id="GI-010",
                matching_rule_version="v1",
                signal_evidence={"a": "1"},
            ),
            classification_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        c2 = RegimeClassification(
            classification_id="CL-001",
            algorithm_version="v1",
            primary_regime=MacroRegime.GOLDILOCKS,
            confidence=0.85,
            evidence=ClassificationEvidence(
                matching_rule_id="GI-010",
                matching_rule_version="v1",
                signal_evidence={"a": "1"},
            ),
            classification_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        assert c1.compute_hash() == c2.compute_hash()

    def test_classification_immutability(self):
        """Test classification immutability."""
        from macro_intelligence.regime.classification import (
            ClassificationEvidence,
            MacroRegime,
            RegimeClassification,
        )

        classification = RegimeClassification(
            classification_id="CL-001",
            algorithm_version="v1",
            primary_regime=MacroRegime.GOLDILOCKS,
            confidence=0.85,
            evidence=ClassificationEvidence(
                matching_rule_id="GI-010",
                matching_rule_version="v1",
                signal_evidence={"a": "1"},
            ),
            classification_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )

        with pytest.raises(AttributeError):
            classification.classification_id = "MODIFIED"


# =============================================================================
# Growth/Inflation classification tests
# =============================================================================


class TestGrowthInflationClassification:
    """Tests for growth/inflation classification rules."""

    def test_goldilocks(self):
        """Test goldilocks classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_growth_inflation(
            inflation_signal="stable",
            growth_signal="expansion",
            inflation_confidence=0.8,
            growth_confidence=0.9,
        )

        assert regime == "goldilocks"
        assert 0.5 <= confidence <= 1.0

    def test_recession(self):
        """Test recession classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_growth_inflation(
            inflation_signal="high",
            growth_signal="contraction",
            inflation_confidence=0.9,
            growth_confidence=0.85,
        )

        assert regime == "recession"

    def test_stagflation(self):
        """Test stagflation classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()

        regime1, _, _ = classifier.classify_growth_inflation(
            inflation_signal="rising",
            growth_signal="slowdown",
            inflation_confidence=0.8,
            growth_confidence=0.75,
        )
        assert regime1 == "stagflation"

        regime2, _, _ = classifier.classify_growth_inflation(
            inflation_signal="high",
            growth_signal="slowdown",
            inflation_confidence=0.9,
            growth_confidence=0.8,
        )
        assert regime2 == "stagflation"

    def test_disinflation(self):
        """Test disinflation classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()

        regime1, _, _ = classifier.classify_growth_inflation(
            inflation_signal="falling",
            growth_signal="slowdown",
            inflation_confidence=0.7,
            growth_confidence=0.65,
        )
        assert regime1 == "disinflation"

        regime2, _, _ = classifier.classify_growth_inflation(
            inflation_signal="falling",
            growth_signal="contraction",
            inflation_confidence=0.7,
            growth_confidence=0.6,
        )
        assert regime2 == "disinflation"

    def test_inflationary_growth(self):
        """Test inflationary growth classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()

        regime1, _, _ = classifier.classify_growth_inflation(
            inflation_signal="rising",
            growth_signal="expansion",
            inflation_confidence=0.8,
            growth_confidence=0.85,
        )
        assert regime1 == "inflationary_growth"

        regime2, _, _ = classifier.classify_growth_inflation(
            inflation_signal="high",
            growth_signal="expansion",
            inflation_confidence=0.9,
            growth_confidence=0.85,
        )
        assert regime2 == "inflationary_growth"

        regime3, _, _ = classifier.classify_growth_inflation(
            inflation_signal="rising",
            growth_signal="recovery",
            inflation_confidence=0.8,
            growth_confidence=0.75,
        )
        assert regime3 == "inflationary_growth"

    def test_deflationary_slowdown(self):
        """Test deflationary slowdown classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_growth_inflation(
            inflation_signal="deflationary",
            growth_signal="slowdown",
            inflation_confidence=0.7,
            growth_confidence=0.65,
        )

        assert regime == "deflationary_slowdown"

    def test_default_classification(self):
        """Test default classification when no rules match."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_growth_inflation(
            inflation_signal="stable",
            growth_signal="normal",
            inflation_confidence=0.5,
            growth_confidence=0.5,
        )

        assert regime == "disinflation"
        assert confidence == 0.5

    def test_classification_deterministic(self):
        """Test that growth/inflation classification is deterministic."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()

        results = [
            classifier.classify_growth_inflation(
                inflation_signal="stable",
                growth_signal="expansion",
                inflation_confidence=0.8,
                growth_confidence=0.9,
            )
            for _ in range(10)
        ]

        for result in results[1:]:
            assert result[0] == results[0][0]
            assert result[1] == results[0][1]


# =============================================================================
# Liquidity classification tests
# =============================================================================


class TestLiquidityClassification:
    """Tests for liquidity classification."""

    def test_liquidity_expansion(self):
        """Test liquidity expansion classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_liquidity(
            liquidity_signal="expanding",
            liquidity_confidence=0.8,
        )

        assert regime == "liquidity_expansion"
        assert confidence == 0.8

    def test_liquidity_contraction(self):
        """Test liquidity contraction classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_liquidity(
            liquidity_signal="contracting",
            liquidity_confidence=0.75,
        )

        assert regime == "liquidity_contraction"

    def test_liquidity_neutral(self):
        """Test liquidity neutral classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_liquidity(
            liquidity_signal="neutral",
            liquidity_confidence=0.6,
        )

        assert regime == "liquidity_neutral"

    def test_liquidity_deterministic(self):
        """Test liquidity classification determinism."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        r1 = classifier.classify_liquidity("expanding", 0.8)
        r2 = classifier.classify_liquidity("expanding", 0.8)

        assert r1 == r2


# =============================================================================
# Risk classification tests
# =============================================================================


class TestRiskClassification:
    """Tests for risk classification."""

    def test_risk_on(self):
        """Test risk-on classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_risk(
            risk_signal="risk_on",
            risk_confidence=0.85,
        )

        assert regime == "risk_on"

    def test_risk_off(self):
        """Test risk-off classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_risk(
            risk_signal="risk_off",
            risk_confidence=0.7,
        )

        assert regime == "risk_off"

    def test_crisis(self):
        """Test crisis classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_risk(
            risk_signal="crisis",
            risk_confidence=0.95,
        )

        assert regime == "crisis"

    def test_risk_deterministic(self):
        """Test risk classification determinism."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        r1 = classifier.classify_risk("crisis", 0.95)
        r2 = classifier.classify_risk("crisis", 0.95)

        assert r1 == r2


# =============================================================================
# Monetary classification tests
# =============================================================================


class TestMonetaryClassification:
    """Tests for monetary classification."""

    def test_hawkish(self):
        """Test hawkish classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_monetary(
            monetary_signal="hawkish",
            monetary_confidence=0.8,
        )

        assert regime == "fed_hawkish"

    def test_dovish(self):
        """Test dovish classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_monetary(
            monetary_signal="dovish",
            monetary_confidence=0.75,
        )

        assert regime == "fed_dovish"

    def test_neutral(self):
        """Test neutral classification."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        regime, confidence, explanation = classifier.classify_monetary(
            monetary_signal="neutral",
            monetary_confidence=0.6,
        )

        assert regime == "fed_neutral"

    def test_monetary_deterministic(self):
        """Test monetary classification determinism."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        r1 = classifier.classify_monetary("hawkish", 0.8)
        r2 = classifier.classify_monetary("hawkish", 0.8)

        assert r1 == r2


# =============================================================================
# Full classification tests
# =============================================================================


class TestFullClassification:
    """Tests for full RegimeClassification output."""

    def test_goldilocks_full_classification(self):
        """Test full classification for goldilocks regime."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classification = classifier.classify_macro_regime(assessment)

        assert classification.primary_regime.value == "goldilocks"
        assert classification.confidence > 0
        assert classification.classification_id is not None
        assert "stable" in classification.explanation.lower()

    def test_recession_full_classification(self):
        """Test full classification for recession regime."""
        from macro_intelligence.regime.classification import RegimeClassifier
        from macro_intelligence.regime.detection.models import DetectionEvidence

        classifier = RegimeClassifier()
        assessment = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="high",
                confidence=0.9,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="contraction",
                confidence=0.85,
                algorithm_version="grw-det/v2.0.0",
            ),
            monetary_signal=DetectionEvidence(
                detector_name="monetary_detector",
                signal="hawkish",
                confidence=0.8,
                algorithm_version="mon-det/v2.0.0",
            ),
            liquidity_signal=DetectionEvidence(
                detector_name="liquidity_detector",
                signal="contracting",
                confidence=0.75,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="stressed",
                confidence=0.9,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="crisis",
                confidence=0.95,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.88,
        )

        classification = classifier.classify_macro_regime(assessment)

        assert classification.primary_regime.value == "recession"

    def test_stagflation_full_classification(self):
        """Test full classification for stagflation regime."""
        from macro_intelligence.regime.classification import RegimeClassifier
        from macro_intelligence.regime.detection.models import DetectionEvidence

        classifier = RegimeClassifier()
        assessment = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="rising",
                confidence=0.8,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="slowdown",
                confidence=0.75,
                algorithm_version="grw-det/v2.0.0",
            ),
            monetary_signal=DetectionEvidence(
                detector_name="monetary_detector",
                signal="hawkish",
                confidence=0.85,
                algorithm_version="mon-det/v2.0.0",
            ),
            liquidity_signal=DetectionEvidence(
                detector_name="liquidity_detector",
                signal="neutral",
                confidence=0.6,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="weakening",
                confidence=0.7,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="risk_off",
                confidence=0.75,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.75,
        )

        classification = classifier.classify_macro_regime(assessment)

        assert classification.primary_regime.value == "stagflation"

    def test_classification_deterministic(self):
        """Test that full classification is deterministic."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classifications = [classifier.classify_macro_regime(assessment) for _ in range(10)]

        for c in classifications[1:]:
            assert c.primary_regime == classifications[0].primary_regime
            assert c.confidence == classifications[0].confidence
            assert c.evidence.signal_evidence == classifications[0].evidence.signal_evidence

    def test_classification_preserves_provenance(self):
        """Test that classification preserves detector provenance."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classification = classifier.classify_macro_regime(assessment)

        provenance = classification.evidence.detector_provenance
        assert "inflation" in provenance
        assert provenance["inflation"] == "infl-det/v2.0.0"
        assert "growth" in provenance
        assert provenance["growth"] == "grw-det/v2.0.0"
        assert "monetary" in provenance
        assert "liquidity" in provenance
        assert "risk" in provenance
        assert "employment" in provenance

    def test_classification_no_mutation(self):
        """Test that classification does not mutate assessment."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        original_hash = assessment.compute_hash()
        classifier.classify_macro_regime(assessment)

        assert assessment.compute_hash() == original_hash

    def test_classification_json_roundtrip(self):
        """Test classification JSON serialization roundtrip."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classification = classifier.classify_macro_regime(assessment, classification_id="CL-TEST-001")

        json_str = classification.to_json()
        restored = type(classification).from_json(json_str)

        assert restored.classification_id == "CL-TEST-001"
        assert restored.primary_regime == classification.primary_regime
        assert restored.confidence == classification.confidence
        assert restored.to_json() == json_str

    def test_custom_classification_id(self):
        """Test custom classification ID."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classification = classifier.classify_macro_regime(assessment, classification_id="CL-MY-CUSTOM-ID")

        assert classification.classification_id == "CL-MY-CUSTOM-ID"

    def test_all_regimes_classifiable(self):
        """Test that all macro regimes can be classified."""
        from macro_intelligence.regime.classification import RegimeClassifier
        from macro_intelligence.regime.detection.models import DetectionEvidence

        classifier = RegimeClassifier()

        test_cases = [
            ("stable", "expansion", "goldilocks"),
            ("rising", "expansion", "inflationary_growth"),
            ("high", "expansion", "inflationary_growth"),
            ("rising", "slowdown", "stagflation"),
            ("high", "slowdown", "stagflation"),
            ("falling", "slowdown", "disinflation"),
            ("falling", "contraction", "disinflation"),
            ("high", "contraction", "recession"),
            ("deflationary", "slowdown", "deflationary_slowdown"),
        ]

        for inflation_signal, growth_signal, expected in test_cases:
            assessment = _make_test_assessment(
                inflation_signal=DetectionEvidence(
                    detector_name="inflation_detector",
                    signal=inflation_signal,
                    confidence=0.8,
                    algorithm_version="infl-det/v2.0.0",
                ),
                growth_signal=DetectionEvidence(
                    detector_name="growth_detector",
                    signal=growth_signal,
                    confidence=0.8,
                    algorithm_version="grw-det/v2.0.0",
                ),
            )
            classification = classifier.classify_macro_regime(assessment)
            assert classification.primary_regime.value == expected, (
                f"Failed for {inflation_signal}/{growth_signal}: "
                f"got {classification.primary_regime.value}, expected {expected}"
            )


# =============================================================================
# Classifier interface tests
# =============================================================================


class TestClassifierInterface:
    """Tests for RegimeClassifier interface."""

    def test_classifier_version(self):
        """Test classifier version."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assert classifier.version == "cls-rules/v3.0.0"

    def test_classifier_to_dict(self):
        """Test classifier metadata."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        meta = classifier.to_dict()

        assert meta["version"] == "cls-rules/v3.0.0"
        assert "growth_inflation" in meta["categories"]
        assert meta["total_rules"] > 0

    def test_get_rule_by_id(self):
        """Test getting a rule by ID."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()

        rule = classifier.get_rule_by_id("GI-010")
        assert rule is not None
        assert rule.rule_id == "GI-010"
        assert rule.result_regime == "goldilocks"

        missing = classifier.get_rule_by_id("NONEXISTENT")
        assert missing is None

    def test_get_all_rules(self):
        """Test getting all rules."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        rules = classifier.get_all_rules()

        assert len(rules) > 0
        for rule in rules:
            assert rule.rule_id
            assert rule.rule_version
            assert rule.conditions
            assert rule.result_regime


# =============================================================================
# Edge cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_all_neutral_signals(self):
        """Test classification with all neutral signals."""
        from macro_intelligence.regime.classification import RegimeClassifier
        from macro_intelligence.regime.detection.models import DetectionEvidence

        classifier = RegimeClassifier()
        assessment = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="stable",
                confidence=0.5,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="slowdown",
                confidence=0.5,
                algorithm_version="grw-det/v2.0.0",
            ),
            monetary_signal=DetectionEvidence(
                detector_name="monetary_detector",
                signal="neutral",
                confidence=0.5,
                algorithm_version="mon-det/v2.0.0",
            ),
            liquidity_signal=DetectionEvidence(
                detector_name="liquidity_detector",
                signal="neutral",
                confidence=0.5,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="normal",
                confidence=0.5,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="normal",
                confidence=0.5,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.5,
        )

        classification = classifier.classify_macro_regime(assessment)

        assert classification.primary_regime is not None
        assert 0 <= classification.confidence <= 1

    def test_mixed_confidence_levels(self):
        """Test classification with mixed confidence levels."""
        from macro_intelligence.regime.classification import RegimeClassifier
        from macro_intelligence.regime.detection.models import DetectionEvidence

        classifier = RegimeClassifier()
        assessment = _make_test_assessment(
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="high",
                confidence=0.95,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="contraction",
                confidence=0.9,
                algorithm_version="grw-det/v2.0.0",
            ),
            monetary_signal=DetectionEvidence(
                detector_name="monetary_detector",
                signal="hawkish",
                confidence=0.3,
                algorithm_version="mon-det/v2.0.0",
            ),
            liquidity_signal=DetectionEvidence(
                detector_name="liquidity_detector",
                signal="contracting",
                confidence=0.4,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="stressed",
                confidence=0.85,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="crisis",
                confidence=0.95,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.75,
        )

        classification = classifier.classify_macro_regime(assessment)

        assert classification.primary_regime.value == "recession"
        assert classification.confidence < 0.9

    def test_empty_classification_id(self):
        """Test that auto-generated classification ID is created."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classification = classifier.classify_macro_regime(assessment)

        assert classification.classification_id is not None
        assert len(classification.classification_id) > 0


# =============================================================================
# MIL-REG invariant tests
# =============================================================================


class TestMILClassificationInvariants:
    """Tests for MIL-REG invariants in classification."""

    def test_mil_reg_009_deterministic(self):
        """MIL-REG-009: Classification is deterministic."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classifications = [classifier.classify_macro_regime(assessment) for _ in range(20)]

        for c in classifications[1:]:
            assert c.primary_regime == classifications[0].primary_regime
            assert c.confidence == classifications[0].confidence
            assert c.evidence.signal_evidence == classifications[0].evidence.signal_evidence
            assert c.evidence.detector_provenance == classifications[0].evidence.detector_provenance

    def test_mil_reg_010_explainable_rules(self):
        """MIL-REG-010: Every classification has explainable rules."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classification = classifier.classify_macro_regime(assessment)

        assert classification.explanation is not None
        assert len(classification.explanation) > 0
        assert classification.rule_applied is not None

    def test_mil_reg_011_provenance_preserved(self):
        """MIL-REG-011: Classification preserves detector provenance."""
        from macro_intelligence.regime.classification import RegimeClassifier

        classifier = RegimeClassifier()
        assessment = _make_test_assessment()

        classification = classifier.classify_macro_regime(assessment)

        provenance = classification.evidence.detector_provenance
        assert len(provenance) == 6
        for detector in ["inflation", "growth", "monetary", "liquidity", "employment", "risk"]:
            assert detector in provenance
            assert "/v" in provenance[detector]

    def test_mil_reg_012_rules_versioned_immutable(self):
        """MIL-REG-012: Rules are versioned and immutable."""
        from macro_intelligence.regime.classification import ClassificationRule, RegimeClassifier

        classifier = RegimeClassifier()
        rules = classifier.get_all_rules()

        assert len(rules) > 0
        for rule in rules:
            assert rule.rule_version == "cls-rules/v3.0.0"
            # Verify immutability
            with pytest.raises(AttributeError):
                rule.rule_id = "MODIFIED"
