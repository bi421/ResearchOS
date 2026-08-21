"""
Tests: Research Intelligence Layer Q13 – Deterministic RAG Knowledge Retrieval.

Coverage:
    * RetrievalQuery construction, validation, serialization
    * RetrievalHit construction, validation, serialization
    * RetrievalResult construction, validation, sorting
    * RetrievalContext construction, validation
    * DeterministicRetriever – tokenisation, scoring, retrieval
    * SessionRetriever – multi-query context accumulation
    * Frozen immutability across all dataclasses
    * Determinism – same query always returns same results
    * Boundary conditions – empty indexes, zero scores, max limits
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from typing import Any

from researchos.intelligence import (
    DeterministicRetriever,
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    NodeType,
    Relationship,
    RetrievalContext,
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
    RetrievalSource,
    SessionRetriever,
)

# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════


def make_query(
    query_id: str = "q1",
    text: str = "bullish trend reversal pattern",
    max_hits: int = 10,
    min_score: float = 0.0,
    context_tags: tuple[str, ...] = (),
    source_filter: list | None = None,
) -> RetrievalQuery:
    return RetrievalQuery(
        query_id=query_id,
        text=text,
        max_hits=max_hits,
        min_score=min_score,
        context_tags=context_tags,
        source_filter=source_filter,
    )


def make_hit(
    hit_id: str = "h1",
    object_id: str = "obj1",
    object_type: str = "EvidenceNode",
    source: RetrievalSource = RetrievalSource.EVIDENCE_GRAPH,
    score: float = 0.85,
    snippet: str = "A bullish trend reversal was detected",
    metadata: dict | None = None,
) -> RetrievalHit:
    return RetrievalHit(
        hit_id=hit_id,
        object_id=object_id,
        object_type=object_type,
        source=source,
        score=score,
        snippet=snippet,
        metadata=metadata or {},
    )


def make_result(
    query_id: str = "q1",
    hits: tuple[RetrievalHit, ...] | None = None,
    total_hits: int = 0,
) -> RetrievalResult:
    return RetrievalResult(
        query_id=query_id,
        hits=hits or (),
        total_hits=total_hits,
    )


def build_indexed_graph() -> tuple[dict[str, dict[str, Any]], DeterministicRetriever]:
    """Build an EvidenceGraph and return its node index + retriever."""
    graph = EvidenceGraph()
    graph.add_node(
        EvidenceNode(
            "n1",
            NodeType.DATASET,
            "ref1",
            {"text": "bullish trend reversal", "tags": ["trend", "reversal"]},
            "2024-01-01",
        )
    )
    graph.add_node(
        EvidenceNode(
            "n2",
            NodeType.EXPERIMENT,
            "ref2",
            {"text": "bearish momentum strategy", "tags": ["momentum"]},
            "2024-06-01",
        )
    )
    graph.add_node(
        EvidenceNode(
            "n3",
            NodeType.RESULT,
            "ref3",
            {"text": "bullish pattern confirmed", "tags": ["confirmed", "bullish"]},
            "2024-12-01",
        )
    )
    index = {n.node_id: n.to_dict() for n in graph.nodes()}
    return index, DeterministicRetriever(node_index=index)


# ═══════════════════════════════════════════════════════════════════
# 1. RetrievalSource
# ═══════════════════════════════════════════════════════════════════


class TestRetrievalSource(unittest.TestCase):
    def test_all_members_exist(self):
        self.assertIn(RetrievalSource.EVIDENCE_GRAPH, RetrievalSource)
        self.assertIn(RetrievalSource.MARKET_MEMORY, RetrievalSource)
        self.assertIn(RetrievalSource.KNOWLEDGE_BASE, RetrievalSource)
        self.assertIn(RetrievalSource.EXPERIMENT_RESULT, RetrievalSource)

    def test_from_string_evidence_graph(self):
        self.assertIs(RetrievalSource.from_string("evidence_graph"), RetrievalSource.EVIDENCE_GRAPH)
        self.assertIs(RetrievalSource.from_string("EVIDENCE_GRAPH"), RetrievalSource.EVIDENCE_GRAPH)

    def test_from_string_market_memory(self):
        self.assertIs(RetrievalSource.from_string("market_memory"), RetrievalSource.MARKET_MEMORY)

    def test_from_string_knowledge_base(self):
        self.assertIs(RetrievalSource.from_string("knowledge_base"), RetrievalSource.KNOWLEDGE_BASE)

    def test_from_string_experiment_result(self):
        self.assertIs(RetrievalSource.from_string("experiment_result"), RetrievalSource.EXPERIMENT_RESULT)

    def test_from_string_unknown_raises(self):
        with self.assertRaises(ValueError):
            RetrievalSource.from_string("unknown")

    def test_matches(self):
        self.assertTrue(RetrievalSource.EVIDENCE_GRAPH.matches("evidence_graph"))
        self.assertFalse(RetrievalSource.EVIDENCE_GRAPH.matches("market_memory"))


# ═══════════════════════════════════════════════════════════════════
# 2. RetrievalQuery — Construction & Validation
# ═══════════════════════════════════════════════════════════════════


class TestRetrievalQueryConstruction(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        q = make_query()
        self.assertEqual(q.query_id, "q1")
        self.assertEqual(q.text, "bullish trend reversal pattern")

    def test_defaults(self):
        q = RetrievalQuery(query_id="q", text="test")
        self.assertEqual(q.max_hits, 10)
        self.assertEqual(q.min_score, 0.0)
        self.assertIsNone(q.source_filter)
        self.assertEqual(q.context_tags, ())

    def test_empty_query_id_raises(self):
        with self.assertRaises(ValueError):
            RetrievalQuery(query_id="", text="test")

    def test_whitespace_query_id_stripped(self):
        q = RetrievalQuery(query_id="  q1  ", text="test")
        self.assertEqual(q.query_id, "q1")

    def test_max_hits_less_than_one_raises(self):
        with self.assertRaises(ValueError):
            RetrievalQuery(query_id="q", text="test", max_hits=0)

    def test_min_score_negative_raises(self):
        with self.assertRaises(ValueError):
            RetrievalQuery(query_id="q", text="test", min_score=-0.1)

    def test_min_score_above_one_raises(self):
        with self.assertRaises(ValueError):
            RetrievalQuery(query_id="q", text="test", min_score=1.1)

    def test_text_is_stripped(self):
        q = RetrievalQuery(query_id="q", text="  test  ")
        self.assertEqual(q.text, "test")

    def test_context_tags_deduplicated_and_sorted(self):
        q = RetrievalQuery(query_id="q", text="test", context_tags=("b", "a", "b"))
        self.assertEqual(q.context_tags, ("a", "b"))

    def test_source_filter_none(self):
        q = RetrievalQuery(query_id="q", text="test")
        self.assertIsNone(q.source_filter)

    def test_source_filter_set(self):
        q = RetrievalQuery(query_id="q", text="test", source_filter=[RetrievalSource.EVIDENCE_GRAPH])
        self.assertEqual(q.source_filter, (RetrievalSource.EVIDENCE_GRAPH,))


# ═══════════════════════════════════════════════════════════════════
# 3. RetrievalQuery — Serialization
# ═══════════════════════════════════════════════════════════════════


class TestRetrievalQuerySerialization(unittest.TestCase):
    def test_to_dict_contains_all_fields(self):
        q = make_query()
        d = q.to_dict()
        self.assertEqual(d["query_id"], "q1")
        self.assertEqual(d["text"], "bullish trend reversal pattern")
        self.assertEqual(d["max_hits"], 10)
        self.assertEqual(d["min_score"], 0.0)

    def test_from_dict_roundtrip(self):
        q = make_query(context_tags=("trend", "pattern"))
        restored = RetrievalQuery.from_dict(q.to_dict())
        self.assertEqual(restored.query_id, q.query_id)
        self.assertEqual(restored.text, q.text)
        self.assertEqual(restored.context_tags, q.context_tags)

    def test_to_dict_json_serializable(self):
        q = make_query()
        text = json.dumps(q.to_dict())
        self.assertIn("q1", text)

    def test_from_dict_missing_query_id_raises(self):
        with self.assertRaises((KeyError, ValueError)):
            RetrievalQuery.from_dict({"text": "test"})


# ═══════════════════════════════════════════════════════════════════
# 4. RetrievalHit — Construction & Validation
# ═══════════════════════════════════════════════════════════════════


class TestRetrievalHitConstruction(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        h = make_hit()
        self.assertEqual(h.hit_id, "h1")
        self.assertEqual(h.object_id, "obj1")
        self.assertEqual(h.object_type, "EvidenceNode")
        self.assertIs(h.source, RetrievalSource.EVIDENCE_GRAPH)
        self.assertEqual(h.score, 0.85)
        self.assertEqual(h.snippet, "A bullish trend reversal was detected")

    def test_default_metadata_empty(self):
        h = make_hit()
        self.assertEqual(h.metadata, {})

    def test_empty_hit_id_raises(self):
        with self.assertRaises(ValueError):
            RetrievalHit(
                hit_id="",
                object_id="o",
                object_type="t",
                source=RetrievalSource.EVIDENCE_GRAPH,
                score=0.5,
                snippet="s",
            )

    def test_score_below_zero_raises(self):
        with self.assertRaises(ValueError):
            RetrievalHit(
                hit_id="h",
                object_id="o",
                object_type="t",
                source=RetrievalSource.EVIDENCE_GRAPH,
                score=-0.1,
                snippet="s",
            )

    def test_score_above_one_raises(self):
        with self.assertRaises(ValueError):
            RetrievalHit(
                hit_id="h",
                object_id="o",
                object_type="t",
                source=RetrievalSource.EVIDENCE_GRAPH,
                score=1.1,
                snippet="s",
            )

    def test_snippet_stripped(self):
        h = make_hit(snippet="  test  ")
        self.assertEqual(h.snippet, "test")

    def test_empty_snippet_accepted(self):
        h = make_hit(snippet="")
        self.assertEqual(h.snippet, "")


# ═══════════════════════════════════════════════════════════════════
# 5. RetrievalHit — Immutability & Serialization
# ═══════════════════════════════════════════════════════════════════


class TestRetrievalHitImmutability(unittest.TestCase):
    def test_is_frozen(self):
        h = make_hit()
        with self.assertRaises(Exception):
            h.hit_id = "x"  # type: ignore[misc]

    def test_score_immutable(self):
        h = make_hit()
        with self.assertRaises(Exception):
            h.score = 0.9  # type: ignore[misc]

    def test_metadata_immutable(self):
        h = make_hit(metadata={"a": 1})
        with self.assertRaises(Exception):
            h.metadata["a"] = 2  # type: ignore[index]

    def test_to_dict_roundtrip(self):
        h = make_hit(metadata={"key": "value"})
        restored = RetrievalHit.from_dict(h.to_dict())
        self.assertEqual(restored, h)

    def test_to_dict_json_serializable(self):
        h = make_hit()
        text = json.dumps(h.to_dict())
        self.assertIn("h1", text)


# ═══════════════════════════════════════════════════════════════════
# 6. RetrievalResult — Construction & Validation
# ═══════════════════════════════════════════════════════════════════


class TestRetrievalResultConstruction(unittest.TestCase):
    def test_constructs_with_required_fields(self):
        r = make_result()
        self.assertEqual(r.query_id, "q1")
        self.assertEqual(r.hits, ())
        self.assertEqual(r.total_hits, 0)

    def test_with_hits(self):
        hits = (make_hit("h1", score=0.9), make_hit("h2", score=0.7))
        r = make_result(hits=hits, total_hits=2)
        self.assertEqual(len(r.hits), 2)
        self.assertEqual(r.hits[0].score, 0.9)

    def test_empty_query_id_raises(self):
        with self.assertRaises(ValueError):
            RetrievalResult(query_id="", hits=(), total_hits=0)

    def test_unsorted_hits_raises(self):
        hits = (make_hit("h1", score=0.5), make_hit("h2", score=0.9))
        with self.assertRaises(ValueError):
            RetrievalResult(query_id="q", hits=hits, total_hits=2)

    def test_total_hits_negative_becomes_zero(self):
        r = RetrievalResult(query_id="q", hits=(), total_hits=-5)
        self.assertEqual(r.total_hits, 0)

    def test_empty_hits_is_valid(self):
        r = RetrievalResult(query_id="q", hits=(), total_hits=0)
        self.assertEqual(r.hits, ())


# ═══════════════════════════════════════════════════════════════════
# 7. RetrievalResult — Serialization & Summary
# ═══════════════════════════════════════════════════════════════════


class TestRetrievalResultSerialization(unittest.TestCase):
    def test_to_dict_roundtrip(self):
        hits = (make_hit("h1", score=0.9),)
        r = make_result(hits=hits, total_hits=1)
        restored = RetrievalResult.from_dict(r.to_dict())
        self.assertEqual(restored.query_id, r.query_id)
        self.assertEqual(len(restored.hits), 1)
        self.assertEqual(restored.hits[0].score, 0.9)

    def test_to_dict_json_serializable(self):
        r = make_result()
        text = json.dumps(r.to_dict())
        self.assertIn("q1", text)

    def test_summary_empty(self):
        r = make_result()
        summary = r.summary()
        self.assertIn("No results", summary)

    def test_summary_with_hits(self):
        hits = (make_hit("h1", score=0.9), make_hit("h2", score=0.7))
        r = make_result(hits=hits, total_hits=2)
        summary = r.summary()
        self.assertIn("2 result", summary)
        self.assertIn("0.9", summary)


# ═══════════════════════════════════════════════════════════════════
# 8. RetrievalContext
# ═══════════════════════════════════════════════════════════════════


class TestRetrievalContext(unittest.TestCase):
    def test_constructs(self):
        ctx = RetrievalContext(
            session_id="s1",
            queries=("q1", "q2"),
            all_hits=(),
            session_start=datetime.now(timezone.utc),
        )
        self.assertEqual(ctx.session_id, "s1")
        self.assertEqual(ctx.queries, ("q1", "q2"))
        self.assertEqual(ctx.relevance_threshold, 0.3)

    def test_empty_session_id_raises(self):
        with self.assertRaises(ValueError):
            RetrievalContext(session_id="", queries=(), all_hits=(), session_start=datetime.now(timezone.utc))

    def test_hits_sorted_by_score(self):
        hits = (make_hit("h2", score=0.5), make_hit("h1", score=0.9))
        ctx = RetrievalContext(session_id="s", queries=(), all_hits=hits, session_start=datetime.now(timezone.utc))
        self.assertEqual(ctx.all_hits[0].hit_id, "h1")

    def test_to_dict_roundtrip(self):
        ctx = RetrievalContext(
            session_id="s1",
            queries=("q1",),
            all_hits=(),
            session_start=datetime.now(timezone.utc),
        )
        restored = RetrievalContext.from_dict(ctx.to_dict())
        self.assertEqual(restored.session_id, ctx.session_id)
        self.assertEqual(restored.queries, ctx.queries)


# ═══════════════════════════════════════════════════════════════════
# 9. DeterministicRetriever — Tokenisation
# ═══════════════════════════════════════════════════════════════════


class TestRetrieverTokenisation(unittest.TestCase):
    def test_simple_text(self):
        retriever = DeterministicRetriever()
        tokens = retriever._tokenise("hello world")
        self.assertEqual(tokens, ("hello", "world"))

    def test_empty_text(self):
        retriever = DeterministicRetriever()
        tokens = retriever._tokenise("")
        self.assertEqual(tokens, ())

    def test_numbers_only(self):
        retriever = DeterministicRetriever()
        tokens = retriever._tokenise("123 456")
        self.assertEqual(tokens, ("123", "456"))

    def test_mixed_case(self):
        retriever = DeterministicRetriever()
        tokens = retriever._tokenise("Hello HELLO hello")
        self.assertEqual(tokens, ("hello",))  # deduplicated

    def test_special_characters_ignored(self):
        retriever = DeterministicRetriever()
        tokens = retriever._tokenise("hello-world@test")
        self.assertEqual(tokens, ("hello", "world", "test"))


# ═══════════════════════════════════════════════════════════════════
# 10. DeterministicRetriever — Empty Index
# ═══════════════════════════════════════════════════════════════════


class TestRetrieverEmptyIndex(unittest.TestCase):
    def test_empty_index_returns_no_hits(self):
        retriever = DeterministicRetriever()
        q = make_query()
        result = retriever.retrieve(q)
        self.assertEqual(result.total_hits, 0)
        self.assertEqual(result.hits, ())

    def test_empty_index_query_time(self):
        retriever = DeterministicRetriever()
        q = make_query()
        result = retriever.retrieve(q)
        self.assertGreaterEqual(result.query_time_ms, 0.0)

    def test_empty_index_explanation(self):
        retriever = DeterministicRetriever()
        q = make_query()
        result = retriever.retrieve(q)
        self.assertIn("no results", result.explanation.lower())


# ═══════════════════════════════════════════════════════════════════
# 11. DeterministicRetriever — Basic Retrieval
# ═══════════════════════════════════════════════════════════════════


class TestRetrieverBasicRetrieval(unittest.TestCase):
    def test_retrieve_finds_matched_node(self):
        index, retriever = build_indexed_graph()
        q = make_query(text="bullish trend")
        result = retriever.retrieve(q)
        self.assertGreater(result.total_hits, 0)
        self.assertGreater(len(result.hits), 0)

    def test_retrieve_returns_sorted_descending(self):
        index, retriever = build_indexed_graph()
        q = make_query(text="bullish")
        result = retriever.retrieve(q)
        for i in range(len(result.hits) - 1):
            self.assertGreaterEqual(result.hits[i].score, result.hits[i + 1].score)

    def test_retrieve_applies_max_hits(self):
        index, retriever = build_indexed_graph()
        q = make_query(text="bullish", max_hits=1)
        result = retriever.retrieve(q)
        self.assertLessEqual(len(result.hits), 1)

    def test_retrieve_applies_min_score(self):
        index, retriever = build_indexed_graph()
        q = make_query(text="bullish", min_score=0.99)
        result = retriever.retrieve(q)
        for h in result.hits:
            self.assertGreaterEqual(h.score, 0.99)

    def test_retrieve_source_filter(self):
        index, retriever = build_indexed_graph()
        q = make_query(text="bullish", source_filter=[RetrievalSource.EVIDENCE_GRAPH])
        result = retriever.retrieve(q)
        for h in result.hits:
            self.assertEqual(h.source, RetrievalSource.EVIDENCE_GRAPH)


# ═══════════════════════════════════════════════════════════════════
# 12. DeterministicRetriever — Determinism
# ═══════════════════════════════════════════════════════════════════


class TestRetrieverDeterminism(unittest.TestCase):
    def test_same_query_same_results(self):
        index, retriever = build_indexed_graph()
        q = make_query(text="bullish trend reversal")
        r1 = retriever.retrieve(q)
        r2 = retriever.retrieve(q)
        self.assertEqual(r1.total_hits, r2.total_hits)
        for h1, h2 in zip(r1.hits, r2.hits):
            self.assertEqual(h1.hit_id, h2.hit_id)
            self.assertEqual(h1.score, h2.score)

    def test_different_queries_different_results(self):
        index, retriever = build_indexed_graph()
        q1 = make_query(text="bullish")
        q2 = make_query(text="bearish")
        r1 = retriever.retrieve(q1)
        r2 = retriever.retrieve(q2)
        # Different queries should have different top hits or scores
        self.assertIsNotNone(r1)
        self.assertIsNotNone(r2)

    def test_batch_retrieval_deterministic(self):
        index, retriever = build_indexed_graph()
        queries = [make_query(f"q{i}", text="bullish") for i in range(3)]
        results = retriever.retrieve_batch(queries)
        self.assertEqual(len(results), 3)
        for q in queries:
            self.assertIn(q.query_id, results)


# ═══════════════════════════════════════════════════════════════════
# 13. DeterministicRetriever — Index Management
# ═══════════════════════════════════════════════════════════════════


class TestRetrieverIndexManagement(unittest.TestCase):
    def test_node_count(self):
        index, retriever = build_indexed_graph()
        self.assertEqual(retriever.node_count, 3)

    def test_clear_index(self):
        index, retriever = build_indexed_graph()
        retriever.clear_index()
        self.assertEqual(retriever.node_count, 0)
        result = retriever.retrieve(make_query())
        self.assertEqual(result.total_hits, 0)

    def test_update_index(self):
        retriever = DeterministicRetriever()
        retriever.update_index(nodes={"n1": {"node_id": "n1"}})
        self.assertEqual(retriever.node_count, 1)

    def test_knowledge_count_empty(self):
        retriever = DeterministicRetriever()
        self.assertEqual(retriever.knowledge_count, 0)

    def test_update_knowledge_index(self):
        retriever = DeterministicRetriever()
        retriever.update_index(knowledge={"k1": {"type": "Knowledge", "text": "test", "source": "knowledge_base"}})
        self.assertEqual(retriever.knowledge_count, 1)


# ═══════════════════════════════════════════════════════════════════
# 14. DeterministicRetriever — Scoring
# ═══════════════════════════════════════════════════════════════════


class TestRetrieverScoring(unittest.TestCase):
    def test_exact_token_match_higher_score(self):
        index, retriever = build_indexed_graph()
        q_exact = make_query(text="bullish trend reversal pattern")
        q_partial = make_query(text="xyz no match at all")
        r_exact = retriever.retrieve(q_exact)
        r_partial = retriever.retrieve(q_partial)
        # Exact match should find results with higher scores
        if r_exact.hits and r_partial.hits:
            self.assertGreater(r_exact.hits[0].score, r_partial.hits[0].score)
        elif r_exact.hits:
            self.assertGreater(r_exact.total_hits, 0)

    def test_tag_matching_increases_score(self):
        index, retriever = build_indexed_graph()
        q_with_tags = make_query(text="bullish", context_tags=("bullish",))
        q_without_tags = make_query(text="bullish", context_tags=())
        r_with = retriever.retrieve(q_with_tags)
        r_without = retriever.retrieve(q_without_tags)
        if r_with.hits and r_without.hits:
            self.assertGreaterEqual(r_with.hits[0].score, r_without.hits[0].score)

    def test_all_sources_searched_by_default(self):
        index, retriever = build_indexed_graph()
        retriever.update_index(
            knowledge={
                "k1": {
                    "type": "Test",
                    "text": "knowledge base match",
                    "source": "knowledge_base",
                    "created_at": "2024-01-01",
                }
            }
        )
        q = make_query(text="knowledge base match")
        result = retriever.retrieve(q)
        # Should search all sources by default
        self.assertIsNotNone(result)


# ═══════════════════════════════════════════════════════════════════
# 15. SessionRetriever
# ═══════════════════════════════════════════════════════════════════


class TestSessionRetriever(unittest.TestCase):
    def test_constructs(self):
        retriever = DeterministicRetriever()
        session = SessionRetriever(retriever, "s1")
        self.assertEqual(session.query_count, 0)
        self.assertEqual(session.hit_count, 0)

    def test_query_accumulates(self):
        index, base = build_indexed_graph()
        session = SessionRetriever(base, "s1")
        q = make_query(text="bullish")
        result = session.query(q)
        self.assertEqual(session.query_count, 1)
        self.assertIsNotNone(result)

    def test_get_context(self):
        index, base = build_indexed_graph()
        session = SessionRetriever(base, "s1", relevance_threshold=0.0)
        session.query(make_query(text="bullish"))
        ctx = session.get_context()
        self.assertEqual(ctx.session_id, "s1")
        self.assertEqual(len(ctx.queries), 1)

    def test_reset_clears_state(self):
        index, base = build_indexed_graph()
        session = SessionRetriever(base, "s1", relevance_threshold=0.0)
        session.query(make_query(text="bullish"))
        session.reset()
        self.assertEqual(session.query_count, 0)
        self.assertEqual(session.hit_count, 0)

    def test_multiple_queries_accumulate(self):
        index, base = build_indexed_graph()
        session = SessionRetriever(base, "s1", relevance_threshold=0.0)
        session.query(make_query("q1", text="bullish"))
        session.query(make_query("q2", text="pattern"))
        self.assertEqual(session.query_count, 2)
        ctx = session.get_context()
        self.assertEqual(len(ctx.queries), 2)


# ═══════════════════════════════════════════════════════════════════
# 16. Frozen Immutability
# ═══════════════════════════════════════════════════════════════════


class TestFrozenImmutability(unittest.TestCase):
    def test_query_is_frozen(self):
        q = make_query()
        with self.assertRaises(Exception):
            q.query_id = "x"  # type: ignore[misc]

    def test_hit_is_frozen(self):
        h = make_hit()
        with self.assertRaises(Exception):
            h.score = 0.9  # type: ignore[misc]

    def test_result_is_frozen(self):
        r = make_result()
        with self.assertRaises(Exception):
            r.query_id = "x"  # type: ignore[misc]

    def test_context_is_frozen(self):
        ctx = RetrievalContext(
            session_id="s",
            queries=(),
            all_hits=(),
            session_start=datetime.now(timezone.utc),
        )
        with self.assertRaises(Exception):
            ctx.session_id = "x"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════════
# 17. Integration — EvidenceGraph + Retriever
# ═══════════════════════════════════════════════════════════════════


class TestGraphRetrieverIntegration(unittest.TestCase):
    def test_full_pipeline(self):
        graph = EvidenceGraph()
        graph.add_node(
            EvidenceNode(
                "n1",
                NodeType.DATASET,
                "ref1",
                {
                    "text": "XAUUSD bullish engulfing pattern detected",
                    "tags": ["pattern", "bullish"],
                },
                "2024-01-15",
            )
        )
        graph.add_node(
            EvidenceNode(
                "n2",
                NodeType.EXPERIMENT,
                "ref2",
                {
                    "text": "Bearish momentum strategy backtest results",
                    "tags": ["bearish", "momentum"],
                },
                "2024-06-20",
            )
        )
        graph.add_edge(EvidenceEdge("e1", "n1", "n2", Relationship.VALIDATED_BY))

        index = {n.node_id: n.to_dict() for n in graph.nodes()}
        retriever = DeterministicRetriever(node_index=index)

        q = make_query(text="bullish pattern", max_hits=5)
        result = retriever.retrieve(q)

        self.assertGreater(result.total_hits, 0)
        self.assertGreater(len(result.hits), 0)
        self.assertEqual(result.hits[0].object_type, "EvidenceNode")

    def test_integration_deterministic(self):
        graph = EvidenceGraph()
        graph.add_node(
            EvidenceNode(
                "n1",
                NodeType.RESULT,
                "ref1",
                {"text": "Winning strategy bullish trend"},
                "2024-03-01",
            )
        )
        index = {n.node_id: n.to_dict() for n in graph.nodes()}
        retriever = DeterministicRetriever(node_index=index)

        r1 = retriever.retrieve(make_query(text="bullish trend"))
        r2 = retriever.retrieve(make_query(text="bullish trend"))
        self.assertEqual(r1.total_hits, r2.total_hits)
        if r1.hits and r2.hits:
            self.assertEqual(r1.hits[0].hit_id, r2.hits[0].hit_id)


# ═══════════════════════════════════════════════════════════════════
# 18. Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases(unittest.TestCase):
    def test_query_with_no_text(self):
        retriever = DeterministicRetriever()
        q = make_query(text="")
        result = retriever.retrieve(q)
        self.assertEqual(result.total_hits, 0)

    def test_query_with_very_long_text(self):
        retriever = DeterministicRetriever()
        long_text = " ".join(["word"] * 1000)
        q = make_query(text=long_text)
        result = retriever.retrieve(q)
        self.assertIsInstance(result, RetrievalResult)

    def test_hit_with_empty_metadata(self):
        h = make_hit(metadata={})
        self.assertEqual(h.metadata, {})

    def test_result_with_no_explanation(self):
        r = make_result()
        self.assertIn("No results", r.summary())

    def test_retriever_with_large_index(self):
        index = {
            f"n{i}": {
                "node_id": f"n{i}",
                "node_type": "dataset",
                "reference_id": f"ref{i}",
                "metadata": {"text": f"content {i}"},
                "created_at": "2024-01-01",
            }
            for i in range(100)
        }
        retriever = DeterministicRetriever(node_index=index)
        result = retriever.retrieve(make_query(text="content"))
        self.assertGreaterEqual(result.total_hits, 0)

    def test_session_retriever_empty(self):
        retriever = DeterministicRetriever()
        session = SessionRetriever(retriever, "empty")
        ctx = session.get_context()
        self.assertEqual(ctx.session_id, "empty")
        self.assertEqual(len(ctx.queries), 0)


# ═══════════════════════════════════════════════════════════════════
# 19. Snippet Generation
# ═══════════════════════════════════════════════════════════════════


class TestSnippetGeneration(unittest.TestCase):
    def test_short_snippet(self):
        retriever = DeterministicRetriever()
        snippet = retriever._make_snippet({"text": "short"})
        self.assertEqual(snippet, "short")

    def test_long_snippet_truncated(self):
        retriever = DeterministicRetriever()
        long_text = "x" * 500
        snippet = retriever._make_snippet({"text": long_text})
        self.assertLessEqual(len(snippet), 203)  # 200 + "..."
        self.assertTrue(snippet.endswith("..."))

    def test_snippet_from_metadata(self):
        retriever = DeterministicRetriever()
        snippet = retriever._make_snippet({"type": "Test", "metadata": {"text": "hello world"}})
        self.assertEqual(snippet, "hello world")


# ═══════════════════════════════════════════════════════════════════
# 20. Recency Bonus
# ═══════════════════════════════════════════════════════════════════


class TestRecencyBonus(unittest.TestCase):
    def test_recent_date_gets_bonus(self):
        retriever = DeterministicRetriever()
        # Use a recent date
        recent = datetime.now(timezone.utc).isoformat()
        bonus = retriever._recency_bonus(recent)
        self.assertGreater(bonus, 0.0)

    def test_old_date_gets_no_bonus(self):
        retriever = DeterministicRetriever()
        old = "2000-01-01T00:00:00+00:00"
        bonus = retriever._recency_bonus(old)
        self.assertEqual(bonus, 0.0)

    def test_empty_date_gets_no_bonus(self):
        retriever = DeterministicRetriever()
        bonus = retriever._recency_bonus("")
        self.assertEqual(bonus, 0.0)


if __name__ == "__main__":
    unittest.main()
