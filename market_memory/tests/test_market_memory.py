"""
Comprehensive tests for the Market Memory module.

Covers:
    - Serialization round-trip for all 4 model types
    - Hash stability and determinism
    - Persistence (save/load) through repository
    - Query retrieval (by asset, date range, tag)
    - Deterministic comparison / similarity
    - Feature computation
    - MacroMarketEvent creation
"""

from __future__ import annotations

from datetime import datetime, timezone

from researchos.core.lifecycle import LifecycleStage
from researchos.market_memory.events import MacroMarketEvent
from researchos.market_memory.features import compute_features
from researchos.market_memory.models import (
    HistoricalScenario,
    MacroContextSnapshot,
    MarketRegime,
    MarketSnapshot,
)
from researchos.market_memory.repository import MarketMemoryRepository
from researchos.market_memory.similarity import (
    compare_snapshots,
    find_similar_snapshots,
)

# =============================================================================
# Helpers
# =============================================================================


def make_snapshot(
    asset: str = "XAUUSD",
    close: float = 2000.0,
    timeframe: str = "1h",
    volatility: float = 0.5,
    open_val: float = 1990.0,
    high_val: float = 2010.0,
    low_val: float = 1988.0,
) -> MarketSnapshot:
    return MarketSnapshot(
        asset=asset,
        timestamp=datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc),
        timeframe=timeframe,
        open=open_val,
        high=high_val,
        low=low_val,
        close=close,
        volume=15000.0,
        volatility=volatility,
        trend_state="Bullish",
        market_regime="Trending",
        indicators={"rsi": 65.0, "atr": 15.0},
        confidence=0.85,
    )


# =============================================================================
# Serialization Tests
# =============================================================================


class TestMarketSnapshotSerialization:
    """Test MarketSnapshot to_dict / from_dict round-trip."""

    def test_round_trip(self):
        s = make_snapshot()
        d = s.to_dict()
        s2 = MarketSnapshot.from_dict(d)
        assert s.id == s2.id
        assert s.hash == s2.hash
        assert s.asset == s2.asset
        assert s.close == s2.close
        assert s.timeframe == s2.timeframe
        assert s.indicators == s2.indicators
        assert s.volatility == s2.volatility
        assert d["object_type"] == "MarketSnapshot"

    def test_hash_stability(self):
        s1 = make_snapshot()
        s2 = make_snapshot()
        assert s1.hash == s2.hash
        assert s1.id == s2.id

    def test_different_inputs_different_hash(self):
        s1 = make_snapshot(close=2000.0)
        s2 = make_snapshot(close=2010.0)
        assert s1.hash != s2.hash
        assert s1.id != s2.id

    def test_lifecycle_preserved(self):
        s = make_snapshot()
        s.lifecycle.transition(LifecycleStage.ACTIVE, "Test")
        d = s.to_dict()
        s2 = MarketSnapshot.from_dict(d)
        assert s2.lifecycle.current_stage == LifecycleStage.ACTIVE
        assert len(s2.lifecycle.transitions) == 2

    def test_empty_indicators(self):
        s = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        d = s.to_dict()
        s2 = MarketSnapshot.from_dict(d)
        assert s2.indicators == {}


class TestMarketRegimeSerialization:
    """Test MarketRegime to_dict / from_dict round-trip."""

    def test_round_trip(self):
        r = MarketRegime(
            regime="Trending",
            asset="XAUUSD",
            timestamp=datetime(2025, 1, 15, tzinfo=timezone.utc),
            confidence=0.85,
            snapshot_ids=["snap_001", "snap_002"],
            volatility_level=15.0,
            trend_strength=0.7,
            duration_bars=120,
            notes="Strong uptrend on H1",
        )
        d = r.to_dict()
        r2 = MarketRegime.from_dict(d)
        assert r.id == r2.id
        assert r.hash == r2.hash
        assert r.regime == r2.regime
        assert r.trend_strength == r2.trend_strength
        assert d["object_type"] == "MarketRegime"

    def test_deterministic_id(self):
        r1 = MarketRegime("Ranging", "XAUUSD", datetime(2025, 1, 1, tzinfo=timezone.utc))
        r2 = MarketRegime("Ranging", "XAUUSD", datetime(2025, 1, 1, tzinfo=timezone.utc))
        assert r1.id == r2.id


class TestMacroStateSerialization:
    """Test MacroContextSnapshot to_dict / from_dict round-trip."""

    def test_round_trip(self):
        m = MacroContextSnapshot(
            timestamp=datetime(2025, 1, 15, tzinfo=timezone.utc),
            geography="US",
            dxy=103.5,
            real_yield=1.8,
            cpi=3.2,
            fed_event="Held rates steady",
            nfp=250000,
            geopolitical_events=["Middle East tensions"],
            overall_assessment="Neutral",
            confidence=0.75,
        )
        d = m.to_dict()
        m2 = MacroContextSnapshot.from_dict(d)
        assert m.id == m2.id
        assert m.hash == m2.hash
        assert m.dxy == m2.dxy
        assert m.cpi == m2.cpi
        assert m.geopolitical_events == m2.geopolitical_events
        assert d["object_type"] == "MacroState"

    def test_deterministic_id(self):
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        m1 = MacroContextSnapshot(ts, "US", dxy=100.0, cpi=3.0)
        m2 = MacroContextSnapshot(ts, "US", dxy=100.0, cpi=3.0)
        assert m1.id == m2.id


class TestHistoricalScenarioSerialization:
    """Test HistoricalScenario to_dict / from_dict round-trip."""

    def test_round_trip(self):
        sc = HistoricalScenario(
            name="Jan 2025 Rally",
            description="XAUUSD rally after Fed hold",
            snapshot_ids=["snap_001"],
            regime_id="reg_001",
            macro_id="macro_001",
            outcome="Price increased 3% over 2 weeks",
            price_outcome=3.0,
            tags=["rally", "fed", "gold"],
            similarity_score=0.0,
        )
        d = sc.to_dict()
        sc2 = HistoricalScenario.from_dict(d)
        assert sc.id == sc2.id
        assert sc.hash == sc2.hash
        assert sc.name == sc2.name
        assert sc.price_outcome == sc2.price_outcome
        assert d["object_type"] == "HistoricalScenario"

    def test_deterministic_id(self):
        sc1 = HistoricalScenario("Test Scenario")
        sc2 = HistoricalScenario("Test Scenario")
        assert sc1.id == sc2.id


# =============================================================================
# Repository / Persistence Tests
# =============================================================================


class TestMarketMemoryRepository:
    """Test the MarketMemoryRepository for persistence and queries."""

    def setup_method(self):
        self.repo = MarketMemoryRepository()

    def test_save_and_get_snapshot(self):
        s = make_snapshot()
        saved = self.repo.save_snapshot(s)
        assert saved.id == s.id
        loaded = self.repo.get_snapshot(s.id)
        assert loaded is not None
        assert loaded.hash == s.hash

    def test_get_snapshots_by_asset(self):
        s1 = make_snapshot(close=2000.0)
        s2 = make_snapshot(asset="EURUSD", close=1.05)
        self.repo.save_snapshot(s1)
        self.repo.save_snapshot(s2)
        results = self.repo.get_snapshots_by_asset("XAUUSD")
        assert len(results) == 1
        assert results[0].asset == "XAUUSD"

    def test_get_snapshots_in_range(self):
        s1 = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2025, 1, 10, tzinfo=timezone.utc),
        )
        s2 = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2025, 1, 20, tzinfo=timezone.utc),
        )
        s3 = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2025, 2, 1, tzinfo=timezone.utc),
        )
        self.repo.save_snapshot(s1)
        self.repo.save_snapshot(s2)
        self.repo.save_snapshot(s3)
        results = self.repo.get_snapshots_in_range(
            "XAUUSD",
            datetime(2025, 1, 5, tzinfo=timezone.utc),
            datetime(2025, 1, 25, tzinfo=timezone.utc),
        )
        assert len(results) == 2

    def test_save_and_get_regime(self):
        r = MarketRegime(
            "Trending",
            "XAUUSD",
            datetime(2025, 1, 15, tzinfo=timezone.utc),
        )
        self.repo.save_regime(r)
        loaded = self.repo.get_regime(r.id)
        assert loaded is not None
        assert loaded.regime == "Trending"

    def test_get_regimes_by_asset(self):
        r1 = MarketRegime("Trending", "XAUUSD", datetime(2025, 1, 1, tzinfo=timezone.utc))
        r2 = MarketRegime("Ranging", "XAUUSD", datetime(2025, 2, 1, tzinfo=timezone.utc))
        r3 = MarketRegime("Trending", "EURUSD", datetime(2025, 1, 1, tzinfo=timezone.utc))
        self.repo.save_regime(r1)
        self.repo.save_regime(r2)
        self.repo.save_regime(r3)
        results = self.repo.get_regimes_by_asset("XAUUSD")
        assert len(results) == 2

    def test_save_and_get_macro_state(self):
        m = MacroContextSnapshot(
            datetime(2025, 1, 15, tzinfo=timezone.utc),
        )
        self.repo.save_macro_state(m)
        loaded = self.repo.get_macro_state(m.id)
        assert loaded is not None

    def test_get_macro_states_in_range(self):
        m1 = MacroContextSnapshot(datetime(2025, 1, 10, tzinfo=timezone.utc))
        m2 = MacroContextSnapshot(datetime(2025, 1, 20, tzinfo=timezone.utc))
        m3 = MacroContextSnapshot(datetime(2025, 2, 1, tzinfo=timezone.utc))
        self.repo.save_macro_state(m1)
        self.repo.save_macro_state(m2)
        self.repo.save_macro_state(m3)
        results = self.repo.get_macro_states_in_range(
            "US",
            datetime(2025, 1, 5, tzinfo=timezone.utc),
            datetime(2025, 1, 25, tzinfo=timezone.utc),
        )
        assert len(results) == 2

    def test_save_and_get_scenario(self):
        sc = HistoricalScenario("Test Scenario")
        self.repo.save_scenario(sc)
        loaded = self.repo.get_scenario(sc.id)
        assert loaded is not None
        assert loaded.name == "Test Scenario"

    def test_find_scenarios_by_tag(self):
        sc1 = HistoricalScenario("S1", tags=["rally", "gold"], ontology_tags=["gold"])
        sc2 = HistoricalScenario("S2", tags=["crash", "silver"], ontology_tags=["silver"])
        self.repo.save_scenario(sc1)
        self.repo.save_scenario(sc2)
        results = self.repo.find_scenarios_by_tag("gold")
        assert len(results) == 1
        assert results[0].name == "S1"

    def test_find_scenarios_by_outcome(self):
        sc1 = HistoricalScenario("S1", outcome="Price increased 5%")
        sc2 = HistoricalScenario("S2", outcome="Price dropped 3%")
        self.repo.save_scenario(sc1)
        self.repo.save_scenario(sc2)
        results = self.repo.find_scenarios_by_outcome("increased")
        assert len(results) == 1

    def test_count_all(self):
        self.repo.save_snapshot(make_snapshot())
        self.repo.save_regime(
            MarketRegime("T", "XAUUSD", datetime(2025, 1, 1, tzinfo=timezone.utc))
        )
        self.repo.save_macro_state(MacroContextSnapshot(datetime(2025, 1, 1, tzinfo=timezone.utc)))
        self.repo.save_scenario(HistoricalScenario("Test"))
        counts = self.repo.count_all()
        assert counts["snapshots"] == 1
        assert counts["regimes"] == 1
        assert counts["macro_states"] == 1
        assert counts["scenarios"] == 1

    def test_clear(self):
        self.repo.save_snapshot(make_snapshot())
        self.repo.clear()
        assert self.repo.count_all()["snapshots"] == 0


# =============================================================================
# Feature Computation Tests
# =============================================================================


class TestFeatureComputation:
    """Test the compute_features function."""

    def test_bullish_candle(self):
        s = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
        )
        f = compute_features(s)
        assert f.is_bullish is True
        assert f.is_bearish is False
        assert f.body == 4.0
        assert f.upper_wick == 1.0
        assert f.lower_wick == 1.0
        assert f.range_pct > 0
        assert f.body_pct > 0

    def test_bearish_candle(self):
        s = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            open=104.0,
            high=105.0,
            low=99.0,
            close=100.0,
        )
        f = compute_features(s)
        assert f.is_bullish is False
        assert f.is_bearish is True
        assert f.body == 4.0

    def test_doji_candle(self):
        s = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
            open=100.0,
            high=105.0,
            low=95.0,
            close=100.0,
        )
        f = compute_features(s)
        assert f.is_bullish is False
        assert f.body_pct < 0.5

    def test_feature_set_to_dict(self):
        s = make_snapshot()
        f = compute_features(s)
        d = f.to_dict()
        assert d["asset"] == "XAUUSD"
        assert d["is_bullish"] is True
        assert d["timeframe"] == "1h"


# =============================================================================
# Similarity / Comparison Tests
# =============================================================================


class TestSimilarity:
    """Test the similarity comparison functions."""

    def test_identical_snapshots(self):
        s1 = make_snapshot()
        s2 = make_snapshot()
        score = compare_snapshots(s1, s2)
        assert score == 1.0

    def test_different_snapshots(self):
        s1 = make_snapshot(
            close=2000.0, volatility=0.5, open_val=1990.0, high_val=2010.0, low_val=1988.0
        )
        s2 = make_snapshot(
            close=1950.0, volatility=2.0, open_val=1960.0, high_val=1970.0, low_val=1940.0
        )
        score = compare_snapshots(s1, s2)
        assert 0.0 <= score <= 1.0
        assert score < 1.0

    def test_opposite_trends(self):
        bullish = make_snapshot(close=2000.0, open_val=1990.0)
        bearish = MarketSnapshot(
            asset="XAUUSD",
            timestamp=bullish.timestamp,
            timeframe="1h",
            open=2010.0,
            high=2020.0,
            low=1995.0,
            close=2000.0,
            volatility=0.5,
        )
        score = compare_snapshots(bullish, bearish)
        assert score < 1.0

    def test_find_similar_snapshots(self):
        target = make_snapshot(close=2000.0)
        candidates = [
            make_snapshot(close=2000.0),
            make_snapshot(close=2005.0),
            make_snapshot(close=1950.0),
            make_snapshot(close=2100.0),
        ]
        results = find_similar_snapshots(target, candidates, top_n=2)
        assert len(results) == 2
        assert results[0][1] >= results[1][1]

    def test_symmetry(self):
        s1 = make_snapshot(close=2000.0, volatility=0.5)
        s2 = make_snapshot(close=2010.0, volatility=0.8)
        score1 = compare_snapshots(s1, s2)
        score2 = compare_snapshots(s2, s1)
        assert abs(score1 - score2) < 0.001

    def test_bounds(self):
        s1 = make_snapshot()
        s2 = make_snapshot()
        score = compare_snapshots(s1, s2)
        assert 0.0 <= score <= 1.0


# =============================================================================
# MacroMarketEvent Tests
# =============================================================================


class TestMarketEvent:
    """Test the MacroMarketEvent object."""

    def test_create_fed_event(self):
        e = MacroMarketEvent(
            event_type="Fed",
            timestamp=datetime(2025, 1, 29, tzinfo=timezone.utc),
            asset="XAUUSD",
            description="FOMC rate decision",
            impact="High",
            expected_value=5.5,
            actual_value=5.5,
        )
        assert e.event_type == "Fed"
        assert e.impact == "High"
        assert e.expected_value == 5.5

    def test_deterministic_id(self):
        ts = datetime(2025, 1, 1, tzinfo=timezone.utc)
        e1 = MacroMarketEvent("CPI", ts, description="CPI data")
        e2 = MacroMarketEvent("CPI", ts, description="CPI data")
        assert e1.id == e2.id

    def test_round_trip(self):
        e = MacroMarketEvent(
            event_type="NFP",
            timestamp=datetime(2025, 2, 7, tzinfo=timezone.utc),
            description="Employment report",
            actual_value=200000.0,
            expected_value=185000.0,
        )
        d = e.to_dict()
        e2 = MacroMarketEvent.from_dict(d)
        assert e.id == e2.id
        assert e.actual_value == e2.actual_value
        assert d["object_type"] == "MarketEvent"

    def test_hash_stability(self):
        e1 = MacroMarketEvent("Fed", datetime(2025, 1, 1, tzinfo=timezone.utc))
        e2 = MacroMarketEvent("Fed", datetime(2025, 1, 1, tzinfo=timezone.utc))
        assert e1.hash == e2.hash


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_workflow(self):
        repo = MarketMemoryRepository()

        # 1. Create a snapshot
        snap = make_snapshot()
        repo.save_snapshot(snap)

        # 2. Create a regime
        regime = MarketRegime(
            "Trending",
            "XAUUSD",
            snap.timestamp,
            confidence=0.85,
            snapshot_ids=[snap.id],
        )
        repo.save_regime(regime)

        # 3. Create a macro state
        macro = MacroContextSnapshot(
            snap.timestamp,
            dxy=103.0,
            cpi=3.2,
        )
        repo.save_macro_state(macro)

        # 4. Create a scenario
        scenario = HistoricalScenario(
            name="Jan 2025 Scenario",
            snapshot_ids=[snap.id],
            regime_id=regime.id,
            macro_id=macro.id,
            outcome="Bullish continuation",
            tags=["trending", "gold"],
        )
        repo.save_scenario(scenario)

        # 5. Query back
        loaded_snap = repo.get_snapshot(snap.id)
        loaded_regime = repo.get_regime(regime.id)
        loaded_macro = repo.get_macro_state(macro.id)
        loaded_scenario = repo.get_scenario(scenario.id)

        assert loaded_snap is not None
        assert loaded_regime is not None
        assert loaded_macro is not None
        assert loaded_scenario is not None

        # 6. Verify determinism
        assert loaded_snap.hash == snap.hash
        assert loaded_regime.hash == regime.hash

        # 7. Verify counts
        counts = repo.count_all()
        assert counts["snapshots"] == 1
        assert counts["regimes"] == 1
        assert counts["macro_states"] == 1
        assert counts["scenarios"] == 1
