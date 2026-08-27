"""
Targeted tests for the decision_engine reasoner and report layers.

These tests EXECUTE the previously untested code paths:
    - DecisionReasoner.reason()
    - generate_decision_report()

Covers (per repair spec):
    1.  DecisionReasoner construction
    2.  reason() executes with a realistic canonical DecisionContext
    3.  no nonexistent DecisionContext fields are accessed (static audit)
    4.  canonical probability fields are consumed
    5.  historical consistency path
    6.  EvidenceScore is consumed correctly
    7.  DecisionReport generation executes
    8.  report serialization round-trip
    9.  no fabricated fields
    10. determinism
    11. missing optional evidence handled explicitly
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from researchos.decision_engine import contracts
from researchos.decision_engine import evidence as evidence_module
from researchos.decision_engine.context import DecisionContext
from researchos.decision_engine.contracts import (
    EvidenceSource,
    ProbabilityOutcome,
    WeightConfiguration,
)
from researchos.decision_engine.evidence import EvidenceAggregator
from researchos.decision_engine.probability import (
    ProbabilityCalculator,
    ProbabilityValidator,
)
from researchos.decision_engine.reasoner import DecisionReasoner, ReasoningStep
from researchos.decision_engine.report import DecisionReport, generate_decision_report
from researchos.decision_engine.score import compute_evidence_score

FIXED_TS = datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)


# =============================================================================
# Helpers
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
        ontology_tags=["gold", "decision_engine"],
    )
    params.update(overrides)
    return DecisionContext(**params)


def make_empty_context() -> DecisionContext:
    return make_context(
        market_snapshot_id="",
        market_regime_id="",
        macro_state_id="",
        historical_scenario_ids=[],
        experiment_result_ids=[],
        validation_ids=[],
        research_ids=[],
        market_memory_report_ids=[],
        simulation_result_ids=[],
        ontology_tags=[],
    )


def make_item(
    source: EvidenceSource = EvidenceSource.MARKET_MEMORY,
    source_id: str = "hist_001",
    direction: ProbabilityOutcome = ProbabilityOutcome.BULLISH,
    strength: float = 0.6,
    weight: float = 0.25,
    confidence: float = 0.7,
    description: str = "test evidence",
):
    from researchos.decision_engine.contracts import DecisionEvidenceItem

    return DecisionEvidenceItem(
        source=source,
        source_id=source_id,
        direction=direction,
        strength=strength,
        weight=weight,
        confidence=confidence,
        description=description,
        supporting_ids=[source_id],
    )


def build_pipeline(context: DecisionContext, items=None):
    """Run aggregator -> score -> probability for the given context."""
    if items is None:
        items = EvidenceAggregator().aggregate(context).items
    score = compute_evidence_score(context.id, items, WeightConfiguration())
    probability = ProbabilityCalculator().compute(
        decision_context_id=context.id,
        evidence_collection_id="coll_test",
        items=items,
        timestamp=FIXED_TS,
    )
    return score, probability


# =============================================================================
# Evidence regression guard (must stay canonical)
# =============================================================================


class TestEvidenceRegressionGuard:
    def test_canonical_identity_preserved(self):
        assert contracts.EvidenceSource is evidence_module.EvidenceSource
        assert contracts.DecisionEvidenceItem is evidence_module.DecisionEvidenceItem


# =============================================================================
# 1-2. Construction and execution
# =============================================================================


class TestDecisionReasonerExecution:
    def test_reasoner_constructible(self):
        reasoner = DecisionReasoner()
        assert reasoner.reasoning_version == "REASON_V1"

    def test_reason_executes_with_full_context(self):
        context = make_context()
        score, probability = build_pipeline(context)
        steps = DecisionReasoner().reason(context, score, probability)
        assert len(steps) == 11
        assert [s.order for s in steps] == list(range(1, 12))
        assert all(isinstance(s, ReasoningStep) for s in steps)
        assert all(s.description for s in steps)

    def test_reason_executes_with_empty_context(self):
        context = make_empty_context()
        score, probability = build_pipeline(context)
        steps = DecisionReasoner().reason(context, score, probability)
        assert len(steps) == 11


# =============================================================================
# 3. Static contract audit — no nonexistent attribute access
# =============================================================================


class TestStaticContractAudit:
    BROKEN_PATTERNS = [
        r"context\.historical_match_data\b",
        r"context\.historical_matches\b",
        r"context\.regime_name\b",
        r"context\.quant_summary_id\b",
        r"context\.quant_statistics\b",
        r"context\.weight_config\b",
        r"context\.tags\b",
        r"context\.macro_state_data\b",
        r"context\.experiment_ids\b",
        r"context\.timestamp\b",
        r"context\.evidence_version\b",
        r"probability\.historical_support\b",
    ]

    @pytest.mark.parametrize("module_name", ["reasoner.py", "report.py"])
    def test_no_broken_attribute_access(self, module_name):
        module_path = Path(contracts.__file__).parent / module_name
        source = module_path.read_text(encoding="utf-8")
        for pattern in self.BROKEN_PATTERNS:
            assert re.search(pattern, source) is None, f"{module_name} contains broken attribute pattern {pattern!r}"


# =============================================================================
# 4-5. Canonical probability fields / historical consistency
# =============================================================================


class TestProbabilityContractConsumption:
    def test_step10_consumes_canonical_probability_fields(self):
        context = make_context()
        items = [
            make_item(source_id="b1", direction=ProbabilityOutcome.BULLISH, confidence=0.8, weight=0.5),
            make_item(source_id="b2", direction=ProbabilityOutcome.BEARISH, confidence=0.6, weight=0.5),
            make_item(source_id="n1", direction=ProbabilityOutcome.NEUTRAL, confidence=0.2, weight=0.5),
        ]
        score, probability = build_pipeline(context, items=items)
        steps = DecisionReasoner().reason(context, score, probability)
        step10 = steps[9]
        assert step10.rule == "ProbabilityCalculation"
        details = step10.details
        assert details["bullish_probability"] == pytest.approx(probability.bullish_probability)
        assert details["bearish_probability"] == pytest.approx(probability.bearish_probability)
        assert details["neutral_probability"] == pytest.approx(probability.neutral_probability)
        assert details["confidence"] == pytest.approx(probability.confidence)
        assert details["uncertainty"] == pytest.approx(probability.uncertainty)
        assert details["sample_size"] == probability.sample_size
        assert details["calculation_method"] == probability.calculation_method.value
        assert details["calculation_version"] == probability.calculation_version
        assert "historical_support" not in details

    def test_historical_consistency_path(self):
        context = make_context()
        items = [
            make_item(source_id="b1", direction=ProbabilityOutcome.BULLISH, confidence=0.8, weight=0.5),
            make_item(source_id="b2", direction=ProbabilityOutcome.BEARISH, confidence=0.6, weight=0.5),
            make_item(source_id="n1", direction=ProbabilityOutcome.NEUTRAL, confidence=0.2, weight=0.5),
        ]
        _, probability = build_pipeline(context, items=items)
        # contributions 0.4 / 0.3 / 0.1 -> max probability = 0.5
        assert probability.historical_consistency == pytest.approx(0.5)
        steps = DecisionReasoner().reason(context, *build_pipeline(context, items=items))
        assert steps[9].details["historical_consistency"] == pytest.approx(0.5)
        assert ProbabilityValidator().is_valid(probability) is True


# =============================================================================
# 6. EvidenceScore consumption
# =============================================================================


class TestEvidenceScoreConsumption:
    def test_step1_source_counts_match_score_items(self):
        context = make_context()
        score, probability = build_pipeline(context)
        steps = DecisionReasoner().reason(context, score, probability)
        step1 = steps[0]
        counts = {}
        for item in score.evidence_items:
            counts[item.source.value] = counts.get(item.source.value, 0) + 1
        assert step1.details["source_counts"] == counts
        assert step1.details["total_evidence"] == score.evidence_count
        assert "evidence_version" not in step1.details

    def test_step2_direction_breakdown(self):
        context = make_context()
        items = [
            make_item(source_id="b1", direction=ProbabilityOutcome.BULLISH),
            make_item(source_id="b2", direction=ProbabilityOutcome.BULLISH),
            make_item(source_id="x1", direction=ProbabilityOutcome.BEARISH),
            make_item(source_id="n1", direction=ProbabilityOutcome.NEUTRAL),
        ]
        score, probability = build_pipeline(context, items=items)
        steps = DecisionReasoner().reason(context, score, probability)
        details = steps[1].details
        assert details["bullish_count"] == 2
        assert details["bearish_count"] == 1
        assert details["neutral_count"] == 1
        assert details["bullish_score"] == pytest.approx(score.bullish_score)

    def test_step3_collects_supporting_ids(self):
        context = make_context()
        score, probability = build_pipeline(context)
        steps = DecisionReasoner().reason(context, score, probability)
        step3 = steps[2]
        assert step3.rule == "MarketMemoryEvidence"
        assert step3.details["match_count"] == 2
        assert step3.details["scenario_ids"] == ["hist_001", "hist_002", "mmr_001"]
        assert step3.inputs == ["hist_001", "hist_002"]


# =============================================================================
# 7. DecisionReport generation
# =============================================================================


class TestDecisionReportGeneration:
    def test_generate_decision_report_executes(self):
        context = make_context()
        score, probability = build_pipeline(context)
        report = generate_decision_report(context, score, probability)
        assert isinstance(report, DecisionReport)
        assert report.asset == "XAUUSD"
        assert report.timeframe == "1h"
        assert report.decision_timestamp == FIXED_TS
        assert report.context_id == context.id
        assert report.score_id == score.id
        assert report.probability_id == probability.id
        assert report.bullish_probability == pytest.approx(probability.bullish_probability)
        assert report.confidence == pytest.approx(probability.confidence)
        assert len(report.reasoning_steps) == 11
        assert "Total evidence: 9 items" in report.evidence_summary

    def test_report_references_derived_from_canonical_context(self):
        context = make_context()
        score, probability = build_pipeline(context)
        report = generate_decision_report(context, score, probability)
        assert report.historical_scenarios == ["hist_001", "hist_002"]
        assert report.experiment_ids == ["exp_001"]
        assert report.supporting_evidence == sorted({item.source_id for item in score.evidence_items})
        assert report.macro_factors == [
            {"indicator": "macro_state_id", "value": "macro_001", "impact": "considered"},
            {"indicator": "market_regime_id", "value": "regime_001", "impact": "considered"},
        ]

    def test_report_versions_and_tags_from_canonical_sources(self):
        context = make_context()
        score, probability = build_pipeline(context)
        report = generate_decision_report(context, score, probability)
        assert report.scoring_version == score.scoring_version
        assert report.probability_version == probability.calculation_version
        assert report.calculation_method == probability.calculation_method
        assert report.tags == context.ontology_tags
        assert report.limitations == probability.limitations

    def test_report_serialization_round_trip(self):
        context = make_context()
        score, probability = build_pipeline(context)
        report = generate_decision_report(context, score, probability)
        restored = DecisionReport.from_dict(report.to_dict())
        assert isinstance(restored, DecisionReport)
        assert restored.compute_hash() == report.compute_hash()
        assert restored == report
        assert restored.summary == report.summary
        assert len(restored.reasoning_steps) == 11
        assert restored.reasoning_steps[0].to_dict() == report.reasoning_steps[0].to_dict()


# =============================================================================
# 9. No fabricated fields
# =============================================================================


class TestNoFabricatedFields:
    def test_empty_context_report_has_no_fabricated_references(self):
        context = make_empty_context()
        score, probability = build_pipeline(context)
        report = generate_decision_report(context, score, probability)
        assert report.macro_factors == []
        assert report.historical_scenarios == []
        assert report.experiment_ids == []
        assert report.supporting_evidence == []

    def test_missing_evidence_reported_explicitly_as_risk_factors(self):
        context = make_empty_context()
        score, probability = build_pipeline(context)
        report = generate_decision_report(context, score, probability)
        assert "No historical scenario matches available" in report.risk_factors
        assert any("Insufficient evidence volume" in r for r in report.risk_factors)
        assert "No evidence items available for probability assessment" in report.limitations


# =============================================================================
# 10. Determinism
# =============================================================================


class TestDeterminism:
    def test_reason_is_deterministic(self):
        context = make_context()
        score, probability = build_pipeline(context)
        reasoner = DecisionReasoner()
        steps1 = reasoner.reason(context, score, probability)
        steps2 = reasoner.reason(context, score, probability)
        assert [s.to_dict() for s in steps1] == [s.to_dict() for s in steps2]

    def test_report_is_deterministic(self):
        context = make_context()
        score, probability = build_pipeline(context)
        report1 = generate_decision_report(context, score, probability)
        report2 = generate_decision_report(context, score, probability)
        assert report1.report_hash == report2.report_hash
        assert report1.compute_hash() == report2.compute_hash()
        assert report1 == report2
        assert report1.id == report2.id

    def test_supporting_evidence_order_deterministic(self):
        context = make_context()
        score, probability = build_pipeline(context)
        report = generate_decision_report(context, score, probability)
        assert report.supporting_evidence == sorted(report.supporting_evidence)


# =============================================================================
# 11. Missing optional evidence end-to-end
# =============================================================================


class TestMissingOptionalEvidencePipeline:
    def test_empty_context_full_pipeline_executes(self):
        context = make_empty_context()
        collection = EvidenceAggregator().aggregate(context)
        assert collection.total_items == 0
        score = compute_evidence_score(context.id, collection.items, WeightConfiguration())
        probability = ProbabilityCalculator().calculate(collection)
        steps = DecisionReasoner().reason(context, score, probability)
        report = generate_decision_report(context, score, probability)
        assert len(steps) == 11
        assert "0 evidence items" in report.summary

    def test_partial_context_pipeline_executes(self):
        context = make_context(
            macro_state_id="",
            market_regime_id="",
            validation_ids=[],
            research_ids=[],
        )
        collection = EvidenceAggregator().aggregate(context)
        assert collection.total_items == 5
        score = compute_evidence_score(context.id, collection.items, WeightConfiguration())
        probability = ProbabilityCalculator().calculate(collection)
        report = generate_decision_report(context, score, probability)
        assert report.macro_factors == []
        assert len(report.reasoning_steps) == 11
