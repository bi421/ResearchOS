"""
Tests: BackendRouter structured validation (Phase 4.2).

Covers routing of ``run_simulation`` (which returns the non-numeric
``SimulationResult``), the ``auto``/``numeric``/``structural`` validation
strategies, deterministic result hashing of structured outputs, and the new
audit metadata fields (``execution_timestamp``, ``capability_profile``).
"""

from __future__ import annotations

import pytest

from researchos.quant_engine import (
    ERROR_EXECUTION_FAILED,
    ERROR_NO_CANDIDATE,
    ERROR_OK,
    ERROR_TRUST_BOUNDARY,
    ERROR_VALIDATION_FAILED,
    BackendCapabilities,
    BackendRouter,
    NumericalComparisonError,
    PythonQuantBackend,
    ValidationStatus,
)
from researchos.quant_engine.capabilities import QUANT_OPERATIONS
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)

V1 = CalculationVersion.CALCULATION_V1
PRICES = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 106.0, 108.0, 110.0, 112.0]


def make_request(dataset_reference: str = "router_structured") -> SimulationRequest:
    return SimulationRequest(
        dataset_reference=dataset_reference,
        parameters={"initial_capital": 100000.0},
        seed=42,
    )


def sim_inputs(request: SimulationRequest, prices=PRICES):
    return {"request": request, "dataset": prices, "calculation_version": V1}


class _CertifiedCandidate(PythonQuantBackend):
    """A conforming candidate that advertises its own identity."""

    BACKEND_NAME = "CertifiedCandidate"

    def capabilities(self):
        return BackendCapabilities(
            backend_name="CertifiedCandidate",
            version="2.0.0",
            supported_operations=QUANT_OPERATIONS,
        )


class _DivergingCandidate(PythonQuantBackend):
    """A candidate whose output diverges from the reference."""

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
        calculation_version: CalculationVersion = V1,
    ) -> SimulationResult:
        result = super().run_simulation(request, dataset, calculation_version)
        result.metrics = dict(result.metrics)
        if result.metrics:
            key = next(iter(result.metrics))
            result.metrics[key] = result.metrics[key] + 999.0
        result.result_hash = result.compute_result_hash()
        return result


class _RaiseCandidate(PythonQuantBackend):
    """A candidate that fails during execution."""

    BACKEND_NAME = "RaiseCandidate"

    def capabilities(self):
        return BackendCapabilities(
            backend_name="RaiseCandidate",
            version="1.0.0",
            supported_operations=QUANT_OPERATIONS,
        )

    def run_simulation(self, request, dataset, calculation_version=V1):
        raise RuntimeError("structured backend exploded")


class _NonDeterministicCandidate(PythonQuantBackend):
    """A candidate that violates the trust boundary (non-deterministic)."""

    BACKEND_NAME = "NonDeterministicCandidate"

    def capabilities(self):
        return BackendCapabilities(
            backend_name="NonDeterministicCandidate",
            version="1.0.0",
            supported_operations=QUANT_OPERATIONS,
            deterministic=False,
        )


class TestRunSimulationRouting:
    def test_auto_structural_candidate_success(self):
        router = BackendRouter(candidates=[_CertifiedCandidate()])
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert result.metadata.error_code == ERROR_OK
        assert result.metadata.fallback_used is False
        assert result.metadata.backend == "CertifiedCandidate"
        assert result.metadata.validation_status == ValidationStatus.PASSED.value
        assert isinstance(result.output, SimulationResult)

    def test_no_candidate_falls_back(self):
        router = BackendRouter()
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_NO_CANDIDATE
        assert result.metadata.backend == "PythonQuantBackend"
        assert result.metadata.validation_status == ValidationStatus.NOT_REQUIRED.value
        assert isinstance(result.output, SimulationResult)

    def test_diverging_candidate_falls_back(self):
        router = BackendRouter(candidates=[_DivergingCandidate()])
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_VALIDATION_FAILED
        assert result.metadata.backend == "PythonQuantBackend"

    def test_raising_candidate_falls_back(self):
        router = BackendRouter(candidates=[_RaiseCandidate()])
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_EXECUTION_FAILED
        assert result.metadata.backend == "PythonQuantBackend"

    def test_trust_boundary_violation_falls_back(self):
        router = BackendRouter(candidates=[_NonDeterministicCandidate()])
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_TRUST_BOUNDARY
        assert result.metadata.backend == "PythonQuantBackend"

    def test_auto_uses_structural_for_structured_outputs(self):
        # 'auto' must not raise NumericalComparisonError on SimulationResult.
        router = BackendRouter(candidates=[_CertifiedCandidate()])
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert result.metadata.validation_status == ValidationStatus.PASSED.value


class TestValidationStrategies:
    def test_numeric_mode_raises_for_structured(self):
        router = BackendRouter(candidates=[_CertifiedCandidate()])
        with pytest.raises(NumericalComparisonError):
            router.execute(
                "run_simulation",
                sim_inputs(make_request()),
                validation="numeric",
            )

    def test_structural_mode_works_for_numeric(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        result = router.execute(
            "calculate_returns",
            {"prices": PRICES},
            validation="structural",
        )
        assert result.metadata.validation_status == ValidationStatus.PASSED.value

    def test_invalid_validation_mode_raises(self):
        router = BackendRouter()
        with pytest.raises(Exception):
            router.execute("run_simulation", sim_inputs(make_request()), validation="bogus")


class TestStructuredDeterminism:
    def test_result_hash_deterministic_across_runs(self):
        router = BackendRouter()
        a = router.execute("run_simulation", sim_inputs(make_request()))
        b = router.execute("run_simulation", sim_inputs(make_request()))
        assert a.metadata.result_hash == b.metadata.result_hash
        assert len(a.metadata.result_hash) == 64

    def test_result_hash_changes_with_input(self):
        router = BackendRouter()
        base = router.execute("run_simulation", sim_inputs(make_request()))
        other = router.execute(
            "run_simulation",
            sim_inputs(make_request(dataset_reference="different_reference")),
        )
        assert base.metadata.result_hash != other.metadata.result_hash

    def test_timestamp_excluded_from_hash(self):
        router = BackendRouter()
        a = router.execute("run_simulation", sim_inputs(make_request()))
        b = router.execute("run_simulation", sim_inputs(make_request()))
        # result_hash is stable even though execution timestamps are
        # observational (and may differ between calls).
        assert a.metadata.result_hash == b.metadata.result_hash
        assert isinstance(a.metadata.execution_timestamp, str)
        assert a.metadata.execution_timestamp


class TestMetadataExtensions:
    def test_execution_timestamp_present(self):
        router = BackendRouter()
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert isinstance(result.metadata.execution_timestamp, str)
        assert result.metadata.execution_timestamp

    def test_capability_profile_present(self):
        router = BackendRouter(candidates=[_CertifiedCandidate()])
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert result.metadata.capability_profile is not None
        assert result.metadata.capability_profile.backend_name == "CertifiedCandidate"
        assert result.metadata.capability_profile.version == "2.0.0"

    def test_capability_profile_reference_on_fallback(self):
        router = BackendRouter()
        result = router.execute("run_simulation", sim_inputs(make_request()))
        assert result.metadata.capability_profile is not None
        assert result.metadata.capability_profile.backend_name == "PythonQuantBackend"

    def test_metadata_to_dict_roundtrip_with_extensions(self):
        router = BackendRouter()
        result = router.execute("run_simulation", sim_inputs(make_request()))
        restored = type(result.metadata).from_dict(result.metadata.to_dict())
        assert restored.to_dict() == result.metadata.to_dict()
        assert restored.capability_profile is not None
        assert restored.execution_timestamp == result.metadata.execution_timestamp
