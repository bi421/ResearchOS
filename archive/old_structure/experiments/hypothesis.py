"""
QuantHypothesis — a testable prediction for quantitative research.

Purpose:
    QuantHypothesis is a purpose-built hypothesis for testing against
    historical market data. Unlike the research-level Hypothesis object
    (which is narrative-driven), QuantHypothesis is statistically defined
    with null/alternative formulations, significance levels, and metric
    expectations.

Based on Article XVII: Object Model — Experiment Layer.
Based on Article XVI: Scientific Reasoning Framework — Hypothesis Layer.

Guarantees:
    - Deterministic: Same inputs → same ID and hash
    - Auditable: Full lifecycle tracking
    - Repeatable: Complete parameter capture
"""

from __future__ import annotations

from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.experiments.contracts import HypothesisStatus, MetricDefinition


class QuantHypothesis(BaseObject):
    """
    A testable prediction formulated for quantitative validation.

    QuantHypothesis represents a specific, measurable prediction about
    market behavior that can be tested against historical data. It is a
    statistically rigorous formulation distinct from the narrative-driven
    Hypothesis used in the research cycle.

    Attributes:
        research_question: The high-level question this hypothesis addresses.
        null_hypothesis: The null hypothesis (H0) — the default position.
        alternative_hypothesis: The alternative hypothesis (H1) — the claim.
        hypothesis_type: Directional, Non-directional, or Equality.
        significance_level: Alpha level for statistical tests (e.g., 0.05).
        expected_effect: Expected effect size or direction.
        parameters: Dict of parameters that define the hypothesis.
        metric_definitions: Metrics that will be used to test this hypothesis.
        status: Current lifecycle status (Formulated → Ready → Tested → Accepted/Rejected).
        tags: Tags for categorisation and search.
        hypothesis_trace: How this hypothesis was derived.
    """

    def __init__(
        self,
        research_question: str,
        null_hypothesis: str,
        alternative_hypothesis: str,
        hypothesis_type: str = "Directional",
        significance_level: float = 0.05,
        expected_effect: float | None = None,
        parameters: dict[str, Any] | None = None,
        metric_definitions: list[MetricDefinition] | None = None,
        tags: list[str] | None = None,
        hypothesis_trace: str = "",
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"QuantHypothesis|{research_question}|{null_hypothesis}|{alternative_hypothesis}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_question = research_question
        self.null_hypothesis = null_hypothesis
        self.alternative_hypothesis = alternative_hypothesis
        self.hypothesis_type = hypothesis_type
        self.significance_level = significance_level
        self.expected_effect = expected_effect
        self.parameters: dict[str, Any] = parameters or {}
        self.metric_definitions: list[MetricDefinition] = metric_definitions or []
        self.tags: list[str] = tags or []
        self.hypothesis_trace = hypothesis_trace
        self.status = HypothesisStatus.FORMULATED

        self.lifecycle.transition(
            LifecycleStage.ACTIVE,
            reason="QuantHypothesis formulated",
        )

    def mark_ready(self) -> None:
        """Mark this hypothesis as ready for testing."""
        self.status = HypothesisStatus.READY
        self.lifecycle.transition(
            LifecycleStage.ACTIVE,
            reason="QuantHypothesis marked ready for testing",
        )

    def mark_accepted(self, reason: str = "") -> None:
        """Mark this hypothesis as accepted (failed to reject H0 or confirmed H1)."""
        self.status = HypothesisStatus.ACCEPTED
        self.lifecycle.transition(
            LifecycleStage.VALIDATED,
            reason=f"QuantHypothesis accepted: {reason}" if reason else "QuantHypothesis accepted",
        )

    def mark_rejected(self, reason: str = "") -> None:
        """Mark this hypothesis as rejected."""
        self.status = HypothesisStatus.REJECTED
        self.lifecycle.transition(
            LifecycleStage.INVALIDATED,
            reason=f"QuantHypothesis rejected: {reason}" if reason else "QuantHypothesis rejected",
        )

    def mark_inconclusive(self, reason: str = "") -> None:
        """Mark this hypothesis as inconclusive."""
        self.status = HypothesisStatus.INCONCLUSIVE
        self.lifecycle.transition(
            LifecycleStage.ANALYZED,
            reason=f"QuantHypothesis inconclusive: {reason}" if reason else "QuantHypothesis inconclusive",
        )

    def _to_hashable_dict(self) -> dict[str, Any]:
        return {
            "research_question": self.research_question,
            "null_hypothesis": self.null_hypothesis,
            "alternative_hypothesis": self.alternative_hypothesis,
            "hypothesis_type": self.hypothesis_type,
            "significance_level": self.significance_level,
            "expected_effect": self.expected_effect,
            "parameters": dict(sorted(self.parameters.items())) if self.parameters else {},
            "metric_definitions": sorted(
                [m.to_dict() for m in self.metric_definitions],
                key=lambda x: x["name"],
            ),
            "tags": sorted(self.tags),
            "hypothesis_trace": self.hypothesis_trace,
            "status": self.status.value,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "research_question": self.research_question,
                "null_hypothesis": self.null_hypothesis,
                "alternative_hypothesis": self.alternative_hypothesis,
                "hypothesis_type": self.hypothesis_type,
                "significance_level": self.significance_level,
                "expected_effect": self.expected_effect,
                "parameters": self.parameters,
                "metric_definitions": [m.to_dict() for m in self.metric_definitions],
                "tags": self.tags,
                "hypothesis_trace": self.hypothesis_trace,
                "status": self.status.value,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuantHypothesis:
        obj = super().from_dict(data)
        obj.research_question = data["research_question"]
        obj.null_hypothesis = data["null_hypothesis"]
        obj.alternative_hypothesis = data["alternative_hypothesis"]
        obj.hypothesis_type = data.get("hypothesis_type", "Directional")
        obj.significance_level = float(data.get("significance_level", 0.05))
        obj.expected_effect = data.get("expected_effect")
        obj.parameters = dict(data.get("parameters", {}))
        obj.metric_definitions = [MetricDefinition.from_dict(m) for m in data.get("metric_definitions", [])]
        obj.tags = list(data.get("tags", []))
        obj.hypothesis_trace = data.get("hypothesis_trace", "")
        obj.status = HypothesisStatus(data.get("status", "Formulated"))
        return obj
