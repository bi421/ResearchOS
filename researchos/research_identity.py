"""Canonical dataset identity contract shared by research provenance layers."""

from __future__ import annotations

from dataclasses import dataclass


DATASET_IDENTITY_SCHEMA_VERSION = "dataset-identity.v1"


@dataclass(frozen=True)
class DatasetIdentity:
    """Immutable identity of the exact validated dataset content."""

    dataset_id: str
    dataset_content_hash: str
    dataset_hash: str

    def __post_init__(self) -> None:
        if not self.dataset_id:
            raise ValueError("dataset_id is required")
        if not self.dataset_content_hash:
            raise ValueError("dataset_content_hash is required")
        if not self.dataset_hash:
            raise ValueError("dataset_hash is required")

    def matches(self, *, dataset_id: str, dataset_content_hash: str, dataset_hash: str) -> bool:
        """Return whether another provenance envelope identifies the same dataset."""
        return (
            self.dataset_id == dataset_id
            and self.dataset_content_hash == dataset_content_hash
            and self.dataset_hash == dataset_hash
        )

    def assert_matches(self, *, dataset_id: str, dataset_content_hash: str, dataset_hash: str) -> None:
        """Reject provenance that points at different dataset content or identity."""
        if not self.matches(
            dataset_id=dataset_id,
            dataset_content_hash=dataset_content_hash,
            dataset_hash=dataset_hash,
        ):
            raise ValueError("dataset identity mismatch: provenance is not bound to the same dataset content")

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": DATASET_IDENTITY_SCHEMA_VERSION,
            "dataset_id": self.dataset_id,
            "dataset_content_hash": self.dataset_content_hash,
            "dataset_hash": self.dataset_hash,
        }


__all__ = ["DATASET_IDENTITY_SCHEMA_VERSION", "DatasetIdentity"]
