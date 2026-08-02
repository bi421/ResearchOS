"""
Backend compatibility verification for the Quant Computation Engine.

This module verifies that two ``QuantComputationInterface`` implementations
(the pure Python reference backend and the C++ adapter) produce equivalent
results. It is a RESEARCH/QA tool — it makes no trading decisions.

What is compared:
    - ``calculate_returns`` (absolute / percentage / log)
    - ``calculate_volatility`` (standard_deviation / rolling / change)
    - ``calculate_drawdown``
    - ``calculate_statistics``
    - ``calculate_metrics``
    - ``calculate_performance_analytics``
    - ``run_simulation`` (full ``SimulationResult`` incl. provenance)

Tolerance policy (CALCULATION_V1):
    - returns / equity_curve : expected bit-identical; tolerance 1e-12 (relative)
      guards against platform differences.
    - metrics / statistics / drawdown / volatility : relative tolerance 1e-9,
      absolute tolerance 1e-12. C++ and Python summation order can differ in
      the last bit (IEEE-754), so values agree to ~1e-16 relative. The adapter
      applies ResearchOS normalization (int ``count`` / ``recovery_period``,
      8dp ``max_drawdown``, recomputed ``calmar_ratio``) so these fields match.
    - performance : exact (computed by the same ResearchOS reference function
      on bit-identical returns).
    - provenance (``input_hash``, ``simulation_id``, dataset fields) : exact.

Hash parity:
    ResearchOS ``compute_result_hash`` serializes full-precision floats, so
    last-bit summation noise between backends changes the raw ``result_hash``.
    ``canonical_result_hash`` removes this noise (12 significant digits for
    floats, plus the ResearchOS 10dp rounding of returns/equity) and produces
    a single deterministic digest both backends must reproduce identically.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from researchos.core.identity import deterministic_hash
from researchos.quant_engine.interface import QuantComputationInterface
from researchos.quant_engine.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)

_DEFAULT_SIG_DIGITS = 12

# Section -> (relative tolerance, absolute tolerance)
DEFAULT_TOLERANCES: Dict[str, Tuple[float, float]] = {
    "returns": (1e-12, 1e-12),
    "equity_curve": (1e-12, 1e-12),
    "metrics": (1e-9, 1e-12),
    "statistics": (1e-9, 1e-12),
    "performance": (0.0, 0.0),
    "drawdown": (1e-9, 1e-12),
    "volatility": (1e-9, 1e-12),
    "provenance": (0.0, 0.0),
}


# ── scalar / collection comparison ───────────────────────────────────────────

def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def compare_values(a: Any, b: Any, *, rtol: float, atol: float) -> bool:
    """Compare two values for equality within ``rtol`` / ``atol``."""
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or a == b

    if _is_number(a) and _is_number(b):
        if math.isnan(a) or math.isnan(b):
            return bool(math.isnan(a) and math.isnan(b))
        if math.isinf(a) or math.isinf(b):
            return bool(a == b)
        return bool(abs(a - b) <= atol + rtol * abs(b))

    if isinstance(a, str) and isinstance(b, str):
        return a == b

    if a is None or b is None:
        return a is b

    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(compare_values(x, y, rtol=rtol, atol=atol) for x, y in zip(a, b))

    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(
            compare_values(a[k], b[k], rtol=rtol, atol=atol) for k in a
        )

    return bool(a == b)


def _rel_diff(a: Any, b: Any) -> Optional[float]:
    if _is_number(a) and _is_number(b) and not math.isnan(a) and not math.isnan(b) and not math.isinf(a) and not math.isinf(b):
        if b == 0.0:
            return 0.0 if a == 0.0 else float("inf")
        return float(abs(a - b) / abs(b))
    return None


def _abs_diff(a: Any, b: Any) -> Optional[float]:
    if _is_number(a) and _is_number(b):
        return float(abs(a - b))
    return None


# ── canonical hash ───────────────────────────────────────────────────────────

def _canonical_scalar(value: Any, sig_digits: int) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return value
        if value == 0.0:
            return 0.0
        return float(f"{value:.{sig_digits}g}")
    if isinstance(value, int):
        return value
    return value


def canonicalize(value: Any, sig_digits: int = _DEFAULT_SIG_DIGITS) -> Any:
    """Recursively round floats to ``sig_digits`` significant digits."""
    if isinstance(value, dict):
        return {k: canonicalize(v, sig_digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonicalize(v, sig_digits) for v in value]
    return _canonical_scalar(value, sig_digits)


def canonical_result_hash(
    result: SimulationResult,
    sig_digits: int = _DEFAULT_SIG_DIGITS,
) -> str:
    """
    Deterministic digest of a ``SimulationResult`` that is stable across the
    Python and C++ backends.

    Follows ``SimulationResult.compute_result_hash`` (returns/equity rounded to
    10 decimal places) but also canonicalizes every other float to 12
    significant digits, absorbing last-bit IEEE-754 summation noise.
    """
    content = {
        "simulation_id": result.simulation_id,
        "dataset_reference": result.dataset_reference,
        "dataset_version": result.dataset_version,
        "calculation_version": result.calculation_version.value,
        "parameters": dict(sorted(result.parameters.items())),
        "start_time": result.start_time,
        "end_time": result.end_time,
        "input_hash": result.input_hash,
        "returns": [round(r, 10) for r in result.returns],
        "equity_curve": [round(e, 10) for e in result.equity_curve],
        "metrics": dict(sorted(result.metrics.items())),
        "statistics": dict(sorted(result.statistics.items())),
        "performance": dict(sorted(result.performance.items())),
        "metadata": dict(sorted(result.metadata.items())),
    }
    return deterministic_hash(canonicalize(content, sig_digits))


# ── report data model ────────────────────────────────────────────────────────

@dataclass
class FieldDiff:
    """A single field comparison between the Python and C++ backends."""

    path: str
    py_value: Any
    cpp_value: Any
    matched: bool
    rel_diff: Optional[float] = None
    abs_diff: Optional[float] = None
    tolerance: str = ""


@dataclass
class SectionResult:
    """Comparison outcome for one result section (returns, metrics, ...)."""

    name: str
    matched: bool
    exact: bool
    detail: str = ""


@dataclass
class CompatibilityReport:
    """Full cross-backend parity report."""

    matched: bool = True
    hash_parity: bool = False
    input_hash_matches: bool = False
    simulation_id_matches: bool = False
    sections: Dict[str, SectionResult] = field(default_factory=dict)
    field_diffs: List[FieldDiff] = field(default_factory=list)
    backend_versions: Dict[str, str] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["Backend compatibility report", "========================="]
        lines.append(f"  Python backend  : {self.backend_versions.get('python', '?')}")
        lines.append(f"  C++ backend     : {self.backend_versions.get('cpp', '?')}")
        lines.append(f"  Overall match   : {self.matched}")
        lines.append(f"  Hash parity     : {self.hash_parity}")
        lines.append(f"  input_hash      : {self.input_hash_matches}")
        lines.append(f"  simulation_id   : {self.simulation_id_matches}")
        for name in sorted(self.sections):
            sec = self.sections[name]
            lines.append(f"  {name:<14}: {'OK' if sec.matched else 'MISMATCH'} "
                         f"({'exact' if sec.exact else 'within tolerance'})")
        for note in self.notes:
            lines.append(f"  note: {note}")
        if not self.matched:
            lines.append("  Field differences:")
            for d in self.field_diffs:
                if not d.matched:
                    lines.append(
                        f"    {d.path}: python={d.py_value!r} "
                        f"cpp={d.cpp_value!r} (tol {d.tolerance})"
                    )
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched": self.matched,
            "hash_parity": self.hash_parity,
            "input_hash_matches": self.input_hash_matches,
            "simulation_id_matches": self.simulation_id_matches,
            "sections": {
                name: {
                    "matched": sec.matched,
                    "exact": sec.exact,
                    "detail": sec.detail,
                }
                for name, sec in sorted(self.sections.items())
            },
            "backend_versions": dict(self.backend_versions),
            "field_diffs": [
                {
                    "path": d.path,
                    "matched": d.matched,
                    "rel_diff": d.rel_diff,
                    "abs_diff": d.abs_diff,
                    "tolerance": d.tolerance,
                }
                for d in self.field_diffs
            ],
            "notes": list(self.notes),
        }

    def assert_matches(self, *, check_hash: bool = True) -> None:
        """Raise AssertionError with a full report if parity is violated."""
        failures = []
        if not self.matched:
            failures.append("field parity mismatch")
        if check_hash and not self.hash_parity:
            failures.append("canonical result-hash parity mismatch")
        if check_hash and not self.input_hash_matches:
            failures.append("input_hash mismatch")
        if not failures:
            return
        raise AssertionError(
            "Backend parity check failed: " + "; ".join(failures) + "\n" + self.summary()
        )


# ── verification entry points ────────────────────────────────────────────────

def _make_default_request(prices: List[float], risk_free_rate: float) -> SimulationRequest:
    return SimulationRequest(
        dataset_reference="XAU/USD:PARITY",
        dataset_version="1.0.0",
        calculation_version=CalculationVersion.CALCULATION_V1,
        start_time="",
        end_time="",
        parameters={
            "initial_capital": 100000.0,
            "risk_free_rate": risk_free_rate,
        },
        seed=42,
    )


def verify_backend_parity(
    python_backend: QuantComputationInterface,
    cpp_backend: QuantComputationInterface,
    prices: List[float],
    request: Optional[SimulationRequest] = None,
    risk_free_rate: float = 0.0,
    tolerances: Optional[Dict[str, Tuple[float, float]]] = None,
) -> CompatibilityReport:
    """
    Run both backends over the same prices and produce a full parity report.

    Args:
        python_backend: The reference ``PythonQuantBackend`` (or any conforming
            implementation).
        cpp_backend: The backend under test (``CppQuantAdapter`` or another).
        prices: Historical price series (oldest to newest).
        request: Optional ``SimulationRequest``; a deterministic default is used
            when omitted.
        risk_free_rate: Annual risk-free rate used when building the default
            request and for the direct ``calculate_metrics`` comparison.
        tolerances: Optional per-section ``{name: (rtol, atol)}`` overrides.

    Returns:
        A ``CompatibilityReport``; call ``assert_matches()`` to raise on failure.
    """
    if request is None:
        request = _make_default_request(prices, risk_free_rate)

    tol = dict(DEFAULT_TOLERANCES)
    if tolerances:
        tol.update(tolerances)

    report = CompatibilityReport()
    report.backend_versions = {
        "python": _safe_version(python_backend),
        "cpp": _safe_version(cpp_backend),
    }

    # Simulation results
    py_result = python_backend.run_simulation(request, prices)
    cpp_result = cpp_backend.run_simulation(request, prices)

    report.input_hash_matches = py_result.input_hash == cpp_result.input_hash
    report.simulation_id_matches = py_result.simulation_id == cpp_result.simulation_id

    equity = py_result.equity_curve

    # Direct helper-method comparisons
    _compare_section(
        report,
        "returns",
        python_backend.calculate_returns(prices, "percentage"),
        cpp_backend.calculate_returns(prices, "percentage"),
        tol["returns"],
        path="calculate_returns",
    )
    _compare_section(
        report,
        "volatility",
        _volatility_by_method(python_backend, py_result.returns),
        _volatility_by_method(cpp_backend, py_result.returns),
        tol["volatility"],
        path="calculate_volatility",
    )
    _compare_section(
        report,
        "drawdown",
        python_backend.calculate_drawdown(equity),
        cpp_backend.calculate_drawdown(equity),
        tol["drawdown"],
        path="calculate_drawdown",
    )
    _compare_section(
        report,
        "statistics",
        python_backend.calculate_statistics(py_result.returns),
        cpp_backend.calculate_statistics(py_result.returns),
        tol["statistics"],
        path="calculate_statistics",
    )
    _compare_section(
        report,
        "metrics",
        python_backend.calculate_metrics(py_result.returns, equity, risk_free_rate),
        cpp_backend.calculate_metrics(py_result.returns, equity, risk_free_rate),
        tol["metrics"],
        path="calculate_metrics",
    )
    _compare_section(
        report,
        "performance",
        python_backend.calculate_performance_analytics(py_result.returns),
        cpp_backend.calculate_performance_analytics(py_result.returns),
        tol["performance"],
        path="calculate_performance_analytics",
    )

    # Result content
    _compare_section(
        report, "returns", py_result.returns, cpp_result.returns, tol["returns"], path="result.returns"
    )
    _compare_section(
        report,
        "equity_curve",
        py_result.equity_curve,
        cpp_result.equity_curve,
        tol["equity_curve"],
        path="result.equity_curve",
    )
    _compare_section(
        report, "metrics", py_result.metrics, cpp_result.metrics, tol["metrics"], path="result.metrics"
    )
    _compare_section(
        report,
        "statistics",
        py_result.statistics,
        cpp_result.statistics,
        tol["statistics"],
        path="result.statistics",
    )
    _compare_section(
        report,
        "performance",
        py_result.performance,
        cpp_result.performance,
        tol["performance"],
        path="result.performance",
    )
    _compare_section(
        report,
        "provenance",
        _provenance(py_result),
        _provenance(cpp_result),
        tol["provenance"],
        path="result.provenance",
    )

    if py_result.input_hash != cpp_result.input_hash:
        report.matched = False

    # Hash parity via canonical digest (removes last-bit summation noise).
    canonical_py = canonical_result_hash(py_result)
    canonical_cpp = canonical_result_hash(cpp_result)
    report.hash_parity = (
        report.input_hash_matches and canonical_py == canonical_cpp
    )
    if py_result.result_hash != cpp_result.result_hash:
        report.notes.append(
            "raw result_hash differs across backends (expected): ResearchOS hashes "
            "full-precision floats, so IEEE-754 last-bit summation noise between "
            "C++ and Python changes the digest; canonical_result_hash removes it "
            "for cross-backend verification."
        )
    if py_result.input_hash != cpp_result.input_hash:
        report.notes.append("input_hash differs: provenance serialization differs across backends.")

    return report


def _safe_version(backend: QuantComputationInterface) -> str:
    getter = getattr(backend, "get_version", None)
    if callable(getter):
        try:
            return str(getter())
        except Exception:
            pass
    return type(backend).__name__


def _volatility_by_method(backend: QuantComputationInterface, returns: List[float]) -> Dict[str, float]:
    """Collect volatility for every supported method that applies to the data."""
    out: Dict[str, float] = {}
    for method in ("standard_deviation", "rolling", "change"):
        try:
            out[method] = backend.calculate_volatility(returns, method=method)
        except ValueError:
            pass  # rolling / change need enough samples; both backends skip equally
    return out


def _provenance(result: SimulationResult) -> Dict[str, Any]:
    return {
        "simulation_id": result.simulation_id,
        "dataset_reference": result.dataset_reference,
        "dataset_version": result.dataset_version,
        "calculation_version": result.calculation_version.value,
        "start_time": result.start_time,
        "end_time": result.end_time,
        "input_hash": result.input_hash,
        "parameters": dict(sorted(result.parameters.items())),
    }


def _compare_section(
    report: CompatibilityReport,
    name: str,
    py_value: Any,
    cpp_value: Any,
    tolerance: Tuple[float, float],
    *,
    path: str,
) -> None:
    rtol, atol = tolerance
    matched = compare_values(py_value, cpp_value, rtol=rtol, atol=atol)
    exact = rtol == 0.0 and atol == 0.0
    report.sections[name] = SectionResult(
        name=name,
        matched=matched,
        exact=matched and exact,
        detail=_section_detail(name, matched, rtol, atol),
    )
    if not matched:
        report.matched = False
    _collect_diffs(report, name, py_value, cpp_value, rtol, atol, path)


def _section_detail(name: str, matched: bool, rtol: float, atol: float) -> str:
    if matched:
        if rtol == 0.0 and atol == 0.0:
            return "exact match"
        return f"within tolerance (rtol={rtol:g}, atol={atol:g})"
    return f"outside tolerance (rtol={rtol:g}, atol={atol:g})"


def _collect_diffs(
    report: CompatibilityReport,
    name: str,
    py_value: Any,
    cpp_value: Any,
    rtol: float,
    atol: float,
    path: str,
) -> None:
    if isinstance(py_value, dict) and isinstance(cpp_value, dict):
        for key in sorted(set(py_value) | set(cpp_value)):
            _collect_diffs(
                report,
                name,
                py_value.get(key, _MISSING),
                cpp_value.get(key, _MISSING),
                rtol,
                atol,
                f"{path}.{key}",
            )
        return
    if isinstance(py_value, (list, tuple)) and isinstance(cpp_value, (list, tuple)):
        if len(py_value) == len(cpp_value):
            for i, (a, b) in enumerate(zip(py_value, cpp_value)):
                _collect_diffs(report, name, a, b, rtol, atol, f"{path}[{i}]")
        else:
            report.field_diffs.append(
                FieldDiff(path, py_value, cpp_value, False, tolerance=f"rtol={rtol:g},atol={atol:g}")
            )
        return
    matched = compare_values(py_value, cpp_value, rtol=rtol, atol=atol)
    report.field_diffs.append(
        FieldDiff(
            path=path,
            py_value=py_value,
            cpp_value=cpp_value,
            matched=matched,
            rel_diff=_rel_diff(py_value, cpp_value) if _is_number(py_value) and _is_number(cpp_value) else None,
            abs_diff=_abs_diff(py_value, cpp_value),
            tolerance=f"rtol={rtol:g},atol={atol:g}",
        )
    )


class _Missing:
    """Sentinel for a key present in one backend but not the other."""

    _instance: Optional["_Missing"] = None

    def __new__(cls) -> "_Missing":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<missing>"


_MISSING = _Missing()
