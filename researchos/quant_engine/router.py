"""
BackendRouter — trust-boundary routing for computation backends.

Phase 4.1: backend certification and trust-boundary hardening.

The router enforces the certified execution flow::

    Request
      ↓
    Capability check
      ↓
    Candidate backend
      ↓
    Validation (against the Python reference backend)
      ↓
    Success → Return
      ↓ (else)
    Automatic Python fallback

The Python reference backend (``PythonQuantBackend``) remains the ONLY
scientific source of truth: candidate outputs are always validated against
it, and any candidate that fails capability, execution, or numerical
validation is replaced by the reference backend's output.

Every execution produces an immutable ``BackendExecutionMetadata`` record
(backend, version, fallback_used, validation_status, execution_time_ms,
result_hash, error_code).  ``result_hash`` is the deterministic canonical
SHA-256 digest of the execution (see ``backend_hash``); ``execution_time_ms``
is observational timing that is intentionally NOT part of the hash.

This is a certification/trust layer only — it computes nothing on its own and
makes no trading, signalling, or prediction decisions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from researchos.quant_engine.backend_hash import (
    compute_backend_result_hash,
    compute_input_hash,
)
from researchos.quant_engine.backend import PythonQuantBackend
from researchos.quant_engine.capabilities import BackendCapabilities
from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.numerical_validation import (
    NumericalComparator,
    NumericalValidationResult,
    ValidationStatus,
)

#: Stable error codes recorded in ``BackendExecutionMetadata.error_code``.
ERROR_OK = "ok"
ERROR_NO_CANDIDATE = "unavailable"
ERROR_EXECUTION_FAILED = "execution_failed"
ERROR_VALIDATION_FAILED = "validation_failed"
ERROR_CAPABILITY_MISSING = "capability_missing"
ERROR_TRUST_BOUNDARY = "trust_boundary_violation"


class BackendRouterError(Exception):
    """Base class for all BackendRouter errors."""


class BackendCapabilityError(BackendRouterError):
    """Raised when a backend advertises capabilities that violate the
    ResearchOS compute contract."""


class BackendValidationError(BackendRouterError):
    """Raised when a backend output fails numerical validation."""


class BackendExecutionError(BackendRouterError):
    """Raised when a backend cannot execute a requested operation."""


@dataclass(frozen=True)
class BackendExecutionMetadata:
    """Immutable audit record for one router execution.

    Attributes:
        operation: Operation name that was executed.
        backend: Backend identifier that produced the returned output.
        version: Backend version that produced the returned output.
        fallback_used: Whether the Python reference backend was used.
        validation_status: ``"passed"`` / ``"failed"`` / ``"not_required"``.
        execution_time_ms: Wall-clock time of the execution (observational).
        result_hash: Deterministic canonical SHA-256 of the execution.
        error_code: Stable error code describing the outcome.
    """

    operation: str
    backend: str
    version: str
    fallback_used: bool
    validation_status: str
    execution_time_ms: float
    result_hash: str
    error_code: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible mapping."""
        return {
            "operation": self.operation,
            "backend": self.backend,
            "version": self.version,
            "fallback_used": self.fallback_used,
            "validation_status": self.validation_status,
            "execution_time_ms": round(float(self.execution_time_ms), 6),
            "result_hash": self.result_hash,
            "error_code": self.error_code,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BackendExecutionMetadata":
        """Reconstruct from a ``to_dict()`` mapping."""
        return cls(
            operation=str(data["operation"]),
            backend=str(data["backend"]),
            version=str(data["version"]),
            fallback_used=bool(data["fallback_used"]),
            validation_status=str(data["validation_status"]),
            execution_time_ms=float(data["execution_time_ms"]),
            result_hash=str(data["result_hash"]),
            error_code=str(data["error_code"]),
        )


@dataclass(frozen=True)
class BackendExecutionResult:
    """Frozen result of one router execution: audit metadata + output.

    Attributes:
        metadata: Immutable ``BackendExecutionMetadata``.
        output: The returned backend output.
    """

    metadata: BackendExecutionMetadata
    output: Any


class BackendRouter:
    """Certification router that enforces the trust-boundary execution flow.

    The router is free of global state: every instance is fully independent.
    It is deterministic — for identical candidates, reference, request, and
    timings-independent inputs, the returned output and ``result_hash`` are
    identical.
    """

    def __init__(
        self,
        reference_backend: Optional[QuantComputationInterface] = None,
        candidates: Optional[List[QuantComputationInterface]] = None,
    ) -> None:
        self._reference = reference_backend or PythonQuantBackend()
        if not isinstance(self._reference, QuantComputationInterface):
            raise TypeError("reference_backend must implement QuantComputationInterface")
        self._candidates: List[QuantComputationInterface] = list(candidates or [])

    # ── configuration ────────────────────────────────────────────────────

    @property
    def reference_backend(self) -> QuantComputationInterface:
        """The certified Python reference backend (source of truth)."""
        return self._reference

    def set_reference(self, backend: QuantComputationInterface) -> None:
        """Replace the reference backend used for validation."""
        if not isinstance(backend, QuantComputationInterface):
            raise TypeError("reference backend must implement QuantComputationInterface")
        self._reference = backend

    def register(self, backend: QuantComputationInterface) -> None:
        """Register a candidate backend eligible for routing.

        Raises:
            TypeError: If ``backend`` does not implement
                ``QuantComputationInterface``.
        """
        if not isinstance(backend, QuantComputationInterface):
            raise TypeError("candidate backend must implement QuantComputationInterface")
        if backend in self._candidates:
            return
        self._candidates.append(backend)

    def list_candidates(self) -> Tuple[BackendCapabilities, ...]:
        """Return the capability declarations of all registered candidates."""
        out: List[BackendCapabilities] = []
        for backend in self._candidates:
            caps = self._safe_capabilities(backend)
            if caps is not None:
                out.append(caps)
        return tuple(out)

    # ── execution ────────────────────────────────────────────────────────

    def execute(
        self,
        operation: str,
        inputs: Mapping[str, Any],
        expected: Any = None,
        atol: float = NumericalComparator.DEFAULT_ATOL,
        rtol: float = NumericalComparator.DEFAULT_RTOL,
    ) -> BackendExecutionResult:
        """Execute ``operation`` through the certified routing flow.

        Args:
            operation: Operation name exposed by ``QuantComputationInterface``.
            inputs: Mapping of keyword arguments for the operation.
            expected: Optional expected/reference output.  When ``None``, the
                reference backend is executed to produce the reference output.
            atol: Absolute tolerance for numerical validation.
            rtol: Relative tolerance for numerical validation.

        Returns:
            A frozen ``BackendExecutionResult`` (metadata + output).

        Raises:
            BackendRouterError: If inputs are not a mapping.
            BackendExecutionError: If no backend (including the reference)
                can execute the operation.
        """
        if not isinstance(inputs, Mapping):
            raise BackendRouterError("inputs must be a mapping of keyword arguments")

        comparator = NumericalComparator()
        input_hash = compute_input_hash(inputs)
        start = time.perf_counter()

        # ── 1. Capability check → candidate backend ──────────────────────
        candidate = self._select_candidate(operation)
        if candidate is None:
            return self._fallback(
                operation=operation,
                inputs=inputs,
                expected=expected,
                atol=atol,
                rtol=rtol,
                input_hash=input_hash,
                start=start,
                error_code=ERROR_NO_CANDIDATE,
            )

        caps = self._safe_capabilities(candidate)
        backend_name = caps.backend_name if caps is not None else type(candidate).__name__
        version = caps.version if caps is not None else "unknown"

        # ── 2. Candidate execution ────────────────────────────────────────
        try:
            output = self._invoke(candidate, operation, inputs)
        except Exception as exc:  # candidate failed → automatic Python fallback
            reason = f"{type(exc).__name__}: {exc}"
            return self._fallback(
                operation=operation,
                inputs=inputs,
                expected=expected,
                atol=atol,
                rtol=rtol,
                input_hash=input_hash,
                start=start,
                error_code=ERROR_EXECUTION_FAILED,
                _detail=reason,
            )

        # ── 3. Validation against the reference (source of truth) ────────
        if expected is None:
            try:
                expected = self._invoke(self._reference, operation, inputs)
            except Exception as exc:  # pragma: no cover - reference must work
                raise BackendExecutionError(
                    f"reference backend failed for {operation!r}: {exc}"
                ) from exc

        validation = comparator.compare(expected, output, atol=atol, rtol=rtol)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if validation.passed:
            result_hash = compute_backend_result_hash(
                operation, backend_name, version, input_hash, output
            )
            metadata = BackendExecutionMetadata(
                operation=operation,
                backend=backend_name,
                version=version,
                fallback_used=False,
                validation_status=ValidationStatus.PASSED.value,
                execution_time_ms=elapsed_ms,
                result_hash=result_hash,
                error_code=ERROR_OK,
            )
            return BackendExecutionResult(metadata=metadata, output=output)

        return self._fallback(
            operation=operation,
            inputs=inputs,
            expected=expected,
            atol=atol,
            rtol=rtol,
            input_hash=input_hash,
            start=start,
            error_code=ERROR_VALIDATION_FAILED,
            _detail=_validation_detail(validation),
        )

    # ── internals ────────────────────────────────────────────────────────

    def _select_candidate(self, operation: str) -> Optional[QuantComputationInterface]:
        for backend in self._candidates:
            caps = self._safe_capabilities(backend)
            if caps is None:
                continue
            if not caps.supports(operation):
                continue
            if not self._trust_boundary_ok(caps):
                continue
            return backend
        return None

    def _fallback(
        self,
        *,
        operation: str,
        inputs: Mapping[str, Any],
        expected: Any,
        atol: float,
        rtol: float,
        input_hash: str,
        start: float,
        error_code: str,
        _detail: str = "",
    ) -> BackendExecutionResult:
        """Execute the operation on the Python reference backend."""
        try:
            output = self._invoke(self._reference, operation, inputs)
        except Exception as exc:
            raise BackendExecutionError(
                f"no backend available for {operation!r}; reference failed: {exc}"
            ) from exc

        caps = self._safe_capabilities(self._reference)
        backend_name = caps.backend_name if caps is not None else type(self._reference).__name__
        version = caps.version if caps is not None else "unknown"

        validation_status = ValidationStatus.NOT_REQUIRED.value
        if expected is not None:
            validation = NumericalComparator().compare(expected, output, atol=atol, rtol=rtol)
            validation_status = validation.status.value

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        result_hash = compute_backend_result_hash(
            operation, backend_name, version, input_hash, output
        )
        metadata = BackendExecutionMetadata(
            operation=operation,
            backend=backend_name,
            version=version,
            fallback_used=True,
            validation_status=validation_status,
            execution_time_ms=elapsed_ms,
            result_hash=result_hash,
            error_code=error_code,
        )
        return BackendExecutionResult(metadata=metadata, output=output)

    @staticmethod
    def _safe_capabilities(backend: Any) -> Optional[BackendCapabilities]:
        getter = getattr(backend, "capabilities", None)
        if not callable(getter):
            return None
        try:
            return getter()
        except Exception:
            return None

    @staticmethod
    def _trust_boundary_ok(caps: BackendCapabilities) -> bool:
        return all(
            (
                caps.deterministic,
                caps.stateless,
                caps.no_timestamps,
                caps.no_randomness,
                caps.explicit_typing,
            )
        )

    @staticmethod
    def _invoke(backend: Any, operation: str, inputs: Mapping[str, Any]) -> Any:
        fn = getattr(backend, operation, None)
        if not callable(fn):
            raise BackendExecutionError(
                f"backend {type(backend).__name__!r} has no callable {operation!r}"
            )
        return fn(**dict(inputs))


def _validation_detail(validation: NumericalValidationResult) -> str:
    parts = []
    if not validation.shape_match:
        parts.append("shape mismatch")
    if validation.has_nan:
        parts.append("nan present")
    if validation.has_inf:
        parts.append("infinite value present")
    if not parts:
        parts.append(
            f"max_abs_error={validation.max_abs_error:.3e} "
            f"max_rel_error={validation.max_rel_error:.3e}"
        )
    return "; ".join(parts)


__all__ = [
    "ERROR_OK",
    "ERROR_NO_CANDIDATE",
    "ERROR_EXECUTION_FAILED",
    "ERROR_VALIDATION_FAILED",
    "ERROR_CAPABILITY_MISSING",
    "ERROR_TRUST_BOUNDARY",
    "BackendCapabilityError",
    "BackendExecutionError",
    "BackendExecutionMetadata",
    "BackendExecutionResult",
    "BackendRouter",
    "BackendRouterError",
    "BackendValidationError",
]
