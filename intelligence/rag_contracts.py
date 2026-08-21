"""
ResearchOS Q13 — Deterministic RAG Knowledge Retrieval Contracts.

Defines immutable, frozen dataclasses for the RAG retrieval layer:
    - RetrievalQuery
    - RetrievalHit
    - RetrievalResult
    - RetrievalContext

No ML, no embeddings, no vector database, no LLM.
Pure deterministic weighted scoring over the Evidence Graph and Market Memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any


class RetrievalSource(str, Enum):
    """The origin of a retrieval hit."""

    EVIDENCE_GRAPH = "evidence_graph"
    MARKET_MEMORY = "market_memory"
    KNOWLEDGE_BASE = "knowledge_base"
    EXPERIMENT_RESULT = "experiment_result"

    def matches(self, source: str) -> bool:
        """Whether this source matches a string label."""
        return self.value == str(source).lower().strip()

    @classmethod
    def from_string(cls, value: str) -> RetrievalSource:
        mapping = {
            "evidence_graph": cls.EVIDENCE_GRAPH,
            "evidencegraph": cls.EVIDENCE_GRAPH,
            "market_memory": cls.MARKET_MEMORY,
            "marketmemory": cls.MARKET_MEMORY,
            "knowledge_base": cls.KNOWLEDGE_BASE,
            "knowledgebase": cls.KNOWLEDGE_BASE,
            "experiment_result": cls.EXPERIMENT_RESULT,
            "experimentresult": cls.EXPERIMENT_RESULT,
        }
        normalized = str(value).lower().strip()
        if normalized not in mapping:
            raise ValueError(f"Unknown retrieval source {value!r}. Valid options: {[s.value for s in cls]}")
        return mapping[normalized]


@dataclass(frozen=True)
class RetrievalQuery:
    """Immutable query for the RAG retrieval layer.

    Attributes:
        query_id: Unique identifier for this query.
        text: The search text (normalized before use).
        source_filter: If set, only retrieve from these sources.
        max_hits: Maximum number of results to return.
        min_score: Minimum relevance score threshold.
        timestamp: When the query was issued.
        context_tags: Optional tags for query context.
    """

    query_id: str
    text: str
    source_filter: list[RetrievalSource] | None = None
    max_hits: int = 10
    min_score: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        if self.max_hits < 1:
            raise ValueError("max_hits must be >= 1")
        if not (0.0 <= self.min_score <= 1.0):
            raise ValueError("min_score must be in [0.0, 1.0]")
        object.__setattr__(self, "query_id", self.query_id.strip())
        object.__setattr__(self, "text", self.text.strip())
        object.__setattr__(
            self,
            "context_tags",
            tuple(sorted(set(t.strip() for t in self.context_tags if t.strip()))),
        )
        if self.source_filter is not None:
            object.__setattr__(self, "source_filter", tuple(self.source_filter))

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "text": self.text,
            "source_filter": [s.value for s in (self.source_filter or [])],
            "max_hits": self.max_hits,
            "min_score": self.min_score,
            "timestamp": self.timestamp.isoformat(),
            "context_tags": list(self.context_tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalQuery:
        return cls(
            query_id=str(data["query_id"]),
            text=str(data.get("text", "")),
            source_filter=[RetrievalSource.from_string(s) for s in data.get("source_filter", [])]
            if data.get("source_filter")
            else None,
            max_hits=int(data.get("max_hits", 10)),
            min_score=float(data.get("min_score", 0.0)),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data.get("timestamp"), str)
            else data.get("timestamp", datetime.now(timezone.utc)),
            context_tags=tuple(data.get("context_tags", [])),
        )


@dataclass(frozen=True)
class RetrievalHit:
    """A single retrieval hit with relevance score.

    Attributes:
        hit_id: Unique identifier for this hit.
        object_id: ID of the source object.
        object_type: Type name of the source object.
        source: Where this hit came from.
        score: Relevance score in [0.0, 1.0].
        snippet: Human-readable excerpt from the object.
        metadata: Additional metadata about the hit.
    """

    hit_id: str
    object_id: str
    object_type: str
    source: RetrievalSource
    score: float
    snippet: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.hit_id.strip():
            raise ValueError("hit_id must be non-empty")
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"score must be in [0.0, 1.0], got {self.score}")
        object.__setattr__(self, "hit_id", self.hit_id.strip())
        object.__setattr__(self, "object_id", self.object_id.strip())
        object.__setattr__(self, "snippet", self.snippet.strip() if self.snippet else "")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)) if self.metadata else MappingProxyType({}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hit_id": self.hit_id,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "source": self.source.value,
            "score": self.score,
            "snippet": self.snippet,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalHit:
        return cls(
            hit_id=str(data["hit_id"]),
            object_id=str(data["object_id"]),
            object_type=str(data["object_type"]),
            source=RetrievalSource.from_string(str(data["source"])),
            score=float(data["score"]),
            snippet=str(data.get("snippet", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class RetrievalResult:
    """Immutable result from a RAG retrieval query.

    Attributes:
        query_id: The query this result is for.
        hits: Sorted list of retrieval hits (highest score first).
        total_hits: Total number of hits before limiting.
        query_time_ms: Approximate query time (for diagnostics).
        sources_queried: Which sources were searched.
        explanation: Human-readable explanation of the retrieval.
    """

    query_id: str
    hits: tuple[RetrievalHit, ...]
    total_hits: int
    query_time_ms: float = 0.0
    sources_queried: tuple[str, ...] = ()
    explanation: str = ""

    def __post_init__(self) -> None:
        if not self.query_id.strip():
            raise ValueError("query_id must be non-empty")
        # Ensure hits are sorted by score descending
        if self.hits:
            for i in range(len(self.hits) - 1):
                if self.hits[i].score < self.hits[i + 1].score:
                    raise ValueError("hits must be sorted by score descending")
        object.__setattr__(self, "query_id", self.query_id.strip())
        object.__setattr__(self, "explanation", self.explanation.strip() if self.explanation else "")
        object.__setattr__(self, "sources_queried", tuple(sorted(set(self.sources_queried))))
        object.__setattr__(self, "hits", tuple(self.hits))
        object.__setattr__(self, "total_hits", max(0, int(self.total_hits)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "hits": [h.to_dict() for h in self.hits],
            "total_hits": self.total_hits,
            "query_time_ms": self.query_time_ms,
            "sources_queried": list(self.sources_queried),
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalResult:
        return cls(
            query_id=str(data["query_id"]),
            hits=tuple(RetrievalHit.from_dict(h) for h in data.get("hits", [])),
            total_hits=int(data.get("total_hits", 0)),
            query_time_ms=float(data.get("query_time_ms", 0.0)),
            sources_queried=tuple(data.get("sources_queried", [])),
            explanation=str(data.get("explanation", "")),
        )

    def summary(self) -> str:
        """Return a human-readable summary of the retrieval result."""
        if not self.hits:
            return f"Query {self.query_id}: No results found."
        lines = [f"Query {self.query_id}: {len(self.hits)} result(s) found."]
        for i, hit in enumerate(self.hits[:5], 1):
            lines.append(
                f"  {i}. [{hit.source.value}] {hit.object_type}({hit.object_id[:16]}...) score={hit.score:.4f}"
            )
        if len(self.hits) > 5:
            lines.append(f"  ... and {len(self.hits) - 5} more")
        return "\n".join(lines)


@dataclass(frozen=True)
class RetrievalContext:
    """Context metadata for a retrieval session.

    Tracks which objects have been retrieved and their scores
    across multiple queries for session-level reasoning.

    Attributes:
        session_id: Unique session identifier.
        queries: List of query IDs in this session.
        all_hits: All hits retrieved across the session.
        session_start: When the session started.
        relevance_threshold: Minimum score to consider a hit relevant.
    """

    session_id: str
    queries: tuple[str, ...]
    all_hits: tuple[RetrievalHit, ...]
    session_start: datetime
    relevance_threshold: float = 0.3

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id must be non-empty")
        object.__setattr__(self, "session_id", self.session_id.strip())
        object.__setattr__(self, "queries", tuple(sorted(set(self.queries))))
        object.__setattr__(self, "all_hits", tuple(sorted(self.all_hits, key=lambda h: (-h.score, h.hit_id))))
        object.__setattr__(self, "session_start", self.session_start)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "queries": list(self.queries),
            "all_hits": [h.to_dict() for h in self.all_hits],
            "session_start": self.session_start.isoformat(),
            "relevance_threshold": self.relevance_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalContext:
        return cls(
            session_id=str(data["session_id"]),
            queries=tuple(data.get("queries", [])),
            all_hits=tuple(RetrievalHit.from_dict(h) for h in data.get("all_hits", [])),
            session_start=datetime.fromisoformat(data["session_start"])
            if isinstance(data.get("session_start"), str)
            else data.get("session_start", datetime.now(timezone.utc)),
            relevance_threshold=float(data.get("relevance_threshold", 0.3)),
        )


__all__ = [
    "RetrievalSource",
    "RetrievalQuery",
    "RetrievalHit",
    "RetrievalResult",
    "RetrievalContext",
]
