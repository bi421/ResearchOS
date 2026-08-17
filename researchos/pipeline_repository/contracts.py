"""
Pipeline Repository — immutable contracts (Q15).

The pipeline repository persists the immutable ``PipelineReport`` objects
produced by the orchestration layer (Q14).  It NEVER modifies a report:
``PipelineRecord`` objects wrap reports with storage metadata only.

Design rules:
    - frozen dataclasses; immutable; hashable; deterministic.
    - stdlib only; no randomness; no timestamps used as identifiers.
    - No modifications to any locked module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Dict, Mapping

from researchos.orchestration.contracts import PipelineReport

PIPELINE_REPOSITORY_VERSION = "1.0.0"


class PipelineRepositoryError(Exception):
    """Base class for all pipeline-repository errors."""


class PipelineNotFoundError(PipelineRepositoryError):
    """Raised when a pipeline id does not exist in the repository."""


class InvalidPipelineRecordError(PipelineRepositoryError):
    """Raised when a record, report, or payload is malformed."""


def _freeze(value: Any) -> Any:
    """Recursively convert a mapping/list value into a hashable form."""
    if isinstance(value, Mapping):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _as_immutable_mapping(value: Any) -> MappingProxyType:
    """Normalise a metadata value to an immutable mapping."""
    if isinstance(value, Mapping):
        return MappingProxyType(dict(value))
    raise InvalidPipelineRecordError(f"metadata must be a mapping, got {type(value).__name__}")


def _validate_identifier(value: Any, name: str) -> str:
    """Ensure a required identifier is a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise InvalidPipelineRecordError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class PipelineRecord:
    """Immutable wrapper linking a stored pipeline report to storage metadata.

    Attributes:
        pipeline_id: Deterministic content-derived identifier.
        report: The immutable ``PipelineReport`` (never mutated).
        stored_at: Deterministic storage timestamp string (default ``""``).
        version: Repository schema version.
        metadata: Immutable mapping of extra storage metadata.
    """

    pipeline_id: str
    report: PipelineReport
    stored_at: str
    version: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate identifiers and freeze all container fields."""
        object.__setattr__(
            self,
            "pipeline_id",
            _validate_identifier(self.pipeline_id, "pipeline_id"),
        )
        if not isinstance(self.report, PipelineReport):
            raise InvalidPipelineRecordError("report must be a PipelineReport")
        object.__setattr__(self, "stored_at", str(self.stored_at))
        object.__setattr__(
            self,
            "version",
            _validate_identifier(self.version, "version"),
        )
        object.__setattr__(self, "metadata", _as_immutable_mapping(self.metadata))

    def __hash__(self) -> int:
        return hash(
            (
                self.pipeline_id,
                hash(self.report),
                self.stored_at,
                self.version,
                _freeze(self.metadata),
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible dictionary."""
        return {
            "pipeline_id": self.pipeline_id,
            "report": self.report.to_dict(),
            "stored_at": self.stored_at,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PipelineRecord":
        """Reconstruct a ``PipelineRecord`` from a ``to_dict()`` mapping.

        Raises:
            InvalidPipelineRecordError: If the payload is malformed.
        """
        try:
            report_data = data["report"]
            if not isinstance(report_data, Mapping):
                raise InvalidPipelineRecordError("report must be a mapping")
            return cls(
                pipeline_id=str(data["pipeline_id"]),
                report=PipelineReport.from_dict(report_data),
                stored_at=str(data.get("stored_at", "")),
                version=str(data.get("version", PIPELINE_REPOSITORY_VERSION)),
                metadata=dict(data.get("metadata", {})),
            )
        except KeyError as exc:
            raise InvalidPipelineRecordError(f"missing key: {exc.args[0]}") from None
        except PipelineRepositoryError:
            raise
        except (TypeError, ValueError) as exc:
            raise InvalidPipelineRecordError(f"invalid pipeline record: {exc}") from None


__all__ = [
    "PIPELINE_REPOSITORY_VERSION",
    "InvalidPipelineRecordError",
    "PipelineNotFoundError",
    "PipelineRecord",
    "PipelineRepositoryError",
]
