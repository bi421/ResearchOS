"""
EvidenceRepository — append-only evidence & lineage storage facade.

Phase 5.3a — Evidence & Lineage storage foundation (hash-contract hardened).

This facade layers an append-only, content-addressed evidence store and a
lineage edge table on top of the existing ``ResearchRepository``.  It is
strictly additive:

    - ``append_artifact()``     — insert an immutable evidence envelope.
    - ``add_lineage_edge()``    — record a parent→child lineage edge.
    - ``get_artifact()``        — retrieve an envelope by artifact hash.
    - ``get_children()``        — list child hashes of an artifact.
    - ``get_parents()``         — list parent hashes of an artifact.

Constraints honored:
    - Append-only: no delete API, no update of existing records.
    - No modification of the existing experiment flow.
    - No artifact emission hooks yet.
    - No Model Registry implementation.
    - No replay execution.

The backing tables (``evidence``, ``lineage``) are created by the additive
schema migration in ``ResearchRepository`` (``SCHEMA_VERSION`` 2 → 3).  This
facade reuses the existing transaction context, WAL mode, and retry handling.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from researchos.core.identity import deterministic_hash
from researchos.evidence.envelope import (
    HASH_SCHEME_VERSION,
    LINEAGE_RELATIONS,
    EvidenceEnvelope,
)
from researchos.storage.repository import ResearchRepository

logger = logging.getLogger(__name__)


class EvidenceRepository:
    """Append-only evidence and lineage store over ``ResearchRepository``."""

    def __init__(self, repository: ResearchRepository | None = None) -> None:
        self._repo = repository or ResearchRepository(db_path=":memory:")

    # ── public API ──────────────────────────────────────────────────────

    def append_artifact(self, envelope: EvidenceEnvelope) -> EvidenceEnvelope:
        """Insert an immutable evidence envelope.

        The envelope is stored keyed by its deterministic ``artifact_hash``.
        Re-inserting an identical hash is a no-op (deduplication); it is never
        an update.  The record is also saved to the generic ``objects`` store
        for discoverability.

        Returns the stored envelope.
        """
        # Validate the envelope self-consistency before persisting.
        if not envelope.verify():
            raise ValueError(f"EvidenceEnvelope lineage_hash mismatch for artifact {envelope.artifact_hash}")
        with self._repo._transaction() as cursor:
            cursor.execute(
                """
                INSERT OR IGNORE INTO evidence
                (artifact_type, artifact_hash, version, created_at, payload,
                 parent_hashes, lineage_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    envelope.artifact_type,
                    envelope.artifact_hash,
                    envelope.version,
                    envelope.created_at,
                    json.dumps(envelope.payload, ensure_ascii=False, default=str),
                    json.dumps(list(envelope.parent_hashes), ensure_ascii=False),
                    envelope.lineage_hash,
                ),
            )
            # Record the lineage edges implied by parent_hashes.
            for parent in envelope.parent_hashes:
                self._insert_edge(
                    cursor,
                    parent,
                    envelope.artifact_hash,
                    _default_relation(envelope.artifact_type),
                )
        # Generic discoverability (matches audit dual-write pattern).
        self._repo.save_object(_envelope_as_object(envelope))
        return envelope

    def add_lineage_edge(
        self,
        parent_hash: str,
        child_hash: str,
        relation: str = "feeds",
    ) -> None:
        """Record a single parent→child lineage edge (append-only)."""
        if relation not in LINEAGE_RELATIONS:
            raise ValueError(f"Unknown lineage relation '{relation}'. Expected one of {LINEAGE_RELATIONS}.")
        with self._repo._transaction() as cursor:
            self._insert_edge(cursor, parent_hash, child_hash, relation)

    def get_artifact(self, artifact_hash: str) -> EvidenceEnvelope | None:
        """Retrieve an evidence envelope by artifact hash, or None."""
        conn = self._repo._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT artifact_type, artifact_hash, version, created_at, payload, parent_hashes, lineage_hash FROM evidence WHERE artifact_hash = ?",
            (artifact_hash,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return EvidenceEnvelope(
            artifact_type=row[0],
            artifact_hash=row[1],
            version=row[2],
            created_at=row[3],
            payload=json.loads(row[4]),
            parent_hashes=tuple(json.loads(row[5])),
            lineage_hash=row[6],
        )

    def get_children(self, artifact_hash: str) -> list[str]:
        """Return the child artifact hashes of the given artifact."""
        conn = self._repo._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT child_hash FROM lineage WHERE parent_hash = ? ORDER BY child_hash",
            (artifact_hash,),
        )
        return [row[0] for row in cursor.fetchall()]

    def get_parents(self, artifact_hash: str) -> list[str]:
        """Return the parent artifact hashes of the given artifact."""
        conn = self._repo._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT parent_hash FROM lineage WHERE child_hash = ? ORDER BY parent_hash",
            (artifact_hash,),
        )
        return [row[0] for row in cursor.fetchall()]

    def verify_evidence(self) -> bool:
        """Verify the integrity of all stored evidence envelopes.

        Recomputes each envelope's ``lineage_hash`` from its stored
        artifact_type + version + payload + parent hashes and confirms it
        matches.  Returns True only if every record is consistent.
        """
        conn = self._repo._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT artifact_type, version, payload, parent_hashes, lineage_hash FROM evidence")
        for row in cursor.fetchall():
            artifact_type = row[0]
            version = row[1]
            payload = json.loads(row[2])
            parent_hashes = tuple(json.loads(row[3]))
            stored = row[4]
            expected = deterministic_hash(
                {
                    "scheme": HASH_SCHEME_VERSION,
                    "artifact_type": artifact_type,
                    "version": version,
                    "payload": payload,
                    "parent_hashes": sorted(parent_hashes),
                }
            )
            if expected != stored:
                return False
        return True

    def count_artifacts(self) -> int:
        """Return the number of stored evidence records."""
        conn = self._repo._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM evidence")
        return cursor.fetchone()[0]

    def count_edges(self) -> int:
        """Return the number of stored lineage edges."""
        conn = self._repo._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM lineage")
        return cursor.fetchone()[0]

    # ── internal helpers ────────────────────────────────────────────────

    def _insert_edge(
        self,
        cursor,
        parent_hash: str,
        child_hash: str,
        relation: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT OR IGNORE INTO lineage
            (parent_hash, child_hash, relation, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (parent_hash, child_hash, relation, now),
        )


def _default_relation(artifact_type: str) -> str:
    """Map an artifact type to its canonical lineage relation label."""
    mapping = {
        "Feature": "feeds",
        "Experiment": "feeds",
        "Run": "executes",
        "Result": "produces",
        "Validation": "validates",
        "Model": "trains",
        "Dataset": "feeds",
    }
    return mapping.get(artifact_type, "feeds")


class _EnvelopeObject:
    """Minimal dict-like shim exposing ``id`` and ``to_dict`` so an envelope
    can be persisted by ``ResearchRepository.save_object`` without introducing
    a new ``BaseObject`` subclass (kept additive and decoupled)."""

    __slots__ = ("_data",)

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @property
    def id(self) -> str:  # noqa: A003 - id attribute per object contract
        return self._data["artifact_hash"]

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)


def _envelope_as_object(envelope: EvidenceEnvelope) -> _EnvelopeObject:
    """Wrap an envelope for generic-store discoverability."""
    data = envelope.to_dict()
    data["object_type"] = "EvidenceEnvelope"
    data["created_at"] = envelope.created_at
    return _EnvelopeObject(data)


__all__ = ["EvidenceRepository"]
