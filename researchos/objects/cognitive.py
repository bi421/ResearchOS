"""
Cognitive objects — tracking trader cognitive growth and bias detection.

Based on Article XVII: Object Model — Cognitive Layer.
Based on Article XIV: Cognitive Growth Engine.

Cognitive objects track the trader's reasoning quality, knowledge growth,
bias profile, and learning progress over time.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now


class Bias(BaseObject):
    """
    A detected cognitive bias in the trader's decision-making.

    Based on Article XVII: Object Model — Bias.

    Bias types:
        - Confirmation: Seeking evidence that confirms existing beliefs
        - Anchoring: Over-relying on the first piece of information
        - Overconfidence: Overestimating one's own abilities
        - Recency: Giving more weight to recent events
        - Availability: Overestimating probability of vivid events
        - Survivorship: Focusing on successes, ignoring failures
        - Hindsight: Seeing events as predictable after they occur
        - Loss_Aversion: Preferring to avoid losses over acquiring gains

    Attributes:
        type: The type of cognitive bias
        trader_id: Identifier for the trader
        decision_id: Link to the affected decision
        description: Human-readable description
        evidence: Evidence supporting the bias detection
        frequency: How often this bias occurs (0.0-1.0)
        trend: Direction of change in frequency
        first_detected: When this bias was first detected
        last_detected: When this bias was last detected
        severity: Impact severity (0.0-1.0)
        bias_trace: How this bias was detected
    """

    def __init__(
        self,
        type: str,
        trader_id: str,
        decision_id: str = "",
        description: str = "",
        evidence: Optional[List[str]] = None,
        frequency: float = 0.0,
        trend: float = 0.0,
        first_detected: Optional[datetime] = None,
        last_detected: Optional[datetime] = None,
        severity: float = 0.0,
        bias_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Bias|{type}|{trader_id}|{decision_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.type = type
        self.trader_id = trader_id
        self.decision_id = decision_id
        self.description = description
        self.evidence: List[str] = evidence or []
        self.frequency = frequency
        self.trend = trend
        self.first_detected = first_detected or utc_now()
        self.last_detected = last_detected or utc_now()
        self.severity = severity
        self.bias_trace = bias_trace

        self.lifecycle.transition(
            LifecycleStage.DETECTED,
            reason=f"Bias detected: {type}",
        )

    def update_occurrence(
        self,
        frequency: float,
        trend: float,
        severity: float,
    ) -> None:
        """Update the bias occurrence metrics."""
        self.frequency = frequency
        self.trend = trend
        self.severity = severity
        self.last_detected = utc_now()
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Bias updated: frequency={frequency:.2f}, severity={severity:.2f}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "type": self.type,
            "trader_id": self.trader_id,
            "decision_id": self.decision_id,
            "description": self.description,
            "evidence": sorted(self.evidence),
            "frequency": self.frequency,
            "trend": self.trend,
            "first_detected": self.first_detected.isoformat(),
            "last_detected": self.last_detected.isoformat(),
            "severity": self.severity,
            "bias_trace": self.bias_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "type": self.type,
            "trader_id": self.trader_id,
            "decision_id": self.decision_id,
            "description": self.description,
            "evidence": self.evidence,
            "frequency": self.frequency,
            "trend": self.trend,
            "first_detected": self.first_detected.isoformat(),
            "last_detected": self.last_detected.isoformat(),
            "severity": self.severity,
            "bias_trace": self.bias_trace,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Bias":
        obj = super().from_dict(data)
        obj.type = data["type"]
        obj.trader_id = data["trader_id"]
        obj.decision_id = data.get("decision_id", "")
        obj.description = data.get("description", "")
        obj.evidence = list(data.get("evidence", []))
        obj.frequency = data.get("frequency", 0.0)
        obj.trend = data.get("trend", 0.0)
        obj.first_detected = parse_timestamp(data["first_detected"]) if data.get("first_detected") else None
        obj.last_detected = parse_timestamp(data["last_detected"]) if data.get("last_detected") else None
        obj.severity = data.get("severity", 0.0)
        obj.bias_trace = data.get("bias_trace", "")
        return obj


class LearningRecord(BaseObject):
    """
    A record of the trader's cognitive learning progress.

    Based on Article XVII: Object Model — LearningRecord.

    Learning dimensions:
        - Knowledge: Growth in market knowledge
        - Reasoning: Quality of reasoning process
        - Bias: Reduction in cognitive bias frequency
        - Discipline: Improvement in trading discipline
        - Reflection: Quality of post-decision reflection
        - Learning_Progress: Overall learning trajectory

    Attributes:
        trader_id: Identifier for the trader
        dimension: The learning dimension being tracked
        score: Current score (0.0-1.0)
        baseline_score: Starting score for comparison
        progress: Improvement from baseline
        trend: Direction of change
        trajectory: Accelerating, Steady, Decelerating, or Plateauing
        recommendations: Improvement recommendations
        learning_trace: How this record was derived
    """

    def __init__(
        self,
        trader_id: str,
        dimension: str,
        score: float = 0.0,
        baseline_score: float = 0.0,
        progress: float = 0.0,
        trend: float = 0.0,
        trajectory: str = "Steady",
        recommendations: Optional[List[str]] = None,
        learning_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"LearningRecord|{trader_id}|{dimension}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.trader_id = trader_id
        self.dimension = dimension
        self.score = score
        self.baseline_score = baseline_score
        self.progress = round(progress, 10)
        self.trend = trend
        self.trajectory = trajectory
        self.recommendations: List[str] = recommendations or []
        self.learning_trace = learning_trace

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"Learning record created for dimension: {dimension}",
        )

    def update(
        self,
        score: float,
        trend: float,
        trajectory: str,
        recommendations: Optional[List[str]] = None,
    ) -> None:
        """Update the learning record with new metrics."""
        self.score = score
        self.progress = round(score - self.baseline_score, 10)
        self.trend = trend
        self.trajectory = trajectory
        if recommendations:
            self.recommendations.extend(recommendations)
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Learning record updated: score={score:.2f}, trajectory={trajectory}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "trader_id": self.trader_id,
            "dimension": self.dimension,
            "score": self.score,
            "baseline_score": self.baseline_score,
            "progress": self.progress,
            "trend": self.trend,
            "trajectory": self.trajectory,
            "recommendations": sorted(self.recommendations),
            "learning_trace": self.learning_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "trader_id": self.trader_id,
            "dimension": self.dimension,
            "score": self.score,
            "baseline_score": self.baseline_score,
            "progress": self.progress,
            "trend": self.trend,
            "trajectory": self.trajectory,
            "recommendations": self.recommendations,
            "learning_trace": self.learning_trace,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "LearningRecord":
        obj = super().from_dict(data)
        obj.trader_id = data["trader_id"]
        obj.dimension = data["dimension"]
        obj.score = data.get("score", 0.0)
        obj.baseline_score = data.get("baseline_score", 0.0)
        obj.progress = data.get("progress", 0.0)
        obj.trend = data.get("trend", 0.0)
        obj.trajectory = data.get("trajectory", "Steady")
        obj.recommendations = list(data.get("recommendations", []))
        obj.learning_trace = data.get("learning_trace", "")
        return obj


class CognitiveAssessment(BaseObject):
    """
    A comprehensive assessment of the trader's cognitive capabilities.

    Based on Article XVII: Object Model — CognitiveAssessment.

    Aggregates all cognitive metrics into a single assessment covering
    knowledge, reasoning, bias profile, discipline, reflection, and
    overall learning progress.

    Attributes:
        trader_id: Identifier for the trader
        research_id: Link to the associated research
        knowledge_score: Knowledge assessment (0.0-1.0)
        reasoning_score: Reasoning quality (0.0-1.0)
        bias_profile: List of detected bias IDs
        discipline_score: Trading discipline (0.0-1.0)
        reflection_score: Reflection quality (0.0-1.0)
        learning_progress: Overall learning progress (0.0-1.0)
        overall_score: Composite score (0.0-1.0)
        feedback: Feedback items for the trader
        recommendations: Improvement recommendations
        assessment_trace: How the assessment was performed
    """

    def __init__(
        self,
        trader_id: str,
        research_id: str = "",
        knowledge_score: float = 0.0,
        reasoning_score: float = 0.0,
        bias_profile: Optional[List[str]] = None,
        discipline_score: float = 0.0,
        reflection_score: float = 0.0,
        learning_progress: float = 0.0,
        overall_score: float = 0.0,
        feedback: Optional[List[str]] = None,
        recommendations: Optional[List[str]] = None,
        assessment_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"CognitiveAssessment|{trader_id}|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.trader_id = trader_id
        self.research_id = research_id
        self.knowledge_score = knowledge_score
        self.reasoning_score = reasoning_score
        self.bias_profile: List[str] = bias_profile or []
        self.discipline_score = discipline_score
        self.reflection_score = reflection_score
        self.learning_progress = learning_progress
        self.overall_score = overall_score
        self.feedback: List[str] = feedback or []
        self.recommendations: List[str] = recommendations or []
        self.assessment_trace = assessment_trace

        self.lifecycle.transition(
            LifecycleStage.INITIATED,
            reason="Cognitive assessment initiated",
        )

    def compute_overall_score(self) -> float:
        """
        Compute the overall cognitive score from all dimensions.

        Overall = Knowledge × 0.25 + Reasoning × 0.25 +
                  (1 - Bias_Count × 0.05) + Discipline × 0.20 +
                  Reflection × 0.15 + Learning_Progress × 0.15
        """
        bias_penalty = min(0.5, len(self.bias_profile) * 0.05)
        overall = (
            self.knowledge_score * 0.25
            + self.reasoning_score * 0.25
            + (1.0 - bias_penalty) * 0.10
            + self.discipline_score * 0.15
            + self.reflection_score * 0.15
            + self.learning_progress * 0.10
        )
        self.overall_score = min(1.0, max(0.0, overall))
        return self.overall_score

    def complete(self) -> None:
        """Mark the cognitive assessment as complete."""
        self.compute_overall_score()
        self.lifecycle.transition(
            LifecycleStage.COMPLETE,
            reason=f"Cognitive assessment completed: overall={self.overall_score:.2f}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "trader_id": self.trader_id,
            "research_id": self.research_id,
            "knowledge_score": self.knowledge_score,
            "reasoning_score": self.reasoning_score,
            "bias_profile": sorted(self.bias_profile),
            "discipline_score": self.discipline_score,
            "reflection_score": self.reflection_score,
            "learning_progress": self.learning_progress,
            "overall_score": self.overall_score,
            "feedback": sorted(self.feedback),
            "recommendations": sorted(self.recommendations),
            "assessment_trace": self.assessment_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "trader_id": self.trader_id,
            "research_id": self.research_id,
            "knowledge_score": self.knowledge_score,
            "reasoning_score": self.reasoning_score,
            "bias_profile": self.bias_profile,
            "discipline_score": self.discipline_score,
            "reflection_score": self.reflection_score,
            "learning_progress": self.learning_progress,
            "overall_score": self.overall_score,
            "feedback": self.feedback,
            "recommendations": self.recommendations,
            "assessment_trace": self.assessment_trace,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "CognitiveAssessment":
        obj = super().from_dict(data)
        obj.trader_id = data["trader_id"]
        obj.research_id = data.get("research_id", "")
        obj.knowledge_score = data.get("knowledge_score", 0.0)
        obj.reasoning_score = data.get("reasoning_score", 0.0)
        obj.bias_profile = list(data.get("bias_profile", []))
        obj.discipline_score = data.get("discipline_score", 0.0)
        obj.reflection_score = data.get("reflection_score", 0.0)
        obj.learning_progress = data.get("learning_progress", 0.0)
        obj.overall_score = data.get("overall_score", 0.0)
        obj.feedback = list(data.get("feedback", []))
        obj.recommendations = list(data.get("recommendations", []))
        obj.assessment_trace = data.get("assessment_trace", "")
        return obj
