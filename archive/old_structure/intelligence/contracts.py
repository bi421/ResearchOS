"""
Research Intelligence Layer — shared contracts and errors.

Q12: Evidence Graph Foundation.

This module defines the shared vocabulary of the Research Intelligence
Layer: the error hierarchy and version constants.  Node and edge contract
types live in ``nodes`` and ``edges``; the graph and its persistence live
in ``graph`` and ``repository``.

Design rules:
    - stdlib only (json, dataclasses) — no pandas / numpy / sklearn /
      torch / tensorflow / LLM libraries / broker APIs.
    - No trading, no signals, no execution, no prediction.  This layer
      only records structured research knowledge.
"""

from __future__ import annotations

INTELLIGENCE_VERSION = "1.0.0"
EVIDENCE_GRAPH_VERSION = "1.0.0"


class EvidenceError(Exception):
    """Base class for all Research Intelligence Layer errors."""


class NodeAlreadyExistsError(EvidenceError):
    """Raised when a node with the same ``node_id`` is added twice."""

    def __init__(self, node_id: str) -> None:
        super().__init__(f"node already exists: {node_id!r}")
        self.node_id = node_id


class NodeNotFoundError(EvidenceError):
    """Raised when a node is requested or referenced that does not exist."""

    def __init__(self, node_id: str) -> None:
        super().__init__(f"node not found: {node_id!r}")
        self.node_id = node_id


class InvalidEdgeError(EvidenceError):
    """Raised when an edge is invalid: dangling, duplicate, or malformed."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


__all__ = [
    "INTELLIGENCE_VERSION",
    "EVIDENCE_GRAPH_VERSION",
    "EvidenceError",
    "NodeAlreadyExistsError",
    "NodeNotFoundError",
    "InvalidEdgeError",
]
