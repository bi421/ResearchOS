"""Attribution objects — traceable reasoning paths from conclusions back to evidence.

Based on Article XVII: Object Model — Attribution Layer.
Based on Article XVI: Scientific Reasoning Framework — Decision Support Layer.

Attribution records answer four questions for every conclusion:
1. Why? — The reasoning path that led to this conclusion
2. Based on what evidence? — Links to specific evidence and observations
3. Confidence? — How confident is each step in the reasoning chain
4. Previous similar situations? — Links to Market Memory for pattern matching

Every attribution is deterministic, immutable, and fully auditable.
"""

from __future__ import annotations

from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage

# Attribution integrity thresholds
ATTRIBUTION_COMPLETE_THRESHOLD = 0.95
ATTRIBUTION_PARTIAL_THRESHOLD = 0.50


class Attribution(BaseObject):
    """A traceable reasoning path from a conclusion back to evidence and observations.

    Based on Article XVII: Object Model — Attribution.

    Every conclusion (hypothesis, scenario, report, etc.) in ResearchOS
    must have an Attribution record that answers:
    1. Why was this conclusion reached? (reasoning_path)
    2. What evidence supports it? (evidence_ids)
    3. What observations underpin it? (observation_ids)
    4. How confident are we? (confidence)
    5. Similar past situations? (market_memory_ids)

    Attributes:
        conclusion_id: ID of the conclusion object being attributed
        conclusion_type: Type of the conclusion ("Hypothesis", "Scenario", etc.)
        reasoning_path: Ordered list of step descriptors showing how the
                        conclusion was derived from its inputs
        reasoning_object_ids: Ordered list of object IDs traversed along the
                              reasoning path (the full chain)
        evidence_ids: All evidence IDs that support this conclusion
        observation_ids: All observation IDs that underpin this conclusion
        confidence: Overall confidence in the attribution (0.0-1.0),
                    computed from chain completeness and evidence quality
        attribution_trace: Human-readable trace of how the attribution
                           was constructed
        market_memory_ids: Links to MarketMemory objects describing similar
                           past situations
        status: "Complete", "Partial", "Broken", or "Pending"
    """

    def __init__(
        self,
        conclusion_id: str,
        conclusion_type: str,
        reasoning_path: list[str] | None = None,
        reasoning_object_ids: list[str] | None = None,
        evidence_ids: list[str] | None = None,
        observation_ids: list[str] | None = None,
        confidence: float = 0.0,
        attribution_trace: str = "",
        market_memory_ids: list[str] | None = None,
        status: str = "Pending",
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"Attribution|{conclusion_id}|{conclusion_type}|{attribution_trace[:100]}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.conclusion_id = conclusion_id
        self.conclusion_type = conclusion_type
        self.reasoning_path: list[str] = reasoning_path or []
        self.reasoning_object_ids: list[str] = reasoning_object_ids or []
        self.evidence_ids: list[str] = evidence_ids or []
        self.observation_ids: list[str] = observation_ids or []
        self.confidence = confidence
        self.attribution_trace = attribution_trace
        self.market_memory_ids: list[str] = market_memory_ids or []
        self.status = status

        self.lifecycle.transition(
            LifecycleStage.ACTIVE,
            reason=f"Attribution created for {conclusion_type} {conclusion_id[:8]}...",
        )

    def update_confidence(self, new_confidence: float) -> None:
        """Update the attribution confidence."""
        self.confidence = new_confidence
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Confidence updated to {new_confidence:.4f}",
        )

    def update_status(self, new_status: str) -> None:
        """Update the attribution status."""
        self.status = new_status
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Status updated to {new_status}",
        )

    def link_market_memory(self, memory_id: str) -> None:
        """Link a MarketMemory object to this attribution."""
        if memory_id not in self.market_memory_ids:
            self.market_memory_ids.append(memory_id)
            self.lifecycle.transition(
                LifecycleStage.UPDATED,
                reason=f"Market memory link added: {memory_id[:8]}...",
            )

    def verify_integrity(self, available_ids: set) -> dict[str, Any]:
        """Verify that all referenced objects exist.

        Args:
            available_ids: Set of object IDs that exist in the repository.

        Returns:
            Dict with keys: complete (bool), missing_references (list),
            status (str).
        """
        all_refs = (
            [self.conclusion_id]
            + self.reasoning_object_ids
            + self.evidence_ids
            + self.observation_ids
            + self.market_memory_ids
        )
        missing = [rid for rid in all_refs if rid not in available_ids]

        ref_ratio = 1.0 - (len(missing) / max(len(all_refs), 1))
        if ref_ratio >= ATTRIBUTION_COMPLETE_THRESHOLD:
            status = "Complete"
        elif ref_ratio >= ATTRIBUTION_PARTIAL_THRESHOLD:
            status = "Partial"
        else:
            status = "Broken"

        return {
            "complete": len(missing) == 0,
            "missing_references": missing,
            "status": status,
            "reference_ratio": ref_ratio,
        }

    def _to_hashable_dict(self) -> dict:
        return {
            "conclusion_id": self.conclusion_id,
            "conclusion_type": self.conclusion_type,
            "reasoning_path": self.reasoning_path,
            "reasoning_object_ids": sorted(self.reasoning_object_ids),
            "evidence_ids": sorted(self.evidence_ids),
            "observation_ids": sorted(self.observation_ids),
            "confidence": self.confidence,
            "attribution_trace": self.attribution_trace,
            "market_memory_ids": sorted(self.market_memory_ids),
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "conclusion_id": self.conclusion_id,
                "conclusion_type": self.conclusion_type,
                "reasoning_path": self.reasoning_path,
                "reasoning_object_ids": self.reasoning_object_ids,
                "evidence_ids": self.evidence_ids,
                "observation_ids": self.observation_ids,
                "confidence": self.confidence,
                "attribution_trace": self.attribution_trace,
                "market_memory_ids": self.market_memory_ids,
                "status": self.status,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> Attribution:
        obj = super().from_dict(data)
        obj.conclusion_id = data["conclusion_id"]
        obj.conclusion_type = data["conclusion_type"]
        obj.reasoning_path = list(data.get("reasoning_path", []))
        obj.reasoning_object_ids = list(data.get("reasoning_object_ids", []))
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.observation_ids = list(data.get("observation_ids", []))
        obj.confidence = data.get("confidence", 0.0)
        obj.attribution_trace = data.get("attribution_trace", "")
        obj.market_memory_ids = list(data.get("market_memory_ids", []))
        obj.status = data.get("status", "Pending")
        return obj


class AttributionGraph(BaseObject):
    """A collection of all attributions for a research cycle.

    Based on Article XVII: Object Model — AttributionGraph.

    The AttributionGraph provides a complete view of how every conclusion
    in a research cycle traces back to evidence and observations. It enables
    holistic integrity checks and confidence aggregation.

    Attributes:
        research_id: Link to Research
        attribution_ids: IDs of all Attribution objects in this graph
    """

    def __init__(
        self,
        research_id: str,
        attributions: list[Attribution] | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            seed = f"AttributionGraph|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)
        self.research_id = research_id
        self.attributions: list[Attribution] = attributions or []
        self._attribution_ids: list[str] = []

    @property
    def total_attributions(self) -> int:
        return len(self.attributions)

    @property
    def complete_count(self) -> int:
        return sum(1 for a in self.attributions if a.status == "Complete")

    @property
    def partial_count(self) -> int:
        return sum(1 for a in self.attributions if a.status == "Partial")

    @property
    def broken_count(self) -> int:
        return sum(1 for a in self.attributions if a.status == "Broken")

    @property
    def average_confidence(self) -> float:
        if not self.attributions:
            return 0.0
        return sum(a.confidence for a in self.attributions) / len(self.attributions)

    def add_attribution(self, attribution: Attribution) -> None:
        """Add an attribution to the graph."""
        self.attributions.append(attribution)

    def get_by_conclusion(self, conclusion_id: str) -> Attribution | None:
        """Get attribution for a specific conclusion."""
        for a in self.attributions:
            if a.conclusion_id == conclusion_id:
                return a
        return None

    def get_by_type(self, conclusion_type: str) -> list[Attribution]:
        """Get all attributions for a specific conclusion type."""
        return [a for a in self.attributions if a.conclusion_type == conclusion_type]

    def verify_all(self, available_ids: set) -> list[dict[str, Any]]:
        """Verify integrity of all attributions in the graph.

        Args:
            available_ids: Set of object IDs that exist.

        Returns:
            List of integrity reports, one per attribution.
        """
        return [a.verify_integrity(available_ids) for a in self.attributions]

    @property
    def attribution_ids(self) -> list[str]:
        if self.attributions:
            return [a.id for a in self.attributions]
        return self._attribution_ids

    @attribution_ids.setter
    def attribution_ids(self, value: list[str]) -> None:
        self._attribution_ids = value

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update(
            {
                "research_id": self.research_id,
                "attribution_ids": self.attribution_ids,
            }
        )
        return base

    @classmethod
    def from_dict(cls, data: dict) -> AttributionGraph:
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.attributions = []
        obj._attribution_ids = list(data.get("attribution_ids", []))
        return obj

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "attribution_ids": sorted(self.attribution_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }
