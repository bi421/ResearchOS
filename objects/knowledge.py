"""
Knowledge objects — structured knowledge about market behavior.

Based on Article XVII: Object Model — Knowledge Layer.
Based on Article XIII: Knowledge Engine.

Knowledge is accumulated over time from research validation and
pattern recognition. It is the long-term memory of the ResearchOS system.
"""

from __future__ import annotations

from typing import List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage


class Knowledge(BaseObject):
    """
    Structured knowledge about market behavior.

    Based on Article XVII: Object Model — Knowledge.

    Knowledge types:
        - Entity_Property: Properties of market entities
        - Classification_Rule: Rules for classifying market states
        - State_Transition: Rules for state changes
        - Relationship_Strength: Strength of intermarket relationships
        - Event_Impact: Impact of events on markets
        - Regime_Characteristic: Characteristics of market regimes

    Attributes:
        type: The type of knowledge
        subject: Ontology concept ID
        predicate: Relationship type
        object: Value or concept ID
        confidence: Confidence in this knowledge (0.0-1.0)
        evidence_count: Number of evidence entries supporting this knowledge
        first_observed: When this knowledge was first observed
        last_updated: When this knowledge was last updated
        source_references: Research IDs that contributed
        knowledge_trace: How this knowledge was derived
    """

    def __init__(
        self,
        type: str,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 0.0,
        evidence_count: int = 0,
        source_references: Optional[List[str]] = None,
        knowledge_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Knowledge|{type}|{subject}|{predicate}|{object}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.type = type
        self.subject = subject
        self.predicate = predicate
        self.object = object
        self.confidence = confidence
        self.evidence_count = evidence_count
        self.source_references: List[str] = source_references or []
        self.knowledge_trace = knowledge_trace

        self.lifecycle.transition(
            LifecycleStage.VALIDATED,
            reason="Knowledge validated from evidence",
        )

    def update_confidence(self, new_confidence: float, evidence_count: int) -> None:
        """Update the confidence and evidence count for this knowledge."""
        self.confidence = new_confidence
        self.evidence_count = evidence_count
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Confidence updated to {new_confidence}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "type": self.type,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "source_references": sorted(self.source_references),
            "knowledge_trace": self.knowledge_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "type": self.type,
                "subject": self.subject,
                "predicate": self.predicate,
                "object": self.object,
                "confidence": self.confidence,
                "evidence_count": self.evidence_count,
                "source_references": self.source_references,
                "knowledge_trace": self.knowledge_trace,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Knowledge":
        obj = super().from_dict(data)
        obj.type = data.get("type") or data.get("pattern_type") or data.get("knowledge_type", "")
        obj.subject = data.get("subject", "")
        obj.predicate = data.get("predicate", "")
        obj.object = data.get("object", "")
        obj.confidence = data.get("confidence", 0.0)
        obj.evidence_count = data.get("evidence_count", 0)
        obj.source_references = list(data.get("source_references", []))
        obj.knowledge_trace = data.get("knowledge_trace", "")
        return obj


class Pattern(BaseObject):
    """
    A recurring market behavior identified from historical data.

    Based on Article XVII: Object Model — Pattern.

    Pattern types:
        - Regime_Transition: Transitions between market regimes
        - Event_Impact: Impact of specific events
        - Cross_Market: Intermarket relationships
        - Technical: Technical analysis patterns
        - Sentiment: Sentiment-based patterns
        - Liquidity: Liquidity-related patterns

    Attributes:
        type: The type of pattern
        description: Human-readable description
        trigger_conditions: Conditions that trigger the pattern
        outcome: Expected outcome
        historical_accuracy: How often this pattern was correct (0.0-1.0)
        sample_size: Number of historical occurrences
        confidence_interval: {lower, upper} bounds
        supporting_evidence: Evidence IDs
        contradicting_evidence: Evidence IDs
        first_identified: When this pattern was first identified
        last_validated: When this pattern was last validated
        pattern_trace: How this pattern was identified
    """

    def __init__(
        self,
        type: str,
        description: str,
        trigger_conditions: Optional[List[str]] = None,
        outcome: str = "",
        historical_accuracy: float = 0.0,
        sample_size: int = 0,
        confidence_interval: Optional[dict] = None,
        supporting_evidence: Optional[List[str]] = None,
        contradicting_evidence: Optional[List[str]] = None,
        pattern_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Pattern|{type}|{description}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.type = type
        self.description = description
        self.trigger_conditions: List[str] = trigger_conditions or []
        self.outcome = outcome
        self.historical_accuracy = historical_accuracy
        self.sample_size = sample_size
        self.confidence_interval = confidence_interval or {"lower": 0.0, "upper": 1.0}
        self.supporting_evidence: List[str] = supporting_evidence or []
        self.contradicting_evidence: List[str] = contradicting_evidence or []
        self.pattern_trace = pattern_trace

        self.lifecycle.transition(
            LifecycleStage.VALIDATED,
            reason="Pattern validated from historical data",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "type": self.type,
            "description": self.description,
            "trigger_conditions": sorted(self.trigger_conditions),
            "outcome": self.outcome,
            "historical_accuracy": self.historical_accuracy,
            "sample_size": self.sample_size,
            "confidence_interval": self.confidence_interval,
            "supporting_evidence": sorted(self.supporting_evidence),
            "contradicting_evidence": sorted(self.contradicting_evidence),
            "pattern_trace": self.pattern_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "type": self.type,
                "description": self.description,
                "trigger_conditions": self.trigger_conditions,
                "outcome": self.outcome,
                "historical_accuracy": self.historical_accuracy,
                "sample_size": self.sample_size,
                "confidence_interval": self.confidence_interval,
                "supporting_evidence": self.supporting_evidence,
                "contradicting_evidence": self.contradicting_evidence,
                "pattern_trace": self.pattern_trace,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        obj = super().from_dict(data)
        obj.type = data["type"]
        obj.description = data["description"]
        obj.trigger_conditions = list(data.get("trigger_conditions", []))
        obj.outcome = data.get("outcome", "")
        obj.historical_accuracy = data.get("historical_accuracy", 0.0)
        obj.sample_size = data.get("sample_size", 0)
        obj.confidence_interval = data.get("confidence_interval", {"lower": 0.0, "upper": 1.0})
        obj.supporting_evidence = list(data.get("supporting_evidence", []))
        obj.contradicting_evidence = list(data.get("contradicting_evidence", []))
        obj.pattern_trace = data.get("pattern_trace", "")
        return obj


class Lesson(BaseObject):
    """
    An actionable insight extracted from research validation.

    Based on Article XVII: Object Model — Lesson.

    Lesson types:
        - Data: Issues with data quality or availability
        - Model: Issues with analytical models
        - Process: Issues with research processes
        - Bias: Cognitive bias issues
        - Scenario: Issues with scenario construction
        - Validation: Issues with validation methodology

    Attributes:
        type: The type of lesson
        description: What was learned
        recommendation: Actionable recommendation
        severity: Importance of the lesson (0.0-1.0)
        frequency: How often this issue occurs
        affected_articles: Which constitutional articles this affects
        supporting_evidence: Evidence IDs
        lesson_trace: How this lesson was extracted
    """

    def __init__(
        self,
        type: str,
        description: str,
        recommendation: str = "",
        severity: float = 0.0,
        frequency: int = 0,
        affected_articles: Optional[List[str]] = None,
        supporting_evidence: Optional[List[str]] = None,
        lesson_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Lesson|{type}|{description}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.type = type
        self.description = description
        self.recommendation = recommendation
        self.severity = severity
        self.frequency = frequency
        self.affected_articles: List[str] = affected_articles or []
        self.supporting_evidence: List[str] = supporting_evidence or []
        self.lesson_trace = lesson_trace

        self.lifecycle.transition(
            LifecycleStage.VALIDATED,
            reason="Lesson extracted from validation",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "type": self.type,
            "description": self.description,
            "recommendation": self.recommendation,
            "severity": self.severity,
            "frequency": self.frequency,
            "affected_articles": sorted(self.affected_articles),
            "supporting_evidence": sorted(self.supporting_evidence),
            "lesson_trace": self.lesson_trace,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "type": self.type,
                "description": self.description,
                "recommendation": self.recommendation,
                "severity": self.severity,
                "frequency": self.frequency,
                "affected_articles": self.affected_articles,
                "supporting_evidence": self.supporting_evidence,
                "lesson_trace": self.lesson_trace,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Lesson":
        obj = super().from_dict(data)
        obj.type = data["type"]
        obj.description = data["description"]
        obj.recommendation = data.get("recommendation", "")
        obj.severity = data.get("severity", 0.0)
        obj.frequency = data.get("frequency", 0)
        obj.affected_articles = list(data.get("affected_articles", []))
        obj.supporting_evidence = list(data.get("supporting_evidence", []))
        obj.lesson_trace = data.get("lesson_trace", "")
        return obj
