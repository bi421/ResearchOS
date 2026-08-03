"""
Evidence Graph — in-memory graph of research knowledge.

``EvidenceGraph`` stores immutable ``EvidenceNode`` objects connected by
immutable ``EvidenceEdge`` objects.  It supports O(1) node lookup, prevents
duplicate ids and dangling edges, and exposes deterministic ordering for
all traversal results.

Guarantees:
    - O(1) node lookup via a dict index.
    - No duplicate node ids or edge ids.
    - No dangling edges: source and target nodes must exist at add time.
    - No duplicate relationships between the same pair of nodes.
    - Deterministic ordering of ``get_edges`` / ``neighbors`` / ``to_dict``.
    - No hidden state: the graph is fully described by its public ``to_dict``.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Set, Tuple

from researchos.intelligence.contracts import (
    InvalidEdgeError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
)
from researchos.intelligence.edges import EvidenceEdge
from researchos.intelligence.nodes import EvidenceNode


class EvidenceGraph:
    """Deterministic, in-memory evidence graph.

    The graph is free of global state: every instance is fully independent
    and safe to construct in tests and research workflows.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, EvidenceNode] = {}
        self._edges: Dict[str, EvidenceEdge] = {}
        self._incident: Dict[str, Set[str]] = {}
        self._adjacency: Dict[str, Set[str]] = {}

    # -- nodes -----------------------------------------------------------

    def add_node(self, node: EvidenceNode) -> None:
        """Add an ``EvidenceNode`` to the graph.

        Raises:
            TypeError: If ``node`` is not an ``EvidenceNode``.
            NodeAlreadyExistsError: If ``node.node_id`` already exists.
        """
        if not isinstance(node, EvidenceNode):
            raise TypeError("add_node() expects an EvidenceNode")
        if node.node_id in self._nodes:
            raise NodeAlreadyExistsError(node.node_id)
        self._nodes[node.node_id] = node
        self._incident.setdefault(node.node_id, set())
        self._adjacency.setdefault(node.node_id, set())

    def get_node(self, node_id: str) -> EvidenceNode:
        """Return the node for ``node_id``.

        Raises:
            NodeNotFoundError: If ``node_id`` is not present.
        """
        try:
            return self._nodes[node_id]
        except KeyError:
            raise NodeNotFoundError(node_id) from None

    def has_node(self, node_id: str) -> bool:
        """Return whether ``node_id`` is present in the graph."""
        return node_id in self._nodes

    # -- edges -----------------------------------------------------------

    def add_edge(self, edge: EvidenceEdge) -> None:
        """Add an ``EvidenceEdge`` to the graph.

        Validates that both endpoints exist and that the edge is not a
        duplicate.

        Raises:
            TypeError: If ``edge`` is not an ``EvidenceEdge``.
            NodeNotFoundError: If ``edge.source_id`` or ``edge.target_id``
                is not present.
            InvalidEdgeError: If the edge id already exists or a duplicate
                relationship already connects the same pair of nodes.
        """
        if not isinstance(edge, EvidenceEdge):
            raise TypeError("add_edge() expects an EvidenceEdge")
        if edge.edge_id in self._edges:
            raise InvalidEdgeError(f"edge already exists: {edge.edge_id!r}")
        if edge.source_id not in self._nodes:
            raise NodeNotFoundError(edge.source_id)
        if edge.target_id not in self._nodes:
            raise NodeNotFoundError(edge.target_id)
        if self._has_relationship(edge.source_id, edge.target_id, edge.relationship):
            raise InvalidEdgeError(
                "duplicate relationship "
                f"'{edge.relationship.value}' between "
                f"{edge.source_id!r} and {edge.target_id!r}"
            )
        self._edges[edge.edge_id] = edge
        self._incident[edge.source_id].add(edge.edge_id)
        self._incident[edge.target_id].add(edge.edge_id)
        self._adjacency[edge.source_id].add(edge.target_id)
        self._adjacency[edge.target_id].add(edge.source_id)

    def get_edges(self, node_id: str) -> Tuple[EvidenceEdge, ...]:
        """Return all edges incident to ``node_id``, sorted by edge id.

        Raises:
            NodeNotFoundError: If ``node_id`` is not present.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return tuple(
            self._edges[eid]
            for eid in sorted(self._incident.get(node_id, set()))
        )

    def neighbors(self, node_id: str) -> Tuple[str, ...]:
        """Return the ``node_id``s of all nodes connected to ``node_id``.

        The result is the union of in-neighbours and out-neighbours,
        returned in deterministic sorted order.

        Raises:
            NodeNotFoundError: If ``node_id`` is not present.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        return tuple(sorted(self._adjacency.get(node_id, set())))

    # -- mutations -------------------------------------------------------

    def remove_node(self, node_id: str) -> None:
        """Remove ``node_id`` and every edge incident to it.

        Raises:
            NodeNotFoundError: If ``node_id`` is not present.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(node_id)
        for edge_id in list(self._incident.get(node_id, set())):
            self._remove_edge(edge_id)
        del self._nodes[node_id]
        del self._incident[node_id]
        del self._adjacency[node_id]

    def remove_edge(self, edge_id: str) -> None:
        """Remove the edge with ``edge_id``.

        Raises:
            InvalidEdgeError: If ``edge_id`` is not present.
        """
        if edge_id not in self._edges:
            raise InvalidEdgeError(f"edge not found: {edge_id!r}")
        self._remove_edge(edge_id)

    def clear(self) -> None:
        """Remove all nodes and edges."""
        self._nodes.clear()
        self._edges.clear()
        self._incident.clear()
        self._adjacency.clear()

    # -- counts ----------------------------------------------------------

    def count_nodes(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._nodes)

    def count_edges(self) -> int:
        """Return the number of edges in the graph."""
        return len(self._edges)

    # -- helpers ---------------------------------------------------------

    def _has_relationship(self, source_id: str, target_id: str, relationship: Any) -> bool:
        for edge_id in self._incident.get(source_id, set()):
            edge = self._edges[edge_id]
            if (
                edge.source_id == source_id
                and edge.target_id == target_id
                and edge.relationship == relationship
            ):
                return True
        return False

    def _remove_edge(self, edge_id: str) -> None:
        edge = self._edges.pop(edge_id)
        self._incident[edge.source_id].discard(edge_id)
        self._incident[edge.target_id].discard(edge_id)
        self._adjacency[edge.source_id].discard(edge.target_id)
        self._adjacency[edge.target_id].discard(edge.source_id)

    # -- serialization ---------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the graph to a deterministic, JSON-compatible mapping.

        Nodes are ordered by ``node_id`` and edges by ``edge_id``.
        """
        return {
            "nodes": [self._nodes[nid].to_dict() for nid in sorted(self._nodes)],
            "edges": [self._edges[eid].to_dict() for eid in sorted(self._edges)],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EvidenceGraph":
        """Reconstruct a graph from a ``to_dict()`` mapping."""
        graph = cls()
        for item in data.get("nodes", []):
            graph.add_node(EvidenceNode.from_dict(item))
        for item in data.get("edges", []):
            graph.add_edge(EvidenceEdge.from_dict(item))
        return graph

    def nodes(self) -> Tuple[EvidenceNode, ...]:
        """Return all nodes in deterministic (sorted) order."""
        return tuple(self._nodes[nid] for nid in sorted(self._nodes))

    def edges(self) -> Tuple[EvidenceEdge, ...]:
        """Return all edges in deterministic (sorted) order."""
        return tuple(self._edges[eid] for eid in sorted(self._edges))


__all__ = ["EvidenceGraph"]
