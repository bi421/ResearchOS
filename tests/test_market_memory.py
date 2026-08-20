"""Tests for the Market Memory Engine — Phase 1 of TRADER-OS Research Intelligence.

Covers:
- Object creation and determinism
- Serialization round-trip (to_dict / from_dict)
- Hash stability
- Lifecycle transitions
- Business logic (confirm, resolve)
- MarketMemoryEngine service
- Query methods
- Edge cases
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from researchos.memory.engine import MarketMemoryEngine
from researchos.objects.market_memory import (
    LiquidityEvent,
    MarketEvent,
    MarketOutcome,
    MarketSession,
    MarketStructure,
    NewsReference,
    VolatilityState,
)
from researchos.repository.memory import MemoryRepository


def ts(year=2024, month=1, day=1, hour=0, minute=0):
    """Helper: deterministic UTC timestamp."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# ===========================================================================
# Market Structure Tests
# ===========================================================================


class TestMarketStructure:
    def test_create_bos(self):
        ms = MarketStructure(
            structure_type="BOS",
            asset="EURUSD",
            timeframe="H1",
            timestamp=ts(2024, 6, 1, 8, 0),
            direction="bullish",
            price_level=1.1050,
        )
        assert ms.structure_type == "BOS"
        assert ms.asset == "EURUSD"
        assert ms.direction == "bullish"
        assert ms.price_level == 1.1050
        assert ms.confirmed is False
        assert ms.id is not None
        assert ms.lifecycle.current_stage.value == "Detected"

    def test_create_choch(self):
        ms = MarketStructure(
            structure_type="CHOCH",
            asset="GBPUSD",
            timeframe="H1",
            timestamp=ts(2024, 6, 1, 10, 0),
            direction="bearish",
            price_level=1.2700,
        )
        assert ms.structure_type == "CHOCH"
        assert ms.direction == "bearish"

    def test_deterministic_id(self):
        ms1 = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
        ms2 = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
        assert ms1.id == ms2.id

    def test_different_inputs_different_id(self):
        ms1 = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
        ms2 = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1100)
        assert ms1.id != ms2.id

    def test_confirm(self):
        ms = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
        assert ms.confirmed is False
        ms.confirm(1.1080)
        assert ms.confirmed is True
        assert ms.confirmation_price == 1.1080
        assert ms.lifecycle.current_stage.value == "Verified"

    def test_serialization_round_trip(self):
        ms = MarketStructure(
            "BOS",
            "EURUSD",
            "H1",
            ts(2024, 6, 1, 8, 0),
            direction="bullish",
            price_level=1.1050,
            notes="Strong breakout",
            ontology_tags=["trend", "momentum"],
        )
        d = ms.to_dict()
        ms2 = MarketStructure.from_dict(d)
        assert ms2.id == ms.id
        assert ms2.structure_type == "BOS"
        assert ms2.asset == "EURUSD"
        assert ms2.timeframe == "H1"
        assert ms2.direction == "bullish"
        assert ms2.price_level == 1.1050
        assert ms2.notes == "Strong breakout"
        assert ms2.ontology_tags == ["trend", "momentum"]
        assert ms2.lifecycle.current_stage == ms.lifecycle.current_stage

    def test_hash_determinism(self):
        ms1 = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
        ms2 = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
        assert ms1.hash == ms2.hash

    def test_hash_matches_after_round_trip(self):
        ms = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
        d = ms.to_dict()
        ms2 = MarketStructure.from_dict(d)
        assert ms2.hash == ms.hash

    def test_defaults(self):
        ms = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0))
        assert ms.direction == "bullish"
        assert ms.price_level == 0.0
        assert ms.confirmed is False
        assert ms.previous_structure_id == ""
        assert ms.notes == ""


# ===========================================================================
# Liquidity Event Tests
# ===========================================================================


class TestLiquidityEvent:
    def test_create_sweep(self):
        le = LiquidityEvent(
            event_type="Sweep",
            asset="EURUSD",
            timeframe="M15",
            timestamp=ts(2024, 6, 1, 9, 30),
            direction="bearish",
            price_level=1.1020,
            swept_levels=[1.1030, 1.1040],
        )
        assert le.event_type == "Sweep"
        assert le.asset == "EURUSD"
        assert le.price_level == 1.1020
        assert le.swept_levels == [1.1030, 1.1040]
        assert le.outcome == "Pending"

    def test_deterministic_id(self):
        le1 = LiquidityEvent("Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30), price_level=1.1020)
        le2 = LiquidityEvent("Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30), price_level=1.1020)
        assert le1.id == le2.id

    def test_resolve(self):
        le = LiquidityEvent("Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30))
        assert le.outcome == "Pending"
        le.resolve("Hit")
        assert le.outcome == "Hit"
        assert le.lifecycle.current_stage.value == "Resolved"

    def test_serialization_round_trip(self):
        le = LiquidityEvent(
            "StopRun",
            "GBPUSD",
            "M15",
            ts(2024, 6, 1, 10, 0),
            direction="bullish",
            price_level=1.2650,
            swept_levels=[1.2630, 1.2620],
        )
        d = le.to_dict()
        le2 = LiquidityEvent.from_dict(d)
        assert le2.id == le.id
        assert le2.event_type == "StopRun"
        assert le2.swept_levels == [1.2630, 1.2620]

    def test_hash_determinism(self):
        le1 = LiquidityEvent("Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30), price_level=1.1020)
        le2 = LiquidityEvent("Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30), price_level=1.1020)
        assert le1.hash == le2.hash


# ===========================================================================
# Market Session Tests
# ===========================================================================


class TestMarketSession:
    def test_create_london_session(self):
        ms = MarketSession(
            session_name="London",
            asset="EURUSD",
            date="2024-06-01",
            start_time=ts(2024, 6, 1, 7, 0),
            end_time=ts(2024, 6, 1, 16, 0),
            open=1.1000,
            high=1.1080,
            low=1.0980,
            close=1.1060,
            direction="bullish",
            volume_ratio=1.2,
        )
        assert ms.session_name == "London"
        assert ms.asset == "EURUSD"
        assert ms.open == 1.1000
        assert ms.close == 1.1060
        assert ms.direction == "bullish"
        assert ms.range == pytest.approx(0.0100, rel=1e-9)
        assert ms.body == pytest.approx(0.0060, rel=1e-9)

    def test_deterministic_id(self):
        ms1 = MarketSession(
            "London", "EURUSD", "2024-06-01", ts(2024, 6, 1, 7, 0), ts(2024, 6, 1, 16, 0)
        )
        ms2 = MarketSession(
            "London", "EURUSD", "2024-06-01", ts(2024, 6, 1, 7, 0), ts(2024, 6, 1, 16, 0)
        )
        assert ms1.id == ms2.id

    def test_serialization_round_trip(self):
        ms = MarketSession(
            "NewYork",
            "GBPUSD",
            "2024-06-01",
            ts(2024, 6, 1, 13, 0),
            ts(2024, 6, 1, 22, 0),
            open=1.2700,
            high=1.2750,
            low=1.2680,
            close=1.2730,
            direction="bullish",
            volume_ratio=0.9,
        )
        d = ms.to_dict()
        ms2 = MarketSession.from_dict(d)
        assert ms2.id == ms.id
        assert ms2.session_name == "NewYork"
        assert ms2.open == 1.2700
        assert ms2.range == ms.range


# ===========================================================================
# Volatility State Tests
# ===========================================================================


class TestVolatilityState:
    def test_create(self):
        vs = VolatilityState(
            asset="EURUSD",
            timeframe="H1",
            timestamp=ts(2024, 6, 1, 12, 0),
            atr_value=0.0015,
            atr_percentile=0.85,
            volatility_regime="High",
            expanding=True,
            bb_width=0.02,
        )
        assert vs.asset == "EURUSD"
        assert vs.atr_value == 0.0015
        assert vs.volatility_regime == "High"
        assert vs.expanding is True

    def test_deterministic_id(self):
        vs1 = VolatilityState("EURUSD", "H1", ts(2024, 6, 1, 12, 0))
        vs2 = VolatilityState("EURUSD", "H1", ts(2024, 6, 1, 12, 0))
        assert vs1.id == vs2.id

    def test_serialization_round_trip(self):
        vs = VolatilityState(
            "EURUSD",
            "H1",
            ts(2024, 6, 1, 12, 0),
            atr_value=0.0015,
            atr_percentile=0.9,
            volatility_regime="Extreme",
            expanding=True,
        )
        d = vs.to_dict()
        vs2 = VolatilityState.from_dict(d)
        assert vs2.id == vs.id
        assert vs2.atr_value == 0.0015
        assert vs2.volatility_regime == "Extreme"
        assert vs2.expanding is True


# ===========================================================================
# News Reference Tests
# ===========================================================================


class TestNewsReference:
    def test_create(self):
        nr = NewsReference(
            title="Fed holds rates steady at 5.5%",
            source="Reuters",
            published_at=ts(2024, 6, 1, 14, 0),
            impact_score=0.8,
            sentiment="neutral",
            affected_assets=["EURUSD", "GBPUSD", "USDJPY"],
            category="CentralBank",
            summary="Federal Reserve maintains current interest rates",
        )
        assert nr.title == "Fed holds rates steady at 5.5%"
        assert nr.impact_score == 0.8
        assert nr.sentiment == "neutral"
        assert "EURUSD" in nr.affected_assets

    def test_deterministic_id(self):
        nr1 = NewsReference("News Title", "Source", ts(2024, 6, 1, 14, 0))
        nr2 = NewsReference("News Title", "Source", ts(2024, 6, 1, 14, 0))
        assert nr1.id == nr2.id

    def test_serialization_round_trip(self):
        nr = NewsReference(
            "CPI data release",
            "Bloomberg",
            ts(2024, 6, 1, 12, 0),
            impact_score=0.7,
            sentiment="positive",
            category="Economic",
            summary="CPI beat expectations",
        )
        d = nr.to_dict()
        nr2 = NewsReference.from_dict(d)
        assert nr2.id == nr.id
        assert nr2.title == "CPI data release"
        assert nr2.impact_score == 0.7


# ===========================================================================
# Market Outcome Tests
# ===========================================================================


class TestMarketOutcome:
    def test_create(self):
        mo = MarketOutcome(
            event_id="event_123",
            event_type="BOS",
            asset="EURUSD",
            timestamp=ts(2024, 6, 1, 16, 0),
            outcome_type="Success",
            actual_move=0.0050,
            expected_move=0.0030,
            confidence=0.75,
        )
        assert mo.event_id == "event_123"
        assert mo.outcome_type == "Success"
        assert mo.actual_move == 0.0050

    def test_deterministic_id(self):
        mo1 = MarketOutcome("e1", "BOS", "EURUSD", ts(2024, 6, 1, 16, 0))
        mo2 = MarketOutcome("e1", "BOS", "EURUSD", ts(2024, 6, 1, 16, 0))
        assert mo1.id == mo2.id

    def test_serialization_round_trip(self):
        mo = MarketOutcome(
            "e1",
            "BOS",
            "EURUSD",
            ts(2024, 6, 1, 16, 0),
            outcome_type="Failure",
            actual_move=-0.0020,
            max_adverse=0.0030,
            duration_minutes=120,
        )
        d = mo.to_dict()
        mo2 = MarketOutcome.from_dict(d)
        assert mo2.id == mo.id
        assert mo2.outcome_type == "Failure"
        assert mo2.duration_minutes == 120


# ===========================================================================
# MarketMemoryEngine Tests
# ===========================================================================


class TestMarketMemoryEngine:
    def setup_method(self):
        self.repo = MemoryRepository()
        self.engine = MarketMemoryEngine(self.repo)

    def test_record_structure_break(self):
        ms = self.engine.record_structure_break(
            "BOS",
            "EURUSD",
            "H1",
            ts(2024, 6, 1, 8, 0),
            direction="bullish",
            price_level=1.1050,
        )
        assert isinstance(ms, MarketStructure)
        assert ms.asset == "EURUSD"
        loaded = self.repo.get(ms.id)
        assert loaded is not None
        assert loaded.structure_type == "BOS"

    def test_confirm_structure_break(self):
        ms = self.engine.record_structure_break("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0))
        confirmed = self.engine.confirm_structure_break(ms.id, 1.1080)
        assert confirmed.confirmed is True
        assert confirmed.confirmation_price == 1.1080

    def test_confirm_nonexistent_raises(self):
        with pytest.raises(ValueError, match="MarketStructure not found"):
            self.engine.confirm_structure_break("nonexistent", 1.10)

    def test_record_liquidity_event(self):
        le = self.engine.record_liquidity_event(
            "Sweep",
            "EURUSD",
            "M15",
            ts(2024, 6, 1, 9, 30),
            direction="bearish",
            price_level=1.1020,
            swept_levels=[1.1030, 1.1040],
        )
        assert isinstance(le, LiquidityEvent)
        assert le.swept_levels == [1.1030, 1.1040]

    def test_resolve_liquidity_event(self):
        le = self.engine.record_liquidity_event("Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30))
        resolved = self.engine.resolve_liquidity_event(le.id, "Hit")
        assert resolved.outcome == "Hit"

    def test_record_session(self):
        ms = self.engine.record_session(
            "London",
            "EURUSD",
            "2024-06-01",
            ts(2024, 6, 1, 7, 0),
            ts(2024, 6, 1, 16, 0),
            open=1.1000,
            high=1.1080,
            low=1.0980,
            close=1.1060,
            direction="bullish",
            volume_ratio=1.2,
        )
        assert isinstance(ms, MarketSession)
        assert ms.range == pytest.approx(0.0100, rel=1e-9)

    def test_record_volatility_state(self):
        vs = self.engine.record_volatility_state(
            "EURUSD",
            "H1",
            ts(2024, 6, 1, 12, 0),
            atr_value=0.0015,
            atr_percentile=0.85,
            volatility_regime="High",
            expanding=True,
        )
        assert isinstance(vs, VolatilityState)
        assert vs.volatility_regime == "High"

    def test_record_news(self):
        nr = self.engine.record_news(
            "Fed holds rates steady",
            "Reuters",
            ts(2024, 6, 1, 14, 0),
            impact_score=0.8,
            sentiment="neutral",
            affected_assets=["EURUSD"],
            category="CentralBank",
        )
        assert isinstance(nr, NewsReference)
        assert nr.impact_score == 0.8

    def test_record_outcome(self):
        mo = self.engine.record_outcome(
            "event_123",
            "BOS",
            "EURUSD",
            ts(2024, 6, 1, 16, 0),
            outcome_type="Success",
            actual_move=0.0050,
        )
        assert isinstance(mo, MarketOutcome)
        assert mo.outcome_type == "Success"


# ===========================================================================
# Query Method Tests
# ===========================================================================


class TestMarketMemoryEngineQueries:
    def setup_method(self):
        self.repo = MemoryRepository()
        self.engine = MarketMemoryEngine(self.repo)
        # Seed with test data
        self.engine.record_structure_break(
            "BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050
        )
        self.engine.record_structure_break(
            "CHOCH", "EURUSD", "H1", ts(2024, 6, 1, 12, 0), price_level=1.1080
        )
        self.engine.record_liquidity_event(
            "Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30), price_level=1.1020
        )
        self.engine.record_session(
            "London", "EURUSD", "2024-06-01", ts(2024, 6, 1, 7, 0), ts(2024, 6, 1, 16, 0)
        )
        self.engine.record_session(
            "NewYork", "EURUSD", "2024-06-01", ts(2024, 6, 1, 13, 0), ts(2024, 6, 1, 22, 0)
        )
        self.engine.record_volatility_state("EURUSD", "H1", ts(2024, 6, 1, 12, 0), atr_value=0.0015)
        self.engine.record_structure_break(
            "BOS", "GBPUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.2700
        )

    def test_get_events_by_asset(self):
        eurusd_events = self.engine.get_events_by_asset("EURUSD")
        assert len(eurusd_events) == 6  # 2 structures + 1 liquidity + 2 sessions + 1 volatility

    def test_get_events_by_asset_filtered(self):
        structures = self.engine.get_events_by_asset("EURUSD", "MarketStructure")
        assert len(structures) == 2

    def test_get_events_in_range(self):
        events = self.engine.get_events_in_range(
            "EURUSD",
            ts(2024, 6, 1, 7, 0),
            ts(2024, 6, 1, 13, 0),
        )
        assert len(events) > 0

    def test_get_events_in_range_excludes_outside(self):
        events = self.engine.get_events_in_range(
            "EURUSD",
            ts(2024, 6, 1, 7, 0),
            ts(2024, 6, 1, 7, 30),
        )
        for e in events:
            assert ts(2024, 6, 1, 7, 0) <= e.timestamp <= ts(2024, 6, 1, 7, 30)

    def test_get_recent_events(self):
        recent = self.engine.get_recent_events("EURUSD", limit=3)
        assert len(recent) <= 3

    def test_get_structures(self):
        bos_list = self.engine.get_structures("EURUSD", structure_type="BOS")
        assert len(bos_list) == 1
        assert bos_list[0].structure_type == "BOS"

    def test_get_liquidity_events(self):
        events = self.engine.get_liquidity_events("EURUSD")
        assert len(events) == 1

    def test_get_sessions(self):
        sessions = self.engine.get_sessions("EURUSD")
        assert len(sessions) == 2

    def test_get_sessions_filtered(self):
        london = self.engine.get_sessions("EURUSD", session_name="London")
        assert len(london) == 1
        assert london[0].session_name == "London"

    def test_get_volatility_history(self):
        history = self.engine.get_volatility_history("EURUSD", "H1")
        assert len(history) == 1

    def test_count_by_type(self):
        assert self.engine.count_by_type("MarketStructure") == 3
        assert self.engine.count_by_type("LiquidityEvent") == 1
        assert self.engine.count_by_type("MarketSession") == 2
        assert self.engine.count_by_type("VolatilityState") == 1
        assert self.engine.count_by_type("UnknownType") == 0

    def test_get_outcomes_for_event(self):
        self.engine.record_outcome("e1", "BOS", "EURUSD", ts(2024, 6, 1, 16, 0))
        outcomes = self.engine.get_outcomes_for_event("e1")
        assert len(outcomes) == 1


# ===========================================================================
# OBJECT_REGISTRY Integration Tests
# ===========================================================================


class TestObjectRegistryIntegration:
    def test_all_types_in_registry(self):
        from researchos.storage.repository import OBJECT_REGISTRY

        expected = {
            "MarketStructure",
            "LiquidityEvent",
            "MarketSession",
            "VolatilityState",
            "NewsReference",
            "MarketOutcome",
        }
        for name in expected:
            assert name in OBJECT_REGISTRY, f"{name} missing from OBJECT_REGISTRY"

    def test_load_from_sqlite_round_trip(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        db_path = str(tmp_path / "test_market_memory.db")
        repo = ResearchRepository(db_path)
        try:
            ms = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
            repo.save(ms)
            loaded = repo.load_object(ms.id)
            assert loaded is not None
            assert type(loaded).__name__ == "MarketStructure"
            assert loaded.structure_type == "BOS"
            assert loaded.price_level == 1.1050
        finally:
            if hasattr(repo, "_conn") and repo._conn:
                repo._conn.close()

    def test_hash_preserved_through_sqlite(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        db_path = str(tmp_path / "test_hash_preserved.db")
        repo = ResearchRepository(db_path)
        try:
            ms = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), price_level=1.1050)
            h1 = ms.hash
            repo.save(ms)
            loaded = repo.load_object(ms.id)
            assert loaded.hash == h1
        finally:
            if hasattr(repo, "_conn") and repo._conn:
                repo._conn.close()

    def test_load_by_type_sqlite(self, tmp_path):
        from researchos.storage.repository import ResearchRepository

        db_path = str(tmp_path / "test_load_by_type.db")
        repo = ResearchRepository(db_path)
        try:
            for i in range(3):
                ms = MarketStructure(
                    "BOS", "EURUSD", "H1", ts(2024, 6, i + 1, 8, 0), price_level=1.10 + i * 0.01
                )
                repo.save(ms)
            loaded = repo.load_objects_by_type("MarketStructure")
            assert len(loaded) == 3
        finally:
            if hasattr(repo, "_conn") and repo._conn:
                repo._conn.close()


# ===========================================================================
# Edge Case Tests
# ===========================================================================


class TestEdgeCases:
    def test_market_structure_empty_lists(self):
        ms = MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0))
        assert ms.ontology_tags == []

    def test_liquidity_event_empty_swept(self):
        le = LiquidityEvent("Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30))
        assert le.swept_levels == []

    def test_session_zero_values(self):
        ms = MarketSession(
            "London", "EURUSD", "2024-06-01", ts(2024, 6, 1, 7, 0), ts(2024, 6, 1, 16, 0)
        )
        assert ms.open == 0.0
        assert ms.range == 0.0

    def test_news_empty_assets(self):
        nr = NewsReference("Title", "Source", ts(2024, 6, 1, 14, 0))
        assert nr.affected_assets == []

    def test_outcome_pending_default(self):
        mo = MarketOutcome("e1", "BOS", "EURUSD", ts(2024, 6, 1, 16, 0))
        assert mo.outcome_type == "Pending"

    def test_metadata_preserved_round_trip(self):
        me = MarketEvent(
            "Custom", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), metadata={"key1": "value1", "key2": 42}
        )
        d = me.to_dict()
        me2 = MarketEvent.from_dict(d)
        assert me2.metadata["key1"] == "value1"
        assert me2.metadata["key2"] == 42

    def test_all_objects_have_to_hashable_dict(self):
        objects = [
            MarketStructure("BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0)),
            LiquidityEvent("Sweep", "EURUSD", "M15", ts(2024, 6, 1, 9, 30)),
            MarketSession(
                "London", "EURUSD", "2024-06-01", ts(2024, 6, 1, 7, 0), ts(2024, 6, 1, 16, 0)
            ),
            VolatilityState("EURUSD", "H1", ts(2024, 6, 1, 12, 0)),
            NewsReference("Title", "Source", ts(2024, 6, 1, 14, 0)),
            MarketOutcome("e1", "BOS", "EURUSD", ts(2024, 6, 1, 16, 0)),
        ]
        for obj in objects:
            h = obj._to_hashable_dict()
            assert isinstance(h, dict)
            assert "ontology_tags" in h

    def test_all_objects_support_find_by_tag(self):
        repo = MemoryRepository()
        ms = MarketStructure(
            "BOS", "EURUSD", "H1", ts(2024, 6, 1, 8, 0), ontology_tags=["trend", "momentum"]
        )
        repo.save(ms)
        found = repo.find_by_tag("trend")
        assert len(found) == 1
        assert found[0].id == ms.id
