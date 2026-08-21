"""
Numerical validation — certification-grade comparison of backend outputs.

Phase 4.1: backend certification and trust-boundary hardening.

``NumericalComparator`` compares an expected (reference) value with an
actual (candidate backend) value for scalars, vectors, and matrices using
the ResearchOS certification tolerance policy:

    - identical shapes required (scalar / vector length / matrix dimensions)
    - NaN is rejected (never accepted, even on both sides)
    - Infinity is rejected
    - absolute tolerance 1e-12
    - relative tolerance 1e-10  (|a - b| <= atol + rtol * |b|)

Every comparison produces a frozen ``NumericalValidationResult`` whose
``comparison_hash`` is a deterministic SHA-256 digest of the comparison
(repeatable across runs for identical inputs).  ``compare_structural`` extends
validation to structured (non-numeric) outputs such as ``SimulationResult`` by
comparing their deterministic digests.

This is a validation/certification layer only — it makes no trading,
signalling, or prediction decisions.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Mapping, Sequence, Tuple, Union

from researchos.engines.quant.backend_hash import canonicalize

Scalar = Union[int, float]
NumericShape = Union[Scalar, Sequence[Scalar], Sequence[Sequence[Scalar]]]


class NumericalComparisonError(ValueError):
    """Raised when inputs to a numerical comparison are structurally invalid."""


class ValidationStatus(str, Enum):
    """Outcome of a numerical validation."""

    PASSED = "passed"
    FAILED = "failed"
    NOT_REQUIRED = "not_required"


@dataclass(frozen=True)
class NumericalValidationResult:
    """Frozen, hashable, serializable outcome of one numerical comparison.

    Attributes:
        status: ``PASSED`` or ``FAILED``.
        shape_match: Whether expected/actual shapes are identical.
        has_nan: Whether NaN appeared in either input.
        has_inf: Whether ±Infinity appeared in either input.
        max_abs_error: Maximum absolute error over compared elements
            (0.0 when no comparable finite elements exist).
        max_rel_error: Maximum relative error over compared elements
            (0.0 when no comparable finite elements exist).
        atol: Absolute tolerance used.
        rtol: Relative tolerance used.
        comparison_hash: Deterministic SHA-256 digest of the comparison.
    """

    status: ValidationStatus
    shape_match: bool
    has_nan: bool
    has_inf: bool
    max_abs_error: float
    max_rel_error: float
    atol: float
    rtol: float
    comparison_hash: str
    mode: str = "numeric"

    @property
    def passed(self) -> bool:
        """Convenience alias for ``status == PASSED``."""
        return self.status == ValidationStatus.PASSED

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible mapping."""
        return {
            "status": self.status.value,
            "shape_match": self.shape_match,
            "has_nan": self.has_nan,
            "has_inf": self.has_inf,
            "max_abs_error": self.max_abs_error,
            "max_rel_error": self.max_rel_error,
            "atol": self.atol,
            "rtol": self.rtol,
            "comparison_hash": self.comparison_hash,
            "mode": self.mode,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "NumericalValidationResult":
        """Reconstruct from a ``to_dict()`` mapping."""
        return cls(
            status=ValidationStatus(str(data["status"])),
            shape_match=bool(data["shape_match"]),
            has_nan=bool(data["has_nan"]),
            has_inf=bool(data["has_inf"]),
            max_abs_error=float(data["max_abs_error"]),
            max_rel_error=float(data["max_rel_error"]),
            atol=float(data["atol"]),
            rtol=float(data["rtol"]),
            comparison_hash=str(data["comparison_hash"]),
            mode=str(data.get("mode", "numeric")),
        )


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_float_rows(value: Any) -> Tuple[Tuple[float, ...], ...]:
    """Normalize a scalar / vector / matrix to nested tuples of floats.

    Raises:
        NumericalComparisonError: If the structure is not numeric.
    """
    if _is_number(value):
        return ((float(value),),)
    if isinstance(value, dict):
        return _as_float_rows(list(value.values()))
    if isinstance(value, (list, tuple)):
        if not value:
            return ()
        first = value[0]
        if _is_number(first):
            return (tuple(float(x) for x in value),)
        if isinstance(first, (list, tuple)):
            return tuple(tuple(float(x) for x in row) for row in value)
        raise NumericalComparisonError("unsupported element type in numeric structure")
    raise NumericalComparisonError("expected a scalar, vector, or matrix of numbers")


def _structural_content(value: Any) -> Any:
    """Reduce a structured output to its comparable, non-observational content.

    For objects exposing a ``to_dict()`` mapping (e.g. ``SimulationResult``),
    the mapping is used with the observational/derived fields
    (``execution_timestamp``, ``result_hash``) removed, mirroring the hashing
    semantics.  All other values are returned as-is.
    """
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            data = to_dict()
        except Exception:
            return value
        if isinstance(data, dict):
            data = dict(data)
            data.pop("execution_timestamp", None)
            data.pop("result_hash", None)
            return data
    return value


def _values_equivalent(expected: Any, actual: Any, atol: float, rtol: float) -> bool:
    """Recursively compare two structured values.

    - numeric leaves must match within ``atol``/``rtol``
    - non-numeric leaves must match exactly
    - container shapes and key sets must be identical
    """
    if _is_number(expected) or _is_number(actual):
        if not (_is_number(expected) and _is_number(actual)):
            return False
        exp, act = float(expected), float(actual)
        # NaN is never accepted, even when present on both sides.
        if math.isnan(exp) or math.isnan(act):
            return False
        # Identical non-finite values (e.g. both +inf) are equivalent.
        if math.isinf(exp) or math.isinf(act):
            return exp == act
        return abs(exp - act) <= atol + rtol * abs(act)

    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        if set(expected.keys()) != set(actual.keys()):
            return False
        return all(_values_equivalent(expected[k], actual[k], atol, rtol) for k in expected)

    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        if len(expected) != len(actual):
            return False
        return all(_values_equivalent(a, b, atol, rtol) for a, b in zip(expected, actual))

    return expected == actual


class NumericalComparator:
    """Deterministic, certification-grade numerical comparator.

    The comparator is stateless: every call depends only on its explicit
    arguments, so identical inputs always produce identical results
    (including the deterministic ``comparison_hash``).
    """

    DEFAULT_ATOL = 1e-12
    DEFAULT_RTOL = 1e-10

    def compare(
        self,
        expected: NumericShape,
        actual: NumericShape,
        atol: float = DEFAULT_ATOL,
        rtol: float = DEFAULT_RTOL,
    ) -> NumericalValidationResult:
        """Compare two numeric values of any supported shape.

        The shape is auto-detected (scalar / vector / matrix).  See the
        module docstring for the validation rules.
        """
        expected_rows = _as_float_rows(expected)
        actual_rows = _as_float_rows(actual)
        return self._compare_rows(expected_rows, actual_rows, atol, rtol)

    def compare_scalar(
        self,
        expected: Scalar,
        actual: Scalar,
        atol: float = DEFAULT_ATOL,
        rtol: float = DEFAULT_RTOL,
    ) -> NumericalValidationResult:
        """Compare two scalar numbers."""
        return self._compare_rows(_as_float_rows(expected), _as_float_rows(actual), atol, rtol)

    def compare_vector(
        self,
        expected: Sequence[Scalar],
        actual: Sequence[Scalar],
        atol: float = DEFAULT_ATOL,
        rtol: float = DEFAULT_RTOL,
    ) -> NumericalValidationResult:
        """Compare two vectors (equal length required)."""
        return self._compare_rows(_as_float_rows(expected), _as_float_rows(actual), atol, rtol)

    def compare_matrix(
        self,
        expected: Sequence[Sequence[Scalar]],
        actual: Sequence[Sequence[Scalar]],
        atol: float = DEFAULT_ATOL,
        rtol: float = DEFAULT_RTOL,
    ) -> NumericalValidationResult:
        """Compare two matrices (identical dimensions required)."""
        return self._compare_rows(_as_float_rows(expected), _as_float_rows(actual), atol, rtol)

    def compare_structural(
        self,
        expected: Any,
        actual: Any,
        atol: float = DEFAULT_ATOL,
        rtol: float = DEFAULT_RTOL,
    ) -> NumericalValidationResult:
        """Compare two structured outputs deterministically.

        Used for operations that return structured objects (e.g.
        ``SimulationResult``) or mappings (statistics/metrics dicts) rather
        than scalar/vector/matrix numbers.  The outputs are reduced to their
        comparable content (excluding observational fields such as execution
        timestamps) and compared field-by-field:

            - numeric leaves must match within ``atol``/``rtol``
            - non-numeric leaves must match exactly
            - container shapes and key sets must be identical

        This mirrors the certification parity policy: a certified accelerated
        backend may differ from the reference in the last ULP of accumulated
        statistics, but must be equivalent within the declared tolerance —
        anything else is rejected.

        Returns a ``NumericalValidationResult`` with deterministic
        ``comparison_hash``.
        """
        _validate_tolerance(atol, rtol)
        exp_content = _structural_content(expected)
        act_content = _structural_content(actual)
        passed = _values_equivalent(exp_content, act_content, atol, rtol)
        comparison_hash = self._structural_hash(exp_content, act_content, atol, rtol)
        return NumericalValidationResult(
            status=(ValidationStatus.PASSED if passed else ValidationStatus.FAILED),
            shape_match=passed,
            has_nan=False,
            has_inf=False,
            max_abs_error=0.0,
            max_rel_error=0.0,
            atol=float(atol),
            rtol=float(rtol),
            comparison_hash=comparison_hash,
            mode="structural",
        )

    @staticmethod
    def _structural_hash(exp_digest: Any, act_digest: Any, atol: float, rtol: float) -> str:
        payload = {
            "expected": exp_digest,
            "actual": act_digest,
            "atol": atol,
            "rtol": rtol,
        }
        return hashlib.sha256(
            json.dumps(canonicalize(payload), sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _compare_rows(
        self,
        expected_rows: Tuple[Tuple[float, ...], ...],
        actual_rows: Tuple[Tuple[float, ...], ...],
        atol: float,
        rtol: float,
    ) -> NumericalValidationResult:
        _validate_tolerance(atol, rtol)

        shape_match = self._shape_matches(expected_rows, actual_rows)
        has_nan = self._contains_nan(expected_rows) or self._contains_nan(actual_rows)
        has_inf = self._contains_inf(expected_rows) or self._contains_inf(actual_rows)

        max_abs_error = 0.0
        max_rel_error = 0.0
        passed = shape_match and not has_nan and not has_inf

        if passed:
            for exp_row, act_row in zip(expected_rows, actual_rows):
                for exp, act in zip(exp_row, act_row):
                    abs_error = abs(exp - act)
                    rel_error = _relative_error(exp, act)
                    max_abs_error = max(max_abs_error, abs_error)
                    max_rel_error = max(max_rel_error, rel_error)
                    if not (abs_error <= atol + rtol * abs(act)):
                        passed = False

        comparison_hash = self._compute_repeat_hash(expected_rows, actual_rows, atol, rtol)

        status = ValidationStatus.PASSED if passed else ValidationStatus.FAILED
        return NumericalValidationResult(
            status=status,
            shape_match=shape_match,
            has_nan=has_nan,
            has_inf=has_inf,
            max_abs_error=float(max_abs_error),
            max_rel_error=float(max_rel_error),
            atol=float(atol),
            rtol=float(rtol),
            comparison_hash=comparison_hash,
        )

    @staticmethod
    def _shape_matches(
        expected_rows: Tuple[Tuple[float, ...], ...],
        actual_rows: Tuple[Tuple[float, ...], ...],
    ) -> bool:
        if len(expected_rows) != len(actual_rows):
            return False
        return all(len(a) == len(b) for a, b in zip(expected_rows, actual_rows))

    @staticmethod
    def _contains_nan(rows: Tuple[Tuple[float, ...], ...]) -> bool:
        return any(math.isnan(x) for row in rows for x in row)

    @staticmethod
    def _contains_inf(rows: Tuple[Tuple[float, ...], ...]) -> bool:
        return any(math.isinf(x) for row in rows for x in row)

    @staticmethod
    def _compute_repeat_hash(
        expected_rows: Tuple[Tuple[float, ...], ...],
        actual_rows: Tuple[Tuple[float, ...], ...],
        atol: float,
        rtol: float,
    ) -> str:
        """Deterministic SHA-256 digest of the full comparison."""
        payload = {
            "expected": expected_rows,
            "actual": actual_rows,
            "atol": atol,
            "rtol": rtol,
        }
        return hashlib.sha256(
            json.dumps(canonicalize(payload), sort_keys=True).encode("utf-8")
        ).hexdigest()


def _relative_error(expected: float, actual: float) -> float:
    """Relative error |a - b| / |b| with a well-defined zero convention."""
    if actual == 0.0:
        return 0.0 if expected == 0.0 else float("inf")
    return abs(expected - actual) / abs(actual)


def _validate_tolerance(atol: float, rtol: float) -> None:
    if not _is_number(atol) or atol < 0.0:
        raise NumericalComparisonError("atol must be a non-negative number")
    if not _is_number(rtol) or rtol < 0.0:
        raise NumericalComparisonError("rtol must be a non-negative number")


__all__ = [
    "NumericalComparator",
    "NumericalComparisonError",
    "NumericalValidationResult",
    "ValidationStatus",
]
