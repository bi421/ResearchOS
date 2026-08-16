"""
Targeted tests for the canonical decision_engine evidence layer.

Covers (per repair spec):
    A. Canonical identity (contracts == evidence == score)
    B. EvidenceAggregator full-context aggregation
    C. Every evidence source collector
    D. EvidenceValidator (valid + invalid canonical items)
    E. EvidenceItem serialization round-trip
    F. EvidenceCollection serialization round-trip
    G. ProbabilityCalculator with canonical EvidenceItem objects
    H. compute_evidence_score with canonical EvidenceItem objects
    I. No legacy attribute access (static source check)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

import researchos.decision_engine.contracts as contracts
import researchos.decision_engine.evidence as evidence_module
import researchos.decision_engine.score as score_module
from researchos.decision_engine.context import DecisionContext
from researchos.decision_engine.contracts import (
    EvidenceItem,
    EvidenceSource,
    ProbabilityOutcome,
    WeightConfiguration,
)
from researchos.decision_engine.evidence import (
    EvidenceAggregator,
    EvidenceCollection,
    EvidenceValidator,
)
from researchos.decision_engine.probability import (
    ProbabilityCalculator,
    ProbabilityValidator,
)
from researchos.decision_engine.score import EvidenceScore, compute_evidence_score


FIXED_TS = datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)


# =============================================================================
# Helpers / Fixtures
# =============================================================================


def make_context(**overrides) -> DecisionContext:
    params = dict(
        asset="XAUUSD",
        market_snapshot_id="snap_001",
        market_regime_id="regime_001",
        macro_state_id="macro_001",
        historical_scenario_ids=["hist_001", "hist_002"],
        experiment_result_ids=["exp_001"],
        validation_ids=["val_001"],
        research_ids=["res_001"],
        market_memory_report_ids=["mmr_001"],
        simulation_result_ids=["sim_001"],
        timeframe="1h",
        decision_timestamp=FIXED_TS,
    )
    params.update(overrides)
    return DecisionContext(**params)


def make_item(
    source: EvidenceSource = EvidenceSource.MARKET_MEMORY,
    source_id: str = "hist_001",
    direction: ProbabilityOutcome = ProbabilityOutcome.BULLISH,
    strength: float = 0.6,
    weight: float = 0.25,
    confidence: float = 0.7,
    description: str = "test evidence",
    supporting_ids=None,
) -> EvidenceItem:
    return EvidenceItem(
        source=source,
        source_id=source_id,
        direction=direction,
        strength=strength,
        weight=weight,
        confidence=confidence,
        description=description,
        supporting_ids=supporting_ids if supporting_ids is not None else [source_id],
    )


@pytest.fixture
def full_collection():
    return EvidenceAggregator().aggregate(make_context())


# =============================================================================
# A. Canonical Identity
# =============================================================================


class TestCanonicalIdentity:
    """There must be exactly ONE EvidenceItem / EvidenceSource."""

    def test_evidence_module_reexports_contracts(self):
        assert evidence_module.EvidenceItem is contracts.EvidenceItem
        assert evidence_module.EvidenceSource is contracts.EvidenceSource

    def test_score_module_uses_contracts(self):
        assert score_module.EvidenceItem is contracts.EvidenceItem
        assert score_module.EvidenceSource is contracts.EvidenceSource

    def test_no_duplicate_class_definitions_in_decision_engine(self):
        decision_engine_dir = Path(contracts.__file__).parent
        item_defs: list[str] = []
        source_defs: list[str] = []
        for py_file in sorted(decision_engine_dir.glob("*.py")):
            source = py_file.read_text(encoding="utf-8")
            for match in re.finditer(r"^class\s+(EvidenceItem|EvidenceSource)\b", source, re.MULTILINE):
                target = item_defs if match.group(1) == "EvidenceItem" else source_defs
                target.append(f"{py_file.name}:{match.group(1)}")
        assert item_defs == ["contracts.py:EvidenceItem"]
        assert source_defs == ["contracts.py:EvidenceSource"]


# =============================================================================
# B. EvidenceAggregator
# =============================================================================


class TestEvidenceAggregator:
    def test_aggregate_returns_canonical_items(self, full_collection):
        assert full_collection.total_items == 9
        for item in full_collection.items:
            assert type(item) is contracts.EvidenceItem

    def test_source_counts_full_context(self, full_collection):
        assert full_collection.get_source_counts() == {
            "Experiment": 1,
            "MacroIntelligence": 2,
            "MarketMemory": 3,
            "QuantEngine": 1,
            "ResearchObjects": 1,
            "Validation": 1,
        }

    def test_aggregate_is_deterministic(self):
        context = make_context()
        coll1 = EvidenceAggregator().aggregate(context)
        coll2 = EvidenceAggregator().aggregate(context)
        assert coll1.id == coll2.id
        assert coll1.collection_hash == coll2.collection_hash
        assert coll1.compute_hash() == coll2.compute_hash()
        assert coll1.items == coll2.items

    def test_collection_timestamp_is_decision_timestamp(self, full_collection):
        assert full_collection.collection_timestamp == FIXED_TS

    def test_aggregate_validates_clean(self, full_collection):
        assert EvidenceValidator().is_valid_collection(full_collection) is True

    def test_empty_context_yields_empty_collection(self):
        collection = EvidenceAggregator().aggregate(make_context(
            market_regime_id="",
            macro_state_id="",
            historical_scenario_ids=[],
            experiment_result_ids=[],
            validation_ids=[],
            research_ids=[],
            market_memory_report_ids=[],
            simulation_result_ids=[],
        ))
        assert collection.total_items == 0
        assert EvidenceValidator().is_valid_collection(collection) is True


# =============================================================================
# C. Individual Source Collectors
# =============================================================================


class TestCollectors:
    """Each collector maps context references to canonical EvidenceItems."""

    @pytest.mark.parametrize(
        ("reference_ids", "context_field"),
        [
            (["h1", "h2"], "historical_scenario_ids"),
            (["m1"], "market_memory_report_ids"),
        ],
    )
    def test_collect_market_memory(self, reference_ids, context_field):
        context = make_context(**{
            "historical_scenario_ids": [],
            "experiment_result_ids": [],
            "validation_ids": [],
            "research_ids": [],
            "market_memory_report_ids": [],
            "simulation_result_ids": [],
            "market_regime_id": "",
            "macro_state_id": "",
            context_field: reference_ids,
        })
        items = EvidenceAggregator()._collect_market_memory(context)
        assert [i.source_id for i in items] == reference_ids
        for item in items:
            assert item.source is EvidenceSource.MARKET_MEMORY
            assert item.direction is ProbabilityOutcome.NEUTRAL
            assert item.strength == pytest.approx(0.5)
            assert item.confidence == pytest.approx(0.5)
            assert item.weight == pytest.approx(0.25)
            assert item.supporting_ids == [item.source_id]

    def test_collect_experiments(self):
        context = make_context(historical_scenario_ids=[], experiment_result_ids=["exp_9"])
        items = EvidenceAggregator()._collect_experiments(context)
        assert len(items) == 1
        item = items[0]
        assert item.source is EvidenceSource.EXPERIMENT
        assert item.source_id == "exp_9"
        assert item.strength == pytest.approx(0.6)
        assert item.confidence == pytest.approx(0.6)
        assert item.weight == pytest.approx(0.20)

    def test_collect_validation(self):
        context = make_context(validation_ids=["val_9"])
        items = EvidenceAggregator()._collect_validation(context)
        assert len(items) == 1
        item = items[0]
        assert item.source is EvidenceSource.VALIDATION
        assert item.source_id == "val_9"
        assert item.strength == pytest.approx(0.8)
        assert item.confidence == pytest.approx(0.8)
        assert item.weight == pytest.approx(0.15)

    def test_collect_macro(self):
        context = make_context(macro_state_id="macro_9", market_regime_id="regime_9")
        items = EvidenceAggregator()._collect_macro(context)
        assert [i.source_id for i in items] == ["macro_9", "regime_9"]
        for item in items:
            assert item.source is EvidenceSource.MACRO_INTELLIGENCE
            assert item.strength == pytest.approx(0.7)
            assert item.confidence == pytest.approx(0.7)
            assert item.weight == pytest.approx(0.25)

    def test_collect_macro_skips_empty_references(self):
        context = make_context(macro_state_id="", market_regime_id="")
        assert EvidenceAggregator()._collect_macro(context) == []

    def test_collect_quant_engine(self):
        context = make_context(simulation_result_ids=["sim_9"])
        items = EvidenceAggregator()._collect_quant_engine(context)
        assert len(items) == 1
        item = items[0]
        assert item.source is EvidenceSource.QUANT_ENGINE
        assert item.source_id == "sim_9"
        assert item.strength == pytest.approx(0.6)
        assert item.confidence == pytest.approx(0.6)
        assert item.weight == pytest.approx(0.15)

    def test_collect_research(self):
        context = make_context(research_ids=["res_9"])
        items = EvidenceAggregator()._collect_research(context)
        assert len(items) == 1
        item = items[0]
        assert item.source is EvidenceSource.RESEARCH_OBJECTS
        assert item.source_id == "res_9"
        assert item.strength == pytest.approx(0.5)
        assert item.confidence == pytest.approx(0.5)
        assert item.weight == pytest.approx(0.15)


# =============================================================================
# D. EvidenceValidator
# =============================================================================


class TestEvidenceValidator:
    def test_valid_item_passes(self):
        assert EvidenceValidator().is_valid_item(make_item()) is True

    def test_empty_source_id_fails(self):
        errors = EvidenceValidator().validate_item(make_item(source_id=""))
        assert any("source_id is empty" in e for e in errors)

    def test_invalid_confidence_fails(self):
        errors = EvidenceValidator().validate_item(make_item(confidence=1.5))
        assert any("confidence" in e for e in errors)

    def test_invalid_weight_fails(self):
        errors = EvidenceValidator().validate_item(make_item(weight=-0.1))
        assert any("weight" in e for e in errors)

    def test_invalid_strength_fails(self):
        errors = EvidenceValidator().validate_item(make_item(strength=2.0))
        assert any("strength" in e for e in errors)

    def test_non_enum_direction_fails(self):
        errors = EvidenceValidator().validate_item(make_item(direction="Bullish"))
        assert any("ProbabilityOutcome" in e for e in errors)

    def test_non_enum_source_fails(self):
        errors = EvidenceValidator().validate_item(make_item(source="MarketMemory"))
        assert any("EvidenceSource" in e for e in errors)

    def test_duplicate_source_ids_in_collection(self):
        collection = EvidenceCollection(
            decision_context_id="ctx_1",
            items=[make_item(source_id="dup"), make_item(source_id="dup")],
        )
        errors = EvidenceValidator().validate_collection(collection)
        assert any("Duplicate source_id" in e for e in errors)

    def test_empty_decision_context_id_fails(self):
        collection = EvidenceCollection(decision_context_id="", items=[])
        errors = EvidenceValidator().validate_collection(collection)
        assert any("decision_context_id is empty" in e for e in errors)


# =============================================================================
# E. EvidenceItem Serialization
# =============================================================================


class TestEvidenceItemSerialization:
    def test_to_dict_contains_exactly_canonical_fields(self):
        d = make_item().to_dict()
        assert set(d.keys()) == {
            "source",
            "source_id",
            "direction",
            "strength",
            "weight",
            "confidence",
            "description",
            "supporting_ids",
        }

    def test_to_dict_values_are_plain_primitives(self):
        d = make_item().to_dict()
        assert d["source"] == "MarketMemory"
        assert d["direction"] == "Bullish"
        assert d["supporting_ids"] == ["hist_001"]

    def test_round_trip(self):
        item = make_item(
            source=EvidenceSource.MACRO_INTELLIGENCE,
            source_id="macro_zz",
            direction=ProbabilityOutcome.BEARISH,
            strength=0.42,
            weight=0.17,
            confidence=0.91,
            description="macro regime shift",
            supporting_ids=["macro_zz", "regime_zz"],
        )
        restored = contracts.EvidenceItem.from_dict(item.to_dict())
        assert type(restored) is contracts.EvidenceItem
        assert restored == item


# =============================================================================
# F. EvidenceCollection Serialization
# =============================================================================


class TestEvidenceCollectionSerialization:
    def test_round_trip_preserves_canonical_items(self, full_collection):
        d = full_collection.to_dict()
        restored = EvidenceCollection.from_dict(d)
        assert type(restored) is EvidenceCollection
        assert restored.decision_context_id == full_collection.decision_context_id
        assert restored.collection_version == full_collection.collection_version
        assert restored.collection_timestamp == full_collection.collection_timestamp
        assert restored.total_items == full_collection.total_items
        for original, item in zip(full_collection.items, restored.items):
            assert type(item) is contracts.EvidenceItem
            assert item == original

    def test_round_trip_preserves_hash(self, full_collection):
        restored = EvidenceCollection.from_dict(full_collection.to_dict())
        assert restored.compute_hash() == full_collection.compute_hash()

    def test_round_trip_is_json_safe(self, full_collection):
        import json

        parsed = json.loads(json.dumps(full_collection.to_dict(), default=str))
        assert parsed["total_items"] == 9
        assert all("source_id" in e for e in parsed["items"])

    def test_add_item_updates_hash(self):
        collection = EvidenceCollection(decision_context_id="ctx_1", items=[])
        before = collection.collection_hash
        collection.add_item(make_item(source_id="a"))
        assert collection.collection_hash != before
        assert collection.total_items == 1


# =============================================================================
# G. ProbabilityCalculator
# =============================================================================


class TestProbabilityCalculator:
    def test_directional_probabilities_with_canonical_items(self):
        items = [
            make_item(source_id="b1", direction=ProbabilityOutcome.BULLISH, confidence=0.8, weight=0.5),
            make_item(source_id="b2", direction=ProbabilityOutcome.BEARISH, confidence=0.6, weight=0.5),
            make_item(source_id="n1", direction=ProbabilityOutcome.NEUTRAL, confidence=0.2, weight=0.5),
        ]
        assessment = ProbabilityCalculator().compute(
            decision_context_id="ctx_1",
            evidence_collection_id="coll_1",
            items=items,
            timestamp=FIXED_TS,
        )
        # contributions: 0.4 bullish, 0.3 bearish, 0.1 neutral (total 0.8)
        assert assessment.bullish_probability == pytest.approx(0.5)
        assert assessment.bearish_probability == pytest.approx(0.375)
        assert assessment.neutral_probability == pytest.approx(0.125)
        assert assessment.bullish_probability + assessment.bearish_probability + assessment.neutral_probability == pytest.approx(1.0)
        assert assessment.confidence == pytest.approx(1.6 / 3.0)
        assert assessment.evidence_strength == pytest.approx(0.8 / 3.0)
        assert assessment.sample_size == 3
        assert assessment.historical_consistency == pytest.approx(0.5)
        assert assessment.uncertainty == pytest.approx(0.5)
        assert assessment.limitations == []

    def test_assessment_passes_probability_validator(self):
        items = [
            make_item(source_id="b1", direction=ProbabilityOutcome.BULLISH, confidence=0.8, weight=0.5),
            make_item(source_id="b2", direction=ProbabilityOutcome.BEARISH, confidence=0.6, weight=0.5),
            make_item(source_id="n1", direction=ProbabilityOutcome.NEUTRAL, confidence=0.2, weight=0.5),
        ]
        assessment = ProbabilityCalculator().compute(
            decision_context_id="ctx_1",
            evidence_collection_id="coll_1",
            items=items,
        )
        assert ProbabilityValidator().validate(assessment) == []

    def test_zero_weight_falls_back_to_uniform(self):
        items = [
            make_item(source_id="n1", direction=ProbabilityOutcome.NEUTRAL, confidence=0.0, weight=0.5),
            make_item(source_id="n2", direction=ProbabilityOutcome.NEUTRAL, confidence=0.0, weight=0.5),
        ]
        assessment = ProbabilityCalculator().compute(
            decision_context_id="ctx_1",
            evidence_collection_id="coll_1",
            items=items,
        )
        assert assessment.bullish_probability == pytest.approx(1.0 / 3.0)
        assert assessment.bearish_probability == pytest.approx(1.0 / 3.0)
        assert assessment.neutral_probability == pytest.approx(1.0 / 3.0)
        assert any("zero effective weight" in note for note in assessment.limitations)

    def test_calculate_from_collection_is_deterministic(self):
        collection = EvidenceAggregator().aggregate(make_context())
        calc = ProbabilityCalculator()
        a1 = calc.calculate(collection)
        a2 = calc.calculate(collection)
        assert a1.assessment_hash == a2.assessment_hash
        assert a1.sample_size == 9


# =============================================================================
# H. compute_evidence_score
# =============================================================================


class TestComputeEvidenceScore:
    def test_directional_aggregation_and_source_scores(self):
        items = [
            make_item(source_id="m1", direction=ProbabilityOutcome.BULLISH, strength=1.0, weight=1.0, confidence=0.9),
            make_item(source_id="m2", direction=ProbabilityOutcome.BEARISH, strength=1.0, weight=1.0, confidence=0.8),
            make_item(
                source=EvidenceSource.EXPERIMENT,
                source_id="e1",
                direction=ProbabilityOutcome.BULLISH,
                strength=0.5,
                weight=1.0,
                confidence=0.6,
            ),
        ]
        score = compute_evidence_score("ctx_1", items, WeightConfiguration())
        # MM weight 0.25: 0.25 bullish + 0.25 bearish; EXP weight 0.20: 0.10 bullish
        assert score.bullish_score == pytest.approx(1.0)
        assert score.bearish_score == pytest.approx(0.25 / 0.35)
        assert score.neutral_score == pytest.approx(0.0)
        assert score.total_score == pytest.approx(0.10)
        assert score.market_memory_score == pytest.approx(0.25)
        assert score.historical_score == pytest.approx(0.25)
        assert score.experiment_score == pytest.approx(0.10)
        assert score.macro_score == pytest.approx(0.0)
        assert score.validation_score == pytest.approx(0.0)
        assert score.quant_score == pytest.approx(0.0)
        assert score.confidence_score == pytest.approx((0.9 + 0.6) / 2.0)
        assert score.uncertainty_score == pytest.approx(0.0)
        assert score.evidence_count == 3
        assert all(type(i) is contracts.EvidenceItem for i in score.evidence_items)

    def test_score_is_deterministic(self):
        items = [
            make_item(source_id="m1", direction=ProbabilityOutcome.BULLISH, strength=1.0, weight=1.0, confidence=0.9),
            make_item(
                source=EvidenceSource.VALIDATION,
                source_id="v1",
                direction=ProbabilityOutcome.BEARISH,
                strength=0.8,
                weight=1.0,
                confidence=0.7,
            ),
        ]
        s1 = compute_evidence_score("ctx_1", items, WeightConfiguration())
        s2 = compute_evidence_score("ctx_1", items, WeightConfiguration())
        assert s1.score_hash == s2.score_hash
        assert s1.id == s2.id
        assert s1 == s2

    def test_empty_items_yield_max_uncertainty(self):
        score = compute_evidence_score("ctx_1", [], WeightConfiguration())
        assert score.evidence_count == 0
        assert score.uncertainty_score == pytest.approx(1.0)
        assert score.total_score == pytest.approx(0.0)

    def test_all_sources_score_via_aggregator_pipeline(self, full_collection):
        score = compute_evidence_score(
            "ctx_1", full_collection.items, WeightConfiguration()
        )
        assert score.evidence_count == 9
        assert EvidenceScore.from_dict(score.to_dict()) == score


# =============================================================================
# I. No Legacy Attribute Access (static check)
# =============================================================================


class TestNoLegacyAttributeAccess:
    """decision_engine evidence/probability/score must not use retired
    EvidenceItem fields or the wrong direction enum."""

    LEGACY_PATTERNS = [
        r"\.reference_id\b",
        r"\.item_hash\b",
        r"\.metadata\b",
        r"\.title\b",
        r"ProbabilityDirection",
    ]

    @pytest.mark.parametrize(
        "module_name",
        ["evidence.py", "probability.py", "score.py"],
    )
    def test_no_legacy_references(self, module_name):
        module_path = Path(contracts.__file__).parent / module_name
        source = module_path.read_text(encoding="utf-8")
        for pattern in self.LEGACY_PATTERNS:
            assert re.search(pattern, source) is None, (
                f"{module_name} contains legacy pattern {pattern!r}"
            )
