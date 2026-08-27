"""
Backend capabilities — certification contract for computation backends.

Phase 4.1: backend certification and trust-boundary hardening.

``BackendCapabilities`` is an immutable description of what a computation
backend advertises and guarantees.  It is the machine-readable half of the
trust boundary: the ``BackendRouter`` refuses to route work to a backend
whose advertised capabilities violate the ResearchOS compute contract
(determinism, statelessness, no timestamps, no randomness, explicit typing).

This is a certification/trust layer only — it computes nothing and executes
nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - annotation-only import
    from researchos.engines.quant.interface import QuantComputationInterface

#: The canonical operations exposed by ``QuantComputationInterface``.
QUANT_OPERATIONS: tuple[str, ...] = (
    "calculate_returns",
    "calculate_volatility",
    "calculate_drawdown",
    "calculate_statistics",
    "calculate_metrics",
    "calculate_performance_analytics",
    "run_simulation",
)

REFERENCE_BACKEND_NAME = "PythonQuantBackend"
REFERENCE_BACKEND_VERSION = "1.0.0"


class BackendCapabilitiesError(Exception):
    """Raised when a ``BackendCapabilities`` object is malformed."""


@dataclass(frozen=True)
class BackendCapabilities:
    """Immutable, hashable, serializable capability declaration.

    Attributes:
        backend_name: Stable backend identifier (e.g. ``"PythonQuantBackend"``).
        version: Backend version string (e.g. ``"1.0.0"``).
        supported_operations: Operations the backend can execute.
        deterministic: Whether identical inputs always produce identical
            outputs (no hidden random state).
        stateless: Whether the backend holds no hidden mutable state that
            affects computation.
        no_timestamps: Whether computation results never depend on wall-clock
            timestamps.
        no_randomness: Whether computation never consumes randomness.
        explicit_typing: Whether all inputs/outputs are explicitly typed
            (declared signatures, no implicit value coercion).
    """

    backend_name: str
    version: str
    supported_operations: tuple[str, ...]
    deterministic: bool = True
    stateless: bool = True
    no_timestamps: bool = True
    no_randomness: bool = True
    explicit_typing: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.backend_name, str) or not self.backend_name.strip():
            raise BackendCapabilitiesError("backend_name must be a non-empty string")
        if not isinstance(self.version, str) or not self.version.strip():
            raise BackendCapabilitiesError("version must be a non-empty string")
        if not isinstance(self.supported_operations, (tuple, list)):
            raise BackendCapabilitiesError("supported_operations must be a sequence of strings")
        operations = tuple(str(op) for op in self.supported_operations)
        object.__setattr__(self, "supported_operations", operations)

    def supports(self, operation: str) -> bool:
        """Return whether ``operation`` is advertised as supported."""
        return operation in self.supported_operations

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic, JSON-compatible mapping."""
        return {
            "backend_name": self.backend_name,
            "version": self.version,
            "supported_operations": sorted(self.supported_operations),
            "deterministic": self.deterministic,
            "stateless": self.stateless,
            "no_timestamps": self.no_timestamps,
            "no_randomness": self.no_randomness,
            "explicit_typing": self.explicit_typing,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BackendCapabilities:
        """Reconstruct a ``BackendCapabilities`` from a ``to_dict()`` mapping."""
        return cls(
            backend_name=str(data["backend_name"]),
            version=str(data["version"]),
            supported_operations=tuple(data.get("supported_operations", ())),
            deterministic=bool(data.get("deterministic", True)),
            stateless=bool(data.get("stateless", True)),
            no_timestamps=bool(data.get("no_timestamps", True)),
            no_randomness=bool(data.get("no_randomness", True)),
            explicit_typing=bool(data.get("explicit_typing", True)),
        )


def default_capabilities(backend: QuantComputationInterface) -> BackendCapabilities:
    """Build the default capability declaration for any conforming backend.

    The default advertises the full ``QuantComputationInterface`` operation
    set with the ResearchOS certification guarantees.  Concrete backends may
    override ``capabilities()`` to declare a narrower or more precise set.
    """
    return BackendCapabilities(
        backend_name=type(backend).__name__,
        version=backend.get_version(),
        supported_operations=QUANT_OPERATIONS,
        deterministic=True,
        stateless=True,
        no_timestamps=True,
        no_randomness=True,
        explicit_typing=True,
    )


__all__ = [
    "QUANT_OPERATIONS",
    "REFERENCE_BACKEND_NAME",
    "REFERENCE_BACKEND_VERSION",
    "BackendCapabilities",
    "BackendCapabilitiesError",
    "default_capabilities",
]
