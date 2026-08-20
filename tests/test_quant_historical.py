"""
Unit tests for the Historical Analytics Engine (WP-4 direct coverage).

Phase 5.1 — Certified Analytical Compute Surface (WP-4).
These tests observe the existing deterministic behavior of the historical
submodule. Pure research-only tests; no trading logic.

Covers:
    - Pattern mining / pattern frequencies
    - Consecutive streaks
    - Market regime detection
    - Seasonality (monthly / weekly)
    - Session statistics
    - Volatility clustering
    - Trend persistence / breakout / mean-reversion
    - Drawdown & recovery statistics
    - State transition table
    - Feature extraction
    - Determinism on identical inputs
    - Edge cases (empty series, insufficient data)
"""

import pytest

from researchos.quant_engine.historical.analytics import (
    breakout_frequency,
    consecutive_streaks,
    detect_market_regimes,
    drawdown_statistics,
    extract_features,
    mean_reversion_frequency,
    monthly_seasonality,
    pattern_frequencies,
    recovery_statistics,
    session_statistics,
    state_transition_table,
    trend_persistence,
    volatility_clustering,
    weekly_seasonality,
)
from researchos.quant_engine.historical.contracts import (
    MarketState,
    ReturnSeries,
)


def _returns(length: int = 60) -> ReturnSeries:
    # Alternating small positive/negative returns, deterministic.
    vals = [0.01 if i % 2 == 0 else -0.005 for i in range(length)]
    return ReturnSeries(returns=vals)


class TestPatternMining:
    def test_pattern_frequencies(self):
        series = _returns(40)
        freq = pattern_frequencies(series, window=3, up_threshold=0.0)
        assert isinstance(freq, dict)
        assert len(freq) > 0
        total = sum(freq.values())
        assert abs(total - 1.0) < 1e-9

    def test_pattern_frequencies_insufficient(self):
        series = _returns(5)
        assert pattern_frequencies(series, window=10) == {}

    def test_consecutive_streaks(self):
        series = _returns(40)
        streaks = consecutive_streaks(series)
        assert "positive_streaks" in streaks
        assert "negative_streaks" in streaks


class TestRegimes:
    def test_detect_market_regimes(self):
        series = _returns(60)
        regimes = detect_market_regimes(series, lookback=20)
        # Alternating small returns should produce at least one segment.
        assert isinstance(regimes, list)
        for reg in regimes:
            assert reg.num_periods > 0
            assert reg.state.value in MarketState._value2member_map_

    def test_detect_market_regimes_insufficient(self):
        series = _returns(10)
        assert detect_market_regimes(series, lookback=20) == []


class TestSeasonality:
    def test_monthly_seasonality(self):
        series = _returns(60)
        profile = monthly_seasonality(series)
        assert profile.group_key == "month"
        assert len(profile.periods) > 0

    def test_weekly_seasonality(self):
        series = _returns(60)
        profile = weekly_seasonality(series)
        assert profile.group_key == "weekday"
        assert len(profile.periods) > 0


class TestSessionAndVolatility:
    def test_session_statistics(self):
        series = _returns(60)
        stats = session_statistics(series)
        assert "mean" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats
        assert "positive_ratio" in stats

    def test_volatility_clustering(self):
        series = _returns(60)
        vc = volatility_clustering(series, window=10)
        assert "abs_return_autocorr" in vc
        assert "squared_return_autocorr" in vc
        assert "clustering_ratio" in vc

    def test_volatility_clustering_insufficient(self):
        series = _returns(5)
        vc = volatility_clustering(series, window=20)
        assert vc["abs_return_autocorr"] == 0.0


class TestTrendBreakout:
    def test_trend_persistence(self):
        series = _returns(60)
        tp = trend_persistence(series, window=10)
        assert "persistence_ratio" in tp
        assert 0.0 <= tp["persistence_ratio"] <= 1.0

    def test_breakout_frequency(self):
        series = _returns(60)
        bf = breakout_frequency(series, window=10)
        assert "breakout_up" in bf
        assert "breakout_down" in bf

    def test_mean_reversion_frequency(self):
        series = _returns(60)
        mr = mean_reversion_frequency(series, window=5)
        assert "mean_reversion_ratio" in mr
        assert 0.0 <= mr["mean_reversion_ratio"] <= 1.0


class TestDrawdown:
    def test_drawdown_statistics(self):
        series = _returns(60)
        dd = drawdown_statistics(series)
        assert dd.num_drawdowns >= 0
        assert dd.max_drawdown <= 0.0

    def test_recovery_statistics(self):
        series = _returns(60)
        rec = recovery_statistics(series)
        assert "avg_recovery_periods" in rec
        assert "max_recovery_periods" in rec
        assert "min_recovery_periods" in rec


class TestStateTransitions:
    def test_state_transition_table(self):
        series = _returns(60)
        table = state_transition_table(series, lookback=20)
        assert table.states is not None
        # Transition matrix rows each sum to 1.0 (or all zeros).
        for row in table.transition_matrix:
            total = sum(row)
            assert total == 0.0 or abs(total - 1.0) < 1e-9


class TestFeatureExtraction:
    def test_extract_features(self):
        series = _returns(60)
        fe = extract_features(series)
        features = fe.to_dict()
        assert "length" in features
        assert "mean_return" in features
        assert "std_return" in features
        assert features["length"] == 60.0

    def test_extract_features_empty_raises(self):
        with pytest.raises(ValueError):
            extract_features(ReturnSeries(returns=[]))


class TestDeterminism:
    def test_pattern_frequencies_deterministic(self):
        series = _returns(40)
        f1 = pattern_frequencies(series, window=3)
        f2 = pattern_frequencies(series, window=3)
        assert f1 == f2

    def test_drawdown_deterministic(self):
        series = _returns(60)
        d1 = drawdown_statistics(series)
        d2 = drawdown_statistics(series)
        assert d1.max_drawdown == d2.max_drawdown
        assert d1.num_drawdowns == d2.num_drawdowns

    def test_extract_features_deterministic(self):
        series = _returns(60)
        fe1 = extract_features(series).to_dict()
        fe2 = extract_features(series).to_dict()
        assert fe1 == fe2
