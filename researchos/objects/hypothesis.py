from __future__ import annotations

from typing import Any

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id


class Hypothesis(BaseObject):
    """
    Research hypothesis.

    Supports evidence/narrative linkage, deterministic ranking,
    invalidation tracking, serialization, and validation.
    """

    def __init__(
        self,
        research_id: str,
        type: str,
        statement: str,
        evidence_strength: float = 0.0,
        coherence: float = 0.0,
        plausibility: float = 0.0,
        falsifiability: float = 0.0,
        narrative_id: str | None = None,
        evidence_ids: list[str] | None = None,
        invalid_if: Any | None = None,
        status: str = "ACTIVE",
        rank_score: float | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
        **kwargs,
    ):
        for name, value in [
            ("evidence_strength", evidence_strength),
            ("coherence", coherence),
            ("plausibility", plausibility),
            ("falsifiability", falsifiability),
        ]:
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {value}")

        if id is None:
            seed = f"Hypothesis|{research_id}|{type}|{statement}|{narrative_id}|{sorted(evidence_ids or [])}"
            id = generate_id(seed)

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.research_id = research_id
        self.type = type
        self.statement = statement

        self.evidence_strength = float(evidence_strength)
        self.coherence = float(coherence)
        self.plausibility = float(plausibility)
        self.falsifiability = float(falsifiability)

        self.narrative_id = narrative_id
        self.evidence_ids = list(evidence_ids or [])
        self.invalid_if = invalid_if

        self.status = status.title() if status else "Active"

        self.rank_score = float(rank_score) if rank_score is not None else self.compute_rank_score()

        for key, value in kwargs.items():
            setattr(self, key, value)

    def compute_rank_score(self) -> float:
        return 0.40 * self.evidence_strength + 0.30 * self.coherence + 0.20 * self.plausibility + 0.10 * self.falsifiability

    def validate(self) -> bool:
        if not self.research_id:
            raise ValueError("research_id cannot be empty")

        if not self.type:
            raise ValueError("type cannot be empty")

        if not self.statement:
            raise ValueError("statement cannot be empty")

        for name in (
            "evidence_strength",
            "coherence",
            "plausibility",
            "falsifiability",
        ):
            value = getattr(self, name)

            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0")

        return True

    def check_invalidation(self, evidence_ids) -> bool:
        if self.invalid_if is None:
            return False

        supplied = set(evidence_ids or [])

        if isinstance(self.invalid_if, str):
            invalidated = self.invalid_if in supplied
        else:
            try:
                required = set(self.invalid_if)
            except TypeError:
                return False

            invalidated = bool(required.intersection(supplied))

        if invalidated:
            self.status = "Invalidated"
            self._hash = None

        return invalidated

    def rank(self) -> float:
        self.rank_score = self.compute_rank_score()
        self._hash = None
        return self.rank_score

    def invalidate(self, reason: str | None = None) -> None:
        self.status = "Invalidated"

        if reason is not None:
            self.invalid_if = reason

        self._hash = None

    def is_valid(self) -> bool:
        return self.status.upper() not in {
            "INVALID",
            "INVALIDATED",
            "REJECTED",
            "FALSIFIED",
        }

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "type": self.type,
            "statement": self.statement,
            "evidence_strength": self.evidence_strength,
            "coherence": self.coherence,
            "plausibility": self.plausibility,
            "falsifiability": self.falsifiability,
            "narrative_id": self.narrative_id,
            "evidence_ids": sorted(self.evidence_ids),
            "invalid_if": self.invalid_if,
            "status": self.status,
            "rank_score": self.rank_score,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(self._to_hashable_dict())
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Hypothesis:
        obj = super().from_dict(data)

        obj.research_id = data["research_id"]
        obj.type = data["type"]
        obj.statement = data["statement"]

        obj.evidence_strength = float(data.get("evidence_strength", 0.0))
        obj.coherence = float(data.get("coherence", 0.0))
        obj.plausibility = float(data.get("plausibility", 0.0))
        obj.falsifiability = float(data.get("falsifiability", 0.0))

        obj.narrative_id = data.get("narrative_id")
        obj.evidence_ids = list(data.get("evidence_ids", []))
        obj.invalid_if = data.get("invalid_if")
        obj.status = data.get("status", "ACTIVE")

        obj.rank_score = float(
            data.get(
                "rank_score",
                obj.compute_rank_score(),
            )
        )

        return obj


class HypothesisSet(BaseObject):
    """
    Deterministic collection of hypotheses.

    Ranking contract:
        1. Higher rank_score first.
        2. ID ascending as deterministic tie-breaker.
    """

    def __init__(
        self,
        research_id: str,
        hypotheses: list[Hypothesis] | None = None,
        hypothesis_ids: list[str] | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            id = generate_id(f"HypothesisSet|{research_id}")

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.research_id = research_id
        self.hypotheses = list(hypotheses or [])

        self.hypothesis_ids = list(hypothesis_ids if hypothesis_ids is not None else [h.id for h in self.hypotheses])

    def add_hypothesis(
        self,
        hypothesis: Hypothesis,
    ) -> None:
        self.hypotheses.append(hypothesis)

        if hypothesis.id not in self.hypothesis_ids:
            self.hypothesis_ids.append(hypothesis.id)

        self._hash = None

    def get_hypothesis(
        self,
        hypothesis_id: str,
    ) -> Hypothesis | None:
        for hypothesis in self.hypotheses:
            if hypothesis.id == hypothesis_id:
                return hypothesis

        return None

    def get_ranked(self) -> list[Hypothesis]:
        """
        Return hypotheses sorted deterministically.

        Primary key:
            rank_score descending

        Tie-break:
            hypothesis ID ascending
        """
        return sorted(
            self.hypotheses,
            key=lambda hypothesis: (
                -hypothesis.rank_score,
                hypothesis.id,
            ),
        )

    @property
    def has_hypotheses(self) -> bool:
        return bool(self.hypotheses)

    def validate(self) -> bool:
        if not self.hypotheses:
            return False

        for hypothesis in self.hypotheses:
            hypothesis.validate()

        return True

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "hypothesis_ids": sorted(self.hypothesis_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()

        data.update(
            {
                "research_id": self.research_id,
                "hypothesis_ids": list(self.hypothesis_ids),
                "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            }
        )

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> HypothesisSet:
        obj = super().from_dict(data)

        obj.research_id = data["research_id"]

        obj.hypotheses = [Hypothesis.from_dict(item) for item in data.get("hypotheses", [])]

        obj.hypothesis_ids = list(
            data.get(
                "hypothesis_ids",
                [h.id for h in obj.hypotheses],
            )
        )

        return obj
