"""
Tests: NumericalComparator — certification-grade numerical validation.

Covers scalars, vectors, matrices, shape checks, NaN / Infinity rejection,
tolerance policy (atol 1e-12, rtol 1e-10), deterministic repeat hash, and
frozen ``NumericalValidationResult``.
"""

from __future__ import annotations

import pytest

from researchos.quant_engine import (
    NumericalComparator,
    NumericalComparisonError,
    NumericalValidationResult,
    ValidationStatus,
)

C = NumericalComparator()


class TestScalarComparison:
    def test_equal_scalars_pass(self):
        result = C.compare_scalar(1.0, 1.0)
        assert result.status == ValidationStatus.PASSED
        assert result.passed is True
        assert result.shape_match is True

    def test_within_abs_tolerance_passes(self):
        assert C.compare_scalar(1.0, 1.0 + 0.5e-12).passed is True

    def test_atol_boundary_passes(self):
        assert C.compare_scalar(1.0, 1.0 + 1e-12, atol=1e-12).passed is True

    def test_exceeding_abs_tolerance_fails(self):
        # 1e-6 exceeds both atol (1e-12) and rtol (1e-10 * |1.0|).
        assert C.compare_scalar(1.0, 1.0 + 1e-6).passed is False

    def test_within_rel_tolerance_passes(self):
        # relative to |actual| = 1000.0: rtol 1e-10 allows 1e-7 abs
        assert C.compare_scalar(1000.0, 1000.0 + 5e-8).passed is True

    def test_large_rel_difference_fails(self):
        assert C.compare_scalar(1000.0, 1000.0 + 1e-3).passed is False

    def test_int_vs_float(self):
        assert C.compare_scalar(1, 1.0).passed is True

    def test_bool_rejected_as_scalar(self):
        with pytest.raises(NumericalComparisonError):
            C.compare_scalar(True, True)  # type: ignore[arg-type]


class TestVectorComparison:
    def test_equal_vectors_pass(self):
        assert C.compare_vector([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]).passed is True

    def test_within_tolerance_pass(self):
        assert C.compare_vector([1.0, 2.0], [1.0, 2.0 + 1e-14]).passed is True

    def test_shape_mismatch_fails(self):
        result = C.compare_vector([1.0, 2.0, 3.0], [1.0, 2.0])
        assert result.passed is False
        assert result.shape_match is False

    def test_empty_vectors_match(self):
        assert C.compare_vector([], []).passed is True

    def test_elementwise_mismatch_fails(self):
        result = C.compare_vector([1.0, 2.0, 3.0], [1.0, 2.0, 9.0])
        assert result.passed is False
        assert result.max_abs_error == 6.0

    def test_tuple_vs_list(self):
        assert C.compare_vector((1.0, 2.0), [1.0, 2.0]).passed is True


class TestMatrixComparison:
    def test_equal_matrices_pass(self):
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[1.0, 2.0], [3.0, 4.0]]
        assert C.compare_matrix(a, b).passed is True

    def test_within_tolerance_pass(self):
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[1.0, 2.0 + 1e-14], [3.0, 4.0]]
        assert C.compare_matrix(a, b).passed is True

    def test_row_count_mismatch_fails(self):
        result = C.compare_matrix([[1.0, 2.0]], [[1.0, 2.0], [3.0, 4.0]])
        assert result.passed is False
        assert result.shape_match is False

    def test_column_count_mismatch_fails(self):
        result = C.compare_matrix([[1.0, 2.0]], [[1.0, 2.0, 3.0]])
        assert result.passed is False
        assert result.shape_match is False

    def test_element_mismatch_fails(self):
        a = [[1.0, 2.0], [3.0, 4.0]]
        b = [[1.0, 2.0], [3.0, 5.0]]
        result = C.compare_matrix(a, b)
        assert result.passed is False
        assert result.max_abs_error == 1.0


class TestAutoDetectCompare:
    def test_scalar_auto(self):
        assert C.compare(1.0, 1.0).passed is True

    def test_vector_auto(self):
        assert C.compare([1.0, 2.0], [1.0, 2.0]).passed is True

    def test_matrix_auto(self):
        assert C.compare([[1.0]], [[1.0]]).passed is True

    def test_scalar_vs_vector_shape_failure(self):
        result = C.compare(1.0, [1.0, 2.0])
        assert result.passed is False
        assert result.shape_match is False

    def test_nested_matrix_auto(self):
        a = [[1.0, 2.0], [3.0, 4.0]]
        assert C.compare(a, a).passed is True


class TestNaNRejection:
    def test_nan_in_expected_rejected(self):
        result = C.compare([1.0, float("nan")], [1.0, 2.0])
        assert result.passed is False
        assert result.has_nan is True

    def test_nan_in_actual_rejected(self):
        result = C.compare([1.0, 2.0], [1.0, float("nan")])
        assert result.passed is False
        assert result.has_nan is True

    def test_both_nan_still_rejected(self):
        # NaN is never accepted, even on both sides.
        result = C.compare([float("nan")], [float("nan")])
        assert result.passed is False
        assert result.has_nan is True

    def test_nan_scalar_rejected(self):
        assert C.compare_scalar(float("nan"), 1.0).passed is False

    def test_nan_in_matrix_rejected(self):
        result = C.compare([[1.0], [2.0]], [[1.0], [float("nan")]])
        assert result.passed is False
        assert result.has_nan is True


class TestInfinityRejection:
    def test_inf_in_expected_rejected(self):
        result = C.compare([1.0, float("inf")], [1.0, 2.0])
        assert result.passed is False
        assert result.has_inf is True

    def test_inf_in_actual_rejected(self):
        result = C.compare([1.0, 2.0], [1.0, float("inf")])
        assert result.passed is False
        assert result.has_inf is True

    def test_neg_inf_rejected(self):
        result = C.compare_scalar(-float("inf"), 1.0)
        assert result.passed is False
        assert result.has_inf is True

    def test_inf_scalar_rejected(self):
        assert C.compare_scalar(float("inf"), float("inf")).passed is False

    def test_inf_in_matrix_rejected(self):
        result = C.compare([[1.0]], [[float("inf")]])
        assert result.passed is False
        assert result.has_inf is True


class TestValidationResult:
    def test_is_frozen(self):
        result = C.compare_scalar(1.0, 1.0)
        with pytest.raises(Exception):
            result.status = ValidationStatus.FAILED  # type: ignore[misc]

    def test_is_hashable(self):
        a = C.compare_scalar(1.0, 1.0)
        b = C.compare_scalar(1.0, 1.0)
        assert hash(a) == hash(b)

    def test_to_dict_roundtrip(self):
        result = C.compare_vector([1.0, 2.0], [1.0, 2.0])
        restored = NumericalValidationResult.from_dict(result.to_dict())
        assert restored == result
        assert restored.passed is True

    def test_to_dict_json_compatible(self):
        import json

        json.dumps(C.compare_scalar(1.0, 1.0).to_dict())

    def test_deterministic_repeat_hash(self):
        a = C.compare_vector([1.0, 2.0], [1.0, 2.0])
        b = C.compare_vector([1.0, 2.0], [1.0, 2.0])
        assert a.comparison_hash == b.comparison_hash
        assert a.comparison_hash == b.comparison_hash

    def test_repeat_hash_differs_for_different_inputs(self):
        a = C.compare_vector([1.0, 2.0], [1.0, 2.0])
        b = C.compare_vector([1.0, 2.0], [1.0, 3.0])
        assert a.comparison_hash != b.comparison_hash

    def test_repeat_hash_is_sha256(self):
        assert len(C.compare_scalar(1.0, 1.0).comparison_hash) == 64

    def test_max_rel_error(self):
        result = C.compare_scalar(2.0, 4.0)
        assert result.passed is False
        assert result.max_rel_error == 0.5

    def test_zero_denominator_rel_error(self):
        result = C.compare_scalar(0.0, 0.0)
        assert result.max_rel_error == 0.0


class TestInvalidInputs:
    def test_non_numeric_structure_raises(self):
        with pytest.raises(NumericalComparisonError):
            C.compare("abc", "abc")  # type: ignore[arg-type]

    def test_mixed_row_types_raises(self):
        # float("x") surfaces as ValueError during normalization; the error
        # hierarchy subclasses ValueError, so both are acceptable here.
        with pytest.raises((NumericalComparisonError, ValueError)):
            C.compare([[1.0, "x"]], [[1.0, 2.0]])  # type: ignore[list-item]

    def test_negative_atol_raises(self):
        with pytest.raises(NumericalComparisonError):
            C.compare_scalar(1.0, 1.0, atol=-1.0)

    def test_negative_rtol_raises(self):
        with pytest.raises(NumericalComparisonError):
            C.compare_scalar(1.0, 1.0, rtol=-1.0)

    def test_non_number_atol_raises(self):
        with pytest.raises(NumericalComparisonError):
            C.compare_scalar(1.0, 1.0, atol="1e-12")  # type: ignore[arg-type]

    def test_default_tolerances(self):
        assert NumericalComparator.DEFAULT_ATOL == 1e-12
        assert NumericalComparator.DEFAULT_RTOL == 1e-10
