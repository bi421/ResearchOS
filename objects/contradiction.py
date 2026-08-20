"""
Contradiction objects — conflicts between evidence, interpretations, or analyses.

Based on Article XVII: Object Model — Contradiction Layer.
Based on Article XVI: Scientific Reasoning Framework — Contradiction Framework.

Contradictions are detected, assessed, and resolved using the
Conflict Resolution Protocol.
"""

from __future__ import annotations

from typing import List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp

# Conflict resolution threshold (Article XVI, Section 7.6)
CONFLICT_RESOLUTION_THRESHOLD = 2.0  # One side must have >= 2x evidence weight


class Contradiction(BaseObject):
    """
    A conflict between evidence, interpretations, or analyses.

    Based on Article XVII: Object Model — Contradiction.

    Contradiction types:
        - Internal: Evidence conflicts, interpretation conflicts, etc.
        - Cross-Market: Relationship breakdowns, flow dislocations
        - Macro: Policy contradictions, data contradictions, regime contradictions
        - Timeframe: Short-term vs long-term, intraday vs daily
        - Research: Analyst disagreements, model disagreements

    Attributes:
        research_id: Link to Research
        type: Internal, Cross-Market, Macro, Timeframe, or Research
        description: Human-readable description of the conflict
        sides: Conflicting positions with evidence and weights
        severity: Computed severity score (0.0-1.0)
        resolution: Resolved, Unresolved, or Escalated
        resolution_method: How the conflict was resolved
        confidence_impact: Impact on affected confidence scores
        resolved_at: Timestamp when resolved (if resolved)
    """

    def __init__(
        self,
        research_id: str,
        type: str,
        description: str,
        sides: Optional[List[dict]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Contradiction|{research_id}|{type}|{description}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_id = research_id
        self.type = type
        self.description = description
        self.sides: List[dict] = sides or []
        self.severity = self._compute_severity()
        self.resolution = "Unresolved"
        self.resolution_method = ""
        self.confidence_impact = 0.0
        self.resolved_at = None

        self.lifecycle.transition(
            LifecycleStage.DETECTED,
            reason=f"Contradiction detected: {type}",
        )

    def _compute_severity(self) -> float:
        """
        Compute the severity of this contradiction.

        Severity is based on the weight difference between sides
        and the number of evidence items involved.
        """
        if not self.sides:
            return 0.0

        weights = [s.get("weight", 0.0) for s in self.sides]
        max_weight = max(weights) if weights else 0.0
        min_weight = min(weights) if weights else 0.0

        # Severity increases with weight difference and evidence count
        weight_diff = max_weight - min_weight
        evidence_count = sum(len(s.get("evidence", [])) for s in self.sides)

        severity = min(1.0, weight_diff * 0.5 + evidence_count * 0.1)
        return severity

    def resolve(self) -> bool:
        """
        Attempt to resolve this contradiction using the Conflict Resolution Protocol.

        1. Severity Assessment — Already computed
        2. Evidence Weight Comparison — Compare evidence weights
        3. Automatic Resolution — If one side has >= 2x evidence weight, it wins
        4. Human Escalation — Unresolved conflicts are flagged for review
        5. Confidence Impact — All unresolved conflicts reduce confidence

        Returns:
            True if the contradiction was automatically resolved.
        """
        if len(self.sides) < 2:
            self.resolution = "Resolved"
            self.resolution_method = "Single side — no conflict"
            self.lifecycle.transition(
                LifecycleStage.RESOLVED,
                reason="Single side — no conflict",
            )
            return True

        weights = [s.get("weight", 0.0) for s in self.sides]
        max_weight = max(weights)
        min_weight = min(weights)

        if min_weight > 0 and max_weight / min_weight >= CONFLICT_RESOLUTION_THRESHOLD:
            # Automatic resolution — heavier side wins
            winning_side = weights.index(max_weight)
            self.resolution = "Resolved"
            self.resolution_method = f"Automatic — side {winning_side} has >= 2x evidence weight"
            self.confidence_impact = 0.0
            self.lifecycle.transition(
                LifecycleStage.RESOLVED,
                reason=f"Automatic resolution — side {winning_side} wins",
            )
            return True
        else:
            # Escalate to human review
            self.resolution = "Escalated"
            self.resolution_method = "Escalated — insufficient evidence weight difference"
            self.confidence_impact = self.severity * 0.1
            self.lifecycle.transition(
                LifecycleStage.RESOLVED_ESCALATED,
                reason="Escalated to human review",
            )
            return False

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "type": self.type,
            "description": self.description,
            "sides": self.sides,
            "severity": self.severity,
            "resolution": self.resolution,
            "resolution_method": self.resolution_method,
            "confidence_impact": self.confidence_impact,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "type": self.type,
                "description": self.description,
                "sides": self.sides,
                "severity": self.severity,
                "resolution": self.resolution,
                "resolution_method": self.resolution_method,
                "confidence_impact": self.confidence_impact,
                "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Contradiction":
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.type = data["type"]
        obj.description = data["description"]
        obj.sides = list(data.get("sides", []))
        obj.severity = data.get("severity", obj._compute_severity())
        obj.resolution = data.get("resolution", "Unresolved")
        obj.resolution_method = data.get("resolution_method", "")
        obj.confidence_impact = data.get("confidence_impact", 0.0)
        obj.resolved_at = parse_timestamp(data["resolved_at"]) if data.get("resolved_at") else None
        return obj


class ContradictionReport(BaseObject):
    """
    A collection of all contradictions for a research cycle.

    Based on Article XVII: Object Model — ContradictionReport.
    """

    def __init__(
        self,
        research_id: str,
        contradictions: Optional[List[Contradiction]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"ContradictionReport|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)
        self.research_id = research_id
        self.contradictions: List[Contradiction] = contradictions or []
        self._contradiction_ids: List[str] = []

    @property
    def total_count(self) -> int:
        return len(self.contradictions)

    @property
    def resolved_count(self) -> int:
        return sum(1 for c in self.contradictions if c.resolution == "Resolved")

    @property
    def unresolved_count(self) -> int:
        return sum(1 for c in self.contradictions if c.resolution in ("Unresolved", "Escalated"))

    @property
    def average_severity(self) -> float:
        if not self.contradictions:
            return 0.0
        return sum(c.severity for c in self.contradictions) / len(self.contradictions)

    def add_contradiction(self, contradiction: Contradiction) -> None:
        """Add a contradiction to the report."""
        self.contradictions.append(contradiction)

    def resolve_all(self) -> None:
        """Attempt to resolve all contradictions."""
        for c in self.contradictions:
            c.resolve()

    @property
    def contradiction_ids(self) -> List[str]:
        if self.contradictions:
            return [c.id for c in self.contradictions]
        return self._contradiction_ids

    @contradiction_ids.setter
    def contradiction_ids(self, value: List[str]) -> None:
        self._contradiction_ids = value

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "contradiction_ids": self.contradiction_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "ContradictionReport":
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.contradictions = []
        obj._contradiction_ids = list(data.get("contradiction_ids", []))
        return obj

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "contradiction_ids": sorted(self.contradiction_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }
