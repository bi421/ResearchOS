"""
Interpretation objects — how evidence becomes market understanding.

Based on Article XVII: Object Model — Interpretation Layer.
Based on Article XVI: Scientific Reasoning Framework — Interpretation Layer.

Evidence becomes interpretation through the application of deterministic
rules that map evidence to market understanding.
"""

from __future__ import annotations

from typing import List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage


class Interpretation(BaseObject):
    """
    The application of deterministic rules to evidence.

    Based on Article XVII: Object Model — Interpretation.

    Interpretation = Evidence × Context × Rules

    Attributes:
        evidence_ids: All evidence supporting this interpretation
        rule_applied: Identifier of the rule applied
        context: Temporal, regime, geopolitical, or seasonal context
        conclusion: The interpreted market understanding
        confidence: Confidence score (0.0-1.0)
        supporting_evidence: Evidence IDs that support this interpretation
        contradicting_evidence: Evidence IDs that contradict this interpretation
        alternatives: Alternative interpretation IDs
        unknowns: Known unknowns related to this interpretation
    """

    def __init__(
        self,
        evidence_ids: List[str],
        rule_applied: str,
        context: str,
        conclusion: str,
        confidence: float = 0.0,
        supporting_evidence: Optional[List[str]] = None,
        contradicting_evidence: Optional[List[str]] = None,
        alternatives: Optional[List[str]] = None,
        unknowns: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Interpretation|{rule_applied}|{conclusion}|{context}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.evidence_ids: List[str] = evidence_ids
        self.rule_applied = rule_applied
        self.context = context
        self.conclusion = conclusion
        self.confidence = confidence
        self.supporting_evidence: List[str] = supporting_evidence or []
        self.contradicting_evidence: List[str] = contradicting_evidence or []
        self.alternatives: List[str] = alternatives or []
        self.unknowns: List[str] = unknowns or []

        self.lifecycle.transition(
            LifecycleStage.VALIDATED,
            reason="Interpretation created from evidence",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "evidence_ids": sorted(self.evidence_ids),
            "rule_applied": self.rule_applied,
            "context": self.context,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "supporting_evidence": sorted(self.supporting_evidence),
            "contradicting_evidence": sorted(self.contradicting_evidence),
            "alternatives": sorted(self.alternatives),
            "unknowns": sorted(self.unknowns),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "evidence_ids": self.evidence_ids,
            "rule_applied": self.rule_applied,
            "context": self.context,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "alternatives": self.alternatives,
            "unknowns": self.unknowns,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Interpretation":
        obj = super().from_dict(data)
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.rule_applied = data["rule_applied"]
        obj.context = data["context"]
        obj.conclusion = data["conclusion"]
        obj.confidence = data.get("confidence", 0.0)
        obj.supporting_evidence = list(data.get("supporting_evidence", []))
        obj.contradicting_evidence = list(data.get("contradicting_evidence", []))
        obj.alternatives = list(data.get("alternatives", []))
        obj.unknowns = list(data.get("unknowns", []))
        return obj


class Narrative(BaseObject):
    """
    A coherent story that explains market conditions.

    Based on Article XVII: Object Model — Narrative.

    Attributes:
        research_id: Link to Research
        thesis: The core narrative thesis
        primary_driver: The key variable driving the narrative
        supporting_drivers: Secondary driving variables
        interpretations: All interpretations in this narrative
        evidence_strength: Total weighted evidence (0.0-1.0)
        coherence_score: Agreement across dimensions (0.0-1.0)
        plausibility_score: Consistency with economic theory (0.0-1.0)
        invalidation_conditions: Conditions that would invalidate the narrative
        catalysts: Events that would confirm the narrative
        confidence: Confidence score (0.0-1.0)
        status: Active, Superseded, or Invalidated
    """

    def __init__(
        self,
        research_id: str,
        thesis: str,
        primary_driver: str = "",
        supporting_drivers: Optional[List[str]] = None,
        interpretations: Optional[List[str]] = None,
        evidence_strength: float = 0.0,
        coherence_score: float = 0.0,
        plausibility_score: float = 0.0,
        invalidation_conditions: Optional[List[str]] = None,
        catalysts: Optional[List[str]] = None,
        confidence: float = 0.0,
        status: str = "Active",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Narrative|{research_id}|{thesis}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_id = research_id
        self.thesis = thesis
        self.primary_driver = primary_driver
        self.supporting_drivers: List[str] = supporting_drivers or []
        self.interpretations: List[str] = interpretations or []
        self.evidence_strength = evidence_strength
        self.coherence_score = coherence_score
        self.plausibility_score = plausibility_score
        self.invalidation_conditions: List[str] = invalidation_conditions or []
        self.catalysts: List[str] = catalysts or []
        self.confidence = confidence
        self.status = status

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "thesis": self.thesis,
            "primary_driver": self.primary_driver,
            "supporting_drivers": sorted(self.supporting_drivers),
            "interpretations": sorted(self.interpretations),
            "evidence_strength": self.evidence_strength,
            "coherence_score": self.coherence_score,
            "plausibility_score": self.plausibility_score,
            "invalidation_conditions": sorted(self.invalidation_conditions),
            "catalysts": sorted(self.catalysts),
            "confidence": self.confidence,
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "research_id": self.research_id,
            "thesis": self.thesis,
            "primary_driver": self.primary_driver,
            "supporting_drivers": self.supporting_drivers,
            "interpretations": self.interpretations,
            "evidence_strength": self.evidence_strength,
            "coherence_score": self.coherence_score,
            "plausibility_score": self.plausibility_score,
            "invalidation_conditions": self.invalidation_conditions,
            "catalysts": self.catalysts,
            "confidence": self.confidence,
            "status": self.status,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Narrative":
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.thesis = data["thesis"]
        obj.primary_driver = data.get("primary_driver", "")
        obj.supporting_drivers = list(data.get("supporting_drivers", []))
        obj.interpretations = list(data.get("interpretations", []))
        obj.evidence_strength = data.get("evidence_strength", 0.0)
        obj.coherence_score = data.get("coherence_score", 0.0)
        obj.plausibility_score = data.get("plausibility_score", 0.0)
        obj.invalidation_conditions = list(data.get("invalidation_conditions", []))
        obj.catalysts = list(data.get("catalysts", []))
        obj.confidence = data.get("confidence", 0.0)
        obj.status = data.get("status", "Active")
        return obj
