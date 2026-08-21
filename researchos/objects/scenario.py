from __future__ import annotations

from typing import Optional, List

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id


class Scenario(BaseObject):
    """
    A possible future state associated with a hypothesis.

    Construction is permissive enough for object creation tests.
    Semantic validation is performed by validate().
    """

    VALID_TYPES = {
        "BASE",
        "BULL",
        "BEAR",
        "BULLISH",
        "BEARISH",
        "NEUTRAL",
        "UPSIDE",
        "DOWNSIDE",
        "RISK",
        "CUSTOM",
    }

    def __init__(
        self,
        hypothesis_id: str,
        type: str,
        probability: float = 0.0,
        narrative: str = "",
        label: Optional[str] = None,
        thesis: Optional[str] = None,
        calibrated_probability: Optional[float] = None,
        expected_return: Optional[float] = None,
        status: str = "ACTIVE",
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        **kwargs,
    ):
        probability = float(probability)

        if probability < 0.0 or probability > 1.0:
            raise ValueError("Scenario probability must be between 0.0 and 1.0")

        if id is None:
            id = generate_id(f"Scenario|{hypothesis_id}|{type}|{label or ''}")

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.hypothesis_id = hypothesis_id
        self.type = type
        self.probability = probability
        self.narrative = narrative
        self.label = label
        self.thesis = thesis
        self.calibrated_probability = calibrated_probability
        self.expected_return = expected_return
        self.status = status.title() if status else "Active"

        for key, value in kwargs.items():
            setattr(self, key, value)

    def validate(self) -> bool:
        if not self.hypothesis_id:
            raise ValueError("Scenario hypothesis_id cannot be empty")

        if not self.type:
            raise ValueError("Scenario type cannot be empty")

        normalized_type = str(self.type).strip().upper()

        if normalized_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid Scenario type: {self.type}")

        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("Scenario probability must be between 0.0 and 1.0")

        if (
            self.calibrated_probability is not None
            and not 0.0 <= float(self.calibrated_probability) <= 1.0
        ):
            raise ValueError("calibrated_probability must be between 0.0 and 1.0")

        return True

    def _to_hashable_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "type": self.type,
            "probability": self.probability,
            "narrative": self.narrative,
            "label": self.label,
            "thesis": self.thesis,
            "calibrated_probability": self.calibrated_probability,
            "expected_return": self.expected_return,
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(self._to_hashable_dict())
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Scenario":
        obj = super().from_dict(data)

        obj.hypothesis_id = data["hypothesis_id"]
        obj.type = data["type"]
        obj.probability = float(data.get("probability", 0.0))
        obj.narrative = data.get("narrative", "")
        obj.label = data.get("label")
        obj.thesis = data.get("thesis")
        obj.calibrated_probability = data.get("calibrated_probability")
        obj.expected_return = data.get("expected_return")
        obj.status = data.get(
            "status",
            "ACTIVE",
        )

        return obj


class ScenarioSet(BaseObject):
    """
    Deterministic collection of scenarios.
    """

    def __init__(
        self,
        research_id: str,
        scenarios: Optional[List[Scenario]] = None,
        scenario_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            id = generate_id(f"ScenarioSet|{research_id}")

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.research_id = research_id
        self.scenarios = list(scenarios or [])

        self.scenario_ids = list(
            scenario_ids if scenario_ids is not None else [s.id for s in self.scenarios]
        )

    def add_scenario(
        self,
        scenario: Scenario,
    ) -> None:
        self.scenarios.append(scenario)

        if scenario.id not in self.scenario_ids:
            self.scenario_ids.append(scenario.id)

        self._hash = None

    @property
    def total_probability(self) -> float:
        return sum(scenario.probability for scenario in self.scenarios)

    def normalize_probabilities(
        self,
        precision: int = 6,
    ) -> None:
        if not self.scenarios:
            raise ValueError("Cannot normalize an empty ScenarioSet")

        if precision < 0:
            raise ValueError("precision must be non-negative")

        total = sum(scenario.probability for scenario in self.scenarios)

        if total <= 0.0:
            raise ValueError("Cannot normalize ScenarioSet with zero total probability")

        for scenario in self.scenarios:
            scenario.probability = round(
                scenario.probability / total,
                precision,
            )

        current = round(
            sum(scenario.probability for scenario in self.scenarios),
            precision,
        )

        target = round(1.0, precision)

        if current != target:
            delta = round(
                target - current,
                precision,
            )

            ordered = sorted(
                self.scenarios,
                key=lambda scenario: scenario.id,
            )

            repaired = round(
                ordered[0].probability + delta,
                precision,
            )

            if repaired < 0.0 or repaired > 1.0:
                raise ValueError("Rounding repair produced invalid probability")

            ordered[0].probability = repaired

        self._hash = None

    def get_scenario(
        self,
        scenario_type: str,
    ) -> Optional[Scenario]:
        for scenario in self.scenarios:
            if scenario.type == scenario_type:
                return scenario

        return None

    @property
    def has_scenarios(self) -> bool:
        return bool(self.scenarios)

    def validate(self) -> bool:
        if not self.scenarios:
            return False

        for scenario in self.scenarios:
            scenario.validate()

        total = self.total_probability

        return abs(total - 1.0) < 1e-9

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "scenario_ids": sorted(self.scenario_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()

        data.update(
            {
                "research_id": self.research_id,
                "scenario_ids": list(self.scenario_ids),
                "scenarios": [scenario.to_dict() for scenario in self.scenarios],
                "total_probability": self.total_probability,
            }
        )

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ScenarioSet":
        obj = super().from_dict(data)

        obj.research_id = data["research_id"]

        obj.scenarios = [Scenario.from_dict(item) for item in data.get("scenarios", [])]

        obj.scenario_ids = list(
            data.get(
                "scenario_ids",
                [scenario.id for scenario in obj.scenarios],
            )
        )

        return obj
