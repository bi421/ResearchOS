"""
ResearchOS Macro Intelligence Layer - Version
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VersionInfo:
    """Semantic version information."""
    major: int = 1
    minor: int = 0
    patch: int = 0
    build_date: str = "2026-08-03"
    commit_hash: str = "architectural_frozen"
    
    @property
    def version_string(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    @property
    def full_version(self) -> str:
        return f"{self.version_string}-{self.build_date}-{self.commit_hash}"
    
    def to_dict(self) -> dict:
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.minor,
            "build_date": self.build_date,
            "commit_hash": self.commit_hash,
            "version_string": self.version_string,
            "full_version": self.full_version,
        }


# Module-level version
VERSION = VersionInfo()
