"""Production execution boundary for deterministic research.

The public research API accepts only ``ResearchInput`` plus a resolver that
materializes the already-validated dataset reference.  Raw ``HistoricalDataset``
objects therefore remain inside the data layer and cannot become an accidental
research execution input.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from researchos.data_engine.boundary import ValidatedDatasetRef
from researchos.data_engine.research_reader import ResearchSeries
from researchos.research_boundary import ResearchInput


class ResearchDataResolver(Protocol):
    """Resolve a validated dataset reference into research-safe series."""

    def resolve(self, reference: ValidatedDatasetRef) -> ResearchSeries:
        ...


@dataclass(frozen=True)
class ResearchExecutionResult:
    """Immutable envelope binding a research result to its input identity."""

    research_id: str
    dataset_id: str
    dataset_content_hash: str
    dataset_hash: str
    methodology_version: str
    result: Any

    def __post_init__(self) -> None:
        for name in (
            "research_id",
            "dataset_id",
            "dataset_content_hash",
            "dataset_hash",
            "methodology_version",
        ):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "research_id": self.research_id,
            "dataset_id": self.dataset_id,
            "dataset_content_hash": self.dataset_content_hash,
            "dataset_hash": self.dataset_hash,
            "methodology_version": self.methodology_version,
            "result": self.result.to_dict() if hasattr(self.result, "to_dict") else self.result,
        }


class ResearchExecutor:
    """Execute a research operation through the validated-data boundary."""

    def __init__(self, resolver: ResearchDataResolver):
        self._resolver = resolver

    def execute(
        self,
        research_input: ResearchInput,
        operation: Callable[[ResearchSeries, Any], Any],
        config: Any = None,
    ) -> ResearchExecutionResult:
        """Resolve validated data and execute the supplied scientific operation.

        ``operation`` receives only ``ResearchSeries`` and configuration; it
        never receives ``HistoricalDataset``.  The caller controls the
        scientific implementation while this boundary controls provenance.
        """
        if not isinstance(research_input, ResearchInput):
            raise TypeError("research execution requires ResearchInput")

        series = self._resolver.resolve(research_input.dataset)
        result = operation(series, config)
        return ResearchExecutionResult(
            research_id=research_input.research_id,
            dataset_id=research_input.dataset.dataset_id,
            dataset_content_hash=research_input.dataset.dataset_content_hash,
            dataset_hash=research_input.dataset.dataset_hash,
            methodology_version=research_input.methodology_version,
            result=result,
        )


__all__ = ["ResearchDataResolver", "ResearchExecutionResult", "ResearchExecutor"]
