"""Core infrastructure for ResearchOS."""

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import Lifecycle, LifecycleStage
from researchos.core.timestamp import utc_now, parse_timestamp
from researchos.core.versioning import Version, VersionHistory

__all__ = [
    "BaseObject",
    "generate_id",
    "deterministic_hash",
    "Lifecycle",
    "LifecycleStage",
    "utc_now",
    "parse_timestamp",
    "Version",
    "VersionHistory",
]
