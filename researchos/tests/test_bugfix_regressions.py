"""
Regression tests for the two forensic-audit production bugs.

BUG-01: researchos/intelligence/rag_contracts.py — RetrievalQuery.from_dict
    and RetrievalContext.from_dict raised TypeError when the optional
    timestamp/session_start key was omitted (datetime default was called
    twice: ``datetime.now(timezone.utc)()``).

BUG-02: researchos/quant_engine/fundamental/__init__.py — ``__all__``
    exported the nonexistent symbol ``commodity_ratio`` (real name:
    ``commodity_correlations``), breaking ``import *``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from researchos.intelligence.rag_contracts import (
    RetrievalContext,
    RetrievalQuery,
)

# =============================================================================
# BUG-01 — missing-timestamp default branch
# =============================================================================


class TestRetrievalQueryMissingTimestamp:
    def test_from_dict_without_timestamp_key(self):
        query = RetrievalQuery.from_dict({"query_id": "q1"})
        assert isinstance(query.timestamp, datetime)

    def test_default_timestamp_is_timezone_aware(self):
        query = RetrievalQuery.from_dict({"query_id": "q1"})
        assert query.timestamp.tzinfo is not None

    def test_default_timestamp_is_utc(self):
        query = RetrievalQuery.from_dict({"query_id": "q1"})
        assert query.timestamp.utcoffset() == timedelta(0)

    def test_existing_timestamp_round_trip_preserved(self):
        fixed = datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        query = RetrievalQuery(query_id="q1", text="gold", timestamp=fixed)
        restored = RetrievalQuery.from_dict(query.to_dict())
        assert restored.timestamp == fixed


class TestRetrievalContextMissingTimestamp:
    def test_from_dict_without_session_start_key(self):
        context = RetrievalContext.from_dict({"session_id": "s1"})
        assert isinstance(context.session_start, datetime)

    def test_default_session_start_is_timezone_aware(self):
        context = RetrievalContext.from_dict({"session_id": "s1"})
        assert context.session_start.tzinfo is not None

    def test_default_session_start_is_utc(self):
        context = RetrievalContext.from_dict({"session_id": "s1"})
        assert context.session_start.utcoffset() == timedelta(0)

    def test_existing_session_start_round_trip_preserved(self):
        fixed = datetime(2025, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
        context = RetrievalContext(session_id="s1", queries=(), all_hits=(), session_start=fixed)
        restored = RetrievalContext.from_dict(context.to_dict())
        assert restored.session_start == fixed


# =============================================================================
# BUG-02 — fundamental package __all__ validity
# =============================================================================


class TestFundamentalAllExports:
    def test_star_import_does_not_raise(self):
        # exec in a fresh namespace; a bad __all__ entry raises AttributeError
        namespace: dict = {}
        exec("from researchos.quant_engine.fundamental import *", namespace)
        assert "commodity_correlations" in namespace

    def test_every_all_name_exists(self):
        from researchos.quant_engine import fundamental

        for name in fundamental.__all__:
            assert hasattr(fundamental, name), f"fundamental.__all__ references missing symbol {name!r}"

    def test_commodity_ratio_not_exported(self):
        from researchos.quant_engine import fundamental

        assert "commodity_ratio" not in fundamental.__all__
