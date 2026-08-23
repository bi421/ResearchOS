"""
Research Intelligence Layer — Q12 Evidence Graph + Q13 RAG Retrieval.

Transforms completed experiments into connected research knowledge by
recording structured, immutable evidence nodes and the relationships
between them.  This is an intelligence *memory* layer: it never trades,
never generates signals, and never predicts.

Architecture:

    EvidenceNode <-- EvidenceEdge --> EvidenceNode
        |                                |
        +----------- EvidenceGraph -----+
                        |
              EvidenceGraphStore (JSON, stdlib only)

    Q13: Deterministic RAG Retrieval
        RetrievalQuery -> DeterministicRetriever -> RetrievalResult
        SessionRetriever (multi-query context accumulation)
"""

from researchos.intelligence.contracts import (
    EVIDENCE_GRAPH_VERSION,
    INTELLIGENCE_VERSION,
    EvidenceError,
    InvalidEdgeError,
    NodeAlreadyExistsError,
    NodeNotFoundError,
)
from researchos.intelligence.edges import EvidenceEdge, Relationship
from researchos.intelligence.graph import EvidenceGraph
from researchos.intelligence.nodes import EvidenceNode, NodeType
from researchos.intelligence.rag_contracts import (
    RetrievalContext,
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
    RetrievalSource,
)
from researchos.intelligence.rag_retriever import DeterministicRetriever, SessionRetriever
from researchos.intelligence.repository import (
    DEFAULT_PATH,
    EvidenceGraphStore,
    EvidenceRepository,
)

__all__ = [
    # Versions
    "INTELLIGENCE_VERSION",
    "EVIDENCE_GRAPH_VERSION",
    # Errors
    "EvidenceError",
    "NodeAlreadyExistsError",
    "NodeNotFoundError",
    "InvalidEdgeError",
    # Nodes
    "NodeType",
    "EvidenceNode",
    # Edges
    "Relationship",
    "EvidenceEdge",
    # Graph
    "EvidenceGraph",
    # Repository (EvidenceGraphStore; EvidenceRepository is a deprecated alias)
    "DEFAULT_PATH",
    "EvidenceGraphStore",
    "EvidenceRepository",
    # RAG Retrieval (Q13)
    "RetrievalSource",
    "RetrievalQuery",
    "RetrievalHit",
    "RetrievalResult",
    "RetrievalContext",
    "DeterministicRetriever",
    "SessionRetriever",
]
