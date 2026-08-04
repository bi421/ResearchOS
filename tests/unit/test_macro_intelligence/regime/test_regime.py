"""
ResearchOS Macro Intelligence Layer - Regime Tests
"""

import pytest
from datetime import datetime, timezone

UTC = timezone.utc


class TestRegimeEnums:
    """Tests for regime enums."""
    
    def test_inflation_states(self):
        """Test inflation states."""
        from macro_intelligence.regime.enums import InflationState
        
        assert InflationState.LOW.is_stable() is True
        assert InflationState.HYPER.is_extreme() is True
        assert InflationState.TARGET.get_severity() == 0
    
    def test_growth_states(self):
        """Test growth states."""
        from macro_intelligence.regime.enums import GrowthState
        
        assert GrowthState.EXPANSION.is_expansionary() is True
        assert GrowthState.RECESSION.is_contractionary() is True
        assert GrowthState.DEPRESSION.get_severity() == 10
    
    def test_monetary_states(self):
        """Test monetary states."""
        from macro_intelligence.regime.enums import MonetaryState
        
        assert MonetaryState.DIVE.is_dovish() is True
        assert MonetaryState.HAWK.is_hawkish() is True
        assert MonetaryState.NEUTRAL.is_neutral() is True
    
    def test_liquidity_states(self):
        """Test liquidity states."""
        from macro_intelligence.regime.enums import LiquidityState
        
        assert LiquidityState.ABUNDANT.is_abundant() is True
        assert LiquidityState.CRITICAL.is_constrained() is True
        assert LiquidityState.TIGHT.get_severity() == 5
    
    def test_employment_states(self):
        """Test employment states."""
        from macro_intelligence.regime.enums import EmploymentState
        
        assert EmploymentState.FULL.is_healthy() is True
        assert EmploymentState.CRISS.is_stressed() is True
    
    def test_risk_states(self):
        """Test risk states."""
        from macro_intelligence.regime.enums import RiskState
        
        assert RiskState.LOW.is_acceptable() is True
        assert RiskState.CRITICAL.is_critical() is True
        assert RiskState.ELEVATED.is_warning() is True
    
    def test_regime_severity(self):
        """Test regime severity."""
        from macro_intelligence.regime.enums import RegimeSeverity
        
        assert RegimeSeverity.NORMAL.get_score() == 0
        assert RegimeSeverity.CRITICAL.get_score() == 10
        assert RegimeSeverity.WARNING.is_serious() is True
    
    def test_regime_transition_type(self):
        """Test regime transition types."""
        from macro_intelligence.regime.enums import RegimeTransitionType
        
        assert RegimeTransitionType.ABRUPT.is_sudden() is True
        assert RegimeTransitionType.GRADUAL.is_sudden() is False


class TestRegimeContracts:
    """Tests for regime contracts."""
    
    def test_regime_confidence_creation(self):
        """Test creating regime confidence."""
        from macro_intelligence.regime.contracts import RegimeConfidence
        
        confidence = RegimeConfidence(
            level=0.85,
            evidence_count=10,
            data_quality=0.9,
            model_version="v1.0.0",
            calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )
        
        assert confidence.level == 0.85
        assert confidence.evidence_count == 10
    
    def test_regime_confidence_immutability(self):
        """Test regime confidence immutability."""
        from macro_intelligence.regime.contracts import RegimeConfidence
        
        confidence = RegimeConfidence(
            level=0.85,
            evidence_count=10,
            data_quality=0.9,
            model_version="v1.0.0",
            calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )
        
        with pytest.raises(AttributeError):
            confidence.level = 0.9
    
    def test_regime_confidence_json_roundtrip(self):
        """Test regime confidence JSON roundtrip."""
        from macro_intelligence.regime.contracts import RegimeConfidence
        
        original = RegimeConfidence(
            level=0.85,
            evidence_count=10,
            data_quality=0.9,
            model_version="v1.0.0",
            calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )
        
        json_str = original.to_json()
        restored = RegimeConfidence.from_json(json_str)
        
        assert restored.level == original.level
        assert restored.to_json() == json_str
    
    def test_regime_confidence_hash_deterministic(self):
        """Test regime confidence hash determinism."""
        from macro_intelligence.regime.contracts import RegimeConfidence
        
        conf1 = RegimeConfidence(
            level=0.85,
            evidence_count=10,
            data_quality=0.9,
            model_version="v1.0.0",
            calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )
        
        conf2 = RegimeConfidence(
            level=0.85,
            evidence_count=10,
            data_quality=0.9,
            model_version="v1.0.0",
            calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
        )
        
        assert conf1.compute_hash() == conf2.compute_hash()
    
    def test_regime_evidence_creation(self):
        """Test creating regime evidence."""
        from macro_intelligence.regime.contracts import RegimeEvidence
        
        evidence = RegimeEvidence(
            evidence_id="EVD_001",
            source="FRED",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            contribution=0.3,
            weight=0.5,
        )
        
        assert evidence.evidence_id == "EVD_001"
        assert evidence.value == 4.25
    
    def test_regime_evidence_immutability(self):
        """Test regime evidence immutability."""
        from macro_intelligence.regime.contracts import RegimeEvidence
        
        evidence = RegimeEvidence(
            evidence_id="EVD_001",
            source="FRED",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            contribution=0.3,
            weight=0.5,
        )
        
        with pytest.raises(AttributeError):
            evidence.value = 5.0
    
    def test_regime_evidence_json_roundtrip(self):
        """Test regime evidence JSON roundtrip."""
        from macro_intelligence.regime.contracts import RegimeEvidence
        
        original = RegimeEvidence(
            evidence_id="EVD_001",
            source="FRED",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            value=4.25,
            contribution=0.3,
            weight=0.5,
        )
        
        json_str = original.to_json()
        restored = RegimeEvidence.from_json(json_str)
        
        assert restored.evidence_id == original.evidence_id
        assert restored.to_json() == json_str
    
    def test_regime_assessment_creation(self):
        """Test creating regime assessment."""
        from macro_intelligence.regime.contracts import RegimeAssessment, RegimeConfidence
        
        assessment = RegimeAssessment(
            assessment_id="ASM_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        assert assessment.assessment_id == "ASM_001"
        assert assessment.inflation_state == "target"
    
    def test_regime_assessment_immutability(self):
        """Test regime assessment immutability."""
        from macro_intelligence.regime.contracts import RegimeAssessment, RegimeConfidence
        
        assessment = RegimeAssessment(
            assessment_id="ASM_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        with pytest.raises(AttributeError):
            assessment.inflation_state = "high"
    
    def test_regime_assessment_json_roundtrip(self):
        """Test regime assessment JSON roundtrip."""
        from macro_intelligence.regime.contracts import RegimeAssessment, RegimeConfidence
        
        original = RegimeAssessment(
            assessment_id="ASM_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        json_str = original.to_json()
        restored = RegimeAssessment.from_json(json_str)
        
        assert restored.assessment_id == original.assessment_id
        assert restored.to_json() == json_str
    
    def test_regime_snapshot_creation(self):
        """Test creating regime snapshot."""
        from macro_intelligence.regime.contracts import RegimeSnapshot, RegimeAssessment, RegimeConfidence
        
        snapshot = RegimeSnapshot(
            snapshot_id="SNAP_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            assessment=RegimeAssessment(
                assessment_id="ASM_001",
                timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                inflation_state="target",
                growth_state="expansion",
                monetary_state="neutral",
                liquidity_state="normal",
                employment_state="full",
                risk_state="low",
                confidence=RegimeConfidence(
                    level=0.85,
                    evidence_count=10,
                    data_quality=0.9,
                    model_version="v1.0.0",
                    calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                ),
            ),
        )
        
        assert snapshot.snapshot_id == "SNAP_001"
    
    def test_regime_snapshot_immutability(self):
        """Test regime snapshot immutability."""
        from macro_intelligence.regime.contracts import RegimeSnapshot, RegimeAssessment, RegimeConfidence
        
        snapshot = RegimeSnapshot(
            snapshot_id="SNAP_001",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            assessment=RegimeAssessment(
                assessment_id="ASM_001",
                timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                inflation_state="target",
                growth_state="expansion",
                monetary_state="neutral",
                liquidity_state="normal",
                employment_state="full",
                risk_state="low",
                confidence=RegimeConfidence(
                    level=0.85,
                    evidence_count=10,
                    data_quality=0.9,
                    model_version="v1.0.0",
                    calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
                ),
            ),
        )
        
        with pytest.raises(AttributeError):
            snapshot.snapshot_id = "SNAP_002"
    
    def test_macro_regime_creation(self):
        """Test creating macro regime."""
        from macro_intelligence.regime.contracts import MacroRegime, RegimeConfidence
        
        regime = MacroRegime(
            regime_id="REG_001",
            name="Normal Expansion",
            description="Normal economic expansion",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            severity="normal",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        assert regime.regime_id == "REG_001"
        assert regime.name == "Normal Expansion"
    
    def test_macro_regime_immutability(self):
        """Test macro regime immutability."""
        from macro_intelligence.regime.contracts import MacroRegime, RegimeConfidence
        
        regime = MacroRegime(
            regime_id="REG_001",
            name="Normal Expansion",
            description="Normal economic expansion",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            severity="normal",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        with pytest.raises(AttributeError):
            regime.name = "Modified"
    
    def test_macro_regime_json_roundtrip(self):
        """Test macro regime JSON roundtrip."""
        from macro_intelligence.regime.contracts import MacroRegime, RegimeConfidence
        
        original = MacroRegime(
            regime_id="REG_001",
            name="Normal Expansion",
            description="Normal economic expansion",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            severity="normal",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        json_str = original.to_json()
        restored = MacroRegime.from_json(json_str)
        
        assert restored.regime_id == original.regime_id
        assert restored.name == original.name
        assert restored.to_json() == json_str
    
    def test_macro_regime_hash_deterministic(self):
        """Test macro regime hash determinism."""
        from macro_intelligence.regime.contracts import MacroRegime, RegimeConfidence
        
        regime1 = MacroRegime(
            regime_id="REG_001",
            name="Normal Expansion",
            description="Normal economic expansion",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            severity="normal",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        regime2 = MacroRegime(
            regime_id="REG_001",
            name="Normal Expansion",
            description="Normal economic expansion",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            severity="normal",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        assert regime1.compute_hash() == regime2.compute_hash()


class TestMILRegInvariants:
    """Tests for MIL-REG invariants."""
    
    def test_mil_reg_001_immutability(self):
        """MIL-REG-001: Regime objects are immutable."""
        from macro_intelligence.regime.contracts import MacroRegime, RegimeConfidence
        
        regime = MacroRegime(
            regime_id="REG_001",
            name="Normal Expansion",
            description="Normal economic expansion",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            severity="normal",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        # Should raise AttributeError on modification
        with pytest.raises(AttributeError):
            regime.inflation_state = "high"
    
    def test_mil_reg_003_identical_evidence(self):
        """MIL-REG-003: Same evidence produces identical regime object."""
        from macro_intelligence.regime.contracts import MacroRegime, RegimeConfidence
        
        # Create two identical regimes
        regime1 = MacroRegime(
            regime_id="REG_001",
            name="Normal Expansion",
            description="Normal economic expansion",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            severity="normal",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        regime2 = MacroRegime(
            regime_id="REG_001",
            name="Normal Expansion",
            description="Normal economic expansion",
            timestamp=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            inflation_state="target",
            growth_state="expansion",
            monetary_state="neutral",
            liquidity_state="normal",
            employment_state="full",
            risk_state="low",
            severity="normal",
            confidence=RegimeConfidence(
                level=0.85,
                evidence_count=10,
                data_quality=0.9,
                model_version="v1.0.0",
                calculated_at=datetime(2026, 8, 3, 12, 0, tzinfo=UTC),
            ),
        )
        
        # Hashes should be identical
        assert regime1.compute_hash() == regime2.compute_hash()
        
        # JSON should be identical
        assert regime1.to_json() == regime2.to_json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
