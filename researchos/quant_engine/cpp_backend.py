"""
CppQuantAdapter — QuantComputationInterface implementation backed by the C++ engine.

The adapter delegates all numerical computation to the compiled C++20 quant
engine through the legacy pybind11 shim (``cpp_quant_engine.cpp_quant_backend``),
while presenting results through the ResearchOS data contract
(``SimulationResult`` / ``SimulationRequest``).

Design:
    - ``CppQuantAdapter`` implements ``QuantComputationInterface`` exactly, so
      it can be swapped in via ``HistoricalSimulationEngine.set_backend(...)``
      with zero changes to upper layers.
    - Constructor signature matches ``PythonQuantBackend`` for drop-in use.
    - Falls back to ``PythonQuantBackend`` (with a warning) when the compiled
      module is not importable, so the interface never breaks.
    - ``calculate_performance_analytics`` and the ``performance`` field are
      computed by the ResearchOS reference implementation
      (``compute_performance_analytics``) so the ResearchOS schema is preserved
      regardless of the C++ performance analytics schema.
    - ResearchOS schema normalization is applied to C++ outputs:
        * ``statistics["count"]`` -> int
        * ``metrics["max_drawdown"]`` -> rounded to 8 decimal places
        * ``metrics["calmar_ratio"]`` -> recomputed from the rounded
          ``max_drawdown`` (ResearchOS definition)
        * ``drawdown["max_drawdown"]`` / ``max_drawdown_pct`` / ``recovery_period``
          -> ResearchOS precision / int
    - Validation contract mirrors ``PythonQuantBackend`` (``ValueError`` on
      empty / insufficient data, unsupported calculation version, unknown
      method), and residual C++ validation errors surface as ``ValueError``.

The legacy shim (``cpp_quant_engine/backend_wrapper.py``) is NOT modified; this
adapter is the ResearchOS-side integration point.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Optional

from researchos.core.timestamp import utc_now
from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)
from researchos.quant_engine.performance import compute_performance_analytics

CALCULATION_V1 = CalculationVersion.CALCULATION_V1

# Periods per year used by ResearchOS annualisation (CALCULATION_V1).
_PERIODS_PER_YEAR = 252


def _require_v1(calculation_version: CalculationVersion) -> None:
    if calculation_version != CALCULATION_V1:
        raise ValueError(f"Unsupported calculation version: {calculation_version}")


def has_cpp_engine() -> bool:
    """Return True if the compiled C++ quant engine module is importable."""
    try:
        from cpp_quant_engine.cpp_quant_backend import CppQuantBackend  # type: ignore[import-not-found]  # noqa: F401

        return True
    except (ImportError, AttributeError, OSError):
        return False


def get_cpp_engine_version() -> Optional[str]:
    """Return the C++ engine version string, or None if unavailable."""
    try:
        from cpp_quant_engine.cpp_quant_backend import CppQuantBackend  # type: ignore[import-not-found]

        return str(CppQuantBackend().get_version())
    except (ImportError, AttributeError, OSError):
        return None


class CppQuantAdapter(QuantComputationInterface):
    """
    ResearchOS computation backend backed by the compiled C++20 quant engine.

    Drop-in replacement for ``PythonQuantBackend``. All computation is delegated
    to C++ (returns, volatility, drawdown, statistics, metrics) except the
    performance analytics, which follow the ResearchOS reference implementation.
    """

    def __init__(self) -> None:
        self._cpp_backend = None
        self._fallback = None

        try:
            from cpp_quant_engine.cpp_quant_backend import CppQuantBackend  # type: ignore[import-not-found]

            self._cpp_backend = CppQuantBackend()
        except (ImportError, AttributeError, OSError) as exc:
            warnings.warn(
                f"C++ Quant Engine not available ({exc}). "
                "Falling back to PythonQuantBackend.",
                stacklevel=2,
            )
            from researchos.quant_engine.backend import PythonQuantBackend

            self._fallback = PythonQuantBackend()

    # ── Identity / availability ──────────────────────────────────────────────

    @property
    def is_cpp(self) -> bool:
        """True when the compiled C++ engine is active (no fallback)."""
        return self._cpp_backend is not None

    @property
    def _backend(self) -> Any:
        """The active computation delegate (C++ shim or Python fallback)."""
        if self._cpp_backend is not None:
            return self._cpp_backend
        if self._fallback is not None:
            return self._fallback
        raise RuntimeError("No backend available")

    def get_version(self) -> str:
        """Return the C++ engine version, or 'python_fallback' if unavailable."""
        if self._cpp_backend is not None:
            return str(self._backend.get_version())
        return "python_fallback"

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _call(self, fn: Any, *args: Any) -> Any:
        """
        Invoke a C++ shim method, translating validation failures to ValueError
        to honor the QuantComputationInterface contract.
        """
        try:
            return fn(*args)
        except RuntimeError as exc:  # legacy shim raises RuntimeError on validation
            raise ValueError(str(exc)) from None

    @staticmethod
    def _normalize_statistics(statistics: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(statistics)
        if "count" in out:
            out["count"] = int(out["count"])
        return out

    @staticmethod
    def _normalize_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
        out: Dict[str, float] = {k: float(v) for k, v in metrics.items()}
        if "max_drawdown" in out:
            out["max_drawdown"] = round(out["max_drawdown"], 8)
        if "max_drawdown" in out and "mean_return" in out and out["max_drawdown"] != 0.0:
            out["calmar_ratio"] = (
                out["mean_return"] * _PERIODS_PER_YEAR / abs(out["max_drawdown"])
            )
        return out

    @staticmethod
    def _normalize_drawdown(drawdown: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if "max_drawdown" in drawdown:
            out["max_drawdown"] = round(float(drawdown["max_drawdown"]), 8)
        if "max_drawdown_pct" in drawdown:
            out["max_drawdown_pct"] = round(float(drawdown["max_drawdown_pct"]), 6)
        if "recovery_period" in drawdown:
            out["recovery_period"] = int(drawdown["recovery_period"])
        return out

    # ── Returns ──────────────────────────────────────────────────────────────

    def calculate_returns(
        self,
        prices: List[float],
        return_type: str = "percentage",
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> List[float]:
        _require_v1(calculation_version)

        if len(prices) < 2:
            raise ValueError(
                f"Need at least 2 prices to calculate returns, got {len(prices)}"
            )
        if return_type not in ("absolute", "percentage", "log"):
            raise ValueError(
                f"Unrecognized return_type '{return_type}'. "
                "Expected 'absolute', 'percentage', or 'log'."
            )

        return list(self._call(self._backend.calculate_returns, prices, return_type))

    # ── Volatility ───────────────────────────────────────────────────────────

    def calculate_volatility(
        self,
        returns: List[float],
        method: str = "standard_deviation",
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> float:
        _require_v1(calculation_version)

        if not returns:
            raise ValueError("Cannot compute volatility on empty dataset")
        if method not in ("standard_deviation", "rolling", "change"):
            raise ValueError(
                f"Unrecognized method '{method}'. "
                "Expected 'standard_deviation', 'rolling', or 'change'."
            )

        return float(self._call(self._backend.calculate_volatility, returns, method))

    # ── Drawdown ─────────────────────────────────────────────────────────────

    def calculate_drawdown(
        self,
        equity_curve: List[float],
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> Dict[str, Any]:
        _require_v1(calculation_version)

        if len(equity_curve) < 2:
            raise ValueError(
                f"Need at least 2 equity values, got {len(equity_curve)}"
            )

        return self._normalize_drawdown(
            dict(self._call(self._backend.calculate_drawdown, equity_curve))
        )

    # ── Statistics ───────────────────────────────────────────────────────────

    def calculate_statistics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> Dict[str, Any]:
        _require_v1(calculation_version)

        if not returns:
            raise ValueError("Cannot compute statistics on empty dataset")

        return self._normalize_statistics(
            dict(self._call(self._backend.calculate_statistics, returns))
        )

    # ── Metrics ──────────────────────────────────────────────────────────────

    def calculate_metrics(
        self,
        returns: List[float],
        equity_curve: List[float],
        risk_free_rate: float = 0.0,
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> Dict[str, float]:
        _require_v1(calculation_version)

        if not returns:
            raise ValueError("Cannot compute statistics on empty dataset")
        if len(returns) < 2:
            raise ValueError(
                f"Insufficient samples: need at least 2, got {len(returns)}"
            )
        if len(equity_curve) < 2:
            raise ValueError(
                f"Need at least 2 equity values, got {len(equity_curve)}"
            )

        raw = dict(
            self._call(
                self._backend.calculate_metrics,
                returns,
                equity_curve,
                risk_free_rate,
            )
        )
        return self._normalize_metrics(raw)

    # ── Performance Analytics (ResearchOS reference) ─────────────────────────

    def calculate_performance_analytics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> Dict[str, Any]:
        return compute_performance_analytics(returns, calculation_version)

    # ── Simulation ───────────────────────────────────────────────────────────

    def run_simulation(
        self,
        request: SimulationRequest,
        prices: List[float],
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> SimulationResult:
        _require_v1(calculation_version)

        if len(prices) < 2:
            raise ValueError(
                f"Need at least 2 prices for simulation, got {len(prices)}"
            )

        # Provenance from the ResearchOS request (not the C++ hashes).
        input_hash = request.compute_input_hash()
        sim_id = f"sim_{input_hash[:16]}"

        initial_capital = request.parameters.get("initial_capital", 100000.0)
        risk_free_rate = request.parameters.get("risk_free_rate", 0.0)

        # Numerical work in C++. Composed from the shim's primitives (the
        # monolithic legacy run_simulation is not used: it is dramatically
        # slower on large series because it builds its own full result hash).
        returns = list(
            self._call(self._backend.calculate_returns, prices, "percentage")
        )
        equity_curve = self._build_equity_curve(returns, initial_capital)
        metrics = self._normalize_metrics(
            dict(
                self._call(
                    self._backend.calculate_metrics,
                    returns,
                    equity_curve,
                    risk_free_rate,
                )
            )
        )
        statistics = self._normalize_statistics(
            dict(self._call(self._backend.calculate_statistics, returns))
        )
        performance = compute_performance_analytics(returns, calculation_version)

        result = SimulationResult(
            simulation_id=sim_id,
            dataset_reference=request.dataset_reference,
            dataset_version=request.dataset_version,
            calculation_version=calculation_version,
            parameters=dict(request.parameters),
            start_time=request.start_time,
            end_time=request.end_time,
            input_hash=input_hash,
            execution_timestamp=utc_now().isoformat(),
            returns=returns,
            equity_curve=equity_curve,
            metrics=metrics,
            statistics=statistics,
            performance=performance,
        )
        result.result_hash = result.compute_result_hash()
        return result

    @staticmethod
    def _build_equity_curve(returns: List[float], initial_capital: float) -> List[float]:
        """Build an equity curve from percentage returns (ResearchOS semantics)."""
        equity = [initial_capital]
        for r in returns:
            equity.append(equity[-1] * (1.0 + r))
        return equity
