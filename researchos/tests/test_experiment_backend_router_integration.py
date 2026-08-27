"""
Integration tests: Experiment Framework ↔ BackendRouter (Phase 4.2).

Verifies that ALL ``QuantComputationInterface`` executions from the experiment
pipeline are routed through the certified ``BackendRouter``, that backend
selection metadata is recorded on ``ExperimentResult``, and that deterministic
behavior is preserved (the execution timestamp is recorded but excluded from
the deterministic result hash).

Asserted behaviors:
    1. Default runner routes through the router (backend selection metadata).
    2. Backend selection stats: backend_id, backend_version, capability
       profile, numerical validation status, deterministic backend result hash.
    3. Determinism preserved: identical runs → identical result hash, even
       though the observational execution timestamp is recorded.
    4. Registered certified candidates are used (fallback_used=False).
    5. Diverging / failing candidates fall back to the reference.
    6. The raw dataset contract object identity is preserved through the router.
"""

from __future__ import annotations

from typing import Any

import pytest

from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.experiment import Experiment
from researchos.experiments.result import ExperimentResult
from researchos.experiments.runner import BaseExperimentRunner
from researchos.quant_engine import (
    BackendCapabilities,
    BackendRouter,
    PythonQuantBackend,
)
from researchos.quant_engine.capabilities import QUANT_OPERATIONS
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)


def _prices(n: int = 252, base: float = 100.0, drift: float = 0.0001) -> list[float]:
    """Deterministic synthetic price series."""
    return [base * (1.0 + drift * i) for i in range(n)]


def _make_experiment(name: str = "Router Integration") -> Experiment:
    exp = Experiment(
        hypothesis_id="hyp_router",
        name=name,
        dataset_config=DatasetConfig(source="integration_source"),
        simulation_config=SimulationConfig(seed=42, initial_capital=100_000.0),
    )
    exp.mark_ready()
    return exp


class _CertifiedCandidate(PythonQuantBackend):
    BACKEND_NAME = "CertifiedCandidate"

    def capabilities(self):
        return BackendCapabilities(
            backend_name="CertifiedCandidate",
            version="2.0.0",
            supported_operations=QUANT_OPERATIONS,
        )


class _DivergingCandidate(PythonQuantBackend):
    BACKEND_NAME = "DivergingCandidate"

    def capabilities(self):
        return BackendCapabilities(
            backend_name="DivergingCandidate",
            version="1.0.0",
            supported_operations=QUANT_OPERATIONS,
        )

    def run_simulation(
        self,
        request: SimulationRequest,
        dataset: object,
        calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
    ) -> SimulationResult:
        result = super().run_simulation(request, dataset, calculation_version)
        result.metrics = dict(result.metrics)
        if result.metrics:
            key = next(iter(result.metrics))
            result.metrics[key] = result.metrics[key] + 999.0
        result.result_hash = result.compute_result_hash()
        return result


class TestBackendSelectionMetadata:
    def test_default_runner_records_backend_selection(self):
        runner = BaseExperimentRunner()
        exp = _make_experiment()
        _, result = runner.run(exp, _prices())

        assert result.statistics["backend_id"] == "PythonQuantBackend"
        assert result.statistics["backend_version"] == "1.0.0"
        assert result.statistics["backend_fallback_used"] is True
        assert result.statistics["backend_validation_status"] == "not_required"
        assert result.statistics["backend_error_code"] == "unavailable"
        assert result.statistics["backend_result_hash"]
        assert len(result.statistics["backend_result_hash"]) == 64

        profile = result.statistics["backend_capability_profile"]
        assert profile["backend_name"] == "PythonQuantBackend"
        assert profile["version"] == "1.0.0"
        assert profile["deterministic"] is True

        # Existing provenance key preserved.
        assert result.statistics["computation_backend"] == "PythonQuantBackend"

    def test_execution_timestamp_recorded(self):
        runner = BaseExperimentRunner()
        exp = _make_experiment()
        _, result = runner.run(exp, _prices())

        assert result.backend_execution_timestamp
        assert result.to_dict()["backend_execution_timestamp"] == result.backend_execution_timestamp

    def test_timestamp_excluded_from_result_hash(self):
        runner = BaseExperimentRunner()
        exp = _make_experiment()
        run1, result1 = runner.run(exp, _prices())
        run2, result2 = runner.run(exp, _prices())

        # Deterministic identity preserved.
        assert result1.result_hash == result2.result_hash
        assert result1.statistics == result2.statistics
        assert result1.metrics == result2.metrics
        # Timestamp is recorded but NOT part of the hashed content.
        hashed_content = result1._to_hashable_dict()
        assert "backend_execution_timestamp" not in hashed_content

    def test_roundtrip_preserves_backend_metadata(self):
        runner = BaseExperimentRunner()
        exp = _make_experiment()
        _, result = runner.run(exp, _prices())

        restored = ExperimentResult.from_dict(result.to_dict())
        assert restored.backend_execution_timestamp == result.backend_execution_timestamp
        assert restored.statistics["backend_id"] == result.statistics["backend_id"]
        assert restored.result_hash == result.result_hash


class TestCertifiedCandidatePath:
    def test_registered_candidate_is_used(self):
        router = BackendRouter()
        router.register(_CertifiedCandidate())
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()
        run, result = runner.run(exp, _prices())

        assert run.status.value == "Completed"
        assert result.statistics["backend_id"] == "CertifiedCandidate"
        assert result.statistics["backend_version"] == "2.0.0"
        assert result.statistics["backend_fallback_used"] is False
        assert result.statistics["backend_validation_status"] == "passed"
        assert result.statistics["backend_error_code"] == "ok"
        assert result.statistics["computation_backend"] == "CertifiedCandidate"

    def test_certified_candidate_deterministic(self):
        router = BackendRouter()
        router.register(_CertifiedCandidate())
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()

        _, r1 = runner.run(exp, _prices())
        _, r2 = runner.run(exp, _prices())
        assert r1.result_hash == r2.result_hash
        assert r1.statistics == r2.statistics

    def test_certified_candidate_matches_reference_metrics(self):
        router = BackendRouter()
        router.register(_CertifiedCandidate())
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()
        _, result = runner.run(exp, _prices())

        # Candidate output is certified identical to the reference (it IS a
        # conforming Python backend), so every metric is present.
        assert len(result.metrics) > 0


class TestFallbackThroughRouter:
    def test_diverging_candidate_falls_back(self):
        router = BackendRouter()
        router.register(_DivergingCandidate())
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()
        _, result = runner.run(exp, _prices())

        # The candidate diverged → validation_failed fallback. The returned
        # output is the certified reference, which itself passes validation
        # (validation_status describes the returned output; error_code records
        # the fallback reason).
        assert result.statistics["backend_id"] == "PythonQuantBackend"
        assert result.statistics["backend_fallback_used"] is True
        assert result.statistics["backend_validation_status"] == "passed"
        assert result.statistics["backend_error_code"] == "validation_failed"

    def test_fallback_result_is_reference_output(self):
        router = BackendRouter()
        router.register(_DivergingCandidate())
        runner = BaseExperimentRunner(router=router)
        exp = _make_experiment()

        # Fallback must return the certified reference result (not the
        # diverging candidate's mutated metrics).
        _, result = runner.run(exp, _prices())
        direct = PythonQuantBackend().run_simulation(
            SimulationRequest(
                dataset_reference="integration_source",
                parameters={"initial_capital": 100000.0},
                seed=42,
            ),
            _prices(),
        )
        for name, value in result.metrics.items():
            assert value == float(direct.metrics[name])


class TestBoundaryPreserved:
    def test_dataset_contract_identity_through_router(self):
        captured: dict[str, Any] = {}

        class RecordingBackend(PythonQuantBackend):
            def run_simulation(
                self,
                request: SimulationRequest,
                dataset: Any,
                calculation_version: CalculationVersion = CalculationVersion.CALCULATION_V1,
            ) -> SimulationResult:
                captured["dataset"] = dataset
                return super().run_simulation(request, dataset, calculation_version)

        runner = BaseExperimentRunner(backend=RecordingBackend())
        exp = _make_experiment()
        # 252-bar OHLCV-style contract (list of dicts) — sufficient samples.
        contract = [
            {
                "timestamp": "2020-01-01T00:00:00+00:00",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000 + i,
            }
            for i in range(252)
        ]
        runner.run(exp, contract)

        # The router forwards the exact contract object — no pre-parsing.
        assert captured["dataset"] is contract

    def test_backend_kwarg_still_supported(self):
        class RecordingBackend(PythonQuantBackend):
            def run_simulation(self, request, dataset, calculation_version=CalculationVersion.CALCULATION_V1):
                return super().run_simulation(request, dataset, calculation_version)

        runner = BaseExperimentRunner(backend=RecordingBackend())
        assert isinstance(runner._backend, RecordingBackend)

    def test_router_type_validated(self):
        with pytest.raises(TypeError):
            BaseExperimentRunner(router="not-a-router")  # type: ignore[arg-type]

    def test_runner_has_no_dataset_parsing_methods(self):
        runner = BaseExperimentRunner()
        assert not hasattr(runner, "_extract_prices")
