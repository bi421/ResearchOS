"""
ResearchCppBackend — certified candidate backend for the analytical surface.

Phase 5.1 — Certified Analytical Compute Surface (WP-1).

This module provides the C++ acceleration candidate for the certified research
analytical surface.  It mirrors ``PythonResearchBackend`` operation-for-
operation, but:

    * delegates the base ``QuantComputationInterface`` operations to the
      existing certified ``CppQuantAdapter`` (the C++20 engine), and
    * uses a deterministic Python fallback for the analytical functions that
      the C++ engine does not yet expose (technical, probability, portfolio,
      historical, fundamental, econometrics, validation).

Design principles:
    - C++ is an OPTIONAL certified acceleration candidate.  Python remains the
      scientific source of truth.  Every ResearchResult is identical to the
      Python reference output (deterministic, tolerance-certified).
    - No new algorithms are invented here; the candidate reuses the frozen
      ``CppQuantAdapter`` capability and the ``PythonResearchBackend``
      reference computations.
    - ``ResearchCppBackend`` subclasses BOTH ``ResearchComputationInterface``
      and ``QuantComputationInterface`` so it is registerable with the
      existing ``BackendRouter`` (which validates candidate output against the
      Python reference).
    - Benchmark scaffolding (Phase 5.4 will optimize): the candidate exposes
      ``is_cpp`` so benchmarks can prove the optional C++ acceleration path.

This is a certification/trust layer only — it computes no trading decisions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from researchos.quant_engine.backend_hash import canonicalize
from researchos.quant_engine.capabilities import BackendCapabilities, default_capabilities
from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)
from researchos.quant_engine.research_engine import PythonResearchBackend
from researchos.quant_engine.research_interface import (
    RESEARCH_SURFACE_VERSION,
    ResearchComputationInterface,
    ResearchResult,
)

CALCULATION_V1 = CalculationVersion.CALCULATION_V1


class ResearchCppBackend(ResearchComputationInterface, QuantComputationInterface):
    """
    Certified C++ acceleration candidate for the research analytical surface.

    Base quant ops delegate to ``CppQuantAdapter`` (C++20 engine) when the
    compiled module is available; otherwise they fall back to the Python
    reference.  Analytical ops (technical, probability, portfolio, historical,
    fundamental, econometrics, validation) delegate to the deterministic
    Python reference (the C++ engine has not yet certified those analytical
    surfaces — Phase 5.4 will optimize).
    """

    def __init__(self) -> None:
        self._python = PythonResearchBackend()
        self._cpp_adapter = None
        try:
            from researchos.quant_engine.cpp_backend import CppQuantAdapter

            adapter = CppQuantAdapter()
            if adapter.is_cpp:
                self._cpp_adapter = adapter
        except Exception:  # pragma: no cover - environment dependent
            self._cpp_adapter = None

    # ── identity / certification ────────────────────────────────────────

    @property
    def is_cpp(self) -> bool:
        """True when the compiled C++ engine is active (no fallback)."""
        return self._cpp_adapter is not None

    def get_version(self) -> str:
        if self._cpp_adapter is not None:
            return f"cpp_research_{self._cpp_adapter.get_version()}"
        return "python_fallback_research_1.0.0"

    def cpp_engine_version(self) -> Optional[str]:
        """Return the underlying C++ engine version, or None when inactive."""
        if self._cpp_adapter is not None:
            return str(self._cpp_adapter.get_version())
        return None

    def capabilities(self) -> BackendCapabilities:
        base = default_capabilities(self._python)
        return BackendCapabilities(
            backend_name="ResearchCppBackend",
            version=self.get_version(),
            supported_operations=base.supported_operations,
            deterministic=base.deterministic,
            stateless=base.stateless,
            no_timestamps=base.no_timestamps,
            no_randomness=base.no_randomness,
            explicit_typing=base.explicit_typing,
        )

    # ── 7 core QuantComputationInterface ops (C++ certified candidate) ──

    def calculate_returns(
        self,
        prices: List[float],
        return_type: str = "percentage",
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> List[float]:
        if self._cpp_adapter is not None:
            return self._cpp_adapter.calculate_returns(prices, return_type, calculation_version)
        return self._python.calculate_returns(prices, return_type, calculation_version)

    def calculate_volatility(
        self,
        returns: List[float],
        method: str = "standard_deviation",
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> float:
        if self._cpp_adapter is not None:
            return self._cpp_adapter.calculate_volatility(returns, method, calculation_version)
        return self._python.calculate_volatility(returns, method, calculation_version)

    def calculate_drawdown(
        self,
        equity_curve: List[float],
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> Dict[str, Any]:
        if self._cpp_adapter is not None:
            return self._cpp_adapter.calculate_drawdown(equity_curve, calculation_version)
        return self._python.calculate_drawdown(equity_curve, calculation_version)

    def calculate_statistics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> Dict[str, Any]:
        if self._cpp_adapter is not None:
            return self._cpp_adapter.calculate_statistics(returns, calculation_version)
        return self._python.calculate_statistics(returns, calculation_version)

    def run_simulation(
        self,
        request: SimulationRequest,
        dataset: Any,
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> SimulationResult:
        if self._cpp_adapter is not None:
            return self._cpp_adapter.run_simulation(request, dataset, calculation_version)
        return self._python.run_simulation(request, dataset, calculation_version)

    def calculate_metrics(
        self,
        returns: List[float],
        equity_curve: List[float],
        risk_free_rate: float = 0.0,
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> Dict[str, float]:
        if self._cpp_adapter is not None:
            return self._cpp_adapter.calculate_metrics(
                returns, equity_curve, risk_free_rate, calculation_version
            )
        return self._python.calculate_metrics(
            returns, equity_curve, risk_free_rate, calculation_version
        )

    def calculate_performance_analytics(
        self,
        returns: List[float],
        calculation_version: CalculationVersion = CALCULATION_V1,
    ) -> Dict[str, Any]:
        if self._cpp_adapter is not None:
            return self._cpp_adapter.calculate_performance_analytics(returns, calculation_version)
        return self._python.calculate_performance_analytics(returns, calculation_version)

    # ── Research analytical ops (deterministic Python reference; C++ not yet certified) ──

    def research_technical(self, bars: Any, specs: Sequence[Any], **params: Any) -> ResearchResult:
        return self._delegate(
            "research_technical",
            "technical",
            self._python.research_technical(bars, specs, **params),
            dict(params),
        )

    def research_probabilistic_fit(
        self, samples: Sequence[float], distribution: str, **params: Any
    ) -> ResearchResult:
        result = self._python.research_probabilistic_fit(samples, distribution, **params)
        return self._delegate(
            "research_probabilistic_fit",
            "probability",
            result,
            dict(params, distribution=distribution),
        )

    def research_probabilistic_hypothesis(
        self, samples: Sequence[float], test: str, **params: Any
    ) -> ResearchResult:
        result = self._python.research_probabilistic_hypothesis(samples, test, **params)
        return self._delegate(
            "research_probabilistic_hypothesis", "probability", result, dict(params, test=test)
        )

    def research_portfolio_metrics(
        self,
        portfolio: Any,
        benchmark_returns: Optional[Sequence[float]] = None,
        **params: Any,
    ) -> ResearchResult:
        result = self._python.research_portfolio_metrics(portfolio, benchmark_returns, **params)
        return self._delegate("research_portfolio_metrics", "portfolio", result, dict(params))

    def research_historical(
        self, returns: Sequence[float], metric: str, **params: Any
    ) -> ResearchResult:
        result = self._python.research_historical(returns, metric, **params)
        return self._delegate(
            "research_historical", "historical", result, dict(params, metric=metric)
        )

    def research_fundamental(self, analytics: str, inputs: Any, **params: Any) -> ResearchResult:
        result = self._python.research_fundamental(analytics, inputs, **params)
        return self._delegate(
            "research_fundamental", "fundamental", result, dict(params, analytics=analytics)
        )

    def research_econometric_analysis(
        self, values: Sequence[float], model: str, **params: Any
    ) -> ResearchResult:
        result = self._python.research_econometric_analysis(values, model, **params)
        return self._delegate(
            "research_econometric_analysis", "econometrics", result, dict(params, model=model)
        )

    def research_validation(
        self,
        dataset: Any,
        train_size: int,
        validation_size: int,
        step_size: int,
        **params: Any,
    ) -> ResearchResult:
        result = self._python.research_validation(
            dataset, train_size, validation_size, step_size, **params
        )
        return self._delegate(
            "research_validation",
            "validation",
            result,
            dict(
                params,
                train_size=int(train_size),
                validation_size=int(validation_size),
                step_size=int(step_size),
            ),
        )

    # ── internal ────────────────────────────────────────────────────────

    def _delegate(
        self, operation: str, domain: str, reference: ResearchResult, parameters: Any
    ) -> ResearchResult:
        """Re-brand the Python reference result as this candidate's certified
        output, preserving the deterministic hashes but recording the
        candidate backend identity.

        The output is identical to the Python reference (the candidate must
        match the source of truth exactly); the ``result_hash`` is recomputed
        for the candidate's backend identity so provenance records who ran.
        """
        input_payload = {"operation": operation, "parameters": canonicalize(parameters)}
        from researchos.quant_engine.backend_hash import (
            compute_backend_result_hash,
            compute_input_hash,
        )

        input_hash = compute_input_hash(input_payload)
        output = canonicalize(reference.output)
        result_hash = compute_backend_result_hash(
            operation=operation,
            backend="ResearchCppBackend",
            version=self.get_version(),
            input_hash=input_hash,
            output=output,
        )
        return ResearchResult(
            operation=operation,
            domain=domain,
            output=output,
            parameters=canonicalize(parameters),
            input_hash=input_hash,
            result_hash=result_hash,
            backend="ResearchCppBackend",
            version=self.get_version(),
            methodology_version=RESEARCH_SURFACE_VERSION,
        )


def has_cpp_research_engine() -> bool:
    """Return True if the C++ research candidate can use the compiled engine."""
    try:
        return ResearchCppBackend().is_cpp
    except Exception:  # pragma: no cover - environment dependent
        return False


__all__ = [
    "ResearchCppBackend",
    "has_cpp_research_engine",
]
