"""
CppQuantBackendWrapper — Python adapter implementing QuantComputationInterface.

This wrapper delegates all numerical computation to the C++20 backend
via pybind11. It implements the same QuantComputationInterface as
PythonQuantBackend, allowing transparent backend swapping.

Upper layers (Experiment Framework, Market Memory, Validation)
do NOT know which backend is running.

Design:
    - Delegates to C++ for all performance-critical calculations
    - Handles Python-level serialization (SimulationRequest/SimulationResult)
    - Falls back to Python if C++ library is not available
    - Maintains full audit compatibility
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)
from researchos.core.identity import deterministic_hash
from researchos.core.timestamp import utc_now


class CppQuantBackendWrapper(QuantComputationInterface):
    """
    Python wrapper that delegates numerical computation to the C++20 backend.

    If the C++ module (cpp_quant_backend) is not available, falls back to
    PythonQuantBackend for graceful degradation.
    """

    def __init__(self) -> None:
        self._cpp_backend = None
        self._fallback = None

        try:
            from cpp_quant_engine.cpp_quant_backend import CppQuantBackend
            self._cpp_backend = CppQuantBackend()
        except ImportError as e:
            import warnings
            warnings.warn(
                f"C++ Quant Engine not available ({e}). "
                "Falling back to PythonQuantBackend."
            )
            from researchos.quant_engine.backend import PythonQuantBackend
            self._fallback = PythonQuantBackend()

    @property
    def _backend(self):
        if self._cpp_backend is not None:
            return self._cpp_backend
        if self._fallback is not None:
            return self._fallback
        raise RuntimeError("No backend available")

    @property
    def is_cpp(self) -> bool:
        """Check if the C++ backend is active."""
        return self._cpp_backend is not None

    def get_version(self) -> str:
        if self._cpp_backend is not None:
            return self._cpp_backend.get_version()
        return "python_fallback"

    # ──────────────────────────────────────────────
    # Returns
    # ──────────────────────────────────────────────

    def calculate_returns(
        self,
        prices: List[float],
        return_type: str = "percentage",
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> List[float]:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")
        return list(self._backend.calculate_returns(prices, return_type))

    # ──────────────────────────────────────────────
    # Volatility
    # ──────────────────────────────────────────────

    def calculate_volatility(
        self,
        returns: List[float],
        method: str = "standard_deviation",
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> float:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")
        if not returns:
            raise ValueError("Cannot compute volatility on empty dataset")
        return float(self._backend.calculate_volatility(returns, method))

    # ──────────────────────────────────────────────
    # Drawdown
    # ──────────────────────────────────────────────

    def calculate_drawdown(
        self,
        equity_curve: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")
        result = self._backend.calculate_drawdown(equity_curve)
        return dict(result)

    # ──────────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────────

    def calculate_statistics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")
        result = self._backend.calculate_statistics(returns)
        return dict(result)

    # ──────────────────────────────────────────────
    # Metrics
    # ──────────────────────────────────────────────

    def calculate_metrics(
        self,
        returns: List[float],
        equity_curve: List[float],
        risk_free_rate: float = 0.0,
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, float]:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")
        result = self._backend.calculate_metrics(returns, equity_curve, risk_free_rate)
        return {k: float(v) for k, v in result.items()}

    # ──────────────────────────────────────────────
    # Performance Analytics
    # ──────────────────────────────────────────────

    def calculate_performance_analytics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> Dict[str, Any]:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")
        result = self._backend.calculate_performance_analytics(returns)
        return dict(result)

    # ──────────────────────────────────────────────
    # Simulation
    # ──────────────────────────────────────────────

    def run_simulation(
        self,
        request: SimulationRequest,
        prices: List[float],
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> SimulationResult:
        if calculation_version != CalculationVersion.CALCULATION_V1:
            raise ValueError(f"Unsupported calculation version: {calculation_version}")

        if len(prices) < 2:
            raise ValueError(
                f"Need at least 2 prices for simulation, got {len(prices)}"
            )

        # Compute input hash for provenance
        input_hash = request.compute_input_hash()

        # Generate simulation ID from request
        sim_id = f"sim_{input_hash[:16]}"

        # Build request dict for C++ backend
        cpp_request = {
            "dataset_reference": request.dataset_reference,
            "dataset_version": request.dataset_version,
            "calculation_version": request.calculation_version.value,
            "initial_capital": request.parameters.get("initial_capital", 100000.0),
            "risk_free_rate": request.parameters.get("risk_free_rate", 0.0),
            "seed": request.seed,
        }

        # Run simulation in C++
        result_dict = self._backend.run_simulation(cpp_request, prices)

        # Convert C++ result to SimulationResult
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
            returns=list(result_dict.get("returns", [])),
            equity_curve=list(result_dict.get("equity_curve", [])),
            metrics={k: float(v) for k, v in result_dict.get("metrics", {}).items()},
            statistics={k: float(v) for k, v in result_dict.get("statistics", {}).items()},
            performance={k: float(v) for k, v in result_dict.get("performance", {}).items()},
        )

        # Compute result hash
        result.result_hash = result.compute_result_hash()

        return result
