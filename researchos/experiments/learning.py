"""
Experiment learning — lessons extracted from validated experiments.

This object belongs to the Experiment layer. It is deliberately distinct
from ``researchos.objects.cognitive.LearningRecord``, which tracks trader
cognitive growth, and from ``researchos.objects.knowledge.Knowledge``, which
is durable semantic market memory.

Boundary:
    Validation → Finding → ExperimentLearningRecord → optional Knowledge certification

The Validation is represented in the evidence graph by a certified Finding.
This object does not certify evidence and does not write durable knowledge by
itself. Those responsibilities belong to the evidence/knowledge boundaries.
"""

from __future__ import annotations

from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage


class ExperimentLearningRecord(BaseObject):
    """Actionable lessons extracted from a validated experiment."""

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
            seed = f"ExperimentLearningRecord|{experiment_id}|{validation_id}"
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
            reason="Experiment learning record created",
        )

    def add_finding(self, finding: str) -> None:
        self.findings.append(finding)
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Finding added: {finding[:50]}...",
        )

    def add_pattern(self, pattern: str) -> None:
        self.patterns_observed.append(pattern)

    def add_recommendation(self, recommendation: str) -> None:
        self.recommendations.append(recommendation)

    def finalize(self) -> None:
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=(
                f"Experiment learning finalized: {len(self.findings)} findings, "
                f"{len(self.recommendations)} recommendations"
            ),
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
    def from_dict(cls, data: dict[str, Any]) -> ExperimentLearningRecord:
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


# Backward-compatible import name. New code should use the explicit name.
LearningRecord = ExperimentLearningRecord
