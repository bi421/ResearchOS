"""
Tests: BackendRouter — trust-boundary routing and Python fallback.

Phase 4.1: backend certification and trust-boundary hardening.

Required failure modes covered:
    - Python fallback (candidate mismatch)
    - Backend unavailable (capabilities raise / execution raises)
    - Numerical mismatch
    - NaN
    - Shape mismatch
    - Deterministic hash
    - Frozen metadata
"""

from __future__ import annotations

import pytest

from researchos.quant_engine import (
    ERROR_EXECUTION_FAILED,
    ERROR_NO_CANDIDATE,
    ERROR_OK,
    ERROR_VALIDATION_FAILED,
    BackendCapabilities,
    BackendExecutionMetadata,
    BackendRouter,
    BackendRouterError,
    BackendValidationError,
    PythonQuantBackend,
    ValidationStatus,
)
from researchos.quant_engine.capabilities import QUANT_OPERATIONS
from researchos.quant_engine.models import CalculationVersion

V1 = CalculationVersion.CALCULATION_V1

PRICES = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]


def reference_returns(prices=PRICES):
    return PythonQuantBackend().calculate_returns(prices, "percentage", V1)


class _ShiftedBackend(PythonQuantBackend):
    """Returns outputs shifted by a constant → numerical mismatch."""

    def calculate_returns(self, prices, return_type="percentage", calculation_version=V1):
        out = super().calculate_returns(prices, return_type, calculation_version)
        return [x + 1.0 for x in out]


class _RaiseBackend(PythonQuantBackend):
    """Raises on execution → backend unavailable / execution failure."""

    def calculate_returns(self, prices, return_type="percentage", calculation_version=V1):
        raise RuntimeError("backend exploded")


class _UnavailableBackend(PythonQuantBackend):
    """Advertises no capabilities → backend unavailable."""

    def capabilities(self):
        raise RuntimeError("capabilities unavailable")


class _NaNBackend(PythonQuantBackend):
    """Returns NaN → rejected by validation."""

    def calculate_returns(self, prices, return_type="percentage", calculation_version=V1):
        out = super().calculate_returns(prices, return_type, calculation_version)
        return [float("nan")] * len(out)


class _ShapeBackend(PythonQuantBackend):
    """Returns a wrong-length vector → shape mismatch."""

    def calculate_returns(self, prices, return_type="percentage", calculation_version=V1):
        return [1.0]


class _NonDeterministicBackend(PythonQuantBackend):
    """Advertises non-determinism → rejected at the capability check."""

    def capabilities(self):
        return BackendCapabilities(
            backend_name="NonDeterministic",
            version="1.0.0",
            supported_operations=QUANT_OPERATIONS,
            deterministic=False,
        )


class TestRouterSuccessPath:
    def test_candidate_success_returns_output(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.fallback_used is False
        assert result.metadata.error_code == ERROR_OK
        assert result.metadata.validation_status == ValidationStatus.PASSED.value
        assert result.output == reference_returns()

    def test_candidate_backend_recorded(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.backend == "PythonQuantBackend"

    def test_no_candidates_falls_back(self):
        router = BackendRouter()
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_NO_CANDIDATE
        assert result.output == reference_returns()

    def test_expected_override_used(self):
        # A provided ``expected`` replaces the reference validation: the shifted
        # candidate's own output equals the provided expected, so it passes —
        # proving the reference backend was NOT executed for validation.
        backend = _ShiftedBackend()
        router = BackendRouter(candidates=[backend])
        shifted = backend.calculate_returns(PRICES, "percentage", V1)
        result = router.execute("calculate_returns", {"prices": PRICES}, expected=shifted)
        assert result.metadata.validation_status == ValidationStatus.PASSED.value
        assert result.metadata.fallback_used is False
        assert result.output == shifted


class TestRouterPythonFallback:
    def test_numerical_mismatch_falls_back(self):
        router = BackendRouter(candidates=[_ShiftedBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_VALIDATION_FAILED
        assert result.metadata.backend == "PythonQuantBackend"
        assert result.output == reference_returns()

    def test_execution_failure_falls_back(self):
        router = BackendRouter(candidates=[_RaiseBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_EXECUTION_FAILED
        assert result.output == reference_returns()

    def test_unavailable_backend_falls_back(self):
        router = BackendRouter(candidates=[_UnavailableBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_NO_CANDIDATE
        assert result.output == reference_returns()

    def test_non_deterministic_backend_rejected(self):
        router = BackendRouter(candidates=[_NonDeterministicBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.fallback_used is True
        assert result.output == reference_returns()

    def test_nan_output_falls_back(self):
        router = BackendRouter(candidates=[_NaNBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_VALIDATION_FAILED
        assert result.output == reference_returns()

    def test_shape_mismatch_falls_back(self):
        router = BackendRouter(candidates=[_ShapeBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_VALIDATION_FAILED
        assert result.output == reference_returns()


class TestRouterValidationStatus:
    def test_fallback_without_expected_not_required(self):
        router = BackendRouter()
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.validation_status == ValidationStatus.NOT_REQUIRED.value

    def test_fallback_with_expected_validated(self):
        router = BackendRouter(candidates=[_ShiftedBackend()])
        expected = reference_returns()
        result = router.execute("calculate_returns", {"prices": PRICES}, expected=expected)
        assert result.metadata.validation_status == ValidationStatus.PASSED.value


class TestRouterDeterministicHash:
    def test_result_hash_deterministic(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        a = router.execute("calculate_returns", {"prices": PRICES})
        b = router.execute("calculate_returns", {"prices": PRICES})
        assert a.metadata.result_hash == b.metadata.result_hash

    def test_result_hash_changes_with_output(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        base = router.execute("calculate_returns", {"prices": PRICES})
        shifted = router.execute("calculate_returns", {"prices": [100.0, 101.0, 102.0, 103.0, 104.0, 106.0]})
        assert base.metadata.result_hash != shifted.metadata.result_hash

    def test_result_hash_is_sha256(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert len(result.metadata.result_hash) == 64

    def test_fallback_hash_stable(self):
        router = BackendRouter(candidates=[_ShiftedBackend()])
        a = router.execute("calculate_returns", {"prices": PRICES})
        b = router.execute("calculate_returns", {"prices": PRICES})
        assert a.metadata.result_hash == b.metadata.result_hash


class TestRouterMetadata:
    def test_metadata_is_frozen(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        with pytest.raises(Exception):
            result.metadata.backend = "Mutated"  # type: ignore[misc]

    def test_metadata_to_dict_roundtrip(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        # execution_time_ms is rounded to 6dp in to_dict(); the roundtrip is
        # exact at the serialized-dict level (not the raw float level).
        restored = BackendExecutionMetadata.from_dict(result.metadata.to_dict())
        assert restored.to_dict() == result.metadata.to_dict()
        assert restored.operation == result.metadata.operation
        assert restored.result_hash == result.metadata.result_hash

    def test_metadata_fields_present(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        md = result.metadata
        assert md.operation == "calculate_returns"
        assert md.execution_time_ms >= 0.0
        assert md.error_code == ERROR_OK

    def test_result_is_frozen(self):
        router = BackendRouter()
        result = router.execute("calculate_returns", {"prices": PRICES})
        with pytest.raises(Exception):
            result.output = []  # type: ignore[misc]


class TestRouterAPI:
    def test_register_validates_type(self):
        router = BackendRouter()
        with pytest.raises(TypeError):
            router.register("not-a-backend")  # type: ignore[arg-type]

    def test_list_candidates(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        caps = router.list_candidates()
        assert len(caps) == 1
        assert caps[0].backend_name == "PythonQuantBackend"

    def test_reference_property(self):
        router = BackendRouter()
        assert isinstance(router.reference_backend, PythonQuantBackend)

    def test_set_reference_validates_type(self):
        router = BackendRouter()
        with pytest.raises(TypeError):
            router.set_reference("nope")  # type: ignore[arg-type]

    def test_execute_requires_mapping_inputs(self):
        router = BackendRouter()
        with pytest.raises(BackendRouterError):
            router.execute("calculate_returns", [1.0, 2.0])  # type: ignore[arg-type]

    def test_register_duplicate_is_noop(self):
        backend = PythonQuantBackend()
        router = BackendRouter()
        router.register(backend)
        router.register(backend)
        assert len(router.list_candidates()) == 1

    def test_unknown_operation_reference_fails(self):
        router = BackendRouter()
        with pytest.raises(BackendRouterError):
            router.execute("no_such_operation", {"a": 1})

    def test_error_constants_exposed(self):
        assert ERROR_OK == "ok"
        assert ERROR_NO_CANDIDATE == "unavailable"
        assert ERROR_VALIDATION_FAILED == "validation_failed"
        assert ERROR_EXECUTION_FAILED == "execution_failed"

    def test_validation_error_type_exists(self):
        assert issubclass(BackendValidationError, BackendRouterError)

    def test_default_tolerances_used(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        result = router.execute("calculate_returns", {"prices": PRICES})
        assert result.metadata.validation_status == ValidationStatus.PASSED.value


class TestRouterVolatility:
    def test_volatility_candidate_success(self):
        router = BackendRouter(candidates=[PythonQuantBackend()])
        returns = reference_returns()
        result = router.execute(
            "calculate_volatility",
            {"returns": returns, "method": "standard_deviation"},
        )
        assert result.metadata.error_code == ERROR_OK
        assert result.metadata.fallback_used is False

    def test_volatility_fallback_on_shift(self):
        class _ShiftedVolatilityBackend(_ShiftedBackend):
            def calculate_volatility(self, returns, method="standard_deviation", calculation_version=V1):
                return super().calculate_volatility(returns, method, calculation_version) + 5.0

        router = BackendRouter(candidates=[_ShiftedVolatilityBackend()])
        result = router.execute(
            "calculate_volatility",
            {"returns": reference_returns(), "method": "standard_deviation"},
        )
        assert result.metadata.fallback_used is True
        assert result.metadata.error_code == ERROR_VALIDATION_FAILED
