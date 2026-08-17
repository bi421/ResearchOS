"""
Tests: Label Generation Engine — deterministic, pure Python.

Covers future return, binary direction, multi-class labels, regression
targets, triple barrier, volatility-adjusted returns, the LabelBuilder
facade, and the frozen LabelResult contract.
"""

from __future__ import annotations

import math
import unittest
from dataclasses import FrozenInstanceError

from researchos.quant_engine.machine_learning.label_builder import LabelBuilder
from researchos.quant_engine.machine_learning.label_contracts import LabelResult
from researchos.quant_engine.machine_learning.labels import (
    binary_label,
    future_return,
    multiclass_label,
    regression_target,
    triple_barrier,
    vol_adjusted_return,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _up(n: int = 50, start: float = 100.0, step: float = 1.0) -> list:
    """Monotonically increasing price series."""
    return [start + i * step for i in range(n)]


def _down(n: int = 50, start: float = 100.0, step: float = 1.0) -> list:
    """Monotonically decreasing price series."""
    return [start - i * step for i in range(n)]


def _flat(n: int = 50, price: float = 100.0) -> list:
    """Constant price series."""
    return [price] * n


class TestFutureReturn(unittest.TestCase):
    def test_empty_returns_empty(self):
        self.assertEqual(future_return([], 1), [])

    def test_single_element_all_none(self):
        self.assertEqual(future_return([100.0], 1), [None])

    def test_length(self):
        c = _up(40)
        out = future_return(c, 5)
        self.assertEqual(len(out), 40)

    def test_tail_none(self):
        c = _up(10)
        h = 3
        out = future_return(c, h)
        self.assertTrue(all(v is None for v in out[-h:]))
        self.assertTrue(all(v is not None for v in out[:-h]))

    def test_first_value(self):
        out = future_return([100.0, 110.0], 1)
        self.assertAlmostEqual(out[0], 0.1, places=12)
        self.assertIsNone(out[1])

    def test_positive_trend(self):
        out = future_return(_up(20, 100.0, 1.0), 5)
        for v in out[:-5]:
            self.assertGreater(v, 0.0)

    def test_negative_trend(self):
        out = future_return(_down(20, 100.0, 1.0), 5)
        for v in out[:-5]:
            self.assertLess(v, 0.0)

    def test_flat_market_zero(self):
        out = future_return(_flat(20), 3)
        for v in out[:-3]:
            self.assertEqual(v, 0.0)

    def test_constant_prices_zero(self):
        out = future_return([5.0] * 10, 2)
        for v in out[:-2]:
            self.assertEqual(v, 0.0)

    def test_determinism(self):
        c = _up(30)
        self.assertEqual(future_return(c, 4), future_return(c, 4))

    def test_horizon_zero_raises(self):
        with self.assertRaises(ValueError):
            future_return(_up(10), 0)

    def test_horizon_negative_raises(self):
        with self.assertRaises(ValueError):
            future_return(_up(10), -3)

    def test_horizon_non_integer_raises(self):
        with self.assertRaises(ValueError):
            future_return(_up(10), 1.5)

    def test_horizon_boolean_raises(self):
        with self.assertRaises(ValueError):
            future_return(_up(10), True)

    def test_horizon_larger_than_len_all_none(self):
        out = future_return(_up(5), 10)
        self.assertEqual(out, [None] * 5)

    def test_zero_base_returns_none(self):
        out = future_return([0.0, 10.0, 12.0], 1)
        self.assertIsNone(out[0])
        self.assertAlmostEqual(out[1], 0.2, places=12)
        self.assertIsNone(out[2])

    def test_none_input_handled(self):
        out = future_return([100.0, None, 120.0], 1)
        self.assertEqual(out, [None, None, None])

    def test_nan_input_not_allowed_in_output(self):
        out = future_return([100.0, float("nan"), 120.0], 1)
        for v in out:
            self.assertFalse(isinstance(v, float) and math.isnan(v))

    def test_no_nan_in_output(self):
        out = future_return(_up(30), 5)
        for v in out:
            if v is not None:
                self.assertFalse(math.isnan(v))


class TestBinaryLabel(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(binary_label([], 1), [])

    def test_single_element_all_none(self):
        self.assertEqual(binary_label([100.0], 1), [None])

    def test_length(self):
        out = binary_label(_up(30), 5)
        self.assertEqual(len(out), 30)

    def test_tail_none(self):
        out = binary_label(_up(10), 3)
        self.assertTrue(all(v is None for v in out[-3:]))

    def test_positive_returns_one(self):
        out = binary_label(_up(10, 100.0, 1.0), 1)
        self.assertEqual(out[0], 1)

    def test_negative_returns_zero(self):
        out = binary_label(_down(10, 100.0, 1.0), 1)
        self.assertEqual(out[0], 0)

    def test_zero_return_zero(self):
        out = binary_label(_flat(10), 1)
        self.assertEqual(out[0], 0)

    def test_values_in_set(self):
        vals = [v for v in binary_label(_up(30), 5) if v is not None]
        self.assertTrue(all(v in (0, 1) for v in vals))

    def test_determinism(self):
        c = _up(30)
        self.assertEqual(binary_label(c, 4), binary_label(c, 4))

    def test_invalid_horizon_raises(self):
        with self.assertRaises(ValueError):
            binary_label(_up(10), 0)


class TestMulticlassLabel(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(multiclass_label([], 1, 0.01), [])

    def test_length(self):
        out = multiclass_label(_up(30), 5, 0.01)
        self.assertEqual(len(out), 30)

    def test_tail_none(self):
        out = multiclass_label(_up(10), 3, 0.01)
        self.assertTrue(all(v is None for v in out[-3:]))

    def test_up_above_threshold(self):
        out = multiclass_label([100.0, 110.0], 1, 0.05)
        self.assertEqual(out[0], 1)

    def test_down_below_negative_threshold(self):
        out = multiclass_label([100.0, 90.0], 1, 0.05)
        self.assertEqual(out[0], -1)

    def test_neutral_within_threshold(self):
        out = multiclass_label([100.0, 101.0], 1, 0.05)
        self.assertEqual(out[0], 0)

    def test_boundary_positive_neutral(self):
        out = multiclass_label([100.0, 105.0], 1, 0.05)
        self.assertEqual(out[0], 0)  # exactly at threshold -> neutral

    def test_boundary_negative_neutral(self):
        out = multiclass_label([100.0, 95.0], 1, 0.05)
        self.assertEqual(out[0], 0)  # exactly at -threshold -> neutral

    def test_threshold_zero(self):
        out = multiclass_label([100.0, 101.0], 1, 0.0)
        self.assertEqual(out[0], 1)

    def test_values_in_set(self):
        vals = [v for v in multiclass_label(_up(30), 5, 0.01) if v is not None]
        self.assertTrue(all(v in (-1, 0, 1) for v in vals))

    def test_determinism(self):
        c = _up(30)
        self.assertEqual(multiclass_label(c, 4, 0.02), multiclass_label(c, 4, 0.02))

    def test_negative_threshold_raises(self):
        with self.assertRaises(ValueError):
            multiclass_label(_up(10), 1, -0.1)

    def test_invalid_horizon_raises(self):
        with self.assertRaises(ValueError):
            multiclass_label(_up(10), 0, 0.01)


class TestRegressionTarget(unittest.TestCase):
    def test_alias_equal_future_return(self):
        c = _up(25)
        self.assertEqual(regression_target(c, 3), future_return(c, 3))

    def test_length(self):
        self.assertEqual(len(regression_target(_up(20), 2)), 20)

    def test_tail_none(self):
        out = regression_target(_up(10), 4)
        self.assertTrue(all(v is None for v in out[-4:]))

    def test_determinism(self):
        c = _up(20)
        self.assertEqual(regression_target(c, 3), regression_target(c, 3))

    def test_empty(self):
        self.assertEqual(regression_target([], 1), [])


class TestTripleBarrier(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(triple_barrier([], 0.02, 0.02, 5), [])

    def test_length(self):
        out = triple_barrier(_up(20), 0.02, 0.02, 5)
        self.assertEqual(len(out), 20)

    def test_tail_none(self):
        n = 20
        h = 5
        out = triple_barrier(_flat(n), 0.02, 0.02, h)
        self.assertTrue(all(v is None for v in out[-h:]))
        self.assertTrue(all(v is not None for v in out[:-h]))

    def test_take_profit_first(self):
        out = triple_barrier([100.0, 105.0, 90.0], 0.03, 0.03, 2)
        self.assertEqual(out[0], 1)

    def test_stop_loss_first(self):
        out = triple_barrier([100.0, 95.0, 110.0], 0.03, 0.03, 2)
        self.assertEqual(out[0], -1)

    def test_neither(self):
        out = triple_barrier([100.0, 101.0, 100.5], 0.03, 0.03, 2)
        self.assertEqual(out[0], 0)

    def test_constant_prices_zero(self):
        out = triple_barrier(_flat(10), 0.02, 0.02, 3)
        for v in out[:-3]:
            self.assertEqual(v, 0)

    def test_uptrend_take_profit(self):
        out = triple_barrier([100.0, 101.0, 102.0, 103.0, 104.0, 105.0], 0.01, 0.01, 2)
        self.assertEqual(out[0], 1)

    def test_downtrend_stop_loss(self):
        out = triple_barrier([100.0, 99.0, 98.0, 97.0], 0.01, 0.01, 2)
        self.assertEqual(out[0], -1)

    def test_determinism(self):
        c = _up(25)
        self.assertEqual(
            triple_barrier(c, 0.02, 0.02, 5),
            triple_barrier(c, 0.02, 0.02, 5),
        )

    def test_invalid_max_horizon_zero_raises(self):
        with self.assertRaises(ValueError):
            triple_barrier(_up(10), 0.02, 0.02, 0)

    def test_invalid_max_horizon_negative_raises(self):
        with self.assertRaises(ValueError):
            triple_barrier(_up(10), 0.02, 0.02, -2)

    def test_invalid_take_profit_raises(self):
        with self.assertRaises(ValueError):
            triple_barrier(_up(10), 0.0, 0.02, 3)

    def test_invalid_stop_loss_raises(self):
        with self.assertRaises(ValueError):
            triple_barrier(_up(10), 0.02, -0.1, 3)

    def test_values_in_set(self):
        vals = [v for v in triple_barrier(_up(30), 0.02, 0.02, 5) if v is not None]
        self.assertTrue(all(v in (-1, 0, 1) for v in vals))

    def test_no_nan(self):
        out = triple_barrier(_up(20), 0.02, 0.02, 5)
        for v in out:
            if v is not None:
                self.assertFalse(math.isnan(v))


class TestVolAdjustedReturn(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(vol_adjusted_return([], [], 1), [])

    def test_length(self):
        c = _up(20)
        vol = [0.1] * 20
        out = vol_adjusted_return(c, vol, 3)
        self.assertEqual(len(out), 20)

    def test_basic_computation(self):
        out = vol_adjusted_return([100.0, 110.0], [0.1, 0.1], 1)
        self.assertAlmostEqual(out[0], 1.0, places=12)
        self.assertIsNone(out[1])

    def test_zero_volatility_none(self):
        out = vol_adjusted_return([100.0, 110.0], [0.0, 0.0], 1)
        self.assertTrue(all(v is None for v in out))

    def test_none_volatility_none(self):
        out = vol_adjusted_return([100.0, 110.0], [None, 0.1], 1)
        self.assertIsNone(out[0])
        self.assertIsNone(out[1])

    def test_short_volatility(self):
        c = [100.0, 110.0, 121.0]
        out = vol_adjusted_return(c, [0.1], 1)
        self.assertAlmostEqual(out[0], 1.0, places=12)
        self.assertIsNone(out[1])
        self.assertIsNone(out[2])

    def test_determinism(self):
        c = _up(20)
        vol = [0.05 + i * 0.001 for i in range(20)]
        self.assertEqual(vol_adjusted_return(c, vol, 3), vol_adjusted_return(c, vol, 3))

    def test_no_nan(self):
        c = _up(20)
        vol = [0.1] * 20
        for v in vol_adjusted_return(c, vol, 3):
            if v is not None:
                self.assertFalse(math.isnan(v))


class TestLabelResult(unittest.TestCase):
    def test_frozen(self):
        result = LabelResult(name="future_return", values=[1.0])
        with self.assertRaises(FrozenInstanceError):
            result.name = "changed"

    def test_fields(self):
        result = LabelResult(
            name="binary",
            values=[1, 0, None],
            metadata={"horizon": 1},
            horizon=1,
            timestamps=[0, 1, 2],
        )
        self.assertEqual(result.name, "binary")
        self.assertEqual(result.values, [1, 0, None])
        self.assertEqual(result.metadata, {"horizon": 1})
        self.assertEqual(result.horizon, 1)
        self.assertEqual(result.timestamps, [0, 1, 2])

    def test_defaults(self):
        result = LabelResult(name="regression", values=[0.1])
        self.assertEqual(result.metadata, {})
        self.assertIsNone(result.horizon)
        self.assertIsNone(result.timestamps)


class TestLabelBuilder(unittest.TestCase):
    def setUp(self):
        self.close = _up(60, 100.0, 1.0)

    def test_build_future_return(self):
        result = LabelBuilder(self.close).build_future_return(horizon=3)
        self.assertIsInstance(result, LabelResult)
        self.assertEqual(result.name, "future_return")
        self.assertEqual(len(result.values), 60)
        self.assertEqual(result.horizon, 3)

    def test_build_binary(self):
        result = LabelBuilder(self.close).build_binary(horizon=3)
        self.assertEqual(result.name, "binary")
        self.assertEqual(len(result.values), 60)

    def test_build_multiclass(self):
        result = LabelBuilder(self.close).build_multiclass(horizon=3, threshold=0.01)
        self.assertEqual(result.name, "multiclass")
        self.assertEqual(result.metadata["threshold"], 0.01)

    def test_build_triple_barrier(self):
        result = LabelBuilder(self.close).build_triple_barrier(
            take_profit=0.02, stop_loss=0.02, max_horizon=5
        )
        self.assertEqual(result.name, "triple_barrier")
        self.assertEqual(result.metadata["max_horizon"], 5)

    def test_build_regression(self):
        result = LabelBuilder(self.close).build_regression(horizon=3)
        self.assertEqual(result.name, "regression")
        self.assertEqual(result.horizon, 3)

    def test_build_all_keys(self):
        result = LabelBuilder(self.close).build_all()
        self.assertEqual(
            set(result.keys()),
            {"future_return", "binary", "multiclass", "triple_barrier", "regression"},
        )

    def test_build_all_values_are_label_results(self):
        result = LabelBuilder(self.close).build_all()
        for name in result:
            self.assertIsInstance(result[name], LabelResult)

    def test_build_all_values_length(self):
        result = LabelBuilder(self.close).build_all()
        for name in result:
            self.assertEqual(len(result[name].values), 60)

    def test_build_all_determinism(self):
        b1 = LabelBuilder(self.close)
        b2 = LabelBuilder(self.close)
        r1 = b1.build_all(horizon=2, threshold=0.01, max_horizon=4)
        r2 = b2.build_all(horizon=2, threshold=0.01, max_horizon=4)
        for name in r1:
            self.assertEqual(r1[name].values, r2[name].values)

    def test_build_all_metadata(self):
        result = LabelBuilder(self.close).build_all(
            horizon=2, threshold=0.01, take_profit=0.02, stop_loss=0.03, max_horizon=4
        )
        self.assertEqual(result["multiclass"].metadata["threshold"], 0.01)
        self.assertEqual(result["triple_barrier"].metadata["take_profit"], 0.02)
        self.assertEqual(result["triple_barrier"].metadata["stop_loss"], 0.03)
        self.assertEqual(result["future_return"].horizon, 2)

    def test_builder_determinism(self):
        b1 = LabelBuilder(self.close)
        b2 = LabelBuilder(self.close)
        self.assertEqual(b1.build_future_return(2).values, b2.build_future_return(2).values)


class TestLabelStructure(unittest.TestCase):
    def test_future_return_uses_only_entry_and_exit(self):
        """No future leakage: label[i] depends only on close[i] and close[i+h]."""
        close = _up(20, 100.0, 2.0)
        h = 3
        labels = future_return(close, h)
        for i in range(len(close) - h):
            expected = (close[i + h] - close[i]) / close[i]
            self.assertAlmostEqual(labels[i], expected, places=12)
        for i in range(len(close) - h, len(close)):
            self.assertIsNone(labels[i])


if __name__ == "__main__":
    unittest.main()
