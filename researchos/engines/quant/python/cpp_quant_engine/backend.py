"""Python binding layer for the C++ Quant Engine.

``CppQuantEngineBackend`` mirrors the C++ ``IBridgeBackend`` contract 1:1 and
translates between typed model objects (models.py) and the plain-dict
BaseObject representation accepted/produced by the pybind11 module.

The facade classes (``Statistics``, ``BacktestEngine``, ``Simulation``,
``Risk``, ``MarketData``) provide ergonomic, stable entry points for the
ResearchOS Python layer. The numerical work always happens in C++; this module
only marshals data and never re-implements computations.

Signal contract (backtest)
--------------------------
``BacktestEngine.run`` accepts an optional ``signal`` callable:

    def signal(bar_index: int, history: List[dict]) -> dict:
        return {"direction": 0, "quantity": 1.0, "stop_loss": 0.0, "take_profit": 0.0}

where ``direction`` is 0 = Buy, 1 = Sell. The bridge transports the signal but
implements no trading logic; ``signal_reference`` is audit metadata.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from researchos.engines.quant.cpp_engine.exceptions import (
    BridgeError,
    InvalidTypeError,
)
from researchos.engines.quant.cpp_engine.models import (
    BacktestRequest,
    BacktestResult,
    MarketData,
    MarketDataRequest,
    MarketDataResult,
    PerformanceRequest,
    PerformanceResult,
    RiskRequest,
    RiskResult,
    SimulationRequest,
    SimulationResult,
    StatisticsRequest,
    StatisticsResult,
)

_native_module = None


def native_module():
    """Lazily import and cache the compiled pybind11 module."""
    global _native_module
    if _native_module is None:
        try:
            import cpp_quant_backend  # standalone install (site-packages)
        except ImportError:
            # In-package layout: python/cpp_quant_engine/cpp_quant_backend.pyd
            from researchos.engines.quant.cpp_engine import cpp_quant_backend
        _native_module = cpp_quant_backend
    return _native_module


def engine_version() -> str:
    return str(native_module().version())


def bridge_version() -> str:
    return str(native_module().bridge_version())


def protocol_version() -> int:
    return int(native_module().protocol_version())


def supported_calculation_versions() -> list[str]:
    return list(native_module().supported_calculation_versions())


def error_codes() -> dict[str, int]:
    return {str(k): int(v) for k, v in native_module().error_codes().items()}


# ── Typed backend ───────────────────────────────────────────────────────────


def _native_call(fn, *args):
    """Invoke a pybind11 method, normalizing type errors.

    BridgeError subclasses (raised by the C++ exception translator) pass
    through untouched; pybind11 cast/type failures surface as RuntimeError
    and are normalized to InvalidTypeError.
    """
    try:
        return fn(*args)
    except BridgeError:
        raise
    except (TypeError, ValueError, RuntimeError) as e:
        raise InvalidTypeError(str(e)) from None


class CppQuantEngineBackend:
    """Typed, production-grade Python facade over the C++ bridge."""

    def __init__(self) -> None:
        self._cpp = native_module().Backend()

    # ── Metadata ──────────────────────────────────────────────────────────

    def meta(self) -> dict[str, Any]:
        return dict(_native_call(self._cpp.meta))

    def version(self) -> str:
        return str(self._cpp.version())

    # ── MarketData ────────────────────────────────────────────────────────

    def market_data_load(self, request: MarketDataRequest | MarketData | dict[str, Any]) -> MarketDataResult:
        req = _coerce_request(request, MarketDataRequest)
        raw = _native_call(self._cpp.market_data_load, req.to_base_object())
        result = MarketDataResult.from_base_object(raw)
        _assert_result_hash(result, result.compute_result_hash())
        return result

    # ── Statistics ────────────────────────────────────────────────────────

    def statistics_compute(self, request: StatisticsRequest | dict[str, Any]) -> StatisticsResult:
        req = _coerce_request(request, StatisticsRequest)
        raw = _native_call(self._cpp.statistics_compute, req.to_base_object())
        result = StatisticsResult.from_base_object(raw)
        _assert_result_hash(result, result.compute_result_hash())
        return result

    # ── Risk ──────────────────────────────────────────────────────────────

    def risk_compute(self, request: RiskRequest | dict[str, Any]) -> RiskResult:
        req = _coerce_request(request, RiskRequest)
        raw = _native_call(self._cpp.risk_compute, req.to_base_object())
        result = RiskResult.from_base_object(raw)
        _assert_result_hash(result, result.compute_result_hash())
        return result

    # ── Simulation ────────────────────────────────────────────────────────

    def simulation_run(self, request: SimulationRequest | dict[str, Any]) -> SimulationResult:
        req = _coerce_request(request, SimulationRequest)
        raw = _native_call(self._cpp.simulation_run, req.to_base_object())
        result = SimulationResult.from_base_object(raw)
        _assert_result_hash(result, result.compute_result_hash())
        return result

    # ── Backtest ──────────────────────────────────────────────────────────

    def backtest_run(
        self,
        request: BacktestRequest | dict[str, Any],
        signal: Callable[..., dict[str, Any]] | None = None,
    ) -> BacktestResult:
        req = _coerce_request(request, BacktestRequest)
        raw = _native_call(self._cpp.backtest_run, req.to_base_object(), signal)
        result = BacktestResult.from_base_object(raw)
        _assert_result_hash(result, result.compute_result_hash())
        return result

    # ── Performance ───────────────────────────────────────────────────────

    def performance_analyze(self, request: PerformanceRequest | dict[str, Any]) -> PerformanceResult:
        req = _coerce_request(request, PerformanceRequest)
        raw = _native_call(self._cpp.performance_analyze, req.to_base_object())
        result = PerformanceResult.from_base_object(raw)
        _assert_result_hash(result, result.compute_result_hash())
        return result


def _coerce_request(request, cls):
    if isinstance(request, cls):
        return request
    if cls is MarketDataRequest and isinstance(request, MarketData):
        return request.to_request()
    if isinstance(request, dict):
        return cls.from_base_object(request)
    raise InvalidTypeError(f"expected {cls.__name__} or BaseObject dict, got {type(request).__name__}")


def _assert_result_hash(result, recomputed: str) -> None:
    from researchos.engines.quant.cpp_engine.exceptions import HashMismatchError

    if result.result_hash and recomputed != result.result_hash:
        raise HashMismatchError(f"bridge result hash mismatch: C++ produced {result.result_hash}, Python recomputed {recomputed}")


def default_backend() -> CppQuantEngineBackend:
    return CppQuantEngineBackend()


# ── Stable facade APIs ──────────────────────────────────────────────────────


class Statistics:
    """Descriptive statistics (delegates to the C++ engine)."""

    @staticmethod
    def compute(data: list[float], calculation_version: str = "CALCULATION_V1") -> StatisticsResult:
        return default_backend().statistics_compute(StatisticsRequest(data=list(data), calculation_version=calculation_version))


class Risk:
    """VaR / CVaR / drawdown / Sharpe / Sortino (delegates to C++)."""

    @staticmethod
    def compute(
        returns: list[float],
        equity_curve: list[float],
        risk_free_rate: float = 0.0,
        calculation_version: str = "CALCULATION_V1",
    ) -> RiskResult:
        return default_backend().risk_compute(
            RiskRequest(
                returns=list(returns),
                equity_curve=list(equity_curve),
                risk_free_rate=risk_free_rate,
                calculation_version=calculation_version,
            )
        )


class Simulation:
    """Deterministic historical simulation (delegates to C++)."""

    @staticmethod
    def run(
        request: SimulationRequest,
        prices: list[float] | None = None,
        calculation_version: str = "CALCULATION_V1",
    ) -> SimulationResult:
        if prices is not None:
            request = SimulationRequest(
                dataset_reference=request.dataset_reference,
                dataset_version=request.dataset_version,
                calculation_version=calculation_version,
                initial_capital=request.initial_capital,
                risk_free_rate=request.risk_free_rate,
                seed=request.seed,
                start_time=request.start_time,
                end_time=request.end_time,
                prices=list(prices),
            )
        return default_backend().simulation_run(request)


class BacktestEngine:
    """Backtest engine facade. The bridge implements no trading logic; the
    caller supplies an optional Python ``signal`` callable."""

    def __init__(
        self,
        backend: CppQuantEngineBackend | None = None,
        initial_capital: float = 100_000.0,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.0005,
        allow_short: bool = True,
        calculation_version: str = "CALCULATION_V1",
    ) -> None:
        self._backend = backend or default_backend()
        self._defaults = {
            "initial_capital": initial_capital,
            "commission_pct": commission_pct,
            "slippage_pct": slippage_pct,
            "allow_short": allow_short,
            "calculation_version": calculation_version,
        }

    def run(
        self,
        market_data: MarketData | MarketDataRequest | dict[str, Any],
        signal: Callable[..., dict[str, Any]] | None = None,
        signal_reference: str = "",
        **overrides: Any,
    ) -> BacktestResult:
        if isinstance(market_data, MarketData):
            base = market_data.to_request().to_base_object()
        elif isinstance(market_data, MarketDataRequest):
            base = market_data.to_base_object()
        elif isinstance(market_data, dict):
            base = dict(market_data)
        else:
            raise InvalidTypeError("market_data must be MarketData, MarketDataRequest, or a BaseObject dict")

        params = dict(self._defaults)
        params.update(overrides)
        base.update(params)
        base["signal_reference"] = signal_reference
        request = BacktestRequest.from_base_object(base)
        return self._backend.backtest_run(request, signal=signal)
