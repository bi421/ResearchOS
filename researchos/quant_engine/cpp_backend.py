"""
CppQuantAdapter — QuantComputationInterface implementation backed by the C++ engine.

The adapter delegates numerical computation to the compiled C++20 quant engine
through the native module loader (``cpp_quant_engine.backend.native_module``),
while presenting results through the ResearchOS data contract
(``SimulationResult`` / ``SimulationRequest``).

The native module loader is the single integration point for the compiled C++
backend. The legacy ``CppQuantBackend`` shim is required by this adapter; if a
native module is present but does not export that shim, the installation is
considered stale/incompatible rather than silently treated as an unavailable
C++ engine.
"""

from __future__ import annotations

import warnings
from typing import Any

from researchos.core.timestamp import utc_now
from researchos.quant_engine.capabilities import QUANT_OPERATIONS, BackendCapabilities
from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.models import CalculationVersion, SimulationRequest, SimulationResult
from researchos.quant_engine.performance import compute_performance_analytics

CALCULATION_V1 = CalculationVersion.CALCULATION_V1
_PERIODS_PER_YEAR = 252


def _require_v1(calculation_version: CalculationVersion) -> None:
    if calculation_version != CALCULATION_V1:
        raise ValueError(f"Unsupported calculation version: {calculation_version}")


def _get_native_module() -> Any:
    from cpp_quant_engine.backend import native_module
    return native_module()


def _get_native_backend_class() -> Any:
    """Resolve the legacy numerical C++ shim used by this adapter.

    The current nanobind binary exports both ``Backend`` (typed bridge API) and
    ``CppQuantBackend`` (ResearchOS QuantComputationInterface compatibility
    shim).  Seeing the native module without the latter means the local .pyd is
    stale relative to the source tree and must be rebuilt.
    """
    module = _get_native_module()
    backend_class = getattr(module, "CppQuantBackend", None)
    if backend_class is None:
        version = getattr(module, "Backend", None)
        version_text = "unknown"
        if version is not None:
            try:
                version_text = str(version().version())
            except Exception:
                pass
        raise ImportError(
            "Loaded cpp_quant_backend native module is stale/incompatible: "
            "CppQuantBackend export is missing "
            f"(native Backend version={version_text}). Rebuild cpp_quant_engine."
        )
    return backend_class


def has_cpp_engine() -> bool:
    """Return True only when the required compiled C++ shim is importable."""
    try:
        _get_native_backend_class()
        return True
    except (ImportError, AttributeError, OSError):
        return False


def get_cpp_engine_version() -> str | None:
    """Return the C++ engine version, or None if the adapter shim is unavailable."""
    try:
        return str(_get_native_backend_class()().get_version())
    except (ImportError, AttributeError, OSError):
        return None


class CppQuantAdapter(QuantComputationInterface):
    """ResearchOS computation backend backed by the compiled C++20 quant engine."""

    def __init__(self) -> None:
        self._cpp_backend = None
        self._fallback = None
        try:
            backend_class = _get_native_backend_class()
            self._cpp_backend = backend_class()
        except (ImportError, AttributeError, OSError) as exc:
            warnings.warn(
                f"C++ Quant Engine unavailable or stale ({exc}). Falling back to PythonQuantBackend.",
                stacklevel=2,
            )
            from researchos.quant_engine.backend import PythonQuantBackend
            self._fallback = PythonQuantBackend()

    @property
    def is_cpp(self) -> bool:
        return self._cpp_backend is not None

    @property
    def _backend(self) -> Any:
        if self._cpp_backend is not None:
            return self._cpp_backend
        if self._fallback is not None:
            return self._fallback
        raise RuntimeError("No backend available")

    def get_version(self) -> str:
        if self._cpp_backend is not None:
            return str(self._backend.get_version())
        return "python_fallback"

    def capabilities(self) -> BackendCapabilities:
        return BackendCapabilities(
            backend_name="CppQuantAdapter",
            version=self.get_version(),
            supported_operations=QUANT_OPERATIONS,
            deterministic=True,
            stateless=True,
            no_timestamps=True,
            no_randomness=True,
            explicit_typing=True,
        )

    def _call(self, fn: Any, *args: Any) -> Any:
        try:
            return fn(*args)
        except RuntimeError as exc:
            raise ValueError(str(exc)) from None

    @staticmethod
    def _normalize_statistics(statistics: dict[str, Any]) -> dict[str, Any]:
        out = dict(statistics)
        if "count" in out:
            out["count"] = int(out["count"])
        return out

    @staticmethod
    def _normalize_metrics(metrics: dict[str, Any]) -> dict[str, float]:
        out: dict[str, float] = {key: float(value) for key, value in metrics.items()}
        if "max_drawdown" in out:
            out["max_drawdown"] = round(out["max_drawdown"], 8)
        if "max_drawdown" in out and "mean_return" in out and out["max_drawdown"] != 0.0:
            out["calmar_ratio"] = out["mean_return"] * _PERIODS_PER_YEAR / abs(out["max_drawdown"])
        return out

    @staticmethod
    def _normalize_drawdown(drawdown: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if "max_drawdown" in drawdown:
            out["max_drawdown"] = float(drawdown["max_drawdown"])
        if "max_drawdown_pct" in drawdown:
            out["max_drawdown_pct"] = float(drawdown["max_drawdown_pct"])
        if "recovery_period" in drawdown:
            out["recovery_period"] = int(drawdown["recovery_period"])
        return out

    def calculate_returns(self, prices: list[float], return_type: str = "percentage", calculation_version: CalculationVersion = CALCULATION_V1) -> list[float]:
        _require_v1(calculation_version)
        if len(prices) < 2:
            raise ValueError(f"Need at least 2 prices to calculate returns, got {len(prices)}")
        if return_type not in ("absolute", "percentage", "log"):
            raise ValueError(f"Unrecognized return_type '{return_type}'. Expected 'absolute', 'percentage', or 'log'.")
        return list(self._call(self._backend.calculate_returns, prices, return_type))

    def calculate_volatility(self, returns: list[float], method: str = "standard_deviation", calculation_version: CalculationVersion = CALCULATION_V1) -> float:
        _require_v1(calculation_version)
        if not returns:
            raise ValueError("Cannot compute volatility on empty dataset")
        if method not in ("standard_deviation", "rolling", "change"):
            raise ValueError(f"Unrecognized method '{method}'. Expected 'standard_deviation', 'rolling', or 'change'.")
        return float(self._call(self._backend.calculate_volatility, returns, method))

    def calculate_drawdown(self, equity_curve: list[float], calculation_version: CalculationVersion = CALCULATION_V1) -> dict[str, Any]:
        _require_v1(calculation_version)
        if len(equity_curve) < 2:
            raise ValueError(f"Need at least 2 equity values, got {len(equity_curve)}")
        return self._normalize_drawdown(dict(self._call(self._backend.calculate_drawdown, equity_curve)))

    def calculate_statistics(self, returns: list[float], calculation_version: CalculationVersion = CALCULATION_V1) -> dict[str, Any]:
        _require_v1(calculation_version)
        if not returns:
            raise ValueError("Cannot compute statistics on empty dataset")
        return self._normalize_statistics(dict(self._call(self._backend.calculate_statistics, returns)))

    def calculate_metrics(self, returns: list[float], equity_curve: list[float], risk_free_rate: float = 0.0, calculation_version: CalculationVersion = CALCULATION_V1) -> dict[str, float]:
        _require_v1(calculation_version)
        if not returns:
            raise ValueError("Cannot compute statistics on empty dataset")
        if len(returns) < 2:
            raise ValueError(f"Insufficient samples: need at least 2, got {len(returns)}")
        if len(equity_curve) < 2:
            raise ValueError(f"Need at least 2 equity values, got {len(equity_curve)}")
        raw = dict(self._call(self._backend.calculate_metrics, returns, equity_curve, risk_free_rate))
        return self._normalize_metrics(raw)

    def calculate_performance_analytics(self, returns: list[float], calculation_version: CalculationVersion = CALCULATION_V1) -> dict[str, Any]:
        _require_v1(calculation_version)
        if not returns:
            raise ValueError("Cannot compute performance analytics on empty dataset")
        raw = dict(self._call(self._backend.calculate_performance_analytics, returns))
        return {key: float(value) for key, value in raw.items()}

    def run_simulation(self, request: SimulationRequest, prices: list[float] | None = None, calculation_version: CalculationVersion = CALCULATION_V1) -> SimulationResult:
        _require_v1(calculation_version)
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
        raw = self._call(self._backend.run_simulation, request.to_dict(), request.prices)
        return SimulationResult.from_dict(raw)
