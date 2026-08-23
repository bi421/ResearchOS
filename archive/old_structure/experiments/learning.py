"""
LearningRecord — extract actionable lessons from validated experiments.

Purpose:
    LearningRecord captures the insights and lessons learned from validated
    experiments. This is the final step in the experiment workflow:
    Validation → Learning. Lessons feed back into the knowledge base to
    improve future research.

Based on Article XVII: Object Model — Experiment Layer.
Based on Article XIII: Knowledge Engine.

Guarantees:
    - Deterministic: Same validation → same learning record
    - Auditable: Full lifecycle tracking
    - Repeatable: Complete trace of how lessons were derived
"""

from __future__ import annotations

from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage


class LearningRecord(BaseObject):
    """
    Actionable insights extracted from validated experiments.

    A LearningRecord captures what was learned from an experiment:
    whether the hypothesis was confirmed or rejected, what patterns
    were observed, and what recommendations can be made for future
    research.

    Attributes:
        experiment_id: Link to the Experiment.
        run_id: Link to the specific ExperimentRun (optional).
        validation_id: Link to the ExperimentValidation.
        hypothesis_id: Link to the QuantHypothesis.
        hypothesis_accepted: Whether the hypothesis was accepted.
        findings: Key findings from the experiment.
        patterns_observed: Patterns identified in the results.
        recommendations: Actionable recommendations.
        confidence: Confidence in the learning (0.0-1.0).
        learning_trace: How this learning was derived.
        tags: Tags for categorisation.
    """

    def __init__(
        self,
        experiment_id: str,
        validation_id: str,
        hypothesis_id: str,
        run_id: str | None = None,
        hypothesis_accepted: bool | None = None,
        findings: list[str] | None = None,
        patterns_observed: list[str] | None = None,
        recommendations: list[str] | None = None,
        confidence: float = 0.0,
        learning_trace: str = "",
        tags: list[str] | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"LearningRecord|{experiment_id}|{validation_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.experiment_id = experiment_id
        self.validation_id = validation_id
        self.hypothesis_id = hypothesis_id
        self.run_id = run_id
        self.hypothesis_accepted = hypothesis_accepted
        self.findings: list[str] = findings or []
        self.patterns_observed: list[str] = patterns_observed or []
        self.recommendations: list[str] = recommendations or []
        self.confidence = confidence
        self.learning_trace = learning_trace
        self.tags: list[str] = tags or []

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason="Learning record created",
        )

    def add_finding(self, finding: str) -> None:
        """Add a finding to the learning record."""
        self.findings.append(finding)
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Finding added: {finding[:50]}...",
        )

    def add_pattern(self, pattern: str) -> None:
        """Add an observed pattern."""
        self.patterns_observed.append(pattern)

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        self.recommendations.append(recommendation)

    def finalize(self) -> None:
        """Mark this learning record as complete."""
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Learning record finalized: {len(self.findings)} findings, {len(self.recommendations)} recommendations",
        )

    def _to_hashable_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "validation_id": self.validation_id,
            "hypothesis_id": self.hypothesis_id,
            "run_id": self.run_id or "",
            "hypothesis_accepted": self.hypothesis_accepted,
            "findings": sorted(self.findings),
            "patterns_observed": sorted(self.patterns_observed),
            "recommendations": sorted(self.recommendations),
            "confidence": self.confidence,
            "learning_trace": self.learning_trace,
            "tags": sorted(self.tags),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "experiment_id": self.experiment_id,
                "validation_id": self.validation_id,
                "hypothesis_id": self.hypothesis_id,
                "run_id": self.run_id,
                "hypothesis_accepted": self.hypothesis_accepted,
                "findings": self.findings,
                "patterns_observed": self.patterns_observed,
                "recommendations": self.recommendations,
                "confidence": self.confidence,
                "learning_trace": self.learning_trace,
                "tags": self.tags,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningRecord:
        obj = super().from_dict(data)
        obj.experiment_id = data["experiment_id"]
        obj.validation_id = data["validation_id"]
        obj.hypothesis_id = data["hypothesis_id"]
        obj.run_id = data.get("run_id")
        obj.hypothesis_accepted = data.get("hypothesis_accepted")
        obj.findings = list(data.get("findings", []))
        obj.patterns_observed = list(data.get("patterns_observed", []))
        obj.recommendations = list(data.get("recommendations", []))
        obj.confidence = float(data.get("confidence", 0.0))
        obj.learning_trace = data.get("learning_trace", "")
        obj.tags = list(data.get("tags", []))
        return obj
