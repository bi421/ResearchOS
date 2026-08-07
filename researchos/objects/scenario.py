"""
Scenario objects — probabilistic future market states.

Based on Article XVII: Object Model — Scenario Layer.
Based on Article XVI: Scientific Reasoning Framework — Scenario Layer.

Scenarios are constructed from hypotheses and represent possible future
market states with associated probabilities.
"""

from __future__ import annotations

from typing import List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id
from researchos.core.lifecycle import LifecycleStage


class Scenario(BaseObject):
    """
    A probabilistic future market state.

    Based on Article XVII: Object Model — Scenario.

    Scenarios are constructed from hypotheses:
        - Base Scenario: Derived from the primary hypothesis
        - Bull Scenario: Derived from the optimistic alternative
        - Bear Scenario: Derived from the pessimistic alternative
        - Tail Scenarios: Derived from invalidation conditions

    Attributes:
        hypothesis_id: Link to source Hypothesis
        type: Base, Bull, Bear, or Tail
        label: Human-readable label (e.g., "Scenario A")
        thesis: The scenario thesis
        probability: Raw probability (0.0-1.0)
        calibrated_probability: After calibration
        confidence_interval: {lower, upper} bounds
        expected_return: Expected return
        return_range: {p5, p95} bounds
        volatility: Expected volatility
        regime: Expected market regime
        assumptions: Key assumptions
        dependencies: Other scenarios or conditions this depends on
        valid_if: Conditions that make this valid
        invalid_if: Conditions that make this invalid
        supporting_evidence: Evidence IDs supporting this scenario
        contradicting_evidence: Evidence IDs contradicting this scenario
        milestones: Confirmation/refutation events
        construction_trace: How this scenario was built
        status: Active, Valid, Invalidated, or Resolved
    """

    def __init__(
        self,
        hypothesis_id: str,
        type: str = "Base",
        label: str = "Scenario A",
        thesis: str = "",
        probability: float = 0.0,
        calibrated_probability: Optional[float] = None,
        confidence_interval: Optional[dict] = None,
        expected_return: float = 0.0,
        return_range: Optional[dict] = None,
        volatility: float = 0.0,
        regime: str = "",
        assumptions: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        valid_if: Optional[List[str]] = None,
        invalid_if: Optional[List[str]] = None,
        supporting_evidence: Optional[List[str]] = None,
        contradicting_evidence: Optional[List[str]] = None,
        milestones: Optional[List[str]] = None,
        construction_trace: str = "",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"Scenario|{hypothesis_id}|{type}|{label}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.hypothesis_id = hypothesis_id
        self.type = type
        self.label = label
        self.thesis = thesis
        self.probability = probability
        self.calibrated_probability = calibrated_probability or probability
        self.confidence_interval = confidence_interval or {"lower": 0.0, "upper": 1.0}
        self.expected_return = expected_return
        self.return_range = return_range or {"p5": 0.0, "p95": 0.0}
        self.volatility = volatility
        self.regime = regime
        self.assumptions: List[str] = assumptions or []
        self.dependencies: List[str] = dependencies or []
        self.valid_if: List[str] = valid_if or []
        self.invalid_if: List[str] = invalid_if or []
        self.supporting_evidence: List[str] = supporting_evidence or []
        self.contradicting_evidence: List[str] = contradicting_evidence or []
        self.milestones: List[str] = milestones or []
        self.construction_trace = construction_trace
        self.status = "Active"

        self.lifecycle.transition(
            LifecycleStage.ACTIVE,
            reason="Scenario constructed from hypothesis",
        )

    def check_invalidation(self, current_evidence: List[str]) -> bool:
        """Check if this scenario has been invalidated."""
        for condition in self.invalid_if:
            if condition in current_evidence:
                self.status = "Invalidated"
                self.lifecycle.transition(
                    LifecycleStage.INVALIDATED,
                    reason=f"Invalidation condition met: {condition}",
                )
                return True
        return False

    def update_probability(self, new_probability: float) -> None:
        """Update the scenario probability."""
        self.probability = new_probability
        self.lifecycle.transition(
            LifecycleStage.UPDATED,
            reason=f"Probability updated to {new_probability}",
        )

    def _to_hashable_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "type": self.type,
            "label": self.label,
            "thesis": self.thesis,
            "probability": self.probability,
            "calibrated_probability": self.calibrated_probability,
            "confidence_interval": self.confidence_interval,
            "expected_return": self.expected_return,
            "return_range": self.return_range,
            "volatility": self.volatility,
            "regime": self.regime,
            "assumptions": sorted(self.assumptions),
            "dependencies": sorted(self.dependencies),
            "valid_if": sorted(self.valid_if),
            "invalid_if": sorted(self.invalid_if),
            "supporting_evidence": sorted(self.supporting_evidence),
            "contradicting_evidence": sorted(self.contradicting_evidence),
            "milestones": sorted(self.milestones),
            "construction_trace": self.construction_trace,
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "hypothesis_id": self.hypothesis_id,
            "type": self.type,
            "label": self.label,
            "thesis": self.thesis,
            "probability": self.probability,
            "calibrated_probability": self.calibrated_probability,
            "confidence_interval": self.confidence_interval,
            "expected_return": self.expected_return,
            "return_range": self.return_range,
            "volatility": self.volatility,
            "regime": self.regime,
            "assumptions": self.assumptions,
            "dependencies": self.dependencies,
            "valid_if": self.valid_if,
            "invalid_if": self.invalid_if,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "milestones": self.milestones,
            "construction_trace": self.construction_trace,
            "status": self.status,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Scenario":
        obj = super().from_dict(data)
        obj.hypothesis_id = data["hypothesis_id"]
        obj.type = data.get("type", "Base")
        obj.label = data.get("label", "Scenario A")
        obj.thesis = data.get("thesis", "")
        obj.probability = data.get("probability", 0.0)
        obj.calibrated_probability = data.get("calibrated_probability", obj.probability)
        obj.confidence_interval = data.get("confidence_interval", {"lower": 0.0, "upper": 1.0})
        obj.expected_return = data.get("expected_return", 0.0)
        obj.return_range = data.get("return_range", {"p5": 0.0, "p95": 0.0})
        obj.volatility = data.get("volatility", 0.0)
        obj.regime = data.get("regime", "")
        obj.assumptions = list(data.get("assumptions", []))
        obj.dependencies = list(data.get("dependencies", []))
        obj.valid_if = list(data.get("valid_if", []))
        obj.invalid_if = list(data.get("invalid_if", []))
        obj.supporting_evidence = list(data.get("supporting_evidence", []))
        obj.contradicting_evidence = list(data.get("contradicting_evidence", []))
        obj.milestones = list(data.get("milestones", []))
        obj.construction_trace = data.get("construction_trace", "")
        obj.status = data.get("status", "Active")
        return obj


class ScenarioSet(BaseObject):
    """
    A collection of all scenarios for a research cycle.

    Based on Article XVII: Object Model — ScenarioSet.
    """

    def __init__(
        self,
        research_id: str,
        scenarios: Optional[List[Scenario]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"ScenarioSet|{research_id}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)
        self.research_id = research_id
        self.scenarios: List[Scenario] = scenarios or []
        self._scenario_ids: List[str] = []

    @property
    def base_id(self) -> Optional[str]:
        for s in self.scenarios:
            if s.type == "Base":
                return s.id
        return None

    @property
    def bull_id(self) -> Optional[str]:
        for s in self.scenarios:
            if s.type == "Bull":
                return s.id
        return None

    @property
    def bear_id(self) -> Optional[str]:
        for s in self.scenarios:
            if s.type == "Bear":
                return s.id
        return None

    @property
    def tail_ids(self) -> List[str]:
        return [s.id for s in self.scenarios if s.type == "Tail"]

    @property
    def total_probability(self) -> float:
        """Total probability (must sum to 1.0)."""
        return sum(s.probability for s in self.scenarios)

    def add_scenario(self, scenario: Scenario) -> None:
        """Add a scenario to the set."""
        self.scenarios.append(scenario)

    def normalize_probabilities(self, precision: int = 6) -> None:
        """
        Normalize probabilities so they sum to 1.0.

        Uses deterministic rounding to avoid floating-point drift.

        Args:
            precision: Number of decimal places for rounding (default 6).
        """
        total = self.total_probability
        if total > 0:
            for s in self.scenarios:
                s.probability = round(s.probability / total, precision)
                s.calibrated_probability = s.probability

    @property
    def scenario_ids(self) -> List[str]:
        if self.scenarios:
            return [s.id for s in self.scenarios]
        return self._scenario_ids

    @scenario_ids.setter
    def scenario_ids(self, value: List[str]) -> None:
        self._scenario_ids = value

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({
            "research_id": self.research_id,
            "scenario_ids": self.scenario_ids,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "ScenarioSet":
        obj = super().from_dict(data)
        obj.research_id = data["research_id"]
        obj.scenarios = []
        obj._scenario_ids = list(data.get("scenario_ids", []))
        return obj

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "scenario_ids": sorted(self.scenario_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }
