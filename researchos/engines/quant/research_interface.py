"""
ResearchComputationInterface — additive certified analytical surface.

Phase 5.1 — Certified Analytical Compute Surface (WP-1).

This module defines a NEW abstract interface that composes the existing,
deterministic analytical engines (technical, probability, portfolio,
historical, fundamental, econometrics, validation) behind the Phase 4
certification boundary.  It is strictly additive and does NOT modify the
frozen ``QuantComputationInterface``.

Design principles:
    - ``ResearchComputationInterface`` is a SEPARATE abstraction (additive),
      not a replacement for ``QuantComputationInterface``.  Research backends
      subclass BOTH so they remain registerable with the existing
      ``BackendRouter`` (which requires ``QuantComputationInterface``).
    - Every analytical operation is a pure, deterministic function of its
      explicit inputs.  No trading logic, no broker integration, no ML, no
      signal generation.
    - Each operation returns a ``ResearchResult`` carrying a deterministic
      ``input_hash`` and ``result_hash`` (canonical SHA-256 via
      ``backend_hash``), enabling provenance chaining.
    - Python reference remains the scientific source of truth; C++ is an
      optional certified acceleration candidate (delegates to the existing
      CppQuantAdapter capability; deterministic Python fallback otherwise).

This is a certification/trust layer only — it computes no trading decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from researchos.engines.quant.backend_hash import (
    canonicalize,
    compute_backend_result_hash,
    compute_input_hash,
)

#: Canonical analytical operations exposed by ResearchComputationInterface.
RESEARCH_OPERATIONS: Tuple[str, ...] = (
    "research_technical",
    "research_probabilistic_fit",
    "research_probabilistic_hypothesis",
    "research_portfolio_metrics",
    "research_historical",
    "research_fundamental",
    "research_econometric_analysis",
    "research_validation",
)

#: Stable version token for the research analytical surface.
RESEARCH_SURFACE_VERSION = "1.0.0"


@dataclass(frozen=True)
class ResearchResult:
    """Immutable, hashable, certified result of a research analytical op.

    Attributes:
        operation: The research operation name.
        domain: The analytical engine domain (e.g. ``"technical"``).
        output: The canonicalized, deterministic analytical output (dict or
            list-of-dict of primitives).
        parameters: The validated parameters used (canonicalized).
        input_hash: Deterministic SHA-256 of the operation inputs + params.
        result_hash: Deterministic SHA-256 of the full execution
            (operation + backend + version + input_hash + output).
        backend: Backend identifier that produced the output.
        version: Backend version that produced the output.
        methodology_version: Stable methodology token for the analytical
            computation (explainability envelope).
    """

    operation: str
    domain: str
    output: Any
    parameters: Any = field(default_factory=dict)
    input_hash: str = ""
    result_hash: str = ""
    backend: str = "unknown"
    version: str = ""
    methodology_version: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Return a deterministic, JSON-compatible mapping."""
        return {
            "operation": self.operation,
            "domain": self.domain,
            "output": self.output,
            "parameters": self.parameters,
            "input_hash": self.input_hash,
            "result_hash": self.result_hash,
            "backend": self.backend,
            "version": self.version,
            "methodology_version": self.methodology_version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ResearchResult":
        """Reconstruct from a ``to_dict()`` mapping."""
        return cls(
            operation=str(data["operation"]),
            domain=str(data["domain"]),
            output=data["output"],
            parameters=data.get("parameters", {}),
            input_hash=str(data.get("input_hash", "")),
            result_hash=str(data.get("result_hash", "")),
            backend=str(data.get("backend", "unknown")),
            version=str(data.get("version", "")),
            methodology_version=str(data.get("methodology_version", "")),
        )


def build_research_result(
    operation: str,
    domain: str,
    output: Any,
    parameters: Any,
    backend: str,
    version: str,
    methodology_version: str,
) -> ResearchResult:
    """Build a fully-hashed ``ResearchResult``.

    The ``input_hash`` covers the operation inputs + parameters (provenance).
    The ``result_hash`` covers the deterministic execution
    (operation + backend + version + input_hash + output), so identical
    executions always produce identical hashes.
    """
    input_payload = {"operation": operation, "parameters": canonicalize(parameters)}
    input_hash = compute_input_hash(input_payload)

    result_hash = compute_backend_result_hash(
        operation=operation,
        backend=backend,
        version=version,
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
        backend=backend,
        version=version,
        methodology_version=methodology_version,
    )


class ResearchComputationInterface:
    """
    Abstract interface for the certified research analytical surface.

    Research backends (Python reference + C++ candidate) implement this
    interface.  Because the certified ``BackendRouter`` requires
    ``QuantComputationInterface``, concrete research backends should also
    subclass that interface (or provide the 7 core operations) so they can be
    registered as router candidates.

    Every operation is deterministic and returns a ``ResearchResult``.
    """

    # ── identity / certification ────────────────────────────────────────

    def get_version(self) -> str:
        """Return a stable backend version string."""
        return type(self).__name__

    def capabilities(self) -> Any:
        """Return the advertised certification capabilities."""
        from researchos.engines.quant.research_engine import research_capabilities

        return research_capabilities(self)

    # ── analytical operations (all deterministic) ───────────────────────

    def research_technical(self, bars: Any, specs: Sequence[Any], **params: Any) -> ResearchResult:
        """Compute a batch of technical indicators. ``bars`` is a
        ``technical.contracts.Bars``; ``specs`` a sequence of
        ``technical.contracts.IndicatorSpec``."""
        raise NotImplementedError

    def research_probabilistic_fit(
        self, samples: Sequence[float], distribution: str, **params: Any
    ) -> ResearchResult:
        """Fit a probability distribution to samples (deterministic)."""
        raise NotImplementedError

    def research_probabilistic_hypothesis(
        self, samples: Sequence[float], test: str, **params: Any
    ) -> ResearchResult:
        """Run a deterministic hypothesis test."""
        raise NotImplementedError

    def research_portfolio_metrics(
        self, portfolio: Any, benchmark_returns: Optional[Sequence[float]] = None, **params: Any
    ) -> ResearchResult:
        """Compute deterministic portfolio analytics."""
        raise NotImplementedError

    def research_historical(
        self, returns: Sequence[float], metric: str, **params: Any
    ) -> ResearchResult:
        """Compute deterministic historical analytics."""
        raise NotImplementedError

    def research_fundamental(self, analytics: str, inputs: Any, **params: Any) -> ResearchResult:
        """Compute deterministic fundamental/macro analytics."""
        raise NotImplementedError

    def research_econometric_analysis(
        self, values: Sequence[float], model: str, **params: Any
    ) -> ResearchResult:
        """Run a deterministic econometric analysis."""
        raise NotImplementedError

    def research_validation(
        self,
        dataset: Any,
        train_size: int,
        validation_size: int,
        step_size: int,
        **params: Any,
    ) -> ResearchResult:
        """Run deterministic walk-forward validation."""
        raise NotImplementedError


__all__ = [
    "RESEARCH_OPERATIONS",
    "RESEARCH_SURFACE_VERSION",
    "ResearchResult",
    "ResearchComputationInterface",
    "build_research_result",
]
