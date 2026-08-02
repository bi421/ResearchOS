"""
DatasetVersioning — version tracking for market datasets.

Based on Article XVII: Object Model — Data Layer.

Dataset versions use semantic versioning (MAJOR.MINOR.PATCH):
    - MAJOR: Breaking changes to data structure or schema
    - MINOR: Non-breaking additions (new records, extended range)
    - PATCH: Bug fixes, data corrections

Guarantees:
    - Deterministic: Same dataset changes → same version
    - Auditable: All version changes recorded with reasons
    - Immutable: Historical versions are never modified
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import parse_timestamp, utc_now
from researchos.data_engine.contracts import DatasetStatus


class DatasetVersion(BaseObject):
    """
    Version tracking for a specific dataset.

    Tracks the version history of a dataset as it evolves through
    data additions, corrections, and schema changes.

    Attributes:
        dataset_id: Link to the HistoricalDataset.
        version: Semantic version string (e.g., "1.0.0").
        previous_version: Previous version string (empty if first).
        dataset_hash: Content hash of the dataset at this version.
        record_count: Number of records at this version.
        change_description: Description of what changed.
        change_reason: Why the change was made.
        author: Who made the change.
        is_current: Whether this is the current version.
    """

    def __init__(
        self,
        dataset_id: str,
        version: str,
        previous_version: str = "",
        dataset_hash: str = "",
        record_count: int = 0,
        change_description: str = "",
        change_reason: str = "",
        author: str = "",
        is_current: bool = True,
        ontology_tags: Optional[List[str]] = None,
        id: Optional[str] = None,
    ):
        if id is None:
            seed = f"DatasetVersion|{dataset_id}|{version}"
            id = generate_id(seed)

        super().__init__(id=id, ontology_tags=ontology_tags)

        self.dataset_id = dataset_id
        self.version = version
        self.previous_version = previous_version
        self.dataset_hash = dataset_hash
        self.record_count = record_count
        self.change_description = change_description
        self.change_reason = change_reason
        self.author = author
        self.is_current = is_current

        self.lifecycle.transition(
            LifecycleStage.CREATED,
            reason=f"DatasetVersion {version} created for {dataset_id}",
        )

    def _to_hashable_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "previous_version": self.previous_version,
            "dataset_hash": self.dataset_hash,
            "record_count": self.record_count,
            "change_description": self.change_description,
            "change_reason": self.change_reason,
            "author": self.author,
            "is_current": self.is_current,
            "ontology_tags": sorted(self.ontology_tags),
        }

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "dataset_id": self.dataset_id,
            "version": self.version,
            "previous_version": self.previous_version,
            "dataset_hash": self.dataset_hash,
            "record_count": self.record_count,
            "change_description": self.change_description,
            "change_reason": self.change_reason,
            "author": self.author,
            "is_current": self.is_current,
        })
        return base

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetVersion":
        obj = super().from_dict(data)
        obj.dataset_id = data["dataset_id"]
        obj.version = data["version"]
        obj.previous_version = data.get("previous_version", "")
        obj.dataset_hash = data.get("dataset_hash", "")
        obj.record_count = int(data.get("record_count", 0))
        obj.change_description = data.get("change_description", "")
        obj.change_reason = data.get("change_reason", "")
        obj.author = data.get("author", "")
        obj.is_current = bool(data.get("is_current", True))
        return obj

    def __repr__(self) -> str:
        return (
            f"DatasetVersion({self.dataset_id[:8]}..., "
            f"v{self.version}, {self.record_count} records)"
        )


def bump_dataset_version(
    current_version: str,
    bump_type: str = "patch",
) -> str:
    """
    Bump a semantic version string.

    Args:
        current_version: Current version (e.g., "1.2.3").
        bump_type: Type of bump ("major", "minor", "patch").

    Returns:
        New version string.

    Raises:
        ValueError: If the version string is invalid.
    """
    parts = current_version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {current_version}")

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

