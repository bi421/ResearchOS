"""
Pipeline Repository — JSON storage engine (Q15).

``PipelineRepository`` persists immutable ``PipelineReport`` objects using
only the Python standard library (``json`` + ``hashlib``).  No database, no
pickle, no external dependencies.

Guarantees:
    - Deterministic content-derived ``pipeline_id`` (SHA-256 of the report's
      canonical JSON).  Identical reports always produce the identical id.
    - ``save`` is idempotent for identical reports.
    - Deterministic serialization: equal repositories serialize to equal
      strings.
    - No randomness, no uuid, no timestamp-based identifiers.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Iterator, Mapping, Optional, Tuple

from researchos.orchestration.contracts import PipelineReport
from researchos.orchestration.contracts import PipelineStatus

from .contracts import (
    PIPELINE_REPOSITORY_VERSION,
    InvalidPipelineRecordError,
    PipelineNotFoundError,
    PipelineRecord,
)

DEFAULT_PATH = "pipeline_repository.json"


def _canonical_json(obj) -> str:
    """Deterministic JSON serialization (sorted keys, compact separators)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _report_id(report: PipelineReport) -> str:
    """Deterministic content-derived pipeline id for a report.

    Uses the report's canonical ``to_dict()`` JSON, NOT the report's own
    ``pipeline_id``, so that two equivalent reports stored under different
    orchestration-generated ids still deduplicate deterministically.
    """
    if not isinstance(report, PipelineReport):
        raise InvalidPipelineRecordError(
            "expected a PipelineReport, got "
            f"{type(report).__name__}"
        )
    canonical = _canonical_json(report.to_dict())
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class PipelineRepository:
    """JSON-backed, deterministic store of ``PipelineReport`` objects.

    Parameters:
        path: Optional file path used by ``save_to_disk`` / ``load_from_disk``.
            Defaults to ``pipeline_repository.json``.
    """

    VERSION = PIPELINE_REPOSITORY_VERSION

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = path or DEFAULT_PATH
        self._records: dict = {}

    # ------------------------------------------------------------------
    # properties
    # ------------------------------------------------------------------

    @property
    def path(self) -> str:
        """The default file path used by disk persistence."""
        return self._path

    # ------------------------------------------------------------------
    # core CRUD
    # ------------------------------------------------------------------

    def save(self, report: PipelineReport, *, stored_at: str = "", metadata=None) -> str:
        """Store a pipeline report and return its deterministic pipeline id.

        Args:
            report: The immutable ``PipelineReport`` to store.
            stored_at: Optional deterministic storage timestamp.
            metadata: Optional extra storage metadata mapping.

        Returns:
            The deterministic content-derived ``pipeline_id``.

        Raises:
            InvalidPipelineRecordError: If ``report`` is not a
                ``PipelineReport``.
        """
        if not isinstance(report, PipelineReport):
            raise InvalidPipelineRecordError(
                f"expected a PipelineReport, got {type(report).__name__}"
            )
        pipeline_id = _report_id(report)
        self._records[pipeline_id] = PipelineRecord(
            pipeline_id=pipeline_id,
            report=report,
            stored_at=stored_at,
            version=self.VERSION,
            metadata=dict(metadata or {}),
        )
        return pipeline_id

    def load(self, pipeline_id: str) -> PipelineRecord:
        """Return the stored record for ``pipeline_id``.

        Raises:
            PipelineNotFoundError: If the id does not exist.
        """
        if pipeline_id not in self._records:
            raise PipelineNotFoundError(pipeline_id)
        return self._records[pipeline_id]

    def list(
        self,
        limit: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Tuple[PipelineRecord, ...]:
        """Return stored records, optionally filtered.

        Args:
            limit: Maximum number of records to return.
            status: Optional ``PipelineStatus`` value to filter by.

        Returns:
            Records sorted deterministically by ``pipeline_id``.
        """
        records = list(self._records.values())
        if status is not None:
            records = [
                r
                for r in records
                if r.report.status == PipelineStatus(status)
            ]
        records.sort(key=lambda r: r.pipeline_id)
        if limit is not None:
            records = records[: max(0, int(limit))]
        return tuple(records)

    def delete(self, pipeline_id: str) -> None:
        """Remove the record for ``pipeline_id``.

        Raises:
            PipelineNotFoundError: If the id does not exist.
        """
        if pipeline_id not in self._records:
            raise PipelineNotFoundError(pipeline_id)
        del self._records[pipeline_id]

    def count(self) -> int:
        """Return the number of stored records."""
        return len(self._records)

    def clear(self) -> None:
        """Remove all stored records."""
        self._records.clear()

    def has(self, pipeline_id: str) -> bool:
        """Return whether ``pipeline_id`` is present."""
        return pipeline_id in self._records

    # ------------------------------------------------------------------
    # iteration / mapping
    # ------------------------------------------------------------------

    def __iter__(self) -> Iterator[PipelineRecord]:
        for record in self.list():
            yield record

    def __len__(self) -> int:
        return self.count()

    def to_mapping(self) -> dict:
        """Return a deterministic mapping of pipeline_id -> record dict."""
        return {
            pid: self._records[pid].to_dict()
            for pid in sorted(self._records)
        }

    # ------------------------------------------------------------------
    # serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a deterministic, JSON-compatible repository mapping."""
        return {
            "version": self.VERSION,
            "records": {
                pid: self._records[pid].to_dict()
                for pid in sorted(self._records)
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping) -> "PipelineRepository":
        """Reconstruct a repository from a ``to_dict()`` mapping.

        Raises:
            InvalidPipelineRecordError: If the payload is malformed.
        """
        repo = cls()
        if not isinstance(data, Mapping):
            raise InvalidPipelineRecordError("payload must be a mapping")
        records = data.get("records", {})
        if not isinstance(records, Mapping):
            raise InvalidPipelineRecordError("'records' must be a mapping")
        for pid, record_data in records.items():
            if not isinstance(record_data, Mapping):
                raise InvalidPipelineRecordError(
                    f"record {pid!r} must be a mapping"
                )
            record = PipelineRecord.from_dict(record_data)
            if record.pipeline_id != pid:
                raise InvalidPipelineRecordError(
                    f"record key {pid!r} does not match pipeline_id "
                    f"{record.pipeline_id!r}"
                )
            repo._records[record.pipeline_id] = record
        return repo

    def serialize(self) -> str:
        """Return a canonical JSON string describing this repository.

        Equal repositories always serialize to equal strings.
        """
        return _canonical_json(self.to_dict())

    @classmethod
    def deserialize(cls, text: str) -> "PipelineRepository":
        """Reconstruct a repository from a ``serialize()`` string.

        Raises:
            InvalidPipelineRecordError: If the payload is malformed.
        """
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidPipelineRecordError(
                f"invalid JSON: {exc}"
            ) from None
        return cls.from_dict(data)

    # ------------------------------------------------------------------
    # disk persistence (stdlib only)
    # ------------------------------------------------------------------

    def save_to_disk(self, path: Optional[str] = None) -> str:
        """Write the repository to ``path`` (or the default path).

        Returns:
            The path that was written.
        """
        target = path or self._path
        text = self.serialize()
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
        return target

    @classmethod
    def load_from_disk(
        cls, path: Optional[str] = None, *, missing_ok: bool = False
    ) -> "PipelineRepository":
        """Read a repository from ``path`` (or the default path).

        Args:
            path: File path to read.
            missing_ok: If ``True`` and the file does not exist, return an
                empty repository instead of raising.

        Raises:
            FileNotFoundError: If the file does not exist and ``missing_ok``
                is ``False``.
            InvalidPipelineRecordError: If the file is malformed.
        """
        target = path or DEFAULT_PATH
        if not os.path.exists(target):
            if missing_ok:
                return cls(path=path)
            raise FileNotFoundError(target)
        with open(target, "r", encoding="utf-8") as handle:
            text = handle.read()
        return cls.from_dict(cls.deserialize(text).to_dict())


__all__ = [
    "DEFAULT_PATH",
    "PipelineRepository",
    "_report_id",
]

