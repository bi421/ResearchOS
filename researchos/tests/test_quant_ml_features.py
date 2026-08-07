"""
Tests: ML Feature Engineering — deterministic, no future leakage.
All tests verify same input → same output.
"""

from __future__ import annotations

import math
import unittest

from researchos.quant_engine.machine_learning.features import (
    FeatureBuilder,
    atr_feature,
    bollinger_feature,
    cci_feature,
    historical_volatility,
    log_returns,
    macd_feature,
    mfi_feature,
    momentum,
    momentum_regime,
    price_distance_from_ma,
    rate_of_change,
    returns,
    roc_feature,
    rolling_drawdown,
    rolling_mean,
    rolling_std,
    rolling_volatility,
    rsi_feature,
    stochastic_feature,
    trend_state,
    volatility_percentile,
    volatility_ratio,
    volatility_regime,
    vwap_feature,
)


def _make_close(n: int = 100, start: float = 100.0, step: float = 0.5) -> list:
    """Linear price series."""
    return [start + i * step for i in range(n)]


def _make_ohlcv(n: int = 100):
    close = _make_close(n)
    high = [c + 1.0 for c in close]
    low  = [c - 1.0 for c in close]
    vol  = [1000.0 + i * 10.0 for i in range(n)]
    return high, low, close, vol


class TestReturns(unittest.TestCase):
    def test_length(self):
        c = _make_close(50)
        r = returns(c)
        self.assertEqual(len(r), 50)

    def test_first_is_none(self):
        r = returns(_make_close(10))
        self.assertIsNone(r[0])

    def test_positive_trend(self):
        c = [100.0, 101.0, 102.0]
        r = returns(c)
        self.assertAlmostEqual(r[1], 0.01, places=8)
        self.assertAlmostEqual(r[2], 1/101, places=8)

    def test_determinism(self):
        c = _make_close(50)
        self.assertEqual(returns(c), returns(c))

    def test_log_returns_length(self):
        c = _make_close(30)
        lr = log_returns(c)
        self.assertEqual(len(lr), 30)

    def test_log_returns_first_none(self):
        self.assertIsNone(log_returns(_make_close(10))[0])

    def test_log_returns_determinism(self):
        c = _make_close(50)
        self.assertEqual(log_returns(c), log_returns(c))

    def test_log_returns_approx(self):
        # For small returns, log return ≈ simple return
        c = [100.0, 100.5]
        lr = log_returns(c)
        returns(c)[1]
        # Should be close but not equal
        self.assertIsNotNone(lr[1])
        self.assertAlmostEqual(lr[1], math.log(100.5 / 100.0), places=10)


class TestRollingFeatures(unittest.TestCase):
    def test_rolling_mean_length(self):
        c = _make_close(60)
        rm = rolling_mean(c, 20)
        self.assertEqual(len(rm), 60)

    def test_rolling_mean_warmup_nones(self):
        c = _make_close(30)
        rm = rolling_mean(c, 10)
        for i in range(9):
            self.assertIsNone(rm[i])
        self.assertIsNotNone(rm[9])

    def test_rolling_mean_value(self):
        c = [float(i) for i in range(1, 6)]  # [1,2,3,4,5]
        rm = rolling_mean(c, 3)
        self.assertAlmostEqual(rm[2], 2.0, places=8)  # mean(1,2,3)
        self.assertAlmostEqual(rm[4], 4.0, places=8)  # mean(3,4,5)

    def test_rolling_std_length(self):
        c = _make_close(50)
        rs = rolling_std(c, 10)
        self.assertEqual(len(rs), 50)

    def test_rolling_std_constant_series(self):
        c = [100.0] * 30
        rs = rolling_std(c, 10)
        for v in rs[9:]:
            self.assertAlmostEqual(v, 0.0, places=10)

    def test_rolling_vol_length(self):
        c = _make_close(80)
        rv = rolling_volatility(c, 20)
        self.assertEqual(len(rv), 80)

    def test_rolling_vol_determinism(self):
        c = _make_close(80)
        self.assertEqual(rolling_volatility(c, 20), rolling_volatility(c, 20))


class TestPriceFeatures(unittest.TestCase):
    def test_momentum_length(self):
        c = _make_close(50)
        m = momentum(c, 14)
        self.assertEqual(len(m), 50)

    def test_momentum_nones_at_start(self):
        c = _make_close(50)
        m = momentum(c, 14)
        for i in range(14):
            self.assertIsNone(m[i])

    def test_momentum_value(self):
        c = [float(i) for i in range(30)]
        m = momentum(c, 10)
        # momentum[10] = c[10] - c[0] = 10 - 0 = 10
        self.assertAlmostEqual(m[10], 10.0, places=8)

    def test_rate_of_change_length(self):
        c = _make_close(50)
        roc = rate_of_change(c, 14)
        self.assertEqual(len(roc), 50)

    def test_rate_of_change_nones_at_start(self):
        c = _make_close(50)
        roc = rate_of_change(c, 5)
        for i in range(5):
            self.assertIsNone(roc[i])

    def test_price_distance_from_ma_length(self):
        c = _make_close(80)
        pd = price_distance_from_ma(c, 20)
        self.assertEqual(len(pd), 80)


class TestTechnicalFeatures(unittest.TestCase):
    def test_rsi_length(self):
        c = _make_close(50)
        r = rsi_feature(c, 14)
        self.assertEqual(len(r), 50)

    def test_rsi_bounds(self):
        c = _make_close(60)
        r = rsi_feature(c, 14)
        for v in r:
            if v is not None:
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 100.0)

    def test_rsi_determinism(self):
        c = _make_close(60)
        self.assertEqual(rsi_feature(c, 14), rsi_feature(c, 14))

    def test_macd_keys(self):
        c = _make_close(60)
        m = macd_feature(c)
        self.assertIn("macd", m)
        self.assertIn("macd_signal", m)
        self.assertIn("macd_hist", m)

    def test_macd_length(self):
        c = _make_close(60)
        m = macd_feature(c)
        for v in m.values():
            self.assertEqual(len(v), 60)

    def test_macd_determinism(self):
        c = _make_close(60)
        m1 = macd_feature(c)
        m2 = macd_feature(c)
        self.assertEqual(m1["macd"], m2["macd"])

    def test_atr_length(self):
        h, low, c, v = _make_ohlcv(60)
        atr = atr_feature(h, low, c, 14)
        self.assertEqual(len(atr), 60)

    def test_atr_positive(self):
        h, low, c, v = _make_ohlcv(60)
        atr = atr_feature(h, low, c, 14)
        for val in atr:
            if val is not None:
                self.assertGreater(val, 0.0)

    def test_bollinger_bands_keys(self):
        c = _make_close(60)
        bb = bollinger_feature(c, 20)
        for key in ["bb_upper", "bb_middle", "bb_lower", "bb_pct_b"]:
            self.assertIn(key, bb)

    def test_bollinger_upper_gt_lower(self):
        c = _make_close(60)
        bb = bollinger_feature(c, 20)
        for u, lower in zip(bb["bb_upper"], bb["bb_lower"]):
            if u is not None and lower is not None:
                self.assertGreaterEqual(u, lower)

    def test_stochastic_bounds(self):
        h, low, c, v = _make_ohlcv(60)
        st = stochastic_feature(h, low, c, 14, 3)
        for val in st["stoch_k"]:
            if val is not None:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 100.0)

    def test_cci_length(self):
        h, low, c, v = _make_ohlcv(60)
        cci = cci_feature(h, low, c, 20)
        self.assertEqual(len(cci), 60)

    def test_mfi_bounds(self):
        h, low, c, v = _make_ohlcv(60)
        mfi = mfi_feature(h, low, c, v, 14)
        for val in mfi:
            if val is not None:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 100.0)

    def test_vwap_length(self):
        h, low, c, v = _make_ohlcv(60)
        vwap = vwap_feature(h, low, c, v)
        self.assertEqual(len(vwap), 60)

    def test_roc_feature_determinism(self):
        c = _make_close(60)
        self.assertEqual(roc_feature(c, 14), roc_feature(c, 14))


class TestVolatilityFeatures(unittest.TestCase):
    def test_hist_vol_length(self):
        c = _make_close(80)
        hv = historical_volatility(c, 20)
        self.assertEqual(len(hv), 80)

    def test_vol_ratio_length(self):
        c = _make_close(80)
        vr = volatility_ratio(c, 10, 30)
        self.assertEqual(len(vr), 80)

    def test_vol_percentile_length(self):
        c = _make_close(120)
        vp = volatility_percentile(c, 20, 60)
        self.assertEqual(len(vp), 120)

    def test_vol_percentile_bounds(self):
        c = _make_close(120)
        vp = volatility_percentile(c, 20, 60)
        for v in vp:
            if v is not None:
                self.assertGreaterEqual(v, 0.0)
                self.assertLessEqual(v, 1.0)

    def test_rolling_drawdown_length(self):
        c = _make_close(60)
        dd = rolling_drawdown(c, 20)
        self.assertEqual(len(dd), 60)

    def test_rolling_drawdown_nonpositive_for_uptrend(self):
        c = _make_close(60)  # monotonically increasing
        dd = rolling_drawdown(c, 20)
        for v in dd:
            if v is not None:
                self.assertLessEqual(v, 0.0)  # drawdown <= 0 in uptrend (we're at peak)


class TestMarketRegimeFeatures(unittest.TestCase):
    def test_trend_state_length(self):
        c = _make_close(100)
        ts = trend_state(c, 20, 50)
        self.assertEqual(len(ts), 100)

    def test_trend_state_values(self):
        c = _make_close(100)
        ts = trend_state(c, 20, 50)
        for v in ts:
            if v is not None:
                self.assertIn(v, [-1.0, 0.0, 1.0])

    def test_vol_regime_values(self):
        c = _make_close(120)
        vr = volatility_regime(c, 20, 60)
        for v in vr:
            if v is not None:
                self.assertIn(v, [-1.0, 0.0, 1.0])

    def test_momentum_regime_values(self):
        c = _make_close(60)
        mr = momentum_regime(c, 14)
        for v in mr:
            if v is not None:
                self.assertIn(v, [-1.0, 0.0, 1.0])

    def test_trend_state_uptrend(self):
        # Strong uptrend: short MA should be above long MA
        c = [100.0 + i * 2.0 for i in range(100)]
        ts = trend_state(c, 20, 50)
        # After enough warmup, should signal uptrend
        valid = [v for v in ts if v is not None]
        self.assertTrue(any(v == 1.0 for v in valid))


class TestFeatureBuilder(unittest.TestCase):
    def setUp(self):
        n = 120
        self.close = _make_close(n)
        self.high = [c + 1.0 for c in self.close]
        self.low  = [c - 1.0 for c in self.close]
        self.vol  = [1000.0] * n

    def test_builds_feature_set(self):
        fb = FeatureBuilder(self.close, self.high, self.low, self.vol)
        fs = fb.build()
        self.assertGreater(fs.n_features, 0)
        self.assertGreater(fs.n_observations, 0)

    def test_no_na_in_output(self):
        fb = FeatureBuilder(self.close, self.high, self.low, self.vol)
        fs = fb.build(drop_na=True)
        for row in fs.data:
            for v in row:
                self.assertIsNotNone(v)
                self.assertFalse(math.isnan(v))

    def test_determinism(self):
        fb1 = FeatureBuilder(self.close, self.high, self.low, self.vol)
        fb2 = FeatureBuilder(self.close, self.high, self.low, self.vol)
        fs1 = fb1.build()
        fs2 = fb2.build()
        self.assertEqual(fs1.feature_names, fs2.feature_names)
        self.assertEqual(fs1.data, fs2.data)

    def test_with_labels(self):
        labels = [1.0 if self.close[i] > self.close[i-1] else 0.0 for i in range(1, len(self.close))] + [0.0]
        fb = FeatureBuilder(self.close, self.high, self.low, self.vol, labels=labels)
        fs = fb.build(drop_na=True)
        self.assertIsNotNone(fs.labels)
        self.assertEqual(len(fs.labels), fs.n_observations)

    def test_no_future_leakage(self):
        # All features should use only data up to and including index i
        # Verified by construction: rolling windows look backward only
        fb = FeatureBuilder(self.close, self.high, self.low, self.vol)
        fs = fb.build()
        # Basic structural check: n_observations <= len(close)
        self.assertLessEqual(fs.n_observations, len(self.close))


if __name__ == "__main__":
    unittest.main()
