"""
ResearchOS Macro Intelligence Layer - NormalizedSeries Contract
Version: ms/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from researchos.macro.contracts.enums import FrequencyEnum, SeriesType


@dataclass(frozen=True)
class NormalizedSeries:
    """
    Canonical representation of macroeconomic time-series data.

    Version: ms/v1
    Immutable: Yes (frozen=True)
    Required fields: All
    """

    # Core identification
    series_id: str
    source: str

    # Time dimensions
    timestamp: datetime
    observation_period: date
    release_time: datetime | None
    available_time: datetime

    # Data
    value: float | None
    unit: str
    frequency: FrequencyEnum
    series_type: SeriesType = SeriesType.LEVEL

    # Revision tracking
    revision_id: str | None = None
    revision_number: int = 0
    quality_score: float = 1.0

    # Provenance
    metadata: dict = field(default_factory=dict)

    # Generated fields
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "ms/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary with deterministic ordering."""
        return {
            "series_id": self.series_id,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "observation_period": self.observation_period.isoformat(),
            "release_time": self.release_time.isoformat() if self.release_time else None,
            "available_time": self.available_time.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "frequency": self.frequency.value,
            "series_type": self.series_type.value,
            "revision_id": self.revision_id,
            "revision_number": self.revision_number,
            "quality_score": self.quality_score,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NormalizedSeries:
        """Deserialize from dictionary."""
        return cls(
            series_id=data["series_id"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            observation_period=date.fromisoformat(data["observation_period"]),
            release_time=(
                datetime.fromisoformat(data["release_time"]) if data.get("release_time") else None
            ),
            available_time=datetime.fromisoformat(data["available_time"]),
            value=data.get("value"),
            unit=data["unit"],
            frequency=FrequencyEnum(data["frequency"]),
            series_type=SeriesType(data.get("series_type", "level")),
            revision_id=data.get("revision_id"),
            revision_number=data.get("revision_number", 0),
            quality_score=data.get("quality_score", 1.0),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
            version=data.get("version", "ms/v1"),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> NormalizedSeries:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """
        Compute deterministic hash for the record.

        MIL-DET-001: Hash depends ONLY on semantic data, never on runtime metadata.

        Allowed hash fields:
        - series_id, timestamp, observation_period
        - value, unit, frequency
        - source, revision_id, quality_score

        Forbidden hash fields:
        - created_at (runtime metadata)
        - version (schema version, not semantic)

        Returns:
            SHA-256 hex digest of canonical representation
        """
        import hashlib

        # Create hash-specific dict excluding runtime metadata
        hash_data = {
            "series_id": self.series_id,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "observation_period": self.observation_period.isoformat(),
            "release_time": self.release_time.isoformat() if self.release_time else None,
            "available_time": self.available_time.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "frequency": self.frequency.value,
            "revision_id": self.revision_id,
            "revision_number": self.revision_number,
            "quality_score": self.quality_score,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the series record.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Validate series_id format
        if not self.series_id.startswith("SER_"):
            errors.append("series_id must start with 'SER_'")

        # Validate timestamp is UTC
        if self.timestamp.tzinfo is None:
            errors.append("timestamp must have timezone info")

        # Validate quality_score range
        if not (0.0 <= self.quality_score <= 1.0):
            errors.append("quality_score must be between 0.0 and 1.0")

        # Validate unit
        valid_units = {
            "index",
            "percent",
            "percent_ann",
            "basis_points",
            "thousands",
            "millions",
            "billions",
            "text",
        }
        if self.unit not in valid_units:
            errors.append(f"Invalid unit: {self.unit}")

        return (len(errors) == 0, errors)
