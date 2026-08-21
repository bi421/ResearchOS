"""
ResearchOS Macro Intelligence Layer - Release Schedule
Version: time/schedule/v1
Status: FROZEN
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from researchos.macro.time.enums import (
    ReleaseStatus,
)
from researchos.macro.time.normalizer import UTC, TimeNormalizer


@dataclass(frozen=True)
class PlannedRelease:
    """
    Planned release schedule entry.

    Tracks:
    - Planned release time
    - Actual release time
    - Release status
    - Deviation from plan
    """

    # Identity
    release_id: str
    event_id: str
    series_id: str

    # Timing
    planned_time: datetime
    actual_time: datetime | None = None
    estimated_time: datetime | None = None

    # Status
    status: ReleaseStatus = ReleaseStatus.PLANNED

    # Deviation
    delay_minutes: int = 0
    cancellation_reason: str | None = None

    # Metadata
    source: str = ""
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)

    # Generated
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: str = "time/schedule/v1"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "release_id": self.release_id,
            "event_id": self.event_id,
            "series_id": self.series_id,
            "planned_time": TimeNormalizer.get_deterministic_timestamp(self.planned_time),
            "actual_time": (TimeNormalizer.get_deterministic_timestamp(self.actual_time) if self.actual_time else None),
            "estimated_time": (TimeNormalizer.get_deterministic_timestamp(self.estimated_time) if self.estimated_time else None),
            "status": self.status.value,
            "delay_minutes": self.delay_minutes,
            "cancellation_reason": self.cancellation_reason,
            "source": self.source,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": TimeNormalizer.get_deterministic_timestamp(self.created_at),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlannedRelease:
        """Deserialize from dictionary."""
        return cls(
            release_id=data["release_id"],
            event_id=data["event_id"],
            series_id=data["series_id"],
            planned_time=TimeNormalizer.parse_deterministic_timestamp(data["planned_time"]),
            actual_time=(TimeNormalizer.parse_deterministic_timestamp(data["actual_time"]) if data.get("actual_time") else None),
            estimated_time=(TimeNormalizer.parse_deterministic_timestamp(data["estimated_time"]) if data.get("estimated_time") else None),
            status=ReleaseStatus(data["status"]),
            delay_minutes=data.get("delay_minutes", 0),
            cancellation_reason=data.get("cancellation_reason"),
            source=data.get("source", ""),
            confidence=data.get("confidence", 0.0),
            metadata=data.get("metadata", {}),
            created_at=TimeNormalizer.parse_deterministic_timestamp(
                data.get("created_at", TimeNormalizer.get_deterministic_timestamp(datetime.now(UTC)))
            ),
            version=data.get("version", "time/schedule/v1"),
        )

    def to_json(self) -> str:
        """Serialize to JSON with deterministic ordering."""
        import json

        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> PlannedRelease:
        """Deserialize from JSON."""
        import json

        data = json.loads(json_str)
        return cls.from_dict(data)

    def compute_hash(self) -> str:
        """
        Compute deterministic hash.

        MIL-TIME-001: All timestamps are stored in UTC.
        """
        import hashlib

        hash_data = {
            "release_id": self.release_id,
            "event_id": self.event_id,
            "series_id": self.series_id,
            "planned_time": TimeNormalizer.get_deterministic_timestamp(self.planned_time),
            "actual_time": (TimeNormalizer.get_deterministic_timestamp(self.actual_time) if self.actual_time else None),
            "status": self.status.value,
            "delay_minutes": self.delay_minutes,
        }
        canonical = __import__("json").dumps(hash_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the planned release.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Validate release_id format
        if not self.release_id.startswith("REL_"):
            errors.append("release_id must start with 'REL_'")

        # Validate planned_time is in UTC
        if self.planned_time.tzinfo != UTC:
            errors.append("planned_time must be in UTC")

        # Validate actual_time >= planned_time if set
        if self.actual_time and self.actual_time < self.planned_time:
            errors.append("actual_time cannot be before planned_time")

        # Validate status transitions
        if self.status == ReleaseStatus.COMPLETED and not self.actual_time:
            errors.append("COMPLETED status requires actual_time")

        if self.status == ReleaseStatus.CANCELLED and not self.cancellation_reason:
            errors.append("CANCELLED status requires cancellation_reason")

        return (len(errors) == 0, errors)

    def get_delay_seconds(self) -> int:
        """Get delay in seconds from planned to actual."""
        if self.actual_time and self.planned_time:
            delta = self.actual_time - self.planned_time
            return int(delta.total_seconds())
        return 0


@dataclass(frozen=True)
class ReleaseSchedule:
    """
    Complete release schedule for a series.

    MIL-TIME-002: Release history is immutable.
    """

    series_id: str
    releases: list[PlannedRelease] = field(default_factory=list)

    def __post_init__(self):
        """Validate the release schedule."""
        # Sort by planned_time
        sorted_releases = sorted(self.releases, key=lambda r: r.planned_time)
        object.__setattr__(self, "releases", sorted_releases)

    def get_release(self, release_id: str) -> PlannedRelease | None:
        """Get release by ID."""
        for release in self.releases:
            if release.release_id == release_id:
                return release
        return None

    def get_releases_in_range(
        self,
        start: datetime,
        end: datetime,
    ) -> list[PlannedRelease]:
        """Get releases in time range."""
        start_utc = TimeNormalizer.to_utc(start)
        end_utc = TimeNormalizer.to_utc(end)

        return [release for release in self.releases if start_utc <= release.planned_time <= end_utc]

    def get_latest_release(self) -> PlannedRelease | None:
        """Get latest release."""
        return self.releases[-1] if self.releases else None

    def get_pending_releases(self) -> list[PlannedRelease]:
        """Get pending (not yet released) releases."""
        return [
            release
            for release in self.releases
            if release.status
            in (
                ReleaseStatus.PLANNED,
                ReleaseStatus.ACTIVE,
            )
        ]

    def get_release_count(self) -> int:
        """Get total number of releases."""
        return len(self.releases)

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """
        Verify schedule integrity.

        MIL-TIME-002: Release history is immutable.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check for duplicate release IDs
        release_ids = [r.release_id for r in self.releases]
        if len(release_ids) != len(set(release_ids)):
            errors.append("Duplicate release IDs detected")

        # Check for overlapping releases
        for i in range(len(self.releases) - 1):
            current = self.releases[i]
            next_release = self.releases[i + 1]

            # Check if next release is before current
            if next_release.planned_time < current.planned_time:
                errors.append(f"Release {next_release.release_id} is before {current.release_id}")

        # Validate each release
        for release in self.releases:
            is_valid, release_errors = release.validate()
            if not is_valid:
                errors.extend(release_errors)

        return (len(errors) == 0, errors)
