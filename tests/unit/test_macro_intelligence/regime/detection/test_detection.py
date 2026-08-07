"""
ResearchOS Macro Intelligence Layer - Regime Detection Tests
Tests for deterministic regime detection engine.
"""

import pytest
from datetime import datetime, timezone

UTC = timezone.utc


class TestFeatureVector:
    """Tests for FeatureVector model."""
    
    def test_create_empty_feature_vector(self):
        """Test creating an empty FeatureVector."""
        from macro_intelligence.regime.detection import FeatureVector
        
        fv = FeatureVector()
        assert fv.cpi_yoy is None
        assert fv.gdp_yoy is None
        assert fv.vix is None
    
    def test_create_feature_vector_with_data(self):
        """Test creating a FeatureVector with data."""
        from macro_intelligence.regime.detection import FeatureVector
        
        fv = FeatureVector(
            cpi_yoy=3.2,
            cpi_core_yoy=3.8,
            gdp_yoy=2.5,
            vix=18.0,
            fed_rate=5.25,
        )
        
        assert fv.cpi_yoy == 3.2
        assert fv.gdp_yoy == 2.5
        assert fv.vix == 18.0
        assert fv.fed_rate == 5.25
    
    def test_feature_vector_immutability(self):
        """Test that FeatureVector is immutable."""
        from macro_intelligence.regime.detection import FeatureVector
        
        fv = FeatureVector(cpi_yoy=3.0)
        
        with pytest.raises(AttributeError):
            fv.cpi_yoy = 4.0
    
    def test_feature_vector_to_dict(self):
        """Test FeatureVector serialization."""
        from macro_intelligence.regime.detection import FeatureVector
        
        fv = FeatureVector(cpi_yoy=3.2, gdp_yoy=2.5)
        data = fv.to_dict()
        
        assert data["cpi_yoy"] == 3.2
        assert data["gdp_yoy"] == 2.5
        assert data["vix"] is None
    
    def test_feature_vector_from_dict(self):
        """Test FeatureVector deserialization."""
        from macro_intelligence.regime.detection import FeatureVector
        
        data = {"cpi_yoy": 3.2, "gdp_yoy": 2.5, "vix": 18.0}
        fv = FeatureVector.from_dict(data)
        
        assert fv.cpi_yoy == 3.2
        assert fv.gdp_yoy == 2.5
        assert fv.vix == 18.0
    
    def test_feature_vector_roundtrip(self):
        """Test FeatureVector serialization roundtrip."""
        from macro_intelligence.regime.detection import FeatureVector
        
        original = FeatureVector(
            cpi_yoy=3.2,
            cpi_core_yoy=3.8,
            gdp_yoy=2.5,
            pmi_mfg=52.0,
            vix=18.0,
            fed_rate=5.25,
        )
        
        json_str = original.to_json()
        restored = FeatureVector.from_json(json_str)
        
        assert restored.cpi_yoy == original.cpi_yoy
        assert restored.gdp_yoy == original.gdp_yoy
        assert restored.vix == original.vix
    
    def test_feature_vector_hash_deterministic(self):
        """Test that FeatureVector hash is deterministic."""
        from macro_intelligence.regime.detection import FeatureVector
        
        fv1 = FeatureVector(cpi_yoy=3.2, gdp_yoy=2.5)
        fv2 = FeatureVector(cpi_yoy=3.2, gdp_yoy=2.5)
        
        assert fv1.compute_hash() == fv2.compute_hash()
    
    def test_feature_vector_different_data_different_hash(self):
        """Test that different data produces different hashes."""
        from macro_intelligence.regime.detection import FeatureVector
        
        fv1 = FeatureVector(cpi_yoy=3.2)
        fv2 = FeatureVector(cpi_yoy=4.0)
        
        assert fv1.compute_hash() != fv2.compute_hash()


class TestDetectionEvidence:
    """Tests for DetectionEvidence model."""
    
    def test_create_evidence(self):
        """Test creating DetectionEvidence."""
        from macro_intelligence.regime.detection import DetectionEvidence
        
        evidence = DetectionEvidence(
            detector_name="inflation_detector",
            signal="stable",
            confidence=0.85,
            contributing_factors={"cpi": 2.1},
            algorithm_version="infl-det/v2.0.0",
        )
        
        assert evidence.detector_name == "inflation_detector"
        assert evidence.signal == "stable"
        assert evidence.confidence == 0.85
    
    def test_evidence_to_dict(self):
        """Test DetectionEvidence serialization."""
        from macro_intelligence.regime.detection import DetectionEvidence
        
        evidence = DetectionEvidence(
            detector_name="growth_detector",
            signal="expansion",
            confidence=0.9,
            algorithm_version="grw-det/v2.0.0",
        )
        
        data = evidence.to_dict()
        assert data["signal"] == "expansion"
        assert data["confidence"] == 0.9
        assert data["algorithm_version"] == "grw-det/v2.0.0"
    
    def test_evidence_from_dict(self):
        """Test DetectionEvidence deserialization."""
        from macro_intelligence.regime.detection import DetectionEvidence
        
        data = {
            "detector_name": "risk_detector",
            "signal": "normal",
            "confidence": 0.75,
            "algorithm_version": "risk-det/v2.0.0",
        }
        
        evidence = DetectionEvidence.from_dict(data)
        assert evidence.detector_name == "risk_detector"
        assert evidence.signal == "normal"
    
    def test_evidence_roundtrip(self):
        """Test DetectionEvidence serialization roundtrip."""
        from macro_intelligence.regime.detection import DetectionEvidence
        
        original = DetectionEvidence(
            detector_name="monetary_detector",
            signal="hawkish",
            confidence=0.8,
            contributing_factors={"fed_rate": 5.25},
            algorithm_version="mon-det/v2.0.0",
        )
        
        data = original.to_dict()
        restored = DetectionEvidence.from_dict(data)
        
        assert restored.signal == original.signal
        assert restored.confidence == original.confidence
    
    def test_evidence_hash_deterministic(self):
        """Test DetectionEvidence hash determinism."""
        from macro_intelligence.regime.detection import DetectionEvidence
        
        e1 = DetectionEvidence(
            detector_name="inflation_detector",
            signal="stable",
            confidence=0.85,
            algorithm_version="infl-det/v2.0.0",
        )
        e2 = DetectionEvidence(
            detector_name="inflation_detector",
            signal="stable",
            confidence=0.85,
            algorithm_version="infl-det/v2.0.0",
        )
        
        assert e1.compute_hash() == e2.compute_hash()


class TestInflationDetector:
    """Tests for inflation detector."""
    
    def test_detect_stable_inflation(self):
        """Test inflation detection in stable range."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(cpi_core_yoy=2.1, inflation_trend="NEUTRAL")
        
        evidence = detector.detect_inflation(features)
        
        assert evidence.signal in ("stable", "rising", "falling")
        assert 0.0 <= evidence.confidence <= 1.0
        assert evidence.algorithm_version == "infl-det/v2.0.0"
    
    def test_detect_high_inflation(self):
        """Test inflation detection in high range."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(cpi_core_yoy=5.5, inflation_trend="UPWARD")
        
        evidence = detector.detect_inflation(features)
        
        assert evidence.signal == "high"
        assert evidence.confidence > 0.5
    
    def test_detect_low_inflation(self):
        """Test inflation detection in low range."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(cpi_core_yoy=1.0, inflation_trend="NEUTRAL")
        
        evidence = detector.detect_inflation(features)
        
        assert evidence.signal == "low"
    
    def test_detect_deflationary(self):
        """Test inflation detection in deflationary range."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(cpi_core_yoy=-0.8, inflation_trend="DOWNWARD")
        
        evidence = detector.detect_inflation(features)
        
        assert evidence.signal == "deflationary"
    
    def test_detect_rising_inflation(self):
        """Test inflation detection with upward trend."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.0,
            inflation_trend="UPWARD",
            inflation_momentum=0.5,
        )
        
        evidence = detector.detect_inflation(features)
        
        assert evidence.signal == "rising"
    
    def test_detect_falling_inflation(self):
        """Test inflation detection with downward trend."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=2.5,
            inflation_trend="DOWNWARD",
            inflation_momentum=-0.5,
        )
        
        evidence = detector.detect_inflation(features)
        
        assert evidence.signal == "falling"
    
    def test_detect_no_data(self):
        """Test inflation detection with no data."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector()
        
        evidence = detector.detect_inflation(features)
        
        assert evidence.signal == "stable"
        assert evidence.confidence == 0.0
    
    def test_detect_with_z_score(self):
        """Test inflation detection with z-score."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.0,
            inflation_z_score=1.8,
            inflation_percentile=75,
        )
        
        evidence = detector.detect_inflation(features)
        
        assert "z_score" in evidence.contributing_factors
    
    def test_detect_deterministic(self):
        """Test that inflation detection is deterministic."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(cpi_core_yoy=3.2, inflation_trend="NEUTRAL")
        
        evidence1 = detector.detect_inflation(features)
        evidence2 = detector.detect_inflation(features)
        
        assert evidence1.signal == evidence2.signal
        assert evidence1.confidence == evidence2.confidence
        assert evidence1.compute_hash() == evidence2.compute_hash()
    
    def test_detect_no_mutation(self):
        """Test that detection does not mutate input features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.2,
            inflation_trend="NEUTRAL",
            cpi_yoy=3.0,
        )
        original = features.to_dict()
        
        detector.detect_inflation(features)
        
        assert features.to_dict() == original


class TestGrowthDetector:
    """Tests for growth detector."""
    
    def test_detect_expansion(self):
        """Test growth detection in expansion."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(gdp_yoy=3.0, pmi_mfg=55.0, pmi_svc=53.0)
        
        evidence = detector.detect_growth(features)
        
        assert evidence.signal in ("expansion", "recovery")
    
    def test_detect_contraction(self):
        """Test growth detection in contraction."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(gdp_yoy=-1.0, pmi_mfg=45.0)
        
        evidence = detector.detect_growth(features)
        
        assert evidence.signal == "contraction"
    
    def test_detect_slowdown(self):
        """Test growth detection in slowdown."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(gdp_yoy=1.5, pmi_mfg=50.0)
        
        evidence = detector.detect_growth(features)
        
        assert evidence.signal == "slowdown"
    
    def test_detect_recovery(self):
        """Test growth detection in recovery."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(gdp_yoy=3.5, growth_momentum=1.0)
        
        evidence = detector.detect_growth(features)
        
        assert evidence.signal == "recovery"
    
    def test_detect_no_data(self):
        """Test growth detection with no data."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector()
        
        evidence = detector.detect_growth(features)
        
        assert evidence.signal == "slowdown"
        assert evidence.confidence == 0.0
    
    def test_detect_deterministic(self):
        """Test growth detection determinism."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(gdp_yoy=2.5, pmi_mfg=52.0)
        
        evidence1 = detector.detect_growth(features)
        evidence2 = detector.detect_growth(features)
        
        assert evidence1.signal == evidence2.signal
        assert evidence1.confidence == evidence2.confidence
    
    def test_detect_no_mutation(self):
        """Test growth detection does not mutate features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(gdp_yoy=2.5, pmi_mfg=52.0)
        original = features.to_dict()
        
        detector.detect_growth(features)
        
        assert features.to_dict() == original


class TestMonetaryDetector:
    """Tests for monetary detector."""
    
    def test_detect_hawkish(self):
        """Test monetary detection in hawkish regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            fed_rate=5.25,
            fed_policy_direction="TIGHTENING",
            real_yield_10y=2.5,
        )
        
        evidence = detector.detect_monetary(features)
        
        assert evidence.signal == "hawkish"
    
    def test_detect_dovish(self):
        """Test monetary detection in dovish regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            fed_rate=0.25,
            fed_policy_direction="EASING",
            real_yield_10y=-0.8,
        )
        
        evidence = detector.detect_monetary(features)
        
        assert evidence.signal == "dovish"
    
    def test_detect_neutral(self):
        """Test monetary detection in neutral regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            fed_rate=3.5,
            fed_policy_direction="HOLD",
            real_yield_10y=1.5,
        )
        
        evidence = detector.detect_monetary(features)
        
        assert evidence.signal == "neutral"
    
    def test_detect_no_data(self):
        """Test monetary detection with no data."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector()
        
        evidence = detector.detect_monetary(features)
        
        assert evidence.signal == "neutral"
        assert evidence.confidence == 0.0
    
    def test_detect_deterministic(self):
        """Test monetary detection determinism."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(fed_rate=5.25, fed_policy_direction="TIGHTENING")
        
        evidence1 = detector.detect_monetary(features)
        evidence2 = detector.detect_monetary(features)
        
        assert evidence1.signal == evidence2.signal
        assert evidence1.confidence == evidence2.confidence
    
    def test_detect_no_mutation(self):
        """Test monetary detection does not mutate features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(fed_rate=5.25, fed_policy_direction="TIGHTENING")
        original = features.to_dict()
        
        detector.detect_monetary(features)
        
        assert features.to_dict() == original


class TestLiquidityDetector:
    """Tests for liquidity detector."""
    
    def test_detect_expanding(self):
        """Test liquidity detection in expanding regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            high_yield_spread=0.3,
            dxy=93.0,
            liquidity_index=0.5,
        )
        
        evidence = detector.detect_liquidity(features)
        
        assert evidence.signal == "expanding"
    
    def test_detect_contracting(self):
        """Test liquidity detection in contracting regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            high_yield_spread=2.0,
            dxy=110.0,
            liquidity_index=-0.5,
        )
        
        evidence = detector.detect_liquidity(features)
        
        assert evidence.signal == "contracting"
    
    def test_detect_neutral(self):
        """Test liquidity detection in neutral regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            high_yield_spread=0.8,
            dxy=100.0,
            liquidity_index=0.0,
        )
        
        evidence = detector.detect_liquidity(features)
        
        assert evidence.signal == "neutral"
    
    def test_detect_no_data(self):
        """Test liquidity detection with no data."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector()
        
        evidence = detector.detect_liquidity(features)
        
        assert evidence.signal == "neutral"
        assert evidence.confidence == 0.0
    
    def test_detect_deterministic(self):
        """Test liquidity detection determinism."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(high_yield_spread=0.5, dxy=100.0)
        
        evidence1 = detector.detect_liquidity(features)
        evidence2 = detector.detect_liquidity(features)
        
        assert evidence1.signal == evidence2.signal
        assert evidence1.confidence == evidence2.confidence
    
    def test_detect_no_mutation(self):
        """Test liquidity detection does not mutate features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(high_yield_spread=0.5, dxy=100.0)
        original = features.to_dict()
        
        detector.detect_liquidity(features)
        
        assert features.to_dict() == original


class TestEmploymentDetector:
    """Tests for employment detector."""
    
    def test_detect_strong(self):
        """Test employment detection in strong regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            nfp_change=250.0,
            unemployment_rate=3.5,
            jolts_total=11000,
        )
        
        evidence = detector.detect_employment(features)
        
        assert evidence.signal == "strong"
    
    def test_detect_stressed(self):
        """Test employment detection in stressed regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            nfp_change=10.0,
            unemployment_rate=7.0,
            jolts_total=6000,
        )
        
        evidence = detector.detect_employment(features)
        
        assert evidence.signal == "stressed"
    
    def test_detect_weakening(self):
        """Test employment detection in weakening regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            nfp_change=50.0,
            unemployment_rate=5.5,
        )
        
        evidence = detector.detect_employment(features)
        
        assert evidence.signal == "weakening"
    
    def test_detect_normal(self):
        """Test employment detection in normal regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            nfp_change=100.0,
            unemployment_rate=4.5,
            jolts_total=8500,
        )
        
        evidence = detector.detect_employment(features)
        
        assert evidence.signal in ("normal", "strong")
    
    def test_detect_no_data(self):
        """Test employment detection with no data."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector()
        
        evidence = detector.detect_employment(features)
        
        assert evidence.signal == "normal"
        assert evidence.confidence == 0.0
    
    def test_detect_deterministic(self):
        """Test employment detection determinism."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(nfp_change=150.0, unemployment_rate=4.2)
        
        evidence1 = detector.detect_employment(features)
        evidence2 = detector.detect_employment(features)
        
        assert evidence1.signal == evidence2.signal
        assert evidence1.confidence == evidence2.confidence
    
    def test_detect_no_mutation(self):
        """Test employment detection does not mutate features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(nfp_change=150.0, unemployment_rate=4.2)
        original = features.to_dict()
        
        detector.detect_employment(features)
        
        assert features.to_dict() == original


class TestRiskDetector:
    """Tests for risk detector."""
    
    def test_detect_risk_on(self):
        """Test risk detection in risk-on regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            vix=12.0,
            move_index=70.0,
            market_volatility_20d=0.10,
        )
        
        evidence = detector.detect_risk(features)
        
        assert evidence.signal == "risk_on"
    
    def test_detect_risk_off(self):
        """Test risk detection in risk-off regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            vix=35.0,
            move_index=150.0,
            market_volatility_20d=0.25,
        )
        
        evidence = detector.detect_risk(features)
        
        assert evidence.signal == "risk_off"
    
    def test_detect_crisis(self):
        """Test risk detection in crisis regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            vix=45.0,
            move_index=250.0,
            market_volatility_20d=0.35,
        )
        
        evidence = detector.detect_risk(features)
        
        assert evidence.signal == "crisis"
    
    def test_detect_normal(self):
        """Test risk detection in normal regime."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            vix=20.0,
            move_index=100.0,
            market_volatility_20d=0.15,
        )
        
        evidence = detector.detect_risk(features)
        
        assert evidence.signal == "normal"
    
    def test_detect_no_data(self):
        """Test risk detection with no data."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector()
        
        evidence = detector.detect_risk(features)
        
        assert evidence.signal == "normal"
        assert evidence.confidence == 0.0
    
    def test_detect_deterministic(self):
        """Test risk detection determinism."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(vix=20.0, move_index=100.0)
        
        evidence1 = detector.detect_risk(features)
        evidence2 = detector.detect_risk(features)
        
        assert evidence1.signal == evidence2.signal
        assert evidence1.confidence == evidence2.confidence
    
    def test_detect_no_mutation(self):
        """Test risk detection does not mutate features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(vix=20.0, move_index=100.0)
        original = features.to_dict()
        
        detector.detect_risk(features)
        
        assert features.to_dict() == original


class TestRegimeAssessment:
    """Tests for RegimeAssessment model."""
    
    def test_create_assessment(self):
        """Test creating a RegimeAssessment."""
        from macro_intelligence.regime.detection import (
            RegimeAssessment, DetectionEvidence,
        )
        
        assessment = RegimeAssessment(
            assessment_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            algorithm_version="det-orch/v2.0.0",
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="stable",
                confidence=0.8,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="expansion",
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
                signal="expanding",
                confidence=0.7,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="strong",
                confidence=0.9,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="normal",
                confidence=0.6,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.78,
            dominant_regime="expansion",
            regime_description="growth expansion and risk normal",
        )
        
        assert assessment.dominant_regime == "expansion"
        assert assessment.overall_confidence == 0.78
    
    def test_assessment_to_dict(self):
        """Test RegimeAssessment serialization."""
        from macro_intelligence.regime.detection import (
            RegimeAssessment, DetectionEvidence,
        )
        
        assessment = RegimeAssessment(
            assessment_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            algorithm_version="det-orch/v2.0.0",
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="stable",
                confidence=0.8,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="expansion",
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
                signal="expanding",
                confidence=0.7,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="strong",
                confidence=0.9,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="normal",
                confidence=0.6,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.78,
        )
        
        data = assessment.to_dict()
        assert data["algorithm_version"] == "det-orch/v2.0.0"
        assert data["overall_confidence"] == 0.78
        assert data["inflation"]["signal"] == "stable"
    
    def test_assessment_from_dict(self):
        """Test RegimeAssessment deserialization."""
        from macro_intelligence.regime.detection import RegimeAssessment
        
        data = {
            "assessment_time": "2026-08-03T12:00:00+00:00",
            "algorithm_version": "det-orch/v2.0.0",
            "inflation": {
                "detector_name": "inflation_detector",
                "signal": "stable",
                "confidence": 0.8,
                "algorithm_version": "infl-det/v2.0.0",
            },
            "growth": {
                "detector_name": "growth_detector",
                "signal": "expansion",
                "confidence": 0.75,
                "algorithm_version": "grw-det/v2.0.0",
            },
            "monetary": {
                "detector_name": "monetary_detector",
                "signal": "hawkish",
                "confidence": 0.85,
                "algorithm_version": "mon-det/v2.0.0",
            },
            "liquidity": {
                "detector_name": "liquidity_detector",
                "signal": "expanding",
                "confidence": 0.7,
                "algorithm_version": "liq-det/v2.0.0",
            },
            "employment": {
                "detector_name": "employment_detector",
                "signal": "strong",
                "confidence": 0.9,
                "algorithm_version": "emp-det/v2.0.0",
            },
            "risk": {
                "detector_name": "risk_detector",
                "signal": "normal",
                "confidence": 0.6,
                "algorithm_version": "risk-det/v2.0.0",
            },
            "overall_confidence": 0.78,
            "dominant_regime": "expansion",
            "regime_description": "Test regime",
        }
        
        assessment = RegimeAssessment.from_dict(data)
        assert assessment.dominant_regime == "expansion"
        assert assessment.inflation_signal.signal == "stable"
    
    def test_assessment_roundtrip(self):
        """Test RegimeAssessment serialization roundtrip."""
        from macro_intelligence.regime.detection import (
            RegimeAssessment, DetectionEvidence,
        )
        
        assessment = RegimeAssessment(
            assessment_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            algorithm_version="det-orch/v2.0.0",
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="stable",
                confidence=0.8,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="expansion",
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
                signal="expanding",
                confidence=0.7,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="strong",
                confidence=0.9,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="normal",
                confidence=0.6,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.78,
        )
        
        json_str = assessment.to_json()
        restored = RegimeAssessment.from_json(json_str)
        
        assert restored.dominant_regime == assessment.dominant_regime
        assert restored.overall_confidence == assessment.overall_confidence
        assert restored.inflation_signal.signal == assessment.inflation_signal.signal
    
    def test_assessment_hash_deterministic(self):
        """Test RegimeAssessment hash determinism."""
        from macro_intelligence.regime.detection import (
            RegimeAssessment, DetectionEvidence,
        )
        
        assessment1 = RegimeAssessment(
            assessment_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            algorithm_version="det-orch/v2.0.0",
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="stable",
                confidence=0.8,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="expansion",
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
                signal="expanding",
                confidence=0.7,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="strong",
                confidence=0.9,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="normal",
                confidence=0.6,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.78,
        )
        
        assessment2 = RegimeAssessment(
            assessment_time=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            algorithm_version="det-orch/v2.0.0",
            inflation_signal=DetectionEvidence(
                detector_name="inflation_detector",
                signal="stable",
                confidence=0.8,
                algorithm_version="infl-det/v2.0.0",
            ),
            growth_signal=DetectionEvidence(
                detector_name="growth_detector",
                signal="expansion",
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
                signal="expanding",
                confidence=0.7,
                algorithm_version="liq-det/v2.0.0",
            ),
            employment_signal=DetectionEvidence(
                detector_name="employment_detector",
                signal="strong",
                confidence=0.9,
                algorithm_version="emp-det/v2.0.0",
            ),
            risk_signal=DetectionEvidence(
                detector_name="risk_detector",
                signal="normal",
                confidence=0.6,
                algorithm_version="risk-det/v2.0.0",
            ),
            overall_confidence=0.78,
        )
        
        assert assessment1.compute_hash() == assessment2.compute_hash()


class TestRegimeDetectorOrchestrator:
    """Tests for the RegimeDetector orchestrator."""
    
    def test_detector_version(self):
        """Test detector version."""
        from macro_intelligence.regime.detection import RegimeDetector
        
        detector = RegimeDetector()
        assert detector.version == "det-orch/v2.0.0"
    
    def test_detector_to_dict(self):
        """Test detector metadata."""
        from macro_intelligence.regime.detection import RegimeDetector
        
        detector = RegimeDetector()
        meta = detector.to_dict()
        
        assert meta["version"] == "det-orch/v2.0.0"
        assert len(meta["detectors"]) == 6
    
    def test_detect_all_empty(self):
        """Test detect_all with empty features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector()
        
        assessment = detector.detect_all(features)
        
        assert assessment.algorithm_version == "det-orch/v2.0.0"
        assert assessment.overall_confidence == 0.0
        assert assessment.dominant_regime is not None  # Returns default regime
        assert assessment.inflation_signal.detector_name == "inflation_detector"
    
    def test_detect_all_full(self):
        """Test detect_all with full feature vector."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.2,
            gdp_yoy=2.5,
            fed_rate=5.25,
            fed_policy_direction="TIGHTENING",
            high_yield_spread=0.5,
            nfp_change=150.0,
            vix=18.0,
        )
        
        assessment = detector.detect_all(features)
        
        assert assessment.algorithm_version == "det-orch/v2.0.0"
        assert assessment.overall_confidence > 0.0
        assert assessment.inflation_signal.detector_name == "inflation_detector"
        assert assessment.growth_signal.detector_name == "growth_detector"
        assert assessment.monetary_signal.detector_name == "monetary_detector"
        assert assessment.liquidity_signal.detector_name == "liquidity_detector"
        assert assessment.employment_signal.detector_name == "employment_detector"
        assert assessment.risk_signal.detector_name == "risk_detector"
    
    def test_detect_all_deterministic(self):
        """Test detect_all determinism."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.2,
            gdp_yoy=2.5,
            fed_rate=5.25,
            vix=18.0,
        )
        
        assessment1 = detector.detect_all(features)
        assessment2 = detector.detect_all(features)
        
        assert assessment1.dominant_regime == assessment2.dominant_regime
        assert assessment1.overall_confidence == assessment2.overall_confidence
        assert assessment1.inflation_signal.signal == assessment2.inflation_signal.signal
        assert assessment1.growth_signal.signal == assessment2.growth_signal.signal
        assert assessment1.monetary_signal.signal == assessment2.monetary_signal.signal
        assert assessment1.liquidity_signal.signal == assessment2.liquidity_signal.signal
        assert assessment1.employment_signal.signal == assessment2.employment_signal.signal
        assert assessment1.risk_signal.signal == assessment2.risk_signal.signal
    
    def test_detect_all_no_mutation(self):
        """Test detect_all does not mutate features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.2,
            gdp_yoy=2.5,
            fed_rate=5.25,
            vix=18.0,
        )
        original = features.to_dict()
        
        detector.detect_all(features)
        
        assert features.to_dict() == original
    
    def test_detect_all_all_signals_present(self):
        """Test that all detector signals are present in assessment."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=2.1,
            gdp_yoy=2.5,
            fed_rate=3.5,
            fed_policy_direction="HOLD",
            high_yield_spread=0.6,
            nfp_change=150.0,
            unemployment_rate=4.0,
            vix=20.0,
        )
        
        assessment = detector.detect_all(features)
        
        # All signals should be set
        assert assessment.inflation_signal.signal is not None
        assert assessment.growth_signal.signal is not None
        assert assessment.monetary_signal.signal is not None
        assert assessment.liquidity_signal.signal is not None
        assert assessment.employment_signal.signal is not None
        assert assessment.risk_signal.signal is not None
        
        # All evidence refs should be lists
        assert isinstance(assessment.inflation_signal.evidence_refs, list)
        assert isinstance(assessment.growth_signal.evidence_refs, list)


class TestProvenancePreservation:
    """Tests for MIL-REG-006: Provenance preservation."""
    
    def test_detection_evidence_preserves_detector_name(self):
        """Test that evidence preserves detector identification."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(cpi_core_yoy=3.2)
        
        evidence = detector.detect_inflation(features)
        assert evidence.detector_name == "inflation_detector"
    
    def test_all_evidence_preserves_algorithm_version(self):
        """Test that all evidence preserves algorithm versions."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.2,
            gdp_yoy=2.5,
            fed_rate=5.25,
            high_yield_spread=0.5,
            nfp_change=150.0,
            vix=18.0,
        )
        
        inflation = detector.detect_inflation(features)
        growth = detector.detect_growth(features)
        monetary = detector.detect_monetary(features)
        liquidity = detector.detect_liquidity(features)
        employment = detector.detect_employment(features)
        risk = detector.detect_risk(features)
        
        assert inflation.algorithm_version == "infl-det/v2.0.0"
        assert growth.algorithm_version == "grw-det/v2.0.0"
        assert monetary.algorithm_version == "mon-det/v2.0.0"
        assert liquidity.algorithm_version == "liq-det/v2.0.0"
        assert employment.algorithm_version == "emp-det/v2.0.0"
        assert risk.algorithm_version == "risk-det/v2.0.0"
    
    def test_regime_assessment_preserves_all_evidence(self):
        """Test that assessment preserves all detection evidence."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.2,
            gdp_yoy=2.5,
        )
        
        assessment = detector.detect_all(features)
        
        assert assessment.inflation_signal.detector_name == "inflation_detector"
        assert assessment.growth_signal.detector_name == "growth_detector"


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_all_none_features(self):
        """Test with all None features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector()
        
        assessment = detector.detect_all(features)
        
        assert assessment.overall_confidence == 0.0
        # dominant_regime will be set to default when no data
    
    def test_single_data_point(self):
        """Test with minimal data."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(cpi_yoy=3.0)
        
        evidence = detector.detect_inflation(features)
        assert evidence.signal is not None
    
    def test_boundary_values_inflation(self):
        """Test boundary values for inflation detection."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        
        # Just below deflation threshold
        features1 = FeatureVector(cpi_core_yoy=-0.4)
        evidence1 = detector.detect_inflation(features1)
        
        # Just at deflation threshold
        features2 = FeatureVector(cpi_core_yoy=-0.5)
        evidence2 = detector.detect_inflation(features2)
        
        assert evidence1.signal != evidence2.signal or evidence1.signal == "deflationary"
    
    def test_boundary_values_growth(self):
        """Test boundary values for growth detection."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        
        # Just below contraction
        features1 = FeatureVector(gdp_yoy=0.1)
        evidence1 = detector.detect_growth(features1)
        
        # Just at contraction
        features2 = FeatureVector(gdp_yoy=-0.1)
        evidence2 = detector.detect_growth(features2)
        
        assert evidence1.signal != evidence2.signal
    
    def test_extreme_values(self):
        """Test with extreme values."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        
        # Extreme inflation
        features = FeatureVector(cpi_core_yoy=25.0)
        evidence = detector.detect_inflation(features)
        assert evidence.signal == "high"
        
        # Extreme risk
        features2 = FeatureVector(vix=80.0)
        evidence2 = detector.detect_risk(features2)
        assert evidence2.signal == "crisis"


class TestMILRegimeInvariants:
    """Tests for MIL-REG invariants."""
    
    def test_mil_reg_005_deterministic(self):
        """MIL-REG-005: Detectors are deterministic."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.2,
            gdp_yoy=2.5,
            fed_rate=5.25,
            high_yield_spread=0.5,
            nfp_change=150.0,
            vix=18.0,
        )
        
        # Run multiple times
        assessments = [detector.detect_all(features) for _ in range(10)]
        
        # All should produce identical signals
        for assessment in assessments[1:]:
            assert assessment.inflation_signal.signal == assessments[0].inflation_signal.signal
            assert assessment.growth_signal.signal == assessments[0].growth_signal.signal
            assert assessment.monetary_signal.signal == assessments[0].monetary_signal.signal
            assert assessment.liquidity_signal.signal == assessments[0].liquidity_signal.signal
            assert assessment.employment_signal.signal == assessments[0].employment_signal.signal
            assert assessment.risk_signal.signal == assessments[0].risk_signal.signal
            assert assessment.overall_confidence == assessments[0].overall_confidence
    
    def test_mil_reg_006_provenance(self):
        """MIL-REG-006: Detector output preserves evidence provenance."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(cpi_core_yoy=3.2)
        
        evidence = detector.detect_inflation(features)
        
        assert evidence.detector_name == "inflation_detector"
        assert evidence.algorithm_version == "infl-det/v2.0.0"
        assert evidence.signal is not None
    
    def test_mil_reg_007_no_mutation(self):
        """MIL-REG-007: Detector logic does not mutate features."""
        from macro_intelligence.regime.detection import RegimeDetector, FeatureVector
        
        detector = RegimeDetector()
        features = FeatureVector(
            cpi_core_yoy=3.2,
            cpi_yoy=3.0,
            gdp_yoy=2.5,
            fed_rate=5.25,
        )
        original_dict = features.to_dict()
        original_hash = features.compute_hash()
        
        detector.detect_all(features)
        
        # Features should be unchanged
        assert features.to_dict() == original_dict
        assert features.compute_hash() == original_hash
    
    def test_mil_reg_008_algorithm_versions_permanent(self):
        """MIL-REG-008: Algorithm versions are permanent."""
        from macro_intelligence.regime.detection import (
            RegimeDetector, FeatureVector,
            detect_inflation, detect_growth,
            detect_monetary, detect_liquidity,
            detect_employment, detect_risk,
        )
        
        assert detect_inflation(FeatureVector()).algorithm_version == "infl-det/v2.0.0"
        assert detect_growth(FeatureVector()).algorithm_version == "grw-det/v2.0.0"
        assert detect_monetary(FeatureVector()).algorithm_version == "mon-det/v2.0.0"
        assert detect_liquidity(FeatureVector()).algorithm_version == "liq-det/v2.0.0"
        assert detect_employment(FeatureVector()).algorithm_version == "emp-det/v2.0.0"
        assert detect_risk(FeatureVector()).algorithm_version == "risk-det/v2.0.0"
        
        detector = RegimeDetector()
        assert detector.version == "det-orch/v2.0.0"
