from __future__ import annotations

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id


class Contradiction(BaseObject):
    """
    Represents a contradiction between evidence, claims, or observations.
    """

    def __init__(
        self,
        research_id: str = "",
        type: str = "Internal",
        description: str = "",
        sides: list[dict] | None = None,
        evidence_id_a: str | None = None,
        evidence_id_b: str | None = None,
        severity: float | None = None,
        resolution: str | None = None,
        status: str = "UNRESOLVED",
        ontology_tags: list[str] | None = None,
        id: str | None = None,
        **kwargs,
    ):
        if id is None:
            id = generate_id(f"Contradiction|{research_id}|{type}|{description}|{evidence_id_a}|{evidence_id_b}")

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.research_id = research_id
        self.type = type
        self.description = description

        self.sides = [dict(side) for side in (sides or [])]

        self.evidence_id_a = evidence_id_a
        self.evidence_id_b = evidence_id_b

        if evidence_id_a is not None:
            self.sides.append({"evidence": [evidence_id_a]})

        if evidence_id_b is not None:
            self.sides.append({"evidence": [evidence_id_b]})

        self.severity = float(severity) if severity is not None else self._compute_severity()

        self.resolution = resolution if resolution is not None else "Unresolved"
        self.status = status.title() if status else "Unresolved"

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.validate()

    def _compute_severity(self) -> float:
        return 0.5

    def validate(self) -> bool:
        if not self.description:
            raise ValueError("Contradiction description cannot be empty")

        if not 0.0 <= self.severity <= 1.0:
            raise ValueError("Contradiction severity must be between 0.0 and 1.0")

        return True

    def resolve(
        self,
        resolution: str | None = None,
        reason: str | None = None,
    ):
        if resolution is None:
            resolution = "Resolved"

        self.resolution = resolution
        self.status = "Resolved"

        if reason:
            self.resolution_reason = reason

        self._hash = None

        return True

    @property
    def is_resolved(self) -> bool:
        return self.status.lower() == "resolved"

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "type": self.type,
            "description": self.description,
            "sides": self.sides,
            "evidence_id_a": self.evidence_id_a,
            "evidence_id_b": self.evidence_id_b,
            "severity": self.severity,
            "resolution": self.resolution,
            "status": self.status,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update(self._to_hashable_dict())

        if hasattr(self, "resolution_reason"):
            data["resolution_reason"] = self.resolution_reason

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> Contradiction:
        obj = super().from_dict(data)

        obj.research_id = data.get(
            "research_id",
            "",
        )
        obj.type = data.get(
            "type",
            "Internal",
        )
        obj.description = data.get(
            "description",
            "",
        )

        obj.sides = [dict(side) for side in data.get("sides", [])]

        obj.evidence_id_a = data.get("evidence_id_a")
        obj.evidence_id_b = data.get("evidence_id_b")

        obj.severity = float(data.get("severity", 0.5))

        obj.resolution = data.get("resolution")
        obj.status = data.get(
            "status",
            "UNRESOLVED",
        )

        if "resolution_reason" in data:
            obj.resolution_reason = data["resolution_reason"]

        return obj


class ContradictionReport(BaseObject):
    def __init__(
        self,
        research_id: str,
        contradictions: list[Contradiction] | None = None,
        contradiction_ids: list[str] | None = None,
        ontology_tags: list[str] | None = None,
        id: str | None = None,
    ):
        if id is None:
            id = generate_id(f"ContradictionReport|{research_id}")

        super().__init__(
            id=id,
            ontology_tags=ontology_tags,
        )

        self.research_id = research_id
        self.contradictions = list(contradictions or [])

        self.contradiction_ids = list(contradiction_ids if contradiction_ids is not None else [c.id for c in self.contradictions])

    def add_contradiction(
        self,
        contradiction: Contradiction,
    ) -> None:
        self.contradictions.append(contradiction)

        if contradiction.id not in self.contradiction_ids:
            self.contradiction_ids.append(contradiction.id)

        self._hash = None

    def add(
        self,
        contradiction: Contradiction,
    ) -> None:
        self.add_contradiction(contradiction)

    @property
    def has_contradictions(self) -> bool:
        return bool(self.contradictions)

    def _to_hashable_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "contradiction_ids": sorted(self.contradiction_ids),
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> dict:
        data = super().to_dict()

        data.update(
            {
                "research_id": self.research_id,
                "contradiction_ids": list(self.contradiction_ids),
                "contradictions": [c.to_dict() for c in self.contradictions],
            }
        )

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> ContradictionReport:
        obj = super().from_dict(data)

        obj.research_id = data["research_id"]

        obj.contradictions = [
            Contradiction.from_dict(c)
            for c in data.get(
                "contradictions",
                [],
            )
        ]

        obj.contradiction_ids = list(
            data.get(
                "contradiction_ids",
                [c.id for c in obj.contradictions],
            )
        )

        return obj
