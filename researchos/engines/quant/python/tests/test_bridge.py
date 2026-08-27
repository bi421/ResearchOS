"""Python <-> C++ bridge test suite.

Covers: serialization, large datasets, bridge validation, invalid parameters,
type conversion, version compatibility, hash consistency, determinism, and the
full backend API (statistics, risk, simulation, market data, backtest,
performance).
"""

import math
from datetime import datetime, timedelta

import pytest
import researchos.engines.quant.cpp_engine as cq
from researchos.engines.quant.cpp_engine.backend import (
    BacktestEngine,
    Risk,
    Simulation,
    Statistics,
    default_backend,
    native_module,
)
from researchos.engines.quant.cpp_engine.exceptions import (
    EmptyDataError,
    HashMismatchError,
    InsufficientDataError,
    InvalidParameterError,
    InvalidTypeError,
    MalformedDataError,
    error_from_code,
)
from researchos.engines.quant.cpp_engine.models import (
    BacktestRequest,
    Candle,
    MarketData,
    MarketDataRequest,
    MarketDataResult,
    PerformanceRequest,
    PerformanceResult,
    RiskRequest,
    SimulationRequest,
    StatisticsRequest,
    StatisticsResult,
    canonical_double_map,
    canonical_float,
    canonical_float_array,
    canonical_json_escape,
    canonical_object,
)

# ── fixtures ────────────────────────────────────────────────────────────────


def make_candles(n, start="1970-01-01T00:00:00", tf="M1"):
    st = datetime.fromisoformat(start)
    out = []
    for i in range(n):
        price = 100.0 + 10.0 * math.sin(i / 7.0) + 0.1 * (i % 13)
        ts = (st + timedelta(minutes=1) * i).strftime("%Y-%m-%dT%H:%M:%S")
        out.append(
            Candle(
                timestamp=ts,
                open=price,
                close=price + 1.0,
                high=max(price, price + 1.0) + 0.5,
                low=min(price, price + 1.0) - 0.5,
                volume=1000.0,
                timeframe=tf,
            )
        )
    return out


def make_prices(n, base=100.0):
    return [base + 0.5 * i + 0.25 * math.sin(i / 5.0) for i in range(n)]


def market_data_request(n=20, symbol="EURUSD", tf="M1"):
    return MarketDataRequest(symbol=symbol, timeframe=tf, candles=make_candles(n, tf=tf))


def simulation_request(n=20):
    return SimulationRequest(
        dataset_reference="XAUUSD",
        dataset_version="1.0.0",
        initial_capital=100_000.0,
        risk_free_rate=0.0,
        seed=42,
        start_time="2026-01-01T00:00:00",
        end_time="2026-02-01T00:00:00",
        prices=make_prices(n),
    )


def backtest_request(n=20, symbol="BTCUSD"):
    return BacktestRequest(symbol=symbol, candles=make_candles(n))


@pytest.fixture(scope="session")
def backend():
    return default_backend()


# ── metadata / version compatibility ────────────────────────────────────────


class TestMetadata:
    def test_engine_version_semver(self):
        v = cq.engine_version()
        parts = v.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_bridge_version(self):
        assert cq.bridge_version() == "1.0.0"

    def test_protocol_version(self):
        assert cq.protocol_version() == 1

    def test_supported_calculation_versions(self):
        versions = cq.supported_calculation_versions()
        assert "CALCULATION_V1" in versions

    def test_error_codes_stable(self):
        codes = cq.error_codes()
        assert codes["InvalidArgument"] == 100
        assert codes["InvalidParameter"] == 101
        assert codes["InvalidType"] == 102
        assert codes["InsufficientData"] == 200
        assert codes["EmptyData"] == 201
        assert codes["MalformedData"] == 202
        assert codes["OutOfBounds"] == 203
        assert codes["UnsupportedVersion"] == 300
        assert codes["ValidationFailed"] == 301
        assert codes["HashMismatch"] == 302
        assert codes["InternalError"] == 500

    def test_backend_meta(self, backend):
        meta = backend.meta()
        assert meta["engine_name"] == "cpp_quant_engine"
        assert meta["protocol_version"] == 1
        assert meta["calculation_version"] == "CALCULATION_V1"


# ── canonical serialization ─────────────────────────────────────────────────


class TestCanonicalSerialization:
    def test_float_fixed_ten_decimals(self):
        assert canonical_float(1.0) == "1.0000000000"
        assert canonical_float(100000.0) == "100000.0000000000"
        assert canonical_float(-0.0) == "-0.0000000000"

    def test_json_escape(self):
        assert canonical_json_escape('"') == '\\"'
        assert canonical_json_escape("\\") == "\\\\"
        assert canonical_json_escape("a\nb") == "a\\nb"
        assert canonical_json_escape("a\tb") == "a\\tb"

    def test_object_sorted_keys(self):
        assert canonical_object({"zeta": "1", "alpha": "2"}) == '{"alpha":2,"zeta":1}'

    def test_float_array(self):
        assert canonical_float_array([1.0, -2.5]) == "[1.0000000000,-2.5000000000]"

    def test_double_map_sorted(self):
        assert canonical_double_map({"y": 2.0, "x": 1.0}) == '{"x":1.0000000000,"y":2.0000000000}'

    def test_candle_canonical(self):
        c = Candle(timestamp="2026-01-01T00:00:00", open=1.0, high=2.0, low=0.5, close=1.5, volume=10.0)
        assert c.to_canonical() == ('{"close":1.5000000000,"high":2.0000000000,"low":0.5000000000,"open":1.0000000000,"timeframe":"M1","timestamp":"2026-01-01T00:00:00","volume":10.0000000000}')


# ── BaseObject round-trips ──────────────────────────────────────────────────


class TestBaseObjectRoundTrip:
    def test_market_data_round_trip(self):
        md = market_data_request(10)
        back = MarketDataRequest.from_base_object(md.to_base_object())
        assert back == md

    def test_simulation_round_trip(self):
        req = simulation_request(15)
        back = SimulationRequest.from_base_object(req.to_base_object())
        assert back == req

    def test_backtest_round_trip(self):
        req = backtest_request(12)
        back = BacktestRequest.from_base_object(req.to_base_object())
        assert back == req

    def test_result_round_trip(self, backend):
        raw = backend._cpp.statistics_compute(StatisticsRequest(data=[1.0, 2.0, 3.0]).to_base_object())
        r = StatisticsResult.from_base_object(raw)
        assert r.to_base_object() == raw

    def test_dict_is_acceptable_request(self, backend):
        d = market_data_request(5).to_base_object()
        res = backend.market_data_load(d)
        assert isinstance(res, MarketDataResult)
        assert res.valid


# ── hash consistency (Python must reproduce C++ digests) ────────────────────


class TestHashConsistency:
    def test_statistics_input_hash_matches(self, backend):
        req = StatisticsRequest(data=[1.0, 2.0, 3.0, 4.0, 5.0])
        res = backend.statistics_compute(req)
        assert res.input_hash == req.compute_input_hash()
        assert res.result_hash == res.compute_result_hash()

    def test_statistics_result_hash_recomputed(self, backend):
        res = backend.statistics_compute(StatisticsRequest(data=[2.0, 4.0, 6.0]))
        assert res.result_hash == StatisticsResult.from_base_object(res.to_base_object()).compute_result_hash()

    def test_simulation_input_hash_matches(self, backend):
        req = simulation_request(25)
        res = backend.simulation_run(req)
        assert res.input_hash == req.compute_input_hash()
        assert res.result_hash == res.compute_result_hash()

    def test_simulation_id_derived_from_hash(self, backend):
        res = backend.simulation_run(simulation_request(10))
        assert res.simulation_id == "sim_" + res.input_hash[:16]

    def test_risk_hash_matches(self, backend):
        req = RiskRequest(returns=[0.01, -0.02, 0.03], equity_curve=[100, 102, 99])
        res = backend.risk_compute(req)
        assert res.input_hash == req.compute_input_hash()
        assert res.result_hash == res.compute_result_hash()

    def test_market_data_hash_matches(self, backend):
        req = market_data_request(15)
        res = backend.market_data_load(req)
        assert res.input_hash == req.compute_input_hash()
        assert res.result_hash == res.compute_result_hash()

    def test_backtest_hash_matches(self, backend):
        req = backtest_request(15)
        res = backend.backtest_run(req)
        assert res.input_hash == req.compute_input_hash()
        assert res.result_hash == res.compute_result_hash()

    def test_performance_hash_matches(self, backend):
        req = PerformanceRequest(equity_curve=[100.0, 101.0, 102.0], initial_capital=100.0)
        res = backend.performance_analyze(req)
        assert res.input_hash == req.compute_input_hash()
        assert res.result_hash == res.compute_result_hash()

    def test_hash_differs_when_data_changes(self, backend):
        a = StatisticsRequest(data=[1.0, 2.0, 3.0]).compute_input_hash()
        b = StatisticsRequest(data=[1.0, 2.0, 3.001]).compute_input_hash()
        assert a != b

    def test_hash_differs_when_calc_version_changes(self):
        a = StatisticsRequest(data=[1.0, 2.0], calculation_version="CALCULATION_V1").compute_input_hash()
        b = StatisticsRequest(data=[1.0, 2.0], calculation_version="CALCULATION_V2").compute_input_hash()
        assert a != b

    def test_large_dataset_hash_stable(self, backend):
        req = market_data_request(5000)
        r1 = backend.market_data_load(req)
        r2 = backend.market_data_load(MarketDataRequest.from_base_object(req.to_base_object()))
        assert r1.result_hash == r2.result_hash


# ── statistics ──────────────────────────────────────────────────────────────


class TestStatistics:
    def test_known_mean_variance(self, backend):
        res = backend.statistics_compute(StatisticsRequest(data=[1.0, 2.0, 3.0, 4.0, 5.0]))
        assert res.count == 5
        assert res.mean == pytest.approx(3.0)
        assert res.variance == pytest.approx(2.0)
        assert res.stddev == pytest.approx(math.sqrt(2.0))
        assert res.min == 1.0
        assert res.max == 5.0

    def test_quantiles(self, backend):
        res = backend.statistics_compute(StatisticsRequest(data=list(range(1, 11))))
        assert res.q1 == pytest.approx(3.25)
        assert res.median == pytest.approx(5.5)
        assert res.q3 == pytest.approx(7.75)

    def test_facade(self):
        res = Statistics.compute([1.0, 2.0, 3.0, 4.0])
        assert res.mean == pytest.approx(2.5)

    def test_empty_raises(self, backend):
        with pytest.raises(InsufficientDataError):
            backend.statistics_compute(StatisticsRequest(data=[]))

    def test_single_point_raises(self, backend):
        with pytest.raises(InsufficientDataError):
            backend.statistics_compute(StatisticsRequest(data=[1.0]))

    def test_nan_raises(self, backend):
        with pytest.raises(InvalidParameterError):
            backend.statistics_compute(StatisticsRequest(data=[1.0, float("nan")]))

    def test_inf_raises(self, backend):
        with pytest.raises(InvalidParameterError):
            backend.statistics_compute(StatisticsRequest(data=[1.0, float("inf")]))

    def test_deterministic(self, backend):
        req = StatisticsRequest(data=[1.5, -2.0, 0.25, 3.75])
        assert backend.statistics_compute(req).result_hash == backend.statistics_compute(req).result_hash


# ── risk ────────────────────────────────────────────────────────────────────


class TestRisk:
    def test_drawdown_magnitude(self, backend):
        res = backend.risk_compute(RiskRequest(returns=[0.01, -0.02, 0.03], equity_curve=[100.0, 105.0, 102.0, 99.0, 101.0]))
        assert res.max_drawdown_pct == pytest.approx(5.7142857143, rel=1e-6)
        assert res.peak_index == 1
        assert res.trough_index == 3

    def test_var_cvar_present(self, backend):
        res = backend.risk_compute(RiskRequest(returns=[0.02, -0.05, 0.01, -0.03, 0.0, -0.04], equity_curve=[100.0, 101.0, 102.0]))
        assert res.var_95 > 0.0
        assert res.var_99 > 0.0
        assert res.cvar_95 > 0.0

    def test_facade(self):
        res = Risk.compute(returns=[0.01, -0.01, 0.02], equity_curve=[100.0, 101.0, 100.0])
        assert res.max_drawdown_pct >= 0.0

    def test_empty_returns_raises(self, backend):
        with pytest.raises(InsufficientDataError):
            backend.risk_compute(RiskRequest(returns=[], equity_curve=[100.0]))


# ── simulation ──────────────────────────────────────────────────────────────


class TestSimulation:
    def test_shape(self, backend):
        res = backend.simulation_run(simulation_request(20))
        assert len(res.returns) == 19
        assert len(res.equity_curve) == 20
        assert res.equity_curve[0] == pytest.approx(100_000.0)

    def test_equity_from_capital(self, backend):
        req = SimulationRequest(dataset_reference="T", initial_capital=1000.0, prices=[100.0, 110.0, 99.0])
        res = backend.simulation_run(req)
        assert res.equity_curve == pytest.approx([1000.0, 1100.0, 990.0])
        assert res.metrics["total_return_pct"] == pytest.approx(-1.0)

    def test_metrics_statistics_performance(self, backend):
        res = backend.simulation_run(simulation_request(30))
        assert "final_equity" in res.metrics
        assert "mean" in res.statistics
        assert "max_drawdown_pct" in res.performance
        assert len(res.performance) > 0

    def test_facade(self, backend):
        req = simulation_request(10)
        res = Simulation.run(req)
        assert res.simulation_id.startswith("sim_")

    def test_too_few_prices_raises(self, backend):
        with pytest.raises(InsufficientDataError):
            backend.simulation_run(SimulationRequest(dataset_reference="X", prices=[100.0]))

    def test_non_positive_capital_raises(self, backend):
        with pytest.raises(InvalidParameterError):
            backend.simulation_run(SimulationRequest(dataset_reference="X", initial_capital=0.0, prices=[100.0, 101.0]))

    def test_empty_dataset_reference_raises(self, backend):
        with pytest.raises(InvalidParameterError):
            backend.simulation_run(SimulationRequest(prices=[100.0, 101.0]))


# ── market data ─────────────────────────────────────────────────────────────


class TestMarketData:
    def test_load_valid(self, backend):
        res = backend.market_data_load(market_data_request(50))
        assert res.valid
        assert res.size == 50
        assert res.symbol == "EURUSD"
        assert res.first_timestamp.startswith("1970-01-01T00:00:00")
        assert res.last_timestamp.startswith("1970-01-01T00:49:00")

    def test_load_timeframe(self, backend):
        res = backend.market_data_load(market_data_request(10, tf="H1"))
        assert res.timeframe == "H1"
        assert res.valid

    def test_empty_symbol_raises(self, backend):
        with pytest.raises(InvalidParameterError):
            backend.market_data_load(MarketDataRequest(symbol="", candles=make_candles(3)))

    def test_empty_candles_raises(self, backend):
        with pytest.raises(EmptyDataError):
            backend.market_data_load(MarketDataRequest(symbol="EURUSD", candles=[]))

    def test_bad_timeframe_raises(self, backend):
        with pytest.raises(InvalidParameterError):
            backend.market_data_load(MarketDataRequest(symbol="EURUSD", timeframe="M7", candles=make_candles(3)))

    def test_bad_ohlc_raises(self, backend):
        candles = make_candles(3)
        candles[1].high = 0.0  # high < low
        with pytest.raises(MalformedDataError):
            backend.market_data_load(MarketDataRequest(symbol="EURUSD", candles=candles))

    def test_duplicate_timestamp_raises(self, backend):
        candles = make_candles(4)
        candles[3].timestamp = candles[2].timestamp
        with pytest.raises(MalformedDataError):
            backend.market_data_load(MarketDataRequest(symbol="EURUSD", candles=candles))

    def test_market_data_facade(self, backend):
        md = MarketData(symbol="EURUSD", candles=make_candles(8))
        res = backend.market_data_load(md)
        assert res.valid
        assert md.compute_input_hash() == md.to_request().compute_input_hash()


# ── backtest ────────────────────────────────────────────────────────────────


def buy_uptick_signal(bar_index, history):
    if not history:
        return {"direction": 0, "quantity": 0.0}
    last = history[-1]
    if last["close"] > last["open"]:
        return {"direction": 0, "quantity": 1.0}
    return {"direction": 0, "quantity": 0.0}


class TestBacktest:
    def test_no_signal_no_trades(self, backend):
        res = backend.backtest_run(backtest_request(60))
        assert res.total_bars == 60
        assert len(res.equity_curve) == 60
        assert len(res.drawdown_curve) == 60
        assert res.num_trades == 0
        assert res.final_equity == pytest.approx(100_000.0)

    def test_with_signal_trades(self, backend):
        res = backend.backtest_run(backtest_request(200), signal=buy_uptick_signal)
        assert res.num_trades > 0
        assert res.signal_reference == ""

    def test_signal_reference_recorded(self, backend):
        req = backtest_request(30)
        req.signal_reference = "strategy://v1"
        res = backend.backtest_run(req)
        assert res.signal_reference == "strategy://v1"

    def test_backtest_deterministic(self, backend):
        req = backtest_request(150)
        a = backend.backtest_run(req, signal=buy_uptick_signal)
        b = backend.backtest_run(BacktestRequest.from_base_object(req.to_base_object()), signal=buy_uptick_signal)
        assert a.equity_curve == b.equity_curve
        assert a.result_hash == b.result_hash

    def test_engine_facade(self):
        engine = BacktestEngine()
        res = engine.run(MarketData(symbol="BTCUSD", candles=make_candles(50)), signal_reference="facade")
        assert res.total_bars == 50

    def test_engine_facade_with_signal(self):
        engine = BacktestEngine()
        res = engine.run(MarketData(symbol="BTCUSD", candles=make_candles(120)), signal=buy_uptick_signal)
        assert res.num_trades > 0

    def test_empty_candles_raises(self, backend):
        with pytest.raises(EmptyDataError):
            backend.backtest_run(BacktestRequest(symbol="BTCUSD", candles=[]))

    def test_bad_commission_raises(self, backend):
        req = backtest_request(5)
        req.commission_pct = 2.0
        with pytest.raises(InvalidParameterError):
            backend.backtest_run(req)

    def test_negative_slippage_raises(self, backend):
        req = backtest_request(5)
        req.slippage_pct = -0.01
        with pytest.raises(InvalidParameterError):
            backend.backtest_run(req)

    def test_empty_symbol_raises(self, backend):
        with pytest.raises(InvalidParameterError):
            backend.backtest_run(BacktestRequest(symbol="", candles=make_candles(3)))


# ── performance ─────────────────────────────────────────────────────────────


class TestPerformance:
    def test_total_return(self, backend):
        res = backend.performance_analyze(PerformanceRequest(equity_curve=[100.0, 110.0, 99.0, 108.9], initial_capital=100.0))
        assert res.total_return == pytest.approx(8.9)
        assert res.total_return_pct == pytest.approx(8.9)

    def test_drawdown_present(self, backend):
        res = backend.performance_analyze(PerformanceRequest(equity_curve=[100.0, 110.0, 99.0, 108.9, 119.79], initial_capital=100.0))
        assert res.max_drawdown_pct > 0.0

    def test_downside_fields_present(self, backend):
        res = backend.performance_analyze(PerformanceRequest(equity_curve=[100.0, 90.0, 95.0, 85.0], initial_capital=100.0))
        assert res.downside_deviation_annualized >= 0.0
        assert res.var_95 != 0.0 or res.cvar_95 != 0.0

    def test_buckets_with_bars(self, backend):
        eq = []
        for i in range(500):
            v = 100.0 + i
            if 200 <= i < 300:
                v -= 50.0
            eq.append(v)
        res = backend.performance_analyze(PerformanceRequest(equity_curve=eq, bars=make_candles(500, tf="D1"), initial_capital=100.0))
        assert res.num_yearly_periods > 0
        assert res.num_monthly_periods > 0
        assert res.max_drawdown_recovery_bars > 0

    def test_empty_equity_raises(self, backend):
        with pytest.raises(InsufficientDataError):
            backend.performance_analyze(PerformanceRequest(equity_curve=[]))

    def test_performance_report_alias(self):
        assert cq.PerformanceReport is PerformanceResult


# ── type conversion / invalid types ─────────────────────────────────────────


class TestTypeConversion:
    def test_ints_accepted_as_floats(self, backend):
        res = backend.statistics_compute(StatisticsRequest(data=[1, 2, 3, 4]))
        assert res.count == 4

    def test_extra_keys_ignored(self, backend):
        d = StatisticsRequest(data=[1.0, 2.0]).to_base_object()
        d["bogus"] = "ignored"
        assert backend.statistics_compute(d).count == 2

    def test_wrong_type_raises_invalid_type(self, backend):
        with pytest.raises(InvalidTypeError):
            backend.statistics_compute(StatisticsRequest(data="not a list"))

    def test_none_data_raises(self, backend):
        with pytest.raises(InvalidTypeError):
            backend.statistics_compute(StatisticsRequest(data=None))

    def test_backtest_rejects_bad_market_data_type(self):
        engine = BacktestEngine()
        with pytest.raises(InvalidTypeError):
            engine.run(12345)

    def test_coerce_dict_request(self, backend):
        d = {"data": [1.0, 2.0, 3.0, 4.0, 5.0], "calculation_version": "CALCULATION_V1"}
        res = backend.statistics_compute(d)
        assert res.mean == pytest.approx(3.0)


# ── exceptions ──────────────────────────────────────────────────────────────


class TestExceptions:
    def test_error_from_code_maps_types(self):
        assert isinstance(error_from_code(100, "m"), cq.InvalidArgumentError)
        assert isinstance(error_from_code(201, "m"), cq.EmptyDataError)
        assert isinstance(error_from_code(300, "m"), cq.UnsupportedVersionError)
        assert isinstance(error_from_code(302, "m"), cq.HashMismatchError)
        assert isinstance(error_from_code(999, "m"), cq.BridgeError)

    def test_exception_code_attribute(self, backend):
        with pytest.raises(cq.UnsupportedVersionError) as excinfo:
            backend.statistics_compute(StatisticsRequest(data=[1.0, 2.0], calculation_version="CALCULATION_V9"))
        assert excinfo.value.code == 300

    def test_native_error_translated(self, backend):
        with pytest.raises(cq.InsufficientDataError):
            backend.simulation_run(SimulationRequest(dataset_reference="X", prices=[1.0]))

    def test_hash_mismatch_raises_typed(self):
        with pytest.raises(HashMismatchError):
            raise HashMismatchError("tampered")

    def test_bridge_error_base_class(self):
        assert issubclass(cq.InvalidParameterError, cq.BridgeError)
        assert issubclass(cq.BridgeError, RuntimeError)


# ── large datasets ──────────────────────────────────────────────────────────


class TestLargeDatasets:
    def test_large_market_data(self, backend):
        res = backend.market_data_load(market_data_request(100_000))
        assert res.valid
        assert res.size == 100_000

    def test_large_simulation(self, backend):
        req = SimulationRequest(dataset_reference="XAUUSD", prices=make_prices(100_000))
        res = backend.simulation_run(req)
        assert len(res.equity_curve) == 100_000
        assert len(res.returns) == 99_999
        assert len(res.result_hash) == 64

    def test_large_backtest(self, backend):
        req = backtest_request(100_000, symbol="BTCUSD")
        res = backend.backtest_run(req)
        assert res.total_bars == 100_000
        assert len(res.equity_curve) == 100_000

    def test_large_performance(self, backend):
        res = backend.performance_analyze(PerformanceRequest(equity_curve=make_prices(100_000, base=1000.0), initial_capital=1000.0))
        assert res.result_hash
        assert res.max_drawdown_recovery_bars >= 0


# ── legacy shim (backward compatibility) ────────────────────────────────────


class TestLegacyShim:
    def test_legacy_returns_percentage(self):
        legacy = native_module().CppQuantBackend()
        out = legacy.calculate_returns([100.0, 110.0], "percentage")
        assert out == pytest.approx([0.1])

    def test_legacy_returns_absolute(self):
        legacy = native_module().CppQuantBackend()
        assert legacy.calculate_returns([100.0, 110.0], "absolute") == pytest.approx([10.0])

    def test_legacy_mean(self):
        legacy = native_module().CppQuantBackend()
        assert legacy.mean([1.0, 2.0, 3.0]) == pytest.approx(2.0)

    def test_legacy_stddev(self):
        legacy = native_module().CppQuantBackend()
        assert legacy.std_dev([1.0, 2.0, 3.0]) == pytest.approx(1.0)

    def test_legacy_variance(self):
        legacy = native_module().CppQuantBackend()
        assert legacy.variance([1.0, 2.0, 3.0]) == pytest.approx(1.0)

    def test_legacy_volatility_empty_raises(self):
        legacy = native_module().CppQuantBackend()
        with pytest.raises(Exception):
            legacy.calculate_volatility([])

    def test_legacy_drawdown(self):
        legacy = native_module().CppQuantBackend()
        dd = legacy.calculate_drawdown([100.0, 105.0, 102.0, 99.0])
        assert dd["max_drawdown_pct"] == pytest.approx(-5.7142857143, rel=1e-6)


# ── determinism / audit ─────────────────────────────────────────────────────


class TestDeterminism:
    def test_simulation_execution_timestamp_present(self, backend):
        res = backend.simulation_run(simulation_request(5))
        assert res.execution_timestamp
        assert len(res.execution_timestamp) == 19

    def test_simulation_id_stable(self, backend):
        a = backend.simulation_run(simulation_request(12))
        b = backend.simulation_run(simulation_request(12))
        assert a.simulation_id == b.simulation_id

    def test_repeat_runs_identical(self, backend):
        req = market_data_request(200)
        a = backend.market_data_load(req)
        b = backend.market_data_load(req)
        assert a.result_hash == b.result_hash
