"""
Evidence Graph — JSON repository.

``EvidenceGraphStore`` persists an ``EvidenceGraph`` to JSON using only the
standard library.  There is no database yet and no external dependency.

Renamed from ``EvidenceRepository`` (2026-08-17) to end the name collision
with ``researchos.evidence.EvidenceRepository`` (the append-only artifact
ledger).  ``EvidenceRepository`` remains available here as a deprecated
compatibility alias.  See docs/architecture/OWNERSHIP.md.

Responsibilities:
    - serialize a graph to a JSON string
    - deserialize a JSON string back to a graph
    - save a graph to a file path
    - load a graph from a file path
"""

from __future__ import annotations

import json

from researchos.intelligence.contracts import (
    EVIDENCE_GRAPH_VERSION,
    EvidenceError,
)
from researchos.intelligence.graph import EvidenceGraph

DEFAULT_PATH = "evidence_graph.json"


class EvidenceGraphStore:
    """JSON-based persistence for ``EvidenceGraph`` objects."""

    VERSION = EVIDENCE_GRAPH_VERSION

    def __init__(self, path: str | None = None) -> None:
        self._path = path or DEFAULT_PATH

    @property
    def path(self) -> str:
        """The default file path used by ``save`` / ``load``."""
        return self._path

    # -- serialize / deserialize ----------------------------------------

    def serialize(self, graph: EvidenceGraph) -> str:
        """Serialize ``graph`` to a deterministic JSON string.

        Raises:
            TypeError: If ``graph`` is not an ``EvidenceGraph``.
        """
        if not isinstance(graph, EvidenceGraph):
            raise TypeError("serialize() expects an EvidenceGraph")
        payload = {
            "version": self.VERSION,
            "graph": graph.to_dict(),
        }
        return json.dumps(payload, sort_keys=True, indent=2)

    def deserialize(self, text: str) -> EvidenceGraph:
        """Deserialize a JSON string produced by ``serialize``.

        Raises:
            EvidenceError: If the payload is malformed or unsupported.
        """
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise EvidenceError(f"invalid JSON: {exc}") from None
        if not isinstance(payload, dict) or "graph" not in payload:
            raise EvidenceError("missing 'graph' section in payload")
        version = payload.get("version", "")
        if not isinstance(version, str):
            raise EvidenceError("payload version must be a string")
        if not isinstance(payload["graph"], dict):
            raise EvidenceError("graph section must be a mapping")
        try:
            return EvidenceGraph.from_dict(payload["graph"])
        except (AttributeError, KeyError, TypeError, ValueError, EvidenceError) as exc:
            raise EvidenceError(f"invalid graph payload: {exc}") from None

    # -- save / load -----------------------------------------------------

    def save(self, graph: EvidenceGraph, path: str | None = None) -> str:
        """Write ``graph`` as JSON to ``path`` (or the default path).

        Returns:
            The path that was written.
        """
        target = path or self._path
        text = self.serialize(graph)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
        return target

    def load(self, path: str | None = None) -> EvidenceGraph:
        """Read a graph from ``path`` (or the default path).

        Raises:
            FileNotFoundError: If ``path`` does not exist.
            EvidenceError: If the file does not contain a valid graph.
        """
        target = path or self._path
        with open(target, encoding="utf-8") as handle:
            text = handle.read()
        return self.deserialize(text)


# Deprecated compatibility alias — canonical name is ``EvidenceGraphStore``.
EvidenceRepository = EvidenceGraphStore

__all__ = [
    "DEFAULT_PATH",
    "EvidenceGraphStore",
    "EvidenceRepository",
]
