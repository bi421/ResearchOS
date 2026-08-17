"""
ResearchOS Macro Intelligence Layer - Knowledge Generation Engine Tests

Verifies MIL-KNOW invariants:
- MIL-KNOW-001: Knowledge objects are immutable
- MIL-KNOW-002: Knowledge has complete provenance
- MIL-KNOW-003: Same inputs produce identical knowledge
- MIL-KNOW-004: Knowledge generation is deterministic
- MIL-KNOW-005: Algorithm versions are permanent
- MIL-KNOW-006: Knowledge never mutates source evidence

Minimum tests required:
- frozen dataclass validation
- serialization
- hash determinism
- evidence linking
- pattern detection
- confidence calculation
- context building
- generator pipeline
- provenance completeness
- regression guards
"""

from datetime import datetime, timezone

import pytest

UTC = timezone.utc


# =============================================================================
# Helpers
# =============================================================================


def _make_knowledge_object(**kwargs):
    """Build a valid KnowledgeObject with defaults."""
    from macro_intelligence.knowledge.models import (
        KnowledgeObject,
        KnowledgeProvenance,
        KnowledgeType,
    )

    defaults = {
        "knowledge_id": "KN_KNOW-001_abc123def456",
        "knowledge_type": KnowledgeType.REGIME_PERSISTENCE,
        "statement": "Inflation persistence regime detected with high confidence.",
        "confidence": 0.85,
        "supporting_evidence": ("EV_1", "EV_2"),
        "supporting_features": ("VEC_1",),
        "supporting_relationships": ("REL_1",),
        "regime_context": "inflationary_growth",
        "provenance": KnowledgeProvenance(
            evidence_ids=("EV_1", "EV_2"),
            feature_vector_ids=("VEC_1",),
            relationship_ids=("REL_1",),
            regime_classification_id="CLS_1",
            transition_id="",
            rules_version="know-rules/v1.0.0",
        ),
    }
    defaults.update(kwargs)
    return KnowledgeObject(**defaults)


def _full_inputs():
    """Build a KnowledgeInputs carrying a full set of frozen upstream signals."""
    from macro_intelligence.knowledge.generator import KnowledgeInputs

    return KnowledgeInputs(
        evidence_ids=("EV_1", "EV_2"),
        feature_vector_ids=("VEC_1",),
        relationship_ids=("REL_1",),
        regime_classification_id="CLS_1",
        transition_id="TRANS_1",
        regime_context="inflationary_growth",
        persistence_periods=12,
        regime_confidence=0.85,
        continuation_probability=0.7,
        regime_name="inflationary_growth",
        transition_detected=True,
        transition_confidence=0.8,
        previous_regime="goldilocks",
        current_regime="inflationary_growth",
        rolling_stability=0.1,
        overall_correlation=0.7,
        relationship_sample_size=100,
        series_a="CPI_YOY",
        series_b="US10Y",
        breaks=(),
        features={},
        dominant_regime="inflationary_growth",
        regime_description="Rising inflation with growth",
        risk_regime="risk_on",
        risk_confidence=0.8,
        safe_haven_correlations={},
        monetary_regime="neutral",
        monetary_confidence=0.7,
        volatility_elevated=False,
        evidence_quality=0.9,
        feature_quality=0.8,
        relationship_stability_quality=0.85,
        regime_confidence_quality=0.85,
        historical_consistency=0.75,
    )


# =============================================================================
# MIL-KNOW-001: Knowledge objects are immutable
# =============================================================================


class TestMILKNOW001Immutable:
    """MIL-KNOW-001: Knowledge objects are immutable (frozen dataclass)."""

    def test_object_is_frozen(self):
        """Fields cannot be reassigned."""
        obj = _make_knowledge_object()
        with pytest.raises(AttributeError):
            obj.statement = "modified"
        with pytest.raises(AttributeError):
            obj.confidence = 0.1

    def test_collections_are_tuples(self):
        """Support collections are immutable tuples."""
        obj = _make_knowledge_object()
        assert isinstance(obj.supporting_evidence, tuple)
        with pytest.raises(AttributeError):
            obj.supporting_evidence = ["EV_9"]

    def test_provenance_is_frozen(self):
        """Provenance object is itself immutable."""
        from macro_intelligence.knowledge.models import KnowledgeProvenance

        prov = KnowledgeProvenance(evidence_ids=("EV_1",))
        with pytest.raises(AttributeError):
            prov.evidence_ids = ("EV_2",)

    def test_dataclass_is_frozen_validation(self):
        """All knowledge models are frozen dataclasses (dataclasses.is_dataclass)."""
        from dataclasses import is_dataclass

        from macro_intelligence.knowledge.models import (
            KnowledgeObject,
            KnowledgeProvenance,
            MacroContext,
        )

        assert is_dataclass(KnowledgeObject) is True
        assert is_dataclass(KnowledgeProvenance) is True
        assert is_dataclass(MacroContext) is True

        # Frozen dataclasses disallow attribute assignment via __setattr__
        obj = _make_knowledge_object()
        with pytest.raises(AttributeError):
            obj.knowledge_id = "KN_MODIFIED"


# =============================================================================
# MIL-KNOW-002: Knowledge has complete provenance
# =============================================================================


class TestMILKNOW002Provenance:
    """MIL-KNOW-002: Knowledge has complete provenance."""

    def test_provenance_is_complete(self):
        """Knowledge built with supporting artifacts has complete provenance."""
        obj = _make_knowledge_object()
        assert obj.provenance.is_complete() is True
        assert "EV_1" in obj.provenance.evidence_ids
        assert "REL_1" in obj.provenance.relationship_ids
        assert obj.provenance.regime_classification_id == "CLS_1"

    def test_validate_rejects_empty_provenance(self):
        """A knowledge object with empty provenance is invalid."""
        from macro_intelligence.knowledge.models import (
            KnowledgeObject,
            KnowledgeProvenance,
        )

        obj = KnowledgeObject(
            knowledge_id="KN_KNOW-001_xyz",
            knowledge_type=_make_knowledge_object().knowledge_type,
            statement="test",
            confidence=0.5,
            provenance=KnowledgeProvenance(),
        )
        is_valid, errors = obj.validate()
        assert is_valid is False
        assert any("provenance" in e for e in errors)

    def test_generated_objects_have_provenance(self):
        """KnowledgeGenerator output always carries provenance."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        generator = KnowledgeGenerator()
        objects = generator.generate(_full_inputs())
        assert len(objects) > 0
        for obj in objects:
            assert obj.provenance.is_complete() is True


# =============================================================================
# MIL-KNOW-003: Same inputs produce identical knowledge
# =============================================================================


class TestMILKNOW003IdenticalKnowledge:
    """MIL-KNOW-003: Same inputs produce identical knowledge."""

    def test_same_inputs_same_ids(self):
        """Two generations from identical inputs produce identical knowledge ids."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        g1 = KnowledgeGenerator().generate(_full_inputs())
        g2 = KnowledgeGenerator().generate(_full_inputs())
        assert [k.knowledge_id for k in g1] == [k.knowledge_id for k in g2]

    def test_same_inputs_same_statements(self):
        """Statements are identical across runs."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        g1 = KnowledgeGenerator().generate(_full_inputs())
        g2 = KnowledgeGenerator().generate(_full_inputs())
        assert [k.statement for k in g1] == [k.statement for k in g2]

    def test_hash_deterministic_same_inputs(self):
        """Hashes are identical across runs for identical inputs."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        g1 = KnowledgeGenerator().generate(_full_inputs())
        g2 = KnowledgeGenerator().generate(_full_inputs())
        assert [k.compute_hash() for k in g1] == [k.compute_hash() for k in g2]


# =============================================================================
# MIL-KNOW-004: Knowledge generation is deterministic
# =============================================================================


class TestMILKNOW004Deterministic:
    """MIL-KNOW-004: Knowledge generation is deterministic."""

    def test_generator_deterministic(self):
        """Repeated generation yields identical semantic output and hashes."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        g1 = KnowledgeGenerator().generate(_full_inputs())
        g2 = KnowledgeGenerator().generate(_full_inputs())

        # Semantic fields (excluding runtime created_timestamp) are identical
        assert [k.statement for k in g1] == [k.statement for k in g2]
        assert [k.confidence for k in g1] == [k.confidence for k in g2]
        assert [k.compute_hash() for k in g1] == [k.compute_hash() for k in g2]

    def test_confidence_no_randomness(self):
        """Confidence calculator is deterministic (no randomness)."""
        from macro_intelligence.knowledge.confidence import (
            ConfidenceCalculator,
            ConfidenceComponents,
        )

        comps = ConfidenceComponents(
            evidence_quality=0.9,
            feature_quality=0.8,
            relationship_stability=0.85,
            regime_confidence=0.85,
            historical_consistency=0.75,
        )
        c1 = ConfidenceCalculator().compute(comps)
        c2 = ConfidenceCalculator().compute(comps)
        assert c1 == c2
        assert 0.0 <= c1 <= 1.0

    def test_pattern_detector_deterministic(self):
        """PatternDetector returns deterministic findings."""
        from macro_intelligence.knowledge.pattern import PatternDetector

        d1 = PatternDetector().detect_all(
            persistence_periods=12,
            regime_confidence=0.85,
            continuation_probability=0.7,
            regime_name="inflationary_growth",
        )
        d2 = PatternDetector().detect_all(
            persistence_periods=12,
            regime_confidence=0.85,
            continuation_probability=0.7,
            regime_name="inflationary_growth",
        )
        assert [f.statement for f in d1] == [f.statement for f in d2]

    def test_created_timestamp_not_in_hash(self):
        """Runtime timestamps do not affect deterministic hash."""
        obj1 = _make_knowledge_object(created_timestamp=datetime(2026, 8, 3, tzinfo=UTC))
        obj2 = _make_knowledge_object(created_timestamp=datetime(2026, 9, 3, tzinfo=UTC))
        assert obj1.compute_hash() == obj2.compute_hash()


# =============================================================================
# MIL-KNOW-005: Algorithm versions are permanent
# =============================================================================


class TestMILKNOW005PermanentVersions:
    """MIL-KNOW-005: Algorithm versions are permanent/immutable."""

    def test_algorithm_version_constant(self):
        """ALGORITHM_VERSION is a fixed semantic version string."""
        from macro_intelligence.knowledge.models import ALGORITHM_VERSION

        assert ALGORITHM_VERSION == "know-eng/v1.0.0"
        assert ALGORITHM_VERSION.startswith("know-eng/")

    def test_rules_version_constant(self):
        """Rules version is a fixed immutable version string."""
        from macro_intelligence.knowledge.rules import (
            KNOWLEDGE_RULES_VERSION,
            get_rules_version,
        )

        assert KNOWLEDGE_RULES_VERSION == "know-rules/v1.0.0"
        assert KNOWLEDGE_RULES_VERSION.startswith("know-rules/")
        assert get_rules_version() == KNOWLEDGE_RULES_VERSION

    def test_rule_hashes_stable(self):
        """Rule records produce stable hashes."""
        from macro_intelligence.knowledge.rules import RULES

        hashes = {rule.rule_id: rule.compute_hash() for rule in RULES.values()}
        assert len(set(hashes.values())) == len(RULES)


# =============================================================================
# MIL-KNOW-006: Knowledge never mutates source evidence
# =============================================================================


class TestMILKNOW006NoMutation:
    """MIL-KNOW-006: Source evidence and features are never mutated."""

    def test_inputs_not_mutated_by_generator(self):
        """KnowledgeInputs frozen object is unchanged after generation."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        inputs = _full_inputs()
        before = inputs.to_dict() if hasattr(inputs, "to_dict") else None
        KnowledgeGenerator().generate(inputs)
        if before is not None:
            assert inputs.to_dict() == before

    def test_supporting_collections_are_tuples_after_generation(self):
        """Generated knowledge references immutable tuples of ids."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        objects = KnowledgeGenerator().generate(_full_inputs())
        for obj in objects:
            assert isinstance(obj.supporting_evidence, tuple)
            assert isinstance(obj.supporting_features, tuple)
            assert isinstance(obj.supporting_relationships, tuple)

    def test_upstream_ids_preserved(self):
        """Generator preserves exactly the upstream identifiers it consumed."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        inputs = _full_inputs()
        objects = KnowledgeGenerator().generate(inputs)
        assert len(objects) > 0
        for obj in objects:
            assert set(obj.provenance.evidence_ids) == set(inputs.evidence_ids)
            assert set(obj.provenance.feature_vector_ids) == set(inputs.feature_vector_ids)
            assert set(obj.provenance.relationship_ids) == set(inputs.relationship_ids)


# =============================================================================
# Frozen dataclass validation & serialization
# =============================================================================


class TestModelSerialization:
    """Serialization and round-trip behavior."""

    def test_knowledge_object_roundtrip(self):
        """to_dict/from_dict round-trip preserves semantic fields."""
        obj = _make_knowledge_object()
        restored = type(obj).from_dict(obj.to_dict())
        assert restored.to_json() == obj.to_json()
        assert restored.knowledge_id == obj.knowledge_id
        assert restored.statement == obj.statement

    def test_knowledge_object_json_roundtrip(self):
        """to_json/from_json round-trip is stable."""
        obj = _make_knowledge_object()
        restored = type(obj).from_json(obj.to_json())
        assert restored.to_json() == obj.to_json()

    def test_different_evidence_different_hash(self):
        """Different evidence yields different knowledge_hash."""
        from macro_intelligence.knowledge.models import KnowledgeProvenance

        obj1 = _make_knowledge_object(
            supporting_evidence=("EV_1",),
            provenance=KnowledgeProvenance(evidence_ids=("EV_1",)),
        )
        obj2 = _make_knowledge_object(
            supporting_evidence=("EV_2",),
            provenance=KnowledgeProvenance(evidence_ids=("EV_2",)),
        )
        assert obj1.compute_hash() != obj2.compute_hash()

    def test_identical_objects_same_hash(self):
        """Identical objects produce identical hashes."""
        obj1 = _make_knowledge_object()
        obj2 = _make_knowledge_object()
        assert obj1.compute_hash() == obj2.compute_hash()

    def test_macro_context_roundtrip(self):
        """MacroContext round-trips through dict."""
        from macro_intelligence.knowledge.models import MacroContext

        context = MacroContext(
            context_id="CTX_abc123",
            regime_context="inflationary_growth",
            knowledge_objects=(_make_knowledge_object(),),
        )
        restored = MacroContext.from_dict(context.to_dict())
        assert restored.to_json() == context.to_json()


# =============================================================================
# Evidence linking
# =============================================================================


class TestEvidenceLinking:
    """EvidenceLinker provenance binding."""

    def test_build_provenance(self):
        """build_provenance records all upstream ids."""
        from macro_intelligence.knowledge.evidence_link import EvidenceLinker

        prov = EvidenceLinker().build_provenance(
            evidence_ids=["EV_1", "EV_2"],
            feature_vector_ids=["VEC_1"],
            relationship_ids=["REL_1"],
            regime_classification_id="CLS_1",
            rules_version="know-rules/v1.0.0",
        )
        assert prov.evidence_ids == ("EV_1", "EV_2")
        assert prov.regime_classification_id == "CLS_1"
        assert prov.is_complete() is True

    def test_build_link(self):
        """build_link creates an EvidenceLink bound to a knowledge id."""
        from macro_intelligence.knowledge.evidence_link import EvidenceLinker

        obj = _make_knowledge_object()
        link = EvidenceLinker().build_link(
            obj,
            evidence_ids=["EV_1"],
            regime_classification_id="CLS_1",
        )
        assert link.knowledge_id == obj.knowledge_id
        assert "EV_1" in link.evidence_ids

    def test_resolve_provenance(self):
        """resolve_provenance returns the knowledge object's provenance."""
        from macro_intelligence.knowledge.evidence_link import EvidenceLinker

        obj = _make_knowledge_object()
        prov = EvidenceLinker().resolve_provenance(obj)
        assert prov == obj.provenance

    def test_linker_deterministic(self):
        """Identical link inputs produce identical hashes."""
        from macro_intelligence.knowledge.evidence_link import EvidenceLinker

        obj = _make_knowledge_object()
        l1 = EvidenceLinker().build_link(
            obj, evidence_ids=["EV_1"], regime_classification_id="CLS_1"
        )
        l2 = EvidenceLinker().build_link(
            obj, evidence_ids=["EV_1"], regime_classification_id="CLS_1"
        )
        assert l1.compute_hash() == l2.compute_hash()


# =============================================================================
# Pattern detection
# =============================================================================


class TestPatternDetection:
    """Deterministic rule-based pattern detection."""

    def test_regime_persistence_pattern(self):
        """Regime persistence beyond thresholds yields REGIME_PERSISTENCE."""
        from macro_intelligence.knowledge.models import KnowledgeType
        from macro_intelligence.knowledge.pattern import PatternDetector

        finding = PatternDetector().detect_regime_persistence(
            persistence_periods=12,
            regime_confidence=0.85,
            continuation_probability=0.7,
            regime_name="inflationary_growth",
        )
        assert finding is not None
        assert finding.pattern_type == KnowledgeType.REGIME_PERSISTENCE

    def test_regime_transition_pattern(self):
        """Detected transition with high confidence yields REGIME_TRANSITION."""
        from macro_intelligence.knowledge.models import KnowledgeType
        from macro_intelligence.knowledge.pattern import PatternDetector

        finding = PatternDetector().detect_regime_transition(
            transition_detected=True,
            transition_confidence=0.85,
            previous_regime="goldilocks",
            current_regime="inflationary_growth",
        )
        assert finding is not None
        assert finding.pattern_type == KnowledgeType.REGIME_TRANSITION

    def test_persistent_relationship_pattern(self):
        """Stable strong correlation yields PERSISTENT_RELATIONSHIP."""
        from macro_intelligence.knowledge.models import KnowledgeType
        from macro_intelligence.knowledge.pattern import PatternDetector

        finding = PatternDetector().detect_persistent_relationship(
            rolling_stability=0.05,
            overall_correlation=0.75,
            sample_size=120,
            series_a="CPI_YOY",
            series_b="US10Y",
        )
        assert finding is not None
        assert finding.pattern_type == KnowledgeType.PERSISTENT_RELATIONSHIP

    def test_correlation_break_pattern(self):
        """Structural break yields CORRELATION_BREAK."""
        from macro_intelligence.knowledge.models import KnowledgeType
        from macro_intelligence.knowledge.pattern import PatternDetector

        class _Break:
            confidence = 0.8
            break_type = "strength_change"

        finding = PatternDetector().detect_correlation_break([_Break()], "CPI_YOY", "US10Y")
        assert finding is not None
        assert finding.pattern_type == KnowledgeType.CORRELATION_BREAK

    def test_anomaly_pattern(self):
        """High z-score feature yields ANOMALY."""
        from macro_intelligence.knowledge.models import KnowledgeType
        from macro_intelligence.knowledge.pattern import PatternDetector

        finding = PatternDetector().detect_anomaly(
            {"FEAT_CPI_Z": {"z_score": 3.2, "quality_score": 0.9}}
        )
        assert finding is not None
        assert finding.pattern_type == KnowledgeType.ANOMALY

    def test_no_pattern_when_below_threshold(self):
        """Below-threshold inputs produce no pattern finding."""
        from macro_intelligence.knowledge.pattern import PatternDetector

        finding = PatternDetector().detect_regime_persistence(
            persistence_periods=2,
            regime_confidence=0.3,
            continuation_probability=0.4,
            regime_name="inflationary_growth",
        )
        assert finding is None

    def test_findings_have_rules_version(self):
        """Every finding records the immutable rules version."""
        from macro_intelligence.knowledge.pattern import PatternDetector

        findings = PatternDetector().detect_all(**_persistence_kwargs())
        assert len(findings) >= 1
        for f in findings:
            assert f.rule_version == "know-rules/v1.0.0"
            assert f.rule_id


def _persistence_kwargs():
    return {
        "persistence_periods": 12,
        "regime_confidence": 0.85,
        "continuation_probability": 0.7,
        "regime_name": "inflationary_growth",
    }


# =============================================================================
# Confidence calculation
# =============================================================================


class TestConfidenceCalculation:
    """Deterministic weighted confidence calculation."""

    def test_weights_sum_to_one(self):
        """Component weights sum to 1.0."""
        from macro_intelligence.knowledge.confidence import CONFIDENCE_WEIGHTS

        assert abs(sum(CONFIDENCE_WEIGHTS.values()) - 1.0) < 1e-9
        assert CONFIDENCE_WEIGHTS["evidence_quality"] == 0.30
        assert CONFIDENCE_WEIGHTS["feature_quality"] == 0.20
        assert CONFIDENCE_WEIGHTS["relationship_stability"] == 0.20
        assert CONFIDENCE_WEIGHTS["regime_confidence"] == 0.20
        assert CONFIDENCE_WEIGHTS["historical_consistency"] == 0.10

    def test_high_components_high_confidence(self):
        """All-high components yield high confidence."""
        from macro_intelligence.knowledge.confidence import (
            ConfidenceCalculator,
            ConfidenceComponents,
        )

        conf = ConfidenceCalculator().compute(
            ConfidenceComponents(
                evidence_quality=1.0,
                feature_quality=1.0,
                relationship_stability=1.0,
                regime_confidence=1.0,
                historical_consistency=1.0,
            )
        )
        assert conf == pytest.approx(1.0, abs=1e-4)

    def test_zero_components_zero_confidence(self):
        """All-zero components yield zero confidence."""
        from macro_intelligence.knowledge.confidence import (
            ConfidenceCalculator,
            ConfidenceComponents,
        )

        conf = ConfidenceCalculator().compute(ConfidenceComponents())
        assert conf == 0.0

    def test_weighted_blend(self):
        """Confidence is the deterministic weighted blend."""
        from macro_intelligence.knowledge.confidence import (
            ConfidenceCalculator,
            ConfidenceComponents,
        )

        comps = ConfidenceComponents(
            evidence_quality=0.9,
            feature_quality=0.8,
            relationship_stability=0.85,
            regime_confidence=0.85,
            historical_consistency=0.75,
        )
        expected = 0.30 * 0.9 + 0.20 * 0.8 + 0.20 * 0.85 + 0.20 * 0.85 + 0.10 * 0.75
        conf = ConfidenceCalculator().compute(comps)
        assert conf == pytest.approx(round(expected, 4), abs=1e-4)

    def test_missing_components_contribute_zero(self):
        """Missing components contribute 0.0 to the blend."""
        from macro_intelligence.knowledge.confidence import (
            ConfidenceCalculator,
            ConfidenceComponents,
        )

        conf = ConfidenceCalculator().compute(ConfidenceComponents(evidence_quality=1.0))
        assert conf == pytest.approx(0.30, abs=1e-4)

    def test_output_range(self):
        """Output is always in [0.0, 1.0]."""
        from macro_intelligence.knowledge.confidence import (
            ConfidenceCalculator,
            ConfidenceComponents,
        )

        calc = ConfidenceCalculator()
        for i in range(11):
            v = i / 10.0
            conf = calc.compute(
                ConfidenceComponents(
                    evidence_quality=v,
                    feature_quality=v,
                    relationship_stability=v,
                    regime_confidence=v,
                    historical_consistency=v,
                )
            )
            assert 0.0 <= conf <= 1.0


# =============================================================================
# Context building
# =============================================================================


class TestContextBuilding:
    """MacroContextBuilder aggregation."""

    def test_context_build(self):
        """Builder aggregates knowledge objects into a MacroContext."""
        from macro_intelligence.knowledge.context import MacroContextBuilder
        from macro_intelligence.knowledge.models import MacroContext

        objects = [_make_knowledge_object()]
        context = MacroContextBuilder().build(objects, regime_context="inflationary_growth")
        assert isinstance(context, MacroContext)
        assert len(context.knowledge_objects) == 1
        assert context.regime_context == "inflationary_growth"

    def test_context_deterministic(self):
        """Identical inputs yield identical context hashes."""
        from macro_intelligence.knowledge.context import MacroContextBuilder

        objects = [_make_knowledge_object()]
        c1 = MacroContextBuilder().build(objects, regime_context="inflationary_growth")
        c2 = MacroContextBuilder().build(objects, regime_context="inflationary_growth")
        assert c1.compute_hash() == c2.compute_hash()

    def test_context_no_mutation(self):
        """Builder does not mutate the input knowledge objects."""
        from macro_intelligence.knowledge.context import MacroContextBuilder

        obj = _make_knowledge_object()
        MacroContextBuilder().build([obj], regime_context="inflationary_growth")
        assert obj.statement == "Inflation persistence regime detected with high confidence."

    def test_context_sorted_deterministic(self):
        """Knowledge objects are deterministically ordered in the context."""
        from macro_intelligence.knowledge.context import MacroContextBuilder
        from macro_intelligence.knowledge.models import KnowledgeType

        obj_a = _make_knowledge_object(
            knowledge_id="KN_KNOW-001_aaa", knowledge_type=KnowledgeType.ANOMALY
        )
        obj_b = _make_knowledge_object(
            knowledge_id="KN_KNOW-001_bbb",
            knowledge_type=KnowledgeType.REGIME_PATTERN,
        )
        c1 = MacroContextBuilder().build([obj_a, obj_b], regime_context="x")
        c2 = MacroContextBuilder().build([obj_b, obj_a], regime_context="x")
        assert [k.knowledge_id for k in c1.knowledge_objects] == [
            k.knowledge_id for k in c2.knowledge_objects
        ]


# =============================================================================
# Generator pipeline
# =============================================================================


class TestGeneratorPipeline:
    """KnowledgeGenerator end-to-end pipeline."""

    def test_generator_returns_objects(self):
        """Generator returns a list of immutable KnowledgeObjects."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator
        from macro_intelligence.knowledge.models import KnowledgeObject

        objects = KnowledgeGenerator().generate(_full_inputs())
        assert len(objects) > 0
        assert all(isinstance(o, KnowledgeObject) for o in objects)

    def test_generator_objects_valid(self):
        """Generated objects pass validation."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        objects = KnowledgeGenerator().generate(_full_inputs())
        for obj in objects:
            is_valid, errors = obj.validate()
            assert is_valid, errors

    def test_generator_objects_have_descriptive_statements(self):
        """Generated statements are descriptive and explainable."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        objects = KnowledgeGenerator().generate(_full_inputs())
        for obj in objects:
            assert obj.statement
            assert "detected" in obj.statement or "Regime" in obj.statement

    def test_generator_empty_inputs(self):
        """Generator returns empty list when nothing crosses thresholds."""
        from macro_intelligence.knowledge.generator import (
            KnowledgeGenerator,
            KnowledgeInputs,
        )

        objects = KnowledgeGenerator().generate(KnowledgeInputs())
        assert objects == []

    def test_generator_version(self):
        """Generator exposes permanent version metadata."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        gen = KnowledgeGenerator()
        meta = gen.to_dict()
        assert meta["version"] == "know-eng/v1.0.0"
        assert meta["rules_version"] == "know-rules/v1.0.0"
        assert meta["pattern_detector_version"] == "know-eng/v1.0.0"


# =============================================================================
# Provenance completeness
# =============================================================================


class TestProvenanceCompleteness:
    """Provenance completeness and traceability."""

    def test_provenance_answers_why(self):
        """Provenance references every upstream artifact used."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        objects = KnowledgeGenerator().generate(_full_inputs())
        for obj in objects:
            assert obj.provenance.is_complete()
            assert obj.provenance.rules_version == "know-rules/v1.0.0"
            assert obj.provenance.algorithm_version == "know-eng/v1.0.0"
            # Evidence and relationship refs flow from inputs
            assert set(obj.provenance.evidence_ids) == {"EV_1", "EV_2"}
            assert obj.provenance.regime_classification_id == "CLS_1"

    def test_supporting_evidence_consistent_with_provenance(self):
        """supporting_* fields are consistent with provenance."""
        from macro_intelligence.knowledge.generator import KnowledgeGenerator

        objects = KnowledgeGenerator().generate(_full_inputs())
        for obj in objects:
            assert set(obj.supporting_evidence) == set(obj.provenance.evidence_ids)
            assert set(obj.supporting_features) == set(obj.provenance.feature_vector_ids)
            assert set(obj.supporting_relationships) == set(obj.provenance.relationship_ids)


# =============================================================================
# Regression guards
# =============================================================================


class TestRegressionGuards:
    """Regression guards for the knowledge engine."""

    def test_knowledge_type_taxonomy_complete(self):
        """All 8 required knowledge types are present."""
        from macro_intelligence.knowledge.models import KnowledgeType

        expected = {
            "regime_persistence",
            "regime_transition",
            "persistent_relationship",
            "correlation_break",
            "anomaly",
            "regime_pattern",
            "risk_off_safe_haven",
            "tightening_volatility",
        }
        actual = {t.value for t in KnowledgeType}
        assert actual == expected

    def test_all_rules_defined(self):
        """Every knowledge type has a corresponding immutable rule."""
        from macro_intelligence.knowledge.rules import RULES

        assert len(RULES) == 8
        # Each rule id KNOW-001..KNOW-008
        assert {r.rule_id for r in RULES.values()} == {
            "KNOW-001",
            "KNOW-002",
            "KNOW-003",
            "KNOW-004",
            "KNOW-005",
            "KNOW-006",
            "KNOW-007",
            "KNOW-008",
        }

    def test_no_v1_dependency(self):
        """Knowledge layer has no dependency on ResearchOS V1 core."""
        import inspect

        import macro_intelligence.knowledge.generator as gen

        source = inspect.getsource(gen)
        assert "researchos.core" not in source
        assert "researchos.quant_engine" not in source
        assert "from macro_intelligence" in source

    def test_no_ml_no_llm(self):
        """Knowledge layer has no ML or LLM dependency."""
        import inspect

        import macro_intelligence.knowledge.pattern as pat

        source = inspect.getsource(pat)
        assert "sklearn" not in source
        assert "torch" not in source
        assert "tensorflow" not in source
        assert "openai" not in source
        assert "llm" not in source.lower() or "not llm" in source.lower()

    def test_knowledge_is_not_a_signal(self):
        """Knowledge statements remain descriptive (no trading directives)."""
        from macro_intelligence.knowledge.models import KnowledgeType

        for t in KnowledgeType:
            assert t.value not in (
                "trading_signal",
                "entry_signal",
                "exit_signal",
            )
