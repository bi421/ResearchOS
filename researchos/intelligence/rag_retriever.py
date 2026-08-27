"""
Deterministic RAG Knowledge Retrieval Engine.

Provides query-time retrieval over the Evidence Graph and Market Memory
using pure deterministic scoring — no embeddings, no ML, no LLM.

Architecture:
    RetrievalQuery
        ↓
    DeterministicRetriever.retrieve(query)
        ↓
    RetrievalResult (sorted by relevance score)

Scoring:
    - Text token overlap with object content
    - Source-type weighting
    - Timestamp recency bonus
    - Context-tag matching bonus

Guarantees:
    - Deterministic: same query → same results
    - No external dependencies beyond stdlib
    - Immutable results
    - Serializable to/from dict
"""

from __future__ import annotations

import re
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from researchos.intelligence.rag_contracts import (
    RetrievalContext,
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
    RetrievalSource,
)

# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════

_TOKENIZER = re.compile(r"[a-zA-Z_]+|[0-9]+", re.IGNORECASE)
"""Simple ASCII tokeniser for text matching."""

_SOURCE_WEIGHTS: dict[RetrievalSource, float] = {
    RetrievalSource.EVIDENCE_GRAPH: 1.0,
    RetrievalSource.MARKET_MEMORY: 0.8,
    RetrievalSource.KNOWLEDGE_BASE: 0.9,
    RetrievalSource.EXPERIMENT_RESULT: 0.7,
}

"""Base relevance weight per source type."""

_TOKEN_WEIGHT: float = 0.1
"""Base weight per matching token."""

_TAG_MATCH_WEIGHT: float = 0.05
"""Bonus per matching context tag."""

_RECENTNESS_WINDOW_DAYS: float = 365.0
"""Days over which recency bonus decays."""

_RECENTNESS_BONUS: float = 0.1
"""Maximum recency bonus."""

_MAX_SNIPPET_LENGTH: int = 200
"""Max characters in a retrieval hit snippet."""


# ═══════════════════════════════════════════════════════════════════
# DeterministicRetriever
# ═══════════════════════════════════════════════════════════════════


class DeterministicRetriever:
    """Deterministic RAG retrieval engine over ResearchOS knowledge sources.

    Searches EvidenceGraph nodes and any registered knowledge sources,
    scores results by token overlap + source weight + recency + tags,
    and returns sorted RetrievalResult.

    Parameters
    ----------
    node_index : Dict[str, Any]
        Mapping of node_id → node dict (from EvidenceGraph.to_dict()).
    knowledge_index : Dict[str, Dict[str, Any]]
        Mapping of object_id → serialised object dict for non-graph sources.
    """

    def __init__(
        self,
        node_index: dict[str, dict[str, Any]] | None = None,
        knowledge_index: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._node_index: dict[str, dict[str, Any]] = dict(node_index or {})
        self._knowledge_index: dict[str, dict[str, Any]] = dict(knowledge_index or {})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: RetrievalQuery,
    ) -> RetrievalResult:
        """Execute a retrieval query against all registered sources.

        Parameters
        ----------
        query : RetrievalQuery
            The query to execute.

        Returns
        -------
        RetrievalResult
            Sorted retrieval hits with relevance scores.
        """
        start_time = time.monotonic()

        # Tokenise query text
        query_tokens = self._tokenise(query.text)
        query_tags = set(query.context_tags)

        all_hits: list[RetrievalHit] = []

        # Search evidence graph nodes
        if query.source_filter is None or RetrievalSource.EVIDENCE_GRAPH in query.source_filter:
            graph_hits = self._search_nodes(query_tokens, query_tags, query.min_score)
            all_hits.extend(graph_hits)

        # Search knowledge index
        if query.source_filter is None or RetrievalSource.KNOWLEDGE_BASE in query.source_filter:
            kb_hits = self._search_knowledge(query_tokens, query_tags, query.min_score)
            all_hits.extend(kb_hits)

        # Search market memory
        if query.source_filter is None or RetrievalSource.MARKET_MEMORY in query.source_filter:
            mm_hits = self._search_market_memory(query_tokens, query_tags, query.min_score)
            all_hits.extend(mm_hits)

        # Search experiment results
        if query.source_filter is None or RetrievalSource.EXPERIMENT_RESULT in query.source_filter:
            exp_hits = self._search_experiment_results(query_tokens, query_tags, query.min_score)
            all_hits.extend(exp_hits)

        # Sort by score descending, then by hit_id for determinism
        all_hits.sort(key=lambda h: (-h.score, h.hit_id))

        # Apply max_hits and min_score
        filtered = [h for h in all_hits if h.score >= query.min_score][: query.max_hits]

        elapsed_ms = (time.monotonic() - start_time) * 1000

        sources_queried = tuple(sorted({h.source.value for h in all_hits}))

        explanation = self._build_explanation(query, filtered, len(all_hits))

        return RetrievalResult(
            query_id=query.query_id,
            hits=tuple(filtered),
            total_hits=len(all_hits),
            query_time_ms=round(elapsed_ms, 2),
            sources_queried=sources_queried,
            explanation=explanation,
        )

    def retrieve_batch(
        self,
        queries: Sequence[RetrievalQuery],
    ) -> dict[str, RetrievalResult]:
        """Execute multiple queries and return results keyed by query_id.

        Parameters
        ----------
        queries : Sequence[RetrievalQuery]
            Queries to execute.

        Returns
        -------
        Dict[str, RetrievalResult]
            Mapping of query_id → RetrievalResult.
        """
        return {q.query_id: self.retrieve(q) for q in queries}

    def update_index(
        self,
        nodes: dict[str, dict[str, Any]] | None = None,
        knowledge: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Update the internal indexes with new data.

        Parameters
        ----------
        nodes : Dict[str, Dict[str, Any]] | None
            New node index (overwrites existing).
        knowledge : Dict[str, Dict[str, Any]] | None
            New knowledge index (overwrites existing).
        """
        if nodes is not None:
            self._node_index = dict(nodes)
        if knowledge is not None:
            self._knowledge_index = dict(knowledge)

    def clear_index(self) -> None:
        """Remove all indexed data."""
        self._node_index.clear()
        self._knowledge_index.clear()

    @property
    def node_count(self) -> int:
        """Number of indexed graph nodes."""
        return len(self._node_index)

    @property
    def knowledge_count(self) -> int:
        """Number of indexed knowledge objects."""
        return len(self._knowledge_index)

    # ------------------------------------------------------------------
    # Internal: tokenisation
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenise(text: str) -> tuple[str, ...]:
        """Tokenise text into lowercased ASCII tokens."""
        if not text:
            return ()
        tokens = _TOKENIZER.findall(text.lower())
        return tuple(dict.fromkeys(tokens))  # unique, order-preserving

    # ------------------------------------------------------------------
    # Internal: source searchers
    # ------------------------------------------------------------------

    def _search_nodes(
        self,
        query_tokens: tuple[str, ...],
        context_tags: set[str],
        min_score: float,
    ) -> list[RetrievalHit]:
        """Search evidence graph nodes."""
        hits: list[RetrievalHit] = []
        for node_id, node_data in self._node_index.items():
            score = self._score_node(node_data, query_tokens, context_tags)
            if score >= min_score:
                hits.append(
                    RetrievalHit(
                        hit_id=f"node-{node_id}",
                        object_id=node_id,
                        object_type="EvidenceNode",
                        source=RetrievalSource.EVIDENCE_GRAPH,
                        score=round(score, 4),
                        snippet=self._make_snippet(node_data),
                        metadata={"node_type": node_data.get("node_type", "")},
                    )
                )
        return hits

    def _search_knowledge(
        self,
        query_tokens: tuple[str, ...],
        context_tags: set[str],
        min_score: float,
    ) -> list[RetrievalHit]:
        """Search knowledge base objects."""
        hits: list[RetrievalHit] = []
        for obj_id, obj_data in self._knowledge_index.items():
            score = self._score_knowledge(obj_data, query_tokens, context_tags)
            if score >= min_score:
                hits.append(
                    RetrievalHit(
                        hit_id=f"kb-{obj_id}",
                        object_id=obj_id,
                        object_type=str(obj_data.get("type", "Unknown")),
                        source=RetrievalSource.KNOWLEDGE_BASE,
                        score=round(score, 4),
                        snippet=self._make_snippet(obj_data),
                        metadata=dict(obj_data.get("metadata", {})),
                    )
                )
        return hits

    def _search_market_memory(
        self,
        query_tokens: tuple[str, ...],
        context_tags: set[str],
        min_score: float,
    ) -> list[RetrievalHit]:
        """Search market memory entries."""
        hits: list[RetrievalHit] = []
        for obj_id, obj_data in self._knowledge_index.items():
            if obj_data.get("source") == "market_memory":
                score = self._score_knowledge(obj_data, query_tokens, context_tags) * 0.8
                if score >= min_score:
                    hits.append(
                        RetrievalHit(
                            hit_id=f"mm-{obj_id}",
                            object_id=obj_id,
                            object_type=str(obj_data.get("type", "MarketMemory")),
                            source=RetrievalSource.MARKET_MEMORY,
                            score=round(score, 4),
                            snippet=self._make_snippet(obj_data),
                            metadata=dict(obj_data.get("metadata", {})),
                        )
                    )
        return hits

    def _search_experiment_results(
        self,
        query_tokens: tuple[str, ...],
        context_tags: set[str],
        min_score: float,
    ) -> list[RetrievalHit]:
        """Search experiment result entries."""
        hits: list[RetrievalHit] = []
        for obj_id, obj_data in self._knowledge_index.items():
            if obj_data.get("source") == "experiment_result":
                score = self._score_knowledge(obj_data, query_tokens, context_tags) * 0.7
                if score >= min_score:
                    hits.append(
                        RetrievalHit(
                            hit_id=f"exp-{obj_id}",
                            object_id=obj_id,
                            object_type=str(obj_data.get("type", "ExperimentResult")),
                            source=RetrievalSource.EXPERIMENT_RESULT,
                            score=round(score, 4),
                            snippet=self._make_snippet(obj_data),
                            metadata=dict(obj_data.get("metadata", {})),
                        )
                    )
        return hits

    # ------------------------------------------------------------------
    # Internal: scoring
    # ------------------------------------------------------------------

    def _score_node(
        self,
        node_data: dict[str, Any],
        query_tokens: tuple[str, ...],
        context_tags: set[str],
    ) -> float:
        """Score a single evidence graph node against query tokens."""
        if not query_tokens:
            return 0.0

        # Gather searchable text from node
        searchable = self._extract_text(node_data)
        node_tokens = self._tokenise(searchable)

        # Token overlap score
        if not node_tokens:
            return 0.0
        matching = len(set(query_tokens) & set(node_tokens))
        token_score = (matching / len(query_tokens)) * _TOKEN_WEIGHT * 10

        # Source weight
        source_weight = _SOURCE_WEIGHTS.get(RetrievalSource.EVIDENCE_GRAPH, 1.0)

        # Tag matching bonus
        node_tags = set(node_data.get("metadata", {}).get("tags", []))
        tag_matches = len(node_tags & context_tags)
        tag_bonus = tag_matches * _TAG_MATCH_WEIGHT

        # Recency bonus (from created_at)
        recency = self._recency_bonus(node_data.get("created_at", ""))

        total = (token_score + tag_bonus + recency) * source_weight
        return min(1.0, max(0.0, total))

    def _score_knowledge(
        self,
        obj_data: dict[str, Any],
        query_tokens: tuple[str, ...],
        context_tags: set[str],
    ) -> float:
        """Score a knowledge base object against query tokens."""
        if not query_tokens:
            return 0.0

        searchable = self._extract_text(obj_data)
        obj_tokens = self._tokenise(searchable)

        if not obj_tokens:
            return 0.0
        matching = len(set(query_tokens) & set(obj_tokens))
        token_score = (matching / len(query_tokens)) * _TOKEN_WEIGHT * 10

        # Tag matching bonus
        obj_tags = set(obj_data.get("metadata", {}).get("tags", []))
        tag_matches = len(obj_tags & context_tags)
        tag_bonus = tag_matches * _TAG_MATCH_WEIGHT

        # Recency
        recency = self._recency_bonus(obj_data.get("created_at", ""))

        # Source weight from metadata
        source = RetrievalSource.from_string(str(obj_data.get("source", "knowledge_base")))
        source_weight = _SOURCE_WEIGHTS.get(source, 0.5)

        total = (token_score + tag_bonus + recency) * source_weight
        return min(1.0, max(0.0, total))

    # ------------------------------------------------------------------
    # Internal: helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        """Extract searchable text from a dict."""
        parts: list[str] = []
        for key in (
            "text",
            "content",
            "statement",
            "thesis",
            "description",
            "finding",
            "pattern",
            "recommendation",
            "label",
            "name",
            "node_type",
            "reference_id",
        ):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                parts.append(val)
            elif isinstance(val, (list, tuple)):
                for item in val:
                    if isinstance(item, str) and item.strip():
                        parts.append(item)
        # Extract from metadata sub-dict
        metadata = data.get("metadata")
        if isinstance(metadata, dict):
            for key in (
                "text",
                "content",
                "statement",
                "thesis",
                "description",
                "finding",
                "pattern",
                "recommendation",
                "tags",
            ):
                val = metadata.get(key)
                if isinstance(val, str) and val.strip():
                    parts.append(val)
                elif isinstance(val, (list, tuple)):
                    for item in val:
                        if isinstance(item, str) and item.strip():
                            parts.append(item)
        return " ".join(parts)

    @staticmethod
    def _make_snippet(data: dict[str, Any]) -> str:
        """Create a short snippet from object data."""
        # Check direct fields first
        for key in ("text", "content", "statement", "thesis", "description", "label", "name"):
            val = data.get(key)
            if isinstance(val, str) and val.strip():
                snippet = val.strip()[:_MAX_SNIPPET_LENGTH]
                if len(val) > _MAX_SNIPPET_LENGTH:
                    snippet += "..."
                return snippet
        # Check metadata
        metadata = data.get("metadata", {})
        if isinstance(metadata, dict):
            for key in ("text", "content", "statement", "thesis"):
                val = metadata.get(key)
                if isinstance(val, str) and val.strip():
                    snippet = val.strip()[:_MAX_SNIPPET_LENGTH]
                    if len(val) > _MAX_SNIPPET_LENGTH:
                        snippet += "..."
                    return snippet
        return f"[{data.get('type', 'object')} {list(data.keys())[:3]}]"

    @staticmethod
    def _recency_bonus(created_at: str) -> float:
        """Compute recency bonus based on creation timestamp."""
        if not created_at:
            return 0.0
        try:
            if isinstance(created_at, str):
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                dt = created_at
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0
            if age_days < 0:
                return 0.0
            return _RECENTNESS_BONUS * max(0.0, 1.0 - age_days / _RECENTNESS_WINDOW_DAYS)
        except (ValueError, TypeError):
            return 0.0

    def _build_explanation(
        self,
        query: RetrievalQuery,
        hits: list[RetrievalHit],
        total: int,
    ) -> str:
        """Build a human-readable explanation of the retrieval result."""
        if not hits:
            return f"Query '{query.text[:50]}...' returned no results (searched {total} objects, min_score={query.min_score:.2f})."
        lines = [
            f"Query: '{query.text[:80]}...'" if len(query.text) > 80 else f"Query: '{query.text}'",
            f"Results: {len(hits)} of {total} objects matched (min_score={query.min_score:.2f}).",
            "Top hits:",
        ]
        for i, hit in enumerate(hits[:3], 1):
            lines.append(f"  {i}. [{hit.source.value}] {hit.object_type}({hit.object_id[:20]}...) score={hit.score:.4f}")
        if len(hits) > 3:
            lines.append(f"  ... and {len(hits) - 3} more results.")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# SessionRetriever — multi-query session management
# ═══════════════════════════════════════════════════════════════════


class SessionRetriever:
    """Manages retrieval sessions with context accumulation.

    A session accumulates retrieval results across multiple queries,
    allowing cross-query reasoning and context-aware follow-up searches.

    Parameters
    ----------
    base_retriever : DeterministicRetriever
        The underlying retrieval engine.
    session_id : str
        Unique session identifier.
    relevance_threshold : float
        Minimum score to consider a hit relevant for context.
    """

    def __init__(
        self,
        base_retriever: DeterministicRetriever,
        session_id: str,
        relevance_threshold: float = 0.3,
    ) -> None:
        self._retriever = base_retriever
        self._session_id = session_id
        self._relevance_threshold = relevance_threshold
        self._queries: list[str] = []
        self._all_hits: list[RetrievalHit] = []
        self._session_start = datetime.now(timezone.utc)

    def query(self, query: RetrievalQuery) -> RetrievalResult:
        """Execute a query and accumulate results into session context.

        Parameters
        ----------
        query : RetrievalQuery
            The query to execute.

        Returns
        -------
        RetrievalResult
            The retrieval result.
        """
        result = self._retriever.retrieve(query)

        # Accumulate hits
        for hit in result.hits:
            if hit.score >= self._relevance_threshold:
                self._all_hits.append(hit)

        self._queries.append(query.query_id)

        return result

    def get_context(self) -> RetrievalContext:
        """Get the accumulated session context.

        Returns
        -------
        RetrievalContext
            Session context with all accumulated hits.
        """
        return RetrievalContext(
            session_id=self._session_id,
            queries=tuple(self._queries),
            all_hits=tuple(self._all_hits),
            session_start=self._session_start,
            relevance_threshold=self._relevance_threshold,
        )

    @property
    def query_count(self) -> int:
        """Number of queries executed in this session."""
        return len(self._queries)

    @property
    def hit_count(self) -> int:
        """Number of relevant hits accumulated."""
        return len(self._all_hits)

    def reset(self) -> None:
        """Clear all session state."""
        self._queries.clear()
        self._all_hits.clear()
        self._session_start = datetime.now(timezone.utc)


__all__ = [
    "DeterministicRetriever",
    "SessionRetriever",
]
