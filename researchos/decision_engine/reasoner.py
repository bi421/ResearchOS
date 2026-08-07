"""
DecisionReasoner — deterministic reasoning that produces explainable decisions.

Based on Article XVII: Object Model — Decision Engine Layer.

Purpose:
    Takes the DecisionContext, EvidenceScore, and ProbabilityAssessment
    and produces structured reasoning that explains:
        - Why this probability was produced
        - What evidence supported it
        - Which evidence contradicted it
        - What reduced confidence
        - Which historical scenarios contributed
        - Which experiments contributed
        - Which macro factors contributed

    The reasoning is recorded as a ReasoningChain for auditability.

Design:
    DecisionReasoner is a stateless service. All state is in the
    inputs passed to it. Output is a fully explainable reasoning
    trace that can be included in the DecisionReport.

Pipeline:
    DecisionContext → EvidenceAggregator → EvidenceScore →
    ProbabilityAssessment → DecisionReasoner → DecisionReport
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from researchos.decision_engine.contracts import (
    EvidenceSource,
    ProbabilityOutcome,
)
from researchos.decision_engine.context import DecisionContext
from researchos.decision_engine.score import EvidenceScore
from researchos.decision_engine.probability import ProbabilityAssessment


class ReasoningStep:
    """
    A single step in the reasoning chain.

    Each step documents one inference made during decision reasoning.

    Attributes:
        order: Step order in the chain.
        description: Human-readable description of this reasoning step.
        inputs: Input IDs used in this step.
        outputs: Output IDs produced by this step.
        rule: The reasoning rule applied.
        details: Additional structured details.
    """

    def __init__(
        self,
        order: int,
        description: str,
        inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        rule: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.order = order
        self.description = description
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.rule = rule
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "rule": self.rule,
            "details": self.details,
        }


class DecisionReasoner:
    """
    Produces explainable reasoning traces from decision pipeline outputs.

    This is a stateless service. It takes the pipeline outputs and
    produces a structured reasoning chain that explains every aspect
    of the decision.

    Args:
        reasoning_version: Version identifier for reasoning methodology.
    """

    def __init__(self, reasoning_version: str = "REASON_V1"):
        self.reasoning_version = reasoning_version

    def reason(
        self,
        context: DecisionContext,
        score: EvidenceScore,
        probability: ProbabilityAssessment,
    ) -> List[ReasoningStep]:
        """
        Produce a full reasoning chain from pipeline outputs.

        Args:
            context: The original decision context.
            score: The computed evidence score.
            probability: The computed probability assessment.

        Returns:
            Ordered list of ReasoningStep objects forming the reasoning chain.
        """
        steps: List[ReasoningStep] = []

        # Step 1: Evidence collection summary
        steps.append(self._step_evidence_summary(context, score))

        # Step 2: Evidence direction breakdown
        steps.append(self._step_direction_breakdown(score))

        # Step 3: Market memory contribution
        steps.append(self._step_market_memory(context, score))

        # Step 4: Experiment contribution
        steps.append(self._step_experiments(context, score))

        # Step 5: Macro intelligence contribution
        steps.append(self._step_macro(context, score))

        # Step 6: Validation contribution
        steps.append(self._step_validation(context, score))

        # Step 7: Quant engine contribution
        steps.append(self._step_quant_engine(context, score))

        # Step 8: Confidence assessment
        steps.append(self._step_confidence(score))

        # Step 9: Uncertainty assessment
        steps.append(self._step_uncertainty(score))

        # Step 10: Probability calculation
        steps.append(self._step_probability_calculation(score, probability))

        # Step 11: Limitations
        steps.append(self._step_limitations(probability))

        return steps

    def _step_evidence_summary(
        self, context: DecisionContext, score: EvidenceScore
    ) -> ReasoningStep:
        """Step 1: Evidence collection summary."""
        source_counts: Dict[str, int] = {}
        for item in score.evidence_items:
            src = item.source.value
            source_counts[src] = source_counts.get(src, 0) + 1

        return ReasoningStep(
            order=1,
            description=(
                f"Collected {score.evidence_count} evidence items from "
                f"{len(source_counts)} sources: "
                + ", ".join(f"{k}={v}" for k, v in sorted(source_counts.items()))
            ),
            inputs=[context.id],
            outputs=[score.id],
            rule="EvidenceCollection",
            details={
                "total_evidence": score.evidence_count,
                "source_counts": source_counts,
                "evidence_version": context.evidence_version,
            },
        )

    def _step_direction_breakdown(self, score: EvidenceScore) -> ReasoningStep:
        """Step 2: Evidence direction breakdown."""
        bullish_items = sum(
            1 for e in score.evidence_items if e.direction == ProbabilityOutcome.BULLISH
        )
        bearish_items = sum(
            1 for e in score.evidence_items if e.direction == ProbabilityOutcome.BEARISH
        )
        neutral_items = sum(
            1 for e in score.evidence_items if e.direction == ProbabilityOutcome.NEUTRAL
        )

        return ReasoningStep(
            order=2,
            description=(
                f"Evidence direction breakdown: "
                f"Bullish={bullish_items}, Bearish={bearish_items}, Neutral={neutral_items}. "
                f"Scores: B={score.bullish_score:.4f}, Be={score.bearish_score:.4f}, "
                f"N={score.neutral_score:.4f}"
            ),
            inputs=[score.id],
            outputs=[],
            rule="DirectionBreakdown",
            details={
                "bullish_count": bullish_items,
                "bearish_count": bearish_items,
                "neutral_count": neutral_items,
                "bullish_score": score.bullish_score,
                "bearish_score": score.bearish_score,
                "neutral_score": score.neutral_score,
                "total_score": score.total_score,
            },
        )

    def _step_market_memory(
        self, context: DecisionContext, score: EvidenceScore
    ) -> ReasoningStep:
        """Step 3: Market memory contribution."""
        mm_items = [
            e for e in score.evidence_items
            if e.source == EvidenceSource.MARKET_MEMORY
        ]
        match_count = len(context.historical_match_data)

        scenario_ids = []
        for item in mm_items:
            scenario_ids.extend(item.supporting_ids)

        return ReasoningStep(
            order=3,
            description=(
                f"Market Memory contribution: {len(mm_items)} evidence items "
                f"from {match_count} historical matches. "
                f"Score={score.market_memory_score:.4f}"
            ),
            inputs=context.historical_matches,
            outputs=[],
            rule="MarketMemoryEvidence",
            details={
                "evidence_count": len(mm_items),
                "match_count": match_count,
                "market_memory_score": score.market_memory_score,
                "historical_score": score.historical_score,
                "scenario_ids": scenario_ids[:10],
            },
        )

    def _step_experiments(
        self, context: DecisionContext, score: EvidenceScore
    ) -> ReasoningStep:
        """Step 4: Experiment contribution."""
        exp_items = [
            e for e in score.evidence_items
            if e.source == EvidenceSource.EXPERIMENT
        ]

        return ReasoningStep(
            order=4,
            description=(
                f"Experiment contribution: {len(exp_items)} experiment results. "
                f"Score={score.experiment_score:.4f}"
            ),
            inputs=context.experiment_ids,
            outputs=[],
            rule="ExperimentEvidence",
            details={
                "evidence_count": len(exp_items),
                "experiment_score": score.experiment_score,
                "experiment_ids": context.experiment_ids,
            },
        )

    def _step_macro(
        self, context: DecisionContext, score: EvidenceScore
    ) -> ReasoningStep:
        """Step 5: Macro intelligence contribution."""
        macro_items = [
            e for e in score.evidence_items
            if e.source == EvidenceSource.MACRO_INTELLIGENCE
        ]

        return ReasoningStep(
            order=5,
            description=(
                f"Macro Intelligence contribution: {len(macro_items)} items. "
                f"Regime={context.regime_name}, Score={score.macro_score:.4f}"
            ),
            inputs=[context.macro_state_id] if context.macro_state_id else [],
            outputs=[],
            rule="MacroEvidence",
            details={
                "evidence_count": len(macro_items),
                "macro_score": score.macro_score,
                "regime": context.regime_name,
                "macro_state_id": context.macro_state_id,
            },
        )

    def _step_validation(
        self, context: DecisionContext, score: EvidenceScore
    ) -> ReasoningStep:
        """Step 6: Validation contribution."""
        val_items = [
            e for e in score.evidence_items
            if e.source == EvidenceSource.VALIDATION
        ]

        return ReasoningStep(
            order=6,
            description=(
                f"Validation contribution: {len(val_items)} validation results. "
                f"Score={score.validation_score:.4f}"
            ),
            inputs=context.validation_ids,
            outputs=[],
            rule="ValidationEvidence",
            details={
                "evidence_count": len(val_items),
                "validation_score": score.validation_score,
                "validation_ids": context.validation_ids,
            },
        )

    def _step_quant_engine(
        self, context: DecisionContext, score: EvidenceScore
    ) -> ReasoningStep:
        """Step 7: Quant engine contribution."""
        quant_items = [
            e for e in score.evidence_items
            if e.source == EvidenceSource.QUANT_ENGINE
        ]

        return ReasoningStep(
            order=7,
            description=(
                f"Quant Engine contribution: {len(quant_items)} statistical summaries. "
                f"Score={score.quant_score:.4f}"
            ),
            inputs=[context.quant_summary_id] if context.quant_summary_id else [],
            outputs=[],
            rule="QuantEngineEvidence",
            details={
                "evidence_count": len(quant_items),
                "quant_score": score.quant_score,
                "statistics": context.quant_statistics,
            },
        )

    def _step_confidence(self, score: EvidenceScore) -> ReasoningStep:
        """Step 8: Confidence assessment."""
        evidence_confidences = [e.confidence for e in score.evidence_items]
        avg_confidence = (
            sum(evidence_confidences) / len(evidence_confidences)
            if evidence_confidences
            else 0.0
        )

        return ReasoningStep(
            order=8,
            description=(
                f"Confidence assessment: composite={score.confidence_score:.4f}, "
                f"avg_item_confidence={avg_confidence:.4f}. "
                f"Based on {score.evidence_count} items from {len(evidence_confidences)} sources."
            ),
            inputs=[score.id],
            outputs=[],
            rule="ConfidenceAssessment",
            details={
                "composite_confidence": score.confidence_score,
                "average_item_confidence": avg_confidence,
                "evidence_count": score.evidence_count,
                "weighting_version": score.weighting_version,
            },
        )

    def _step_uncertainty(self, score: EvidenceScore) -> ReasoningStep:
        """Step 9: Uncertainty assessment."""
        return ReasoningStep(
            order=9,
            description=(
                f"Uncertainty assessment: uncertainty_score={score.uncertainty_score:.4f}. "
                f"Source disagreement metric."
            ),
            inputs=[score.id],
            outputs=[],
            rule="UncertaintyAssessment",
            details={
                "uncertainty_score": score.uncertainty_score,
                "bullish_score": score.bullish_score,
                "bearish_score": score.bearish_score,
                "neutral_score": score.neutral_score,
            },
        )

    def _step_probability_calculation(
        self, score: EvidenceScore, probability: ProbabilityAssessment
    ) -> ReasoningStep:
        """Step 10: Probability calculation."""
        return ReasoningStep(
            order=10,
            description=(
                f"Probability calculation (v{probability.calculation_version}): "
                f"WeightedEvidence method. "
                f"Bullish={probability.bullish_probability:.2%}, "
                f"Bearish={probability.bearish_probability:.2%}, "
                f"Neutral={probability.neutral_probability:.2%}. "
                f"Sum={probability.bullish_probability + probability.bearish_probability + probability.neutral_probability:.4f}"
            ),
            inputs=[score.id],
            outputs=[probability.id],
            rule="ProbabilityCalculation",
            details={
                "bullish_probability": probability.bullish_probability,
                "bearish_probability": probability.bearish_probability,
                "neutral_probability": probability.neutral_probability,
                "confidence": probability.confidence,
                "uncertainty": probability.uncertainty,
                "sample_size": probability.sample_size,
                "historical_support": probability.historical_support,
                "calculation_method": probability.calculation_method.value,
                "calculation_version": probability.calculation_version,
            },
        )

    def _step_limitations(self, probability: ProbabilityAssessment) -> ReasoningStep:
        """Step 11: Limitations identification."""
        return ReasoningStep(
            order=11,
            description=(
                f"Identified {len(probability.limitations)} limitations: "
                + "; ".join(probability.limitations)
                if probability.limitations
                else "No significant limitations identified."
            ),
            inputs=[probability.id],
            outputs=[],
            rule="LimitationsIdentification",
            details={
                "limitations": probability.limitations,
                "limitation_count": len(probability.limitations),
            },
        )

