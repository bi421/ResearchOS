"""
Integration tests: C++ quant backend through the certified BackendRouter (Phase 4.3).

Verifies that the compiled C++ engine, wrapped by ``CppQuantAdapter``, can be
registered as a certified router candidate and that its outputs are numerically
equivalent to the Python reference backend while the router's certification
flow (capability check → validation → fallback) and metadata are preserved.

Asserted behaviors:
    1. ``has_cpp_engine()`` is True when the compiled module is discoverable.
    2. ``CppQuantAdapter`` can be registered via ``register_cpp_backend`` and
       is selected by the router (capability registration).
    3. Python vs C++ outputs are numerically equivalent for every operation.
    4. Router validation passes with the C++ candidate (validation_status).
    5. Determinism preserved: identical C++ routed runs → identical result hash.
    6. Automatic Python fallback still works when the C++ candidate raises.
    7. Provenance (input_hash / simulation_id) and result_hash parity.

All tests are skipped when the compiled C++ engine is not available.
"""

from __future__ import annotations

import math
from typing import Any, List

import pytest

from researchos.quant_engine.backend import PythonQuantBackend
from researchos.quant_engine.capabilities import QUANT_OPERATIONS
from researchos.quant_engine.cpp_backend import (
    CppQuantAdapter,
    create_cpp_router,
    has_cpp_engine,
    register_cpp_backend,
)
from researchos.quant_engine.models import CalculationVersion, SimulationRequest
from researchos.quant_engine.router import BackendRouter

pytestmark = pytest.mark.skipif(
    not has_cpp_engine(), reason="compiled C++ quant engine not available"
)

_V1 = CalculationVersion.CALCULATION_V1

#: Minimum data length for rolling volatility / volatility change (window 21).
_ROLLING_MIN = 60


def _prices(n: int, base: float = 100.0) -> List[float]:
    """Deterministic, non-trivial price series (identical to parity suite)."""
    return [base + 30.0 * math.sin(i / 4.0) + 0.5 * (i % 7) for i in range(n)]


def _make_request(**params: Any) -> SimulationRequest:
    merged = {"initial_capital": 100000.0, "risk_free_rate": 0.0}
    merged.update(params)
    return SimulationRequest(
        dataset_reference="XAU/USD:ROUTER",
        dataset_version="1.0.0",
        calculation_version=_V1,
        start_time="2026-01-01T00:00:00",
        end_time="2026-12-31T00:00:00",
        parameters=merged,
        seed=42,
        tags=["router-cpp"],
    )


@pytest.fixture(scope="module")
def router() -> BackendRouter:
    return create_cpp_router()


@pytest.fixture(scope="module")
def python_backend() -> PythonQuantBackend:
    return PythonQuantBackend()


class TestEngineDiscovery:
    def test_engine_available(self):
        assert has_cpp_engine() is True

    def test_cpp_adapter_is_active(self):
        adapter = CppQuantAdapter()
        assert adapter.is_cpp is True
        assert adapter.get_version().startswith("1.")


class TestCapabilityRegistration:
    def test_register_cpp_backend_adds_candidate(self):
        router = BackendRouter()
        adapter = register_cpp_backend(router)
        assert adapter is not None
        caps = router.list_candidates()
        assert len(caps) == 1
        assert caps[0].backend_name == "CppQuantAdapter"
        assert caps[0].version == adapter.get_version()
        assert set(caps[0].supported_operations) == set(QUANT_OPERATIONS)
        assert caps[0].deterministic and caps[0].stateless
        assert caps[0].no_timestamps and caps[0].no_randomness
        assert caps[0].explicit_typing

    def test_register_force_when_engine_present(self):
        router = BackendRouter()
        adapter = register_cpp_backend(router, force=True)
        assert adapter is not None
        assert len(router.list_candidates()) == 1

    def test_create_cpp_router_has_reference_python(self, router):
        # The Python reference backend remains the source of truth.
        assert router.reference_backend is not None
        assert isinstance(router.reference_backend, PythonQuantBackend)
        assert len(router.list_candidates()) == 1

    def test_cpp_candidate_selected(self, router):
        result = router.execute(
            "calculate_returns",
            {"prices": _prices(_ROLLING_MIN), "return_type": "percentage"},
        )
        assert result.metadata.backend == "CppQuantAdapter"
        assert result.metadata.error_code == "ok"
        assert result.metadata.fallback_used is False


class TestNumericalEquivalence:
    def test_returns_equivalence(self, router, python_backend):
        prices = _prices(_ROLLING_MIN)
        cpp = router.execute(
            "calculate_returns", {"prices": prices, "return_type": "percentage"}
        )
        assert cpp.output == python_backend.calculate_returns(prices, "percentage")

    def test_volatility_equivalence(self, router, python_backend):
        returns = python_backend.calculate_returns(_prices(_ROLLING_MIN))
        for method in ("standard_deviation", "rolling", "change"):
            cpp = router.execute(
                "calculate_volatility", {"returns": returns, "method": method}
            )
            assert cpp.output == pytest.approx(
                python_backend.calculate_volatility(returns, method), rel=1e-9
            )

    def test_drawdown_equivalence(self, router, python_backend):
        returns = python_backend.calculate_returns(_prices(_ROLLING_MIN))
        equity = [100000.0]
        for r in returns:
            equity.append(equity[-1] * (1.0 + r))
        cpp = router.execute("calculate_drawdown", {"equity_curve": equity})
        assert cpp.output == python_backend.calculate_drawdown(equity)

    def test_statistics_equivalence(self, router, python_backend):
        returns = python_backend.calculate_returns(_prices(_ROLLING_MIN))
        cpp = router.execute("calculate_statistics", {"returns": returns})
        assert set(cpp.output) == set(python_backend.calculate_statistics(returns))
        for key in cpp.output:
            assert cpp.output[key] == pytest.approx(
                python_backend.calculate_statistics(returns)[key], rel=1e-9, abs=1e-12
            )

    def test_metrics_equivalence(self, router, python_backend):
        returns = python_backend.calculate_returns(_prices(_ROLLING_MIN))
        equity = [100000.0]
        for r in returns:
            equity.append(equity[-1] * (1.0 + r))
        for rf in (0.0, 0.05):
            cpp = router.execute(
                "calculate_metrics",
                {"returns": returns, "equity_curve": equity, "risk_free_rate": rf},
            )
            py = python_backend.calculate_metrics(returns, equity, rf)
            assert set(cpp.output) == set(py)
            for key in py:
                assert cpp.output[key] == pytest.approx(py[key], rel=1e-9, abs=1e-12)

    def test_performance_analytics_equivalence(self, router, python_backend):
        returns = python_backend.calculate_returns(_prices(_ROLLING_MIN))
        cpp = router.execute("calculate_performance_analytics", {"returns": returns})
        assert cpp.output == python_backend.calculate_performance_analytics(returns)

    def test_run_simulation_equivalence(self, router, python_backend):
        prices = _prices(_ROLLING_MIN)
        request = _make_request()
        cpp = router.execute(
            "run_simulation",
            {"request": request, "dataset": prices},
        )
        py_result = python_backend.run_simulation(request, prices)
        assert cpp.output.returns == py_result.returns
        assert cpp.output.equity_curve == py_result.equity_curve
        assert cpp.output.performance == py_result.performance
        assert cpp.output.input_hash == py_result.input_hash
        assert cpp.output.simulation_id == py_result.simulation_id


class TestRouterValidationMetadata:
    def test_validation_status_passed(self, router):
        result = router.execute(
            "calculate_returns", {"prices": _prices(_ROLLING_MIN)}
        )
        assert result.metadata.validation_status == "passed"
        assert result.metadata.backend == "CppQuantAdapter"
        assert result.metadata.error_code == "ok"

    def test_capability_profile_recorded(self, router, python_backend):
        returns = python_backend.calculate_returns(_prices(_ROLLING_MIN))
        result = router.execute(
            "calculate_statistics",
            {"returns": returns},
        )
        profile = result.metadata.capability_profile
        assert profile is not None
        assert profile.backend_name == "CppQuantAdapter"
        assert profile.version == "1.0.0"

    def test_deterministic_across_runs(self, router):
        prices = _prices(_ROLLING_MIN)
        request = _make_request()
        a = router.execute("run_simulation", {"request": request, "dataset": prices})
        b = router.execute("run_simulation", {"request": request, "dataset": prices})
        assert a.metadata.result_hash == b.metadata.result_hash
        assert a.metadata.validation_status == b.metadata.validation_status


class TestAutomaticFallback:
    def test_failing_candidate_falls_back(self):
        class _Broken(CppQuantAdapter):
            def calculate_returns(self, *args: Any, **kwargs: Any) -> List[float]:
                raise RuntimeError("broken candidate")

        router = BackendRouter(candidates=[_Broken()])
        result = router.execute(
            "calculate_returns", {"prices": _prices(_ROLLING_MIN)}
        )
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == "execution_failed"
        assert result.metadata.backend == "PythonQuantBackend"
        assert result.output == PythonQuantBackend().calculate_returns(
            _prices(_ROLLING_MIN)
        )


class TestProvenanceAndBoundaries:
    def test_dataset_contract_flow(self, router, python_backend):
        # C++ adapter normalizes the same dataset contracts as Python backend.
        prices = _prices(_ROLLING_MIN)
        request = _make_request()
        cpp_result = router.execute(
            "run_simulation", {"request": request, "dataset": prices}
        )
        py_result = python_backend.run_simulation(request, prices)
        assert cpp_result.output.input_hash == py_result.input_hash
        assert cpp_result.output.dataset_reference == request.dataset_reference

    def test_result_hash_self_consistent(self, router):
        prices = _prices(_ROLLING_MIN)
        result = router.execute(
            "run_simulation", {"request": _make_request(), "dataset": prices}
        )
        assert result.output.result_hash == result.output.compute_result_hash()
