"""
Hypothesis objects — testable predictions about market behavior.

Based on Article XVII: Object Model — Hypothesis Layer.
Based on Article XVI: Scientific Reasoning Framework — Hypothesis Layer.

A hypothesis is a testable prediction derived from interpretations and narratives.
Every hypothesis must be falsifiable.
"""

from __future__ import annotations

from typing import List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage

# Hypothesis ranking weights (Article XVI, Section 4.5)
RANK_EVIDENCE_STRENGTH = 0.40
RANK_COHERENCE = 0.30
RANK_PLAUSIBILITY = 0.20
RANK_FALSIFIABILITY = 0.10


class Hypothesis(BaseObject):
    """
    A testable prediction about market behavior.

    Based on Article XVII: Object Model — Hypothesis.

    Every hypothesis must be:
        - Specific: Clearly states what is expected to happen
        - Testable: Can be proven wrong by specific observations
        - Evidence-Based: Supported by current evidence
        - Actionable: Has implications for market understanding

    Attributes:
        research_id: Link to Research
        type: Primary, Alternative, Null, or Tail
        statement: The testable prediction
        narrative_id: Link to supporting Narrative
        evidence_ids: All evidence supporting this hypothesis
        evidence_strength: Total weighted evidence (0.0-1.0)
        coherence: Agreement with known relationships (0.0-1.0)
        plausibility: Consistency with theory (0.0-1.0)
        falsifiability: How easily it can be proven wrong (0.0-1.0)
        rank_score: Computed ranking score
        confidence: Confidence score (0.0-1.0)
        valid_if: Conditions that must hold
        invalid_if: Conditions that would prove it wrong
        monitoring_conditions: Conditions tracked for early warning
        status: Active, Invalidated, or Retired
    """

    def __init__(
        self,
        research_id: str,
        type: str,
        statement: str,
        narrative_id: str = "",
        evidence_ids: Optional[List[str]] = None,
        evidence_strength: float = 0.0,
        coherence: float = 0.0,
        plausibility: float = 0.0,
        falsifiability: float = 0.0,
        confidence: float = 0.0,
        valid_if: Optional[List[str]] = None,
        invalid_if: Optional[List[str]] = None,
        monitoring_conditions: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Hypothesis|{research_id}|{type}|{statement}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.research_id = research_id
        self.type = type
        self.statement = statement
        self.narrative_id = narrative_id
        self.evidence_ids: List[str] = evidence_ids or []
        self.evidence_strength = evidence_strength
        self.coherence = coherence
        self.plausibility = plausibility
        self.falsifiability = falsifiability
        self.confidence = confidence
        self.valid_if: List[str] = valid_if or []
        self.invalid_if: List[str] = invalid_if or []
        self.monitoring_conditions: List[str] = monitoring_conditions or []
        self.status = "Active"

        # Compute rank score
        self.rank_score = self._compute_rank_score()

        self.lifecycle.transition(
            LifecycleStage.ACTIVE,
            reason="Hypothesis created and ranked",
        )

    def _compute_rank_score(self) -> float:
        """
        Compute the hypothesis ranking score.

        Rank_Score = Evidence_Strength × 0.40 + Coherence × 0.30 +
                     Plausibility × 0.20 + Falsifiability × 0.10
        """
        return (
            self.evidence_strength * RANK_EVIDENCE_STRENGTH
            + self.coherence * RANK_COHERENCE
            + self.plausibility * RANK_PLAUSIBILITY
            + self.falsifiability * RANK_FALSIFIABILITY
        )

    def check_invalidation(self, current_evidence: List[str]) -> bool:
        """
        Check if this hypothesis has been invalidated.

        Args:
            current_evidence: List of current evidence IDs.

        Returns:
            True if the hypothesis is invalidated.
        """
        # Check if any invalid_if condition is met
        for condition in self.invalid_if:
            if condition in current_evidence:
                self.status = "Invalidated"
                self.lifecycle.transition(
                    LifecycleStage.INVALIDATED,
                    reason=f"Invalidation condition met: {condition}",
                )
                return True
        return False

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "type": self.type,
            "statement": self.statement,
            "narrative_id": self.narrative_id,
            "evidence_ids": sorted(self.evidence_ids),
            "evidence_strength": self.evidence_strength,
            "coherence": self.coherence,
            "plausibility": self.plausibility,
            "falsifiability": self.falsifiability,
            "confidence": self.confidence,
            "valid_if": sorted(self.valid_if),
            "invalid_if": sorted(self.invalid_if),
            "monitoring_conditions": sorted(self.monitoring_conditions),
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "type": self.type,
                "statement": self.statement,
                "narrative_id": self.narrative_id,
                "evidence_ids": self.evidence_ids,
                "evidence_strength": self.evidence_strength,
                "coherence": self.coherence,
                "plausibility": self.plausibility,
                "falsifiability": self.falsifiability,
                "rank_score": self.rank_score,
                "confidence": self.confidence,
                "valid_if": self.valid_if,
                "invalid_if": self.invalid_if,
                "monitoring_conditions": self.monitoring_conditions,
                "status": self.status,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Hypothesis":
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.type = data["type"]
        obj.statement = data["statement"]
        obj.narrative_id = data.get("narrative_id", "")
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.evidence_strength = data.get("evidence_strength", 0.0)
        obj.coherence = data.get("coherence", 0.0)
        obj.plausibility = data.get("plausibility", 0.0)
        obj.falsifiability = data.get("falsifiability", 0.0)
        obj.confidence = data.get("confidence", 0.0)
        obj.valid_if = list(data.get("valid_if", []))
        obj.invalid_if = list(data.get("invalid_if", []))
        obj.monitoring_conditions = list(data.get("monitoring_conditions", []))
        obj.status = data.get("status", "Active")
        obj.rank_score = data.get("rank_score", obj._compute_rank_score())
        return obj


class HypothesisSet(BaseObject):
    """
    A collection of all hypotheses for a research cycle.

    Based on Article XVII: Object Model — HypothesisSet.
    """

    def __init__(
        self,
        research_id: str,
        hypotheses: Optional[List[Hypothesis]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"HypothesisSet|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)
        self.research_id = research_id
        self.hypotheses: List[Hypothesis] = hypotheses or []
        self._hypothesis_ids: List[str] = []

    @property
    def primary_id(self) -> Optional[str]:
        """Get the ID of the primary hypothesis."""
        for h in self.hypotheses:
            if h.type == "Primary":
                return h.id
        return None

    @property
    def alternatives(self) -> List[str]:
        """Get IDs of alternative hypotheses."""
        return [h.id for h in self.hypotheses if h.type == "Alternative"]

    @property
    def null_id(self) -> Optional[str]:
        """Get the ID of the null hypothesis."""
        for h in self.hypotheses:
            if h.type == "Null":
                return h.id
        return None

    @property
    def tail_ids(self) -> List[str]:
        """Get IDs of tail hypotheses."""
        return [h.id for h in self.hypotheses if h.type == "Tail"]

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        """Add a hypothesis to the set."""
        self.hypotheses.append(hypothesis)

    def get_ranked(self) -> List[Hypothesis]:
        """Get hypotheses sorted by rank score (descending), with deterministic tie-breaking by ID."""
        return sorted(
            self.hypotheses,
            key=lambda h: (-h.rank_score, h.id),
        )

    @property
    def hypothesis_ids(self) -> List[str]:
        if self.hypotheses:
            return [h.id for h in self.hypotheses]
        return self._hypothesis_ids

    @hypothesis_ids.setter
    def hypothesis_ids(self, value: List[str]) -> None:
        self._hypothesis_ids = value

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "hypothesis_ids": self.hypothesis_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "HypothesisSet":
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.hypotheses = []
        obj._hypothesis_ids = list(data.get("hypothesis_ids", []))
        return obj

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "hypothesis_ids": sorted(self.hypothesis_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }
