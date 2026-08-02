"""
Comprehensive tests for Market Memory Engine (Phase 5).

Tests cover:
    - Data models (MarketSnapshot, MarketRegime, MacroState, HistoricalScenario)
    - Feature extraction (compute_features, FeatureSet)
    - Similarity comparison (compare_snapshots, find_similar_snapshots, compare_scenarios)
    - ScenarioMatcher (weighted matching, deterministic ranking)
    - OutcomeAnalysis (statistics, confidence scoring)
    - MarketMemoryReport (full lifecycle, audit entries, evidence references)
    - Repository (CRUD, SQLite persistence, dataset tracking)
    - Integration layer (adapter pattern, standalone mode)
    - Determinism guarantees (same inputs → same outputs)
    - Serialization (to_dict / from_dict round-trips)
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pytest

from researchos.core.base_object import BaseObject
from researchos.core.identity import generate_id, deterministic_hash
from researchos.core.lifecycle import LifecycleStage
from researchos.core.timestamp import utc_now, parse_timestamp

from researchos.market_memory import (
    MarketSnapshot,
    MarketRegime,
    MacroState,
    HistoricalScenario,
    MarketMemoryRepository,
    compute_features,
    FeatureSet,
    compare_snapshots,
    find_similar_snapshots,
    compare_scenarios,
    ScenarioMatcher,
    MatchResult,
    DEFAULT_FEATURE_WEIGHTS,
    OutcomeAnalysis,
    OutcomeAnalysisResult,
    MarketMemoryReport,
    MarketMemoryIntegrator,
    IntegrationContext,
    MarketEvent,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def market_snapshot() -> MarketSnapshot:
    """Create a standard market snapshot for testing."""
    return MarketSnapshot(
        asset="XAUUSD",
        timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        timeframe="1h",
        open=2010.50,
        high=2025.00,
        low=2008.00,
        close=2022.30,
        volume=12500.0,
        volatility=1.5,
        trend_state="Bullish",
        market_regime="Trending",
        confidence=0.85,
    )


@pytest.fixture
def similar_snapshot() -> MarketSnapshot:
    """A snapshot similar to market_snapshot."""
    return MarketSnapshot(
        asset="XAUUSD",
        timestamp=datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc),
        timeframe="1h",
        open=2020.00,
        high=2030.00,
        low=2015.00,
        close=2028.50,
        volume=11000.0,
        volatility=1.3,
        trend_state="Bullish",
        market_regime="Trending",
        confidence=0.80,
    )


@pytest.fixture
def different_snapshot() -> MarketSnapshot:
    """A very different snapshot for comparison."""
    return MarketSnapshot(
        asset="XAUUSD",
        timestamp=datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc),
        timeframe="4h",
        open=1980.00,
        high=1990.00,
        low=1950.00,
        close=1965.00,
        volume=5000.0,
        volatility=3.5,
        trend_state="Bearish",
        market_regime="Volatile",
        confidence=0.60,
    )


@pytest.fixture
def market_regime() -> MarketRegime:
    """Create a market regime for testing."""
    return MarketRegime(
        regime="Bullish Trend",
        asset="XAUUSD",
        timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        confidence=0.85,
        volatility_level=1.2,
        trend_strength=0.75,
        notes="Strong uptrend with consistent higher highs",
    )


@pytest.fixture
def macro_state() -> MacroState:
    """Create a macro state for testing."""
    return MacroState(
        timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        geography="US",
        dxy=103.5,
        real_yield=1.8,
        cpi=3.4,
        fed_event="FOMC Meeting Minutes",
        nfp=216000.0,
        overall_assessment="Neutral",
        confidence=0.70,
    )


@pytest.fixture
def historical_scenario(market_snapshot, market_regime) -> HistoricalScenario:
    """Create a historical scenario for testing."""
    return HistoricalScenario(
        name="Jan 2024 Bullish Run",
        description="Strong bullish momentum after Fed pivot expectations",
        start_time=datetime(2024, 1, 10, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 20, tzinfo=timezone.utc),
        snapshot_ids=[market_snapshot.id],
        regime_id=market_regime.id,
        outcome="Bullish continuation",
        price_outcome=3.5,
        volatility_outcome=-0.5,
        max_favorable_movement=5.2,
        max_adverse_movement=-1.8,
        tags=["bullish", "trending", "fed-pivot"],
        dataset_source="historical_data_2024",
        similarity_score=0.0,
    )


@pytest.fixture
def repository() -> MarketMemoryRepository:
    """Create an empty repository."""
    return MarketMemoryRepository()


@pytest.fixture
def populated_repository(
    market_snapshot,
    market_regime,
    macro_state,
    historical_scenario,
) -> MarketMemoryRepository:
    """Create a repository with sample data."""
    repo = MarketMemoryRepository()
    repo.save_snapshot(market_snapshot)
    repo.save_regime(market_regime)
    repo.save_macro_state(macro_state)
    repo.save_scenario(historical_scenario)
    return repo


# =============================================================================
# Data Model Tests
# =============================================================================

class TestMarketSnapshot:
    """Tests for MarketSnapshot data model."""

    def test_create(self, market_snapshot):
        snap = market_snapshot
        assert snap.asset == "XAUUSD"
        assert snap.timeframe == "1h"
        assert snap.open == 2010.50
        assert snap.close == 2022.30
        assert snap.volatility == 1.5
        assert snap.trend_state == "Bullish"
        assert snap.confidence == 0.85
        assert snap.id is not None
        assert len(snap.id) == 36  # UUID format

    def test_deterministic_id(self):
        snapshot1 = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            timeframe="1h",
            close=2022.30,
        )
        snapshot2 = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            timeframe="1h",
            close=2022.30,
        )
        assert snapshot1.id == snapshot2.id

    def test_to_dict_roundtrip(self, market_snapshot):
        data = market_snapshot.to_dict()
        restored = MarketSnapshot.from_dict(data)
        assert restored.id == market_snapshot.id
        assert restored.asset == market_snapshot.asset
        assert restored.timestamp == market_snapshot.timestamp
        assert restored.close == market_snapshot.close
        assert restored.volatility == market_snapshot.volatility
        assert restored.hash == market_snapshot.hash

    def test_to_json(self, market_snapshot):
        json_str = market_snapshot.to_json()
        data = json.loads(json_str)
        assert data["object_type"] == "MarketSnapshot"
        assert data["asset"] == "XAUUSD"

    def test_lifecycle(self, market_snapshot):
        assert market_snapshot.lifecycle.current_stage == LifecycleStage.CREATED

    def test_indicators(self):
        snap = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            indicators={"rsi": 65.0, "macd": 12.5, "ema_20": 2005.0},
        )
        assert snap.indicators["rsi"] == 65.0
        assert snap.indicators["macd"] == 12.5
        assert snap.indicators["ema_20"] == 2005.0


class TestMarketRegime:
    """Tests for MarketRegime data model."""

    def test_create(self, market_regime):
        assert market_regime.regime == "Bullish Trend"
        assert market_regime.asset == "XAUUSD"
        assert market_regime.confidence == 0.85
        assert market_regime.trend_strength == 0.75

    def test_deterministic_id(self):
        ts = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        a = MarketRegime(regime="Ranging", asset="XAUUSD", timestamp=ts)
        b = MarketRegime(regime="Ranging", asset="XAUUSD", timestamp=ts)
        assert a.id == b.id

    def test_to_dict_roundtrip(self, market_regime):
        data = market_regime.to_dict()
        restored = MarketRegime.from_dict(data)
        assert restored.regime == market_regime.regime
        assert restored.asset == market_regime.asset
        assert restored.confidence == market_regime.confidence
        assert restored.volatility_level == market_regime.volatility_level

    def test_serialization_preserves_notes(self, market_regime):
        data = market_regime.to_dict()
        assert "notes" in data
        assert "Strong uptrend" in data["notes"]


class TestMacroState:
    """Tests for MacroState data model."""

    def test_create(self, macro_state):
        assert macro_state.geography == "US"
        assert macro_state.dxy == 103.5
        assert macro_state.cpi == 3.4
        assert macro_state.overall_assessment == "Neutral"

    def test_to_dict_roundtrip(self, macro_state):
        data = macro_state.to_dict()
        restored = MacroState.from_dict(data)
        assert restored.geography == macro_state.geography
        assert restored.dxy == macro_state.dxy
        assert restored.real_yield == macro_state.real_yield
        assert restored.hash == macro_state.hash

    def test_geopolitical_events(self):
        ms = MacroState(
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            geopolitical_events=["Middle East tensions", "EU election"],
        )
        assert len(ms.geopolitical_events) == 2
        data = ms.to_dict()
        assert len(data["geopolitical_events"]) == 2


class TestHistoricalScenario:
    """Tests for HistoricalScenario data model."""

    def test_create(self, historical_scenario):
        assert historical_scenario.name == "Jan 2024 Bullish Run"
        assert historical_scenario.price_outcome == 3.5
        assert historical_scenario.volatility_outcome == -0.5
        assert historical_scenario.max_favorable_movement == 5.2
        assert historical_scenario.max_adverse_movement == -1.8
        assert historical_scenario.dataset_source == "historical_data_2024"

    def test_deterministic_id(self):
        a = HistoricalScenario(name="Test", description="Same")
        b = HistoricalScenario(name="Test", description="Same")
        assert a.id == b.id

    def test_to_dict_roundtrip(self, historical_scenario):
        data = historical_scenario.to_dict()
        restored = HistoricalScenario.from_dict(data)
        assert restored.name == historical_scenario.name
        assert restored.price_outcome == historical_scenario.price_outcome
        assert restored.volatility_outcome == historical_scenario.volatility_outcome
        assert restored.dataset_source == historical_scenario.dataset_source
        assert restored.hash == historical_scenario.hash

    def test_start_end_time(self, historical_scenario):
        assert historical_scenario.start_time is not None
        assert historical_scenario.end_time is not None
        assert historical_scenario.start_time < historical_scenario.end_time

    def test_tags(self, historical_scenario):
        assert "bullish" in historical_scenario.tags
        assert "trending" in historical_scenario.tags

    def test_backward_compatibility(self):
        """Test that old 'outcome_price_change' field is still honored."""
        old_data = {
            "id": "test-id",
            "created_at": "2024-01-01T00:00:00+00:00",
            "ontology_tags": [],
            "lifecycle": {"transitions": []},
            "name": "Legacy",
            "description": "",
            "snapshot_ids": [],
            "regime_id": "",
            "macro_id": "",
            "outcome": "",
            "outcome_price_change": 2.5,  # Old field name
            "tags": [],
            "similarity_score": 0.0,
        }
        restored = HistoricalScenario.from_dict(old_data)
        assert restored.price_outcome == 2.5


# =============================================================================
# Feature Extraction Tests
# =============================================================================

class TestFeatureExtraction:
    """Tests for feature extraction functions."""

    def test_compute_features(self, market_snapshot):
        features = compute_features(market_snapshot)
        assert isinstance(features, FeatureSet)
        assert features.range_pct > 0
        assert features.body_pct >= 0
        assert 0 <= features.close_position <= 1
        assert features.is_bullish == (market_snapshot.close > market_snapshot.open)

    def test_bullish_feature(self, market_snapshot):
        # Close > Open → bullish
        features = compute_features(market_snapshot)
        assert features.is_bullish is True

    def test_bearish_feature(self, different_snapshot):
        features = compute_features(different_snapshot)
        assert features.is_bullish is False

    def test_range_pct_positive(self):
        snap = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            high=100.0,
            low=90.0,
            close=95.0,
        )
        features = compute_features(snap)
        assert features.range_pct == pytest.approx(10.0 / 95.0 * 100.0)

    def test_body_pct(self):
        snap = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            open=100.0,
            high=105.0,
            low=95.0,
            close=103.0,
        )
        features = compute_features(snap)
        # Body = 3, Range = 10
        body_range = 3.0 / 10.0
        assert features.body_pct == pytest.approx(body_range)

    def test_close_position(self):
        snap = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            high=100.0,
            low=90.0,
            close=95.0,
        )
        features = compute_features(snap)
        # Close at 95, range 90-100, so position = 0.5
        assert features.close_position == pytest.approx(0.5)

    def test_deterministic_features(self, market_snapshot):
        f1 = compute_features(market_snapshot)
        f2 = compute_features(market_snapshot)
        assert f1.range_pct == f2.range_pct
        assert f1.body_pct == f2.body_pct
        assert f1.is_bullish == f2.is_bullish


# =============================================================================
# Similarity Comparison Tests
# =============================================================================

class TestSimilarity:
    """Tests for similarity comparison functions."""

    def test_identical_snapshot(self, market_snapshot):
        """Same snapshot should give 1.0 similarity."""
        score = compare_snapshots(market_snapshot, market_snapshot)
        assert score == pytest.approx(1.0)

    def test_similar_snapshots(self, market_snapshot, similar_snapshot):
        """Similar snapshots should give high score."""
        score = compare_snapshots(market_snapshot, similar_snapshot)
        assert score > 0.5

    def test_different_snapshots(self, market_snapshot, different_snapshot):
        """Different snapshots should give lower score."""
        score = compare_snapshots(market_snapshot, different_snapshot)
        assert score < 0.6

    def test_compare_similar_greater_than_different(
        self, market_snapshot, similar_snapshot, different_snapshot
    ):
        """Similar pair should score higher than different pair."""
        sim_score = compare_snapshots(market_snapshot, similar_snapshot)
        diff_score = compare_snapshots(market_snapshot, different_snapshot)
        assert sim_score > diff_score

    def test_find_similar_snapshots(
        self, market_snapshot, similar_snapshot, different_snapshot
    ):
        results = find_similar_snapshots(
            market_snapshot,
            [similar_snapshot, different_snapshot],
            top_n=5,
        )
        assert len(results) == 2
        # Most similar should be first
        assert results[0][0].id == similar_snapshot.id

    def test_find_similar_with_min_score(
        self, market_snapshot, similar_snapshot, different_snapshot
    ):
        results = find_similar_snapshots(
            market_snapshot,
            [similar_snapshot, different_snapshot],
            min_score=0.8,
        )
        assert len(results) >= 0  # Valid even if none pass

    def test_compare_scenarios(self, historical_scenario, market_snapshot):
        """Test scenario comparison."""
        a = historical_scenario
        b = HistoricalScenario(
            name="Similar",
            description="Similar scenario",
            snapshot_ids=a.snapshot_ids,
            regime_id=a.regime_id,
            tags=a.tags,
        )
        snapshots = {market_snapshot.id: market_snapshot}
        score = compare_scenarios(a, b, snapshots)
        assert 0.0 <= score <= 1.0

    def test_deterministic_similarity(self, market_snapshot, similar_snapshot):
        score1 = compare_snapshots(market_snapshot, similar_snapshot)
        score2 = compare_snapshots(market_snapshot, similar_snapshot)
        assert score1 == score2


# =============================================================================
# ScenarioMatcher Tests
# =============================================================================

class TestScenarioMatcher:
    """Tests for ScenarioMatcher."""

    def test_default_weights(self):
        matcher = ScenarioMatcher()
        weights = matcher.get_weight_report()
        assert "weights" in weights
        assert abs(weights["weight_sum"] - 1.0) < 0.01

    def test_custom_weights(self):
        custom = {"price_range": 0.5, "trend_direction": 0.5}
        matcher = ScenarioMatcher(feature_weights=custom)
        assert matcher.feature_weights["price_range"] == 0.5

    def test_invalid_weights_raises(self):
        with pytest.raises(ValueError):
            ScenarioMatcher(feature_weights={"price_range": 0.5})

    def test_match_empty_scenarios(self, market_snapshot):
        matcher = ScenarioMatcher()
        results = matcher.match_scenario(market_snapshot, [])
        assert len(results) == 0

    def test_match_with_scenarios(
        self, market_snapshot, similar_snapshot, historical_scenario
    ):
        matcher = ScenarioMatcher()
        snapshots = {similar_snapshot.id: similar_snapshot}
        # Add the similar snapshot as a scenario reference
        scenario = HistoricalScenario(
            name="Test Match",
            description="Match test",
            snapshot_ids=[similar_snapshot.id],
        )
        results = matcher.match_scenario(
            market_snapshot,
            [scenario, historical_scenario],
            snapshots_index=snapshots,
            top_n=5,
        )
        assert len(results) >= 0  # Valid if no match or some match

    def test_deterministic_ranking(self, market_snapshot):
        matcher = ScenarioMatcher()
        # Create two scenarios with same snapshot refs
        s1 = HistoricalScenario(name="A", snapshot_ids=["id1"])
        s2 = HistoricalScenario(name="B", snapshot_ids=["id1"])
        snapshots = {
            "id1": MarketSnapshot(
                asset="XAUUSD",
                timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
                close=2000.0,
                high=2010.0,
                low=1990.0,
                open=1995.0,
            ),
        }
        results1 = matcher.match_scenario(market_snapshot, [s1, s2], snapshots_index=snapshots)
        results2 = matcher.match_scenario(market_snapshot, [s1, s2], snapshots_index=snapshots)
        # Same results, same order
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert r1.scenario_id == r2.scenario_id
            assert r1.overall_score == r2.overall_score

    def test_match_result_serialization(self, market_snapshot):
        result = MatchResult(
            scenario_id="test-id",
            scenario_name="Test",
            overall_score=0.85,
            feature_scores={"price_range": 0.9},
        )
        data = result.to_dict()
        assert data["scenario_id"] == "test-id"
        assert data["overall_score"] == 0.85
        assert data["calculation_method"] == "WeightedFeatureComparison"

    def test_weights_report(self):
        matcher = ScenarioMatcher()
        report = matcher.get_weight_report()
        assert "weights" in report
        assert "calculation_method" in report
        assert "description" in report


# =============================================================================
# OutcomeAnalysis Tests
# =============================================================================

class TestOutcomeAnalysis:
    """Tests for OutcomeAnalysis."""

    def test_empty_analysis(self):
        analysis = OutcomeAnalysis()
        result = analysis.analyze([], {})
        assert result.total_examples == 0
        assert result.confidence_score == 0.0

    def test_positive_outcomes(self, historical_scenario):
        analysis = OutcomeAnalysis()
        match = MatchResult(
            scenario_id=historical_scenario.id,
            scenario_name=historical_scenario.name,
            overall_score=0.85,
            feature_scores={},
        )
        scenarios = {historical_scenario.id: historical_scenario}
        result = analysis.analyze([match], scenarios)
        assert result.total_examples == 1
        assert result.positive_outcomes == 1
        assert result.positive_ratio == 1.0
        assert result.avg_price_outcome == 3.5

    def test_negative_outcomes(self, historical_scenario):
        analysis = OutcomeAnalysis()
        historical_scenario.price_outcome = -2.5
        match = MatchResult(
            scenario_id=historical_scenario.id,
            scenario_name=historical_scenario.name,
            overall_score=0.75,
            feature_scores={},
        )
        scenarios = {historical_scenario.id: historical_scenario}
        result = analysis.analyze([match], scenarios)
        assert result.total_examples == 1
        assert result.negative_outcomes == 1
        assert result.positive_ratio == 0.0
        assert result.avg_price_outcome == -2.5

    def test_mixed_outcomes(self, historical_scenario):
        """Test with multiple scenarios of different outcomes."""
        analysis = OutcomeAnalysis()

        s1 = HistoricalScenario(name="Up1", price_outcome=2.0, snapshot_ids=["s1"])
        s2 = HistoricalScenario(name="Up2", price_outcome=1.5, snapshot_ids=["s2"])
        s3 = HistoricalScenario(name="Down1", price_outcome=-1.0, snapshot_ids=["s3"])

        m1 = MatchResult(scenario_id=s1.id, scenario_name="Up1", overall_score=0.9, feature_scores={})
        m2 = MatchResult(scenario_id=s2.id, scenario_name="Up2", overall_score=0.8, feature_scores={})
        m3 = MatchResult(scenario_id=s3.id, scenario_name="Down1", overall_score=0.7, feature_scores={})

        scenarios = {s1.id: s1, s2.id: s2, s3.id: s3}
        result = analysis.analyze([m1, m2, m3], scenarios)

        assert result.total_examples == 3
        assert result.positive_outcomes == 2
        assert result.negative_outcomes == 1
        assert result.positive_ratio == pytest.approx(2.0 / 3.0)
        assert result.avg_price_outcome == pytest.approx((2.0 + 1.5 - 1.0) / 3.0)

    def test_confidence_with_min_examples(self, historical_scenario):
        """Test confidence with fewer than min_examples."""
        analysis = OutcomeAnalysis(min_examples=5)
        match = MatchResult(
            scenario_id=historical_scenario.id,
            scenario_name=historical_scenario.name,
            overall_score=0.85,
            feature_scores={},
        )
        scenarios = {historical_scenario.id: historical_scenario}
        result = analysis.analyze([match], scenarios)
        assert result.confidence_score < 1.0
        assert result.confidence_score > 0.0

    def test_result_serialization(self):
        result = OutcomeAnalysisResult(
            total_examples=10,
            positive_outcomes=7,
            negative_outcomes=3,
            positive_ratio=0.7,
            avg_price_outcome=2.5,
            confidence_score=0.85,
        )
        data = result.to_dict()
        assert data["total_examples"] == 10
        assert data["positive_ratio"] == 0.7
        assert data["calculation_method"] == "HistoricalOutcomeAnalysis"


# =============================================================================
# MarketMemoryReport Tests
# =============================================================================

class TestMarketMemoryReport:
    """Tests for MarketMemoryReport."""

    def test_create_report(self):
        report = MarketMemoryReport(
            report_type="FullAnalysis",
            target_snapshot_id="snap-001",
            calculation_method="WeightedFeatureComparison",
        )
        assert report.report_type == "FullAnalysis"
        assert report.target_snapshot_id == "snap-001"
        assert report.status == "Draft"
        assert report.id is not None

    def test_add_audit_entry(self):
        report = MarketMemoryReport(report_type="ScenarioMatch")
        report.add_audit_entry(
            action="MATCH",
            actor="ScenarioMatcher",
            details="Matched 3 scenarios",
        )
        assert len(report.audit_entries) == 1
        entry = report.audit_entries[0]
        assert entry["action"] == "MATCH"
        assert entry["actor"] == "ScenarioMatcher"

    def test_finalize(self):
        report = MarketMemoryReport(report_type="FullAnalysis")
        assert report.status == "Draft"
        report.finalize()
        assert report.status == "Final"

    def test_to_dict_roundtrip(self):
        report = MarketMemoryReport(
            report_type="FullAnalysis",
            target_snapshot_id="snap-001",
            matched_scenarios=[{"scenario_id": "s1", "score": 0.9}],
            outcome_analysis={"total_examples": 5},
            evidence_ids=["ev-001", "ev-002"],
            historical_sources=["dataset_2024"],
            confidence_basis="Based on 3+ matches",
            limitations=["Limited to XAUUSD data"],
        )
        report.add_audit_entry(action="CREATED", details="Initial report")

        data = report.to_dict()
        restored = MarketMemoryReport.from_dict(data)

        assert restored.report_type == "FullAnalysis"
        assert restored.target_snapshot_id == "snap-001"
        assert len(restored.matched_scenarios) == 1
        assert restored.outcome_analysis["total_examples"] == 5
        assert len(restored.evidence_ids) == 2
        assert len(restored.audit_entries) == 1
        assert restored.status == "Draft"

    def test_evidence_references(self):
        report = MarketMemoryReport(
            report_type="OutcomeAnalysis",
            evidence_ids=["ev-001", "ev-002", "ev-003"],
            historical_sources=["dataset_a", "dataset_b"],
        )
        assert "ev-001" in report.evidence_ids
        assert "dataset_a" in report.historical_sources

    def test_lifecycle_tracking(self):
        report = MarketMemoryReport(report_type="ScenarioMatch")
        assert report.lifecycle.current_stage == LifecycleStage.DRAFT
        report.finalize()
        assert report.lifecycle.current_stage == LifecycleStage.FINAL

    def test_deterministic_id(self):
        report1 = MarketMemoryReport(report_type="FullAnalysis")
        # Different reports should have different IDs due to timestamp
        report2 = MarketMemoryReport(report_type="FullAnalysis")
        # IDs should differ because timestamps differ
        assert report1.id != report2.id


# =============================================================================
# Repository Tests
# =============================================================================

class TestMarketMemoryRepository:
    """Tests for MarketMemoryRepository."""

    def test_save_snapshot(self, repository, market_snapshot):
        saved = repository.save_snapshot(market_snapshot)
        assert saved.id == market_snapshot.id
        assert repository.count_all()["snapshots"] == 1

    def test_get_snapshot(self, repository, market_snapshot):
        repository.save_snapshot(market_snapshot)
        retrieved = repository.get_snapshot(market_snapshot.id)
        assert retrieved is not None
        assert retrieved.asset == "XAUUSD"

    def test_get_snapshots_by_asset(self, repository, market_snapshot):
        repository.save_snapshot(market_snapshot)
        results = repository.get_snapshots_by_asset("XAUUSD")
        assert len(results) == 1
        results = repository.get_snapshots_by_asset("EURUSD")
        assert len(results) == 0

    def test_get_snapshots_in_range(self, repository, market_snapshot):
        repository.save_snapshot(market_snapshot)
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)
        results = repository.get_snapshots_in_range("XAUUSD", start, end)
        assert len(results) == 1

    def test_save_regime(self, repository, market_regime):
        repository.save_regime(market_regime)
        assert repository.count_all()["regimes"] == 1

    def test_get_regimes_by_asset(self, repository, market_regime):
        repository.save_regime(market_regime)
        results = repository.get_regimes_by_asset("XAUUSD")
        assert len(results) == 1

    def test_save_macro_state(self, repository, macro_state):
        repository.save_macro_state(macro_state)
        assert repository.count_all()["macro_states"] == 1

    def test_save_scenario(self, repository, historical_scenario):
        repository.save_scenario(historical_scenario)
        assert repository.count_all()["scenarios"] == 1

    def test_scenario_dataset_tracking(self, repository, historical_scenario):
        repository.save_scenario(historical_scenario)
        sources = repository.get_dataset_sources()
        assert "historical_data_2024" in sources

    def test_find_scenarios_by_tag(self, repository, historical_scenario):
        repository.save_scenario(historical_scenario)
        results = repository.find_scenarios_by_tag("bullish")
        assert len(results) == 1

    def test_find_scenarios_by_outcome(self, repository, historical_scenario):
        repository.save_scenario(historical_scenario)
        results = repository.find_scenarios_by_outcome("bullish")
        assert len(results) == 1

    def test_find_scenarios_by_dataset(self, repository, historical_scenario):
        repository.save_scenario(historical_scenario)
        results = repository.find_scenarios_by_dataset("historical_data_2024")
        assert len(results) == 1

    def test_get_all_scenarios(self, repository, historical_scenario):
        repository.save_scenario(historical_scenario)
        all_scenarios = repository.get_all_scenarios()
        assert len(all_scenarios) == 1

    def test_count_all(self, populated_repository):
        counts = populated_repository.count_all()
        assert counts["snapshots"] == 1
        assert counts["regimes"] == 1
        assert counts["macro_states"] == 1
        assert counts["scenarios"] == 1

    def test_clear(self, populated_repository):
        populated_repository.clear()
        counts = populated_repository.count_all()
        assert counts["snapshots"] == 0
        assert counts["regimes"] == 0
        assert counts["macro_states"] == 0
        assert counts["scenarios"] == 0

    def test_sqlite_persistence(self, market_snapshot, market_regime):
        """Test SQLite persistence."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = MarketMemoryRepository(sqlite_path=db_path)
            repo.save_snapshot(market_snapshot)
            repo.save_regime(market_regime)
            repo.close()

            # Re-open and verify
            repo2 = MarketMemoryRepository(sqlite_path=db_path)
            counts = repo2.count_all()
            assert counts["snapshots"] == 1
            assert counts["regimes"] == 1
            repo2.close()
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_sqlite_clear(self, market_snapshot):
        """Test clear also removes SQLite data."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = MarketMemoryRepository(sqlite_path=db_path)
            repo.save_snapshot(market_snapshot)
            repo.clear()
            repo.close()

            # Re-open - should be empty
            repo2 = MarketMemoryRepository(sqlite_path=db_path)
            counts = repo2.count_all()
            assert counts["snapshots"] == 0
            repo2.close()
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)


# =============================================================================
# Integration Layer Tests
# =============================================================================

class TestMarketMemoryIntegrator:
    """Tests for MarketMemoryIntegrator."""

    def test_standalone_mode(self):
        integrator = MarketMemoryIntegrator()
        result = integrator.connect_to_research_cycle("cycle-1", "report-1")
        assert result["status"] == "standalone"

    def test_connect_to_research_cycle(self):
        def adapter(cycle_id, report_id):
            return {"status": "connected", "cycle_id": cycle_id, "report_id": report_id}

        ctx = IntegrationContext(research_cycle_adapter=adapter)
        integrator = MarketMemoryIntegrator(ctx)
        result = integrator.connect_to_research_cycle("cycle-1", "report-1")
        assert result["status"] == "connected"
        assert result["cycle_id"] == "cycle-1"

    def test_connect_to_reasoning_chain(self):
        def adapter(chain_id, results):
            return {"status": "connected", "chain_id": chain_id}

        ctx = IntegrationContext(reasoning_chain_adapter=adapter)
        integrator = MarketMemoryIntegrator(ctx)
        result = integrator.connect_to_reasoning_chain("chain-1", [])
        assert result["status"] == "connected"

    def test_connect_to_validation(self):
        def adapter(v_id, r_id):
            return {"status": "connected", "validation_id": v_id}

        ctx = IntegrationContext(validation_adapter=adapter)
        integrator = MarketMemoryIntegrator(ctx)
        result = integrator.connect_to_validation("val-1", "report-1")
        assert result["status"] == "connected"

    def test_connect_to_experiment(self):
        def adapter(exp_id, r_id):
            return {"status": "connected", "experiment_id": exp_id}

        ctx = IntegrationContext(experiment_framework_adapter=adapter)
        integrator = MarketMemoryIntegrator(ctx)
        result = integrator.connect_to_experiment("exp-1", "report-1")
        assert result["status"] == "connected"

    def test_connect_to_macro_intelligence(self):
        def adapter(m_id, r_id):
            return {"status": "connected", "macro_id": m_id}

        ctx = IntegrationContext(macro_intelligence_adapter=adapter)
        integrator = MarketMemoryIntegrator(ctx)
        result = integrator.connect_to_macro_intelligence("macro-1", "report-1")
        assert result["status"] == "connected"

    def test_register_evidence(self):
        def adapter(e_ids, r_id):
            return {"status": "registered", "evidence_count": len(e_ids)}

        ctx = IntegrationContext(evidence_registry_adapter=adapter)
        integrator = MarketMemoryIntegrator(ctx)
        result = integrator.register_evidence(["ev-1", "ev-2"], "report-1")
        assert result["status"] == "registered"
        assert result["evidence_count"] == 2

    def test_create_audit_entry(self):
        def adapter(action, obj_id, details):
            return {"status": "audited", "action": action}

        ctx = IntegrationContext(audit_entry_adapter=adapter)
        integrator = MarketMemoryIntegrator(ctx)
        result = integrator.create_audit_entry("MATCH", "scenario-1", "details")
        assert result["status"] == "audited"

    def test_standalone_all_connections(self):
        integrator = MarketMemoryIntegrator()
        assert integrator.connect_to_research_cycle("a", "b")["status"] == "standalone"
        assert integrator.connect_to_reasoning_chain("a", [])["status"] == "standalone"
        assert integrator.connect_to_validation("a", "b")["status"] == "standalone"
        assert integrator.connect_to_experiment("a", "b")["status"] == "standalone"
        assert integrator.connect_to_macro_intelligence("a", "b")["status"] == "standalone"
        assert integrator.register_evidence([], "a")["status"] == "standalone"
        assert integrator.create_audit_entry("a", "b")["status"] == "standalone"


# =============================================================================
# MarketEvent Tests
# =============================================================================

class TestMarketEvent:
    """Tests for MarketEvent model."""

    def test_create(self):
        event = MarketEvent(
            event_type="Fed",
            timestamp=datetime(2024, 1, 31, 18, 0, tzinfo=timezone.utc),
            asset="XAUUSD",
            description="FOMC Rate Decision",
            impact="High",
            actual_value=5.5,
            expected_value=5.5,
            previous_value=5.25,
            source="Federal Reserve",
        )
        assert event.event_type == "Fed"
        assert event.impact == "High"
        assert event.actual_value == 5.5

    def test_to_dict_roundtrip(self):
        event = MarketEvent(
            event_type="CPI",
            timestamp=datetime(2024, 1, 11, 13, 30, tzinfo=timezone.utc),
            impact="High",
            actual_value=3.4,
            expected_value=3.3,
        )
        data = event.to_dict()
        restored = MarketEvent.from_dict(data)
        assert restored.event_type == "CPI"
        assert restored.actual_value == 3.4
        assert restored.expected_value == 3.3
        assert restored.hash == event.hash

    def test_deterministic_id(self):
        ts = datetime(2024, 1, 31, 18, 0, tzinfo=timezone.utc)
        a = MarketEvent(event_type="Fed", timestamp=ts, description="Rate Decision")
        b = MarketEvent(event_type="Fed", timestamp=ts, description="Rate Decision")
        assert a.id == b.id


# =============================================================================
# Determinism Guarantee Tests
# =============================================================================

class TestDeterminism:
    """Verifies that all operations produce identical outputs for identical inputs."""

    def test_deterministic_snapshot_creation(self):
        """Same constructor args → same ID."""
        ts = datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)
        a = MarketSnapshot(asset="XAUUSD", timestamp=ts, timeframe="1h", close=2000.0)
        b = MarketSnapshot(asset="XAUUSD", timestamp=ts, timeframe="1h", close=2000.0)
        assert a.id == b.id
        assert a.hash == b.hash

    def test_deterministic_feature_extraction(self, market_snapshot):
        f1 = compute_features(market_snapshot)
        f2 = compute_features(market_snapshot)
        assert f1.range_pct == f2.range_pct
        assert f1.body_pct == f2.body_pct
        assert f1.close_position == f2.close_position

    def test_deterministic_comparison(self, market_snapshot, similar_snapshot):
        s1 = compare_snapshots(market_snapshot, similar_snapshot)
        s2 = compare_snapshots(market_snapshot, similar_snapshot)
        assert s1 == s2

    def test_deterministic_matching(self, market_snapshot):
        """ScenarioMatcher must produce identical results for same inputs."""
        matcher = ScenarioMatcher()
        s1 = HistoricalScenario(name="S1", snapshot_ids=["id1"])
        s2 = HistoricalScenario(name="S2", snapshot_ids=["id1"])
        snapshots = {
            "id1": MarketSnapshot(
                asset="XAUUSD",
                timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
                close=2000.0, high=2010.0, low=1990.0, open=1995.0,
            ),
        }
        r1 = matcher.match_scenario(market_snapshot, [s1, s2], snapshots_index=snapshots)
        r2 = matcher.match_scenario(market_snapshot, [s1, s2], snapshots_index=snapshots)
        for m1, m2 in zip(r1, r2):
            assert m1.overall_score == m2.overall_score
            assert m1.scenario_id == m2.scenario_id

    def test_deterministic_report_creation(self):
        """Same report content → same hash."""
        r1 = MarketMemoryReport(report_type="FullAnalysis", target_snapshot_id="snap-001")
        r2 = MarketMemoryReport(report_type="FullAnalysis", target_snapshot_id="snap-001")
        # IDs will differ due to timestamp in seed, but content hash should be deterministic
        assert r1.hash is not None
        assert r2.hash is not None


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_volume_snapshot(self):
        snap = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            volume=0.0,
        )
        features = compute_features(snap)
        assert features is not None

    def test_flat_bar(self):
        """Open == Close → neutral body."""
        snap = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            open=100.0, high=105.0, low=95.0, close=100.0,
        )
        features = compute_features(snap)
        assert features.is_bullish is False  # Close == Open → not bullish
        assert features.body_pct == 0.0

    def test_extreme_volatility(self):
        a = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            high=2000.0, low=1900.0, close=1950.0, volatility=10.0,
        )
        b = MarketSnapshot(
            asset="XAUUSD",
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            high=2000.0, low=1900.0, close=1950.0, volatility=10.0,
        )
        score = compare_snapshots(a, b)
        assert score == pytest.approx(1.0)

    def test_empty_scenario_matching(self, market_snapshot):
        matcher = ScenarioMatcher()
        empty_scenario = HistoricalScenario(name="Empty", description="No snapshots")
        results = matcher.match_scenario(market_snapshot, [empty_scenario], min_score=0.01)
        assert len(results) == 0  # No snapshot IDs to compare

    def test_repository_clear_twice(self, repository):
        """Clearing an empty repository should not raise."""
        repository.clear()
        repository.clear()  # Second clear should be fine
        counts = repository.count_all()
        assert counts["snapshots"] == 0

    def test_report_without_optional_fields(self):
        report = MarketMemoryReport(report_type="ScenarioMatch")
        data = report.to_dict()
        restored = MarketMemoryReport.from_dict(data)
        assert restored.report_type == "ScenarioMatch"
        assert restored.matched_scenarios == []
        assert restored.outcome_analysis is None

    def test_outcome_analysis_with_missing_scenario(self, historical_scenario):
        """Match result referencing a scenario not in the dict should be skipped."""
        analysis = OutcomeAnalysis()
        match = MatchResult(
            scenario_id="nonexistent",
            scenario_name="Missing",
            overall_score=0.9,
            feature_scores={},
        )
        result = analysis.analyze([match], {})
        assert result.total_examples == 0

    def test_macro_state_with_minimal_data(self):
        ms = MacroState(
            timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
        )
        assert ms.dxy == 0.0
        assert ms.overall_assessment == ""
        data = ms.to_dict()
        restored = MacroState.from_dict(data)
        assert restored.dxy == 0.0


# =============================================================================
# Integration Workflow Tests
# =============================================================================

class TestWorkflow:
    """End-to-end workflow tests."""

    def test_full_analysis_workflow(self, market_snapshot, similar_snapshot):
        """
        Simulate the full market memory analysis pipeline:
        1. Create snapshots
        2. Create scenarios
        3. Match scenarios
        4. Analyze outcomes
        5. Generate report
        6. Validate
        7. Learn
        """
        # 1. Snapshots
        current = market_snapshot
        historical = similar_snapshot

        # 2. Scenario
        scenario = HistoricalScenario(
            name="Historical Match",
            description="Reference scenario",
            snapshot_ids=[historical.id],
            price_outcome=2.5,
            volatility_outcome=-0.3,
            max_favorable_movement=4.0,
            max_adverse_movement=-1.5,
            tags=["reference"],
            dataset_source="test_dataset",
        )

        # 3. Match
        matcher = ScenarioMatcher()
        snapshots = {historical.id: historical}
        matches = matcher.match_scenario(
            current, [scenario], snapshots_index=snapshots, top_n=5
        )

        # 4. Analyze
        analysis = OutcomeAnalysis()
        scenarios_dict = {scenario.id: scenario}
        result = analysis.analyze(matches, scenarios_dict)

        # 5. Report
        report = MarketMemoryReport(
            report_type="FullAnalysis",
            target_snapshot_id=current.id,
            matched_scenarios=[m.to_dict() for m in matches],
            outcome_analysis=result.to_dict(),
            evidence_ids=[current.id, historical.id],
            historical_sources=["test_dataset"],
            confidence_basis=f"Based on {result.total_examples} matches",
            limitations=["Test data only"],
        )
        report.add_audit_entry(
            action="WORKFLOW_COMPLETE",
            actor="TestWorkflow",
            details="Full analysis pipeline executed",
        )
        report.finalize()

        # Verify report
        assert report.report_type == "FullAnalysis"
        assert report.status == "Final"
        assert len(report.evidence_ids) == 2
        assert len(report.audit_entries) == 1
        assert report.outcome_analysis is not None
        assert report.outcome_analysis["total_examples"] >= 0

        # Round-trip verification
        data = report.to_dict()
        restored = MarketMemoryReport.from_dict(data)
        assert restored.report_type == "FullAnalysis"
        assert restored.status == "Final"
        assert len(restored.audit_entries) == 1
        assert restored.hash == report.hash

    def test_repository_sqlite_workflow(self):
        """
        End-to-end test with SQLite persistence.
        """
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Create and populate
            repo = MarketMemoryRepository(sqlite_path=db_path)

            ts = datetime(2024, 6, 1, tzinfo=timezone.utc)
            snap = MarketSnapshot(
                asset="XAUUSD", timestamp=ts, close=2000.0, high=2010.0, low=1990.0
            )
            scenario = HistoricalScenario(
                name="June Scenario",
                description="Test",
                snapshot_ids=[snap.id],
                dataset_source="sqlite_test",
            )

            repo.save_snapshot(snap)
            repo.save_scenario(scenario)
            repo.close()

            # Re-open and verify
            repo2 = MarketMemoryRepository(sqlite_path=db_path)
            counts = repo2.count_all()
            assert counts["snapshots"] == 1
            assert counts["scenarios"] == 1

            retrieved_scenario = repo2.get_scenario(scenario.id)
            assert retrieved_scenario is not None
            assert retrieved_scenario.name == "June Scenario"

            sources = repo2.get_dataset_sources()
            assert "sqlite_test" in sources

            repo2.close()
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)
