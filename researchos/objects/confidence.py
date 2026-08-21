from __future__ import annotations

from typing import Optional, List

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id


class Confidence(BaseObject):
    """
    Confidence assessment attached to a research object.
    """

    def __init__(
        self,
        target_id: str,
        target_type: str = "",
        score: Optional[float] = None,
        rationale: str = "",
        evidence_strength: float = 0.0,
        coherence: float = 0.0,
        historical_precedent: float = 0.0,
        model_uncertainty: float = 0.0,
        recency: float = 0.0,
        penalties: Optional[List[str]] = None,
        boosters: Optional[List[str]] = None,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
        calibration_bin: Optional[str] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        **kwargs,
    ):
        factors = [
            evidence_strength,
            coherence,
            historical_precedent,
            model_uncertainty,
            recency,
        ]

        for factor in factors:
            if not 0.0 <= float(factor) <= 1.0:
                raise ValueError("Confidence factors must be between 0.0 and 1.0")

        if id is None:
            id = generate_id(f"Confidence|{target_id}|{target_type}")

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.target_id = target_id
        self.target_type = target_type
        self.rationale = rationale

        self.evidence_strength = float(evidence_strength)
        self.coherence = float(coherence)
        self.historical_precedent = float(historical_precedent)
        self.model_uncertainty = float(model_uncertainty)
        self.recency = float(recency)

        self.penalties = list(penalties or [])
        self.boosters = list(boosters or [])

        self.value = float(score) if score is not None else self._compute_value()

        self.lower_bound = (
            float(lower_bound) if lower_bound is not None else max(0.0, self.value - 0.1)
        )

        self.upper_bound = (
            float(upper_bound) if upper_bound is not None else min(1.0, self.value + 0.1)
        )

        self.calibration_bin = (
            calibration_bin if calibration_bin is not None else self._compute_calibration_bin()
        )

        for key, value in kwargs.items():
            setattr(self, key, value)

    def _compute_value(self) -> float:
        factors = [
            self.evidence_strength,
            self.coherence,
            self.historical_precedent,
            self.model_uncertainty,
            self.recency,
        ]

        return max(
            0.0,
            min(
                1.0,
                sum(factors) / len(factors),
            ),
        )

    def _compute_calibration_bin(self) -> str:
        lower = int(self.value * 10) / 10

        if lower >= 1.0:
            lower = 0.9

        upper = lower + 0.1

        return f"{lower:.1f}-{upper:.1f}"

    def validate(self) -> bool:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Confidence value must be between 0.0 and 1.0")

        if not 0.0 <= self.lower_bound <= 1.0:
            raise ValueError("Confidence lower_bound must be between 0.0 and 1.0")

        if not 0.0 <= self.upper_bound <= 1.0:
            raise ValueError("Confidence upper_bound must be between 0.0 and 1.0")

        if self.lower_bound > self.upper_bound:
            raise ValueError("Confidence lower_bound cannot exceed upper_bound")

        return True

    def _to_hashable_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "value": self.value,
            "rationale": self.rationale,
            "evidence_strength": self.evidence_strength,
            "coherence": self.coherence,
            "historical_precedent": self.historical_precedent,
            "model_uncertainty": self.model_uncertainty,
            "recency": self.recency,
            "penalties": sorted(self.penalties),
            "boosters": sorted(self.boosters),
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "calibration_bin": self.calibration_bin,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(self._to_hashable_dict())
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Confidence":
        obj = super().from_dict(data)

        obj.target_id = data["target_id"]
        obj.target_type = data.get("target_type", "")
        obj.value = float(data.get("value", 0.0))
        obj.rationale = data.get("rationale", "")

        obj.evidence_strength = float(data.get("evidence_strength", 0.0))
        obj.coherence = float(data.get("coherence", 0.0))
        obj.historical_precedent = float(data.get("historical_precedent", 0.0))
        obj.model_uncertainty = float(data.get("model_uncertainty", 0.0))
        obj.recency = float(data.get("recency", 0.0))

        obj.penalties = list(data.get("penalties", []))
        obj.boosters = list(data.get("boosters", []))

        obj.lower_bound = float(
            data.get(
                "lower_bound",
                max(0.0, obj.value - 0.1),
            )
        )

        obj.upper_bound = float(
            data.get(
                "upper_bound",
                min(1.0, obj.value + 0.1),
            )
        )

        obj.calibration_bin = data.get(
            "calibration_bin",
            obj._compute_calibration_bin(),
        )

        return obj


class ConfidenceReport(BaseObject):
    def __init__(
        self,
        research_id: str,
        confidences: Optional[List[Confidence]] = None,
        confidence_ids: Optional[List[str]] = None,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            id = generate_id(f"ConfidenceReport|{research_id}")

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.research_id = research_id
        self.confidences = list(confidences or [])

        self.confidence_ids = list(
            confidence_ids if confidence_ids is not None else [c.id for c in self.confidences]
        )

    def add_confidence(
        self,
        confidence: Confidence,
    ) -> None:
        self.confidences.append(confidence)

        if confidence.id not in self.confidence_ids:
            self.confidence_ids.append(confidence.id)

        self._hash = None

    def add(
        self,
        confidence: Confidence,
    ) -> None:
        self.add_confidence(confidence)

    @property
    def overall_confidence(self) -> float:
        if not self.confidences:
            return 0.0

        return sum(c.value for c in self.confidences) / len(self.confidences)

    @property
    def aggregate_score(self) -> float:
        return self.overall_confidence

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "confidence_ids": sorted(self.confidence_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()

        data.update(
            {
                "research_id": self.research_id,
                "confidence_ids": list(self.confidence_ids),
                "confidences": [c.to_dict() for c in self.confidences],
            }
        )

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "ConfidenceReport":
        obj = super().from_dict(data)

        obj.research_id = data["research_id"]

        obj.confidences = [Confidence.from_dict(c) for c in data.get("confidences", [])]

        obj.confidence_ids = list(
            data.get(
                "confidence_ids",
                [c.id for c in obj.confidences],
            )
        )

        return obj
