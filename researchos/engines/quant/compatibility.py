"""
Backend compatibility verification for the Quant Computation Engine.

This module verifies numerical and structural parity between the Python
reference backend and the C++ backend.

This is a RESEARCH/QA certification tool only.
It makes no trading decisions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from researchos.core.identity import deterministic_hash
from researchos.engines.quant.interface import QuantComputationInterface
from researchos.engines.quant.models import (
    CalculationVersion,
    SimulationRequest,
    SimulationResult,
)

_DEFAULT_SIG_DIGITS = 12

DEFAULT_TOLERANCES: Dict[str, Tuple[float, float]] = {
    "returns": (1e-12, 1e-12),
    "equity_curve": (1e-12, 1e-12),
    "metrics": (1e-8, 1e-12),
    "statistics": (1e-9, 1e-12),
    "performance": (0.0, 0.0),
    "drawdown": (1e-9, 1e-12),
    "volatility": (1e-9, 1e-12),
    "provenance": (0.0, 0.0),
}


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def compare_values(
    a: Any,
    b: Any,
    *,
    rtol: float,
    atol: float,
) -> bool:
    """Compare two values recursively using rtol/atol."""

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

        return all(
            compare_values(
                x,
                y,
                rtol=rtol,
                atol=atol,
            )
            for x, y in zip(a, b)
        )

    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False

        return all(
            compare_values(
                a[k],
                b[k],
                rtol=rtol,
                atol=atol,
            )
            for k in a
        )

    return bool(a == b)


def _rel_diff(a: Any, b: Any) -> Optional[float]:
    if (
        _is_number(a)
        and _is_number(b)
        and not math.isnan(a)
        and not math.isnan(b)
        and not math.isinf(a)
        and not math.isinf(b)
    ):
        if b == 0.0:
            return 0.0 if a == 0.0 else float("inf")

        return float(abs(a - b) / abs(b))

    return None


def _abs_diff(a: Any, b: Any) -> Optional[float]:
    if _is_number(a) and _is_number(b):
        return float(abs(a - b))

    return None


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


def canonicalize(
    value: Any,
    sig_digits: int = _DEFAULT_SIG_DIGITS,
) -> Any:
    """Recursively canonicalize floating-point values."""

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
    Produce a deterministic cross-backend result digest.

    Returns and equity_curve follow ResearchOS 10dp hashing behavior.
    Other floating-point values are canonicalized to significant digits
    to absorb harmless IEEE-754 last-bit differences.
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


@dataclass
class FieldDiff:
    """Single field comparison."""

    path: str
    py_value: Any
    cpp_value: Any
    matched: bool
    rel_diff: Optional[float] = None
    abs_diff: Optional[float] = None
    tolerance: str = ""


@dataclass
class SectionResult:
    """Comparison outcome for one independent section."""

    name: str
    matched: bool
    exact: bool
    detail: str = ""


@dataclass
class CompatibilityReport:
    """Complete cross-backend parity certification report."""

    matched: bool = True
    hash_parity: bool = False
    input_hash_matches: bool = False
    simulation_id_matches: bool = False

    sections: Dict[str, SectionResult] = field(default_factory=dict)

    field_diffs: List[FieldDiff] = field(default_factory=list)

    backend_versions: Dict[str, str] = field(default_factory=dict)

    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "Backend compatibility report",
            "============================",
            f"  Python backend  : {self.backend_versions.get('python', '?')}",
            f"  C++ backend     : {self.backend_versions.get('cpp', '?')}",
            f"  Overall match   : {self.matched}",
            f"  Hash parity     : {self.hash_parity}",
            f"  input_hash      : {self.input_hash_matches}",
            f"  simulation_id   : {self.simulation_id_matches}",
            "",
            "  Sections:",
        ]

        for name in sorted(self.sections):
            sec = self.sections[name]

            status = "OK" if sec.matched else "MISMATCH"

            mode = "exact" if sec.exact else "within tolerance"

            lines.append(f"    {name:<24}: {status} ({mode})")

            if sec.detail:
                lines.append(f"      {sec.detail}")

        for note in self.notes:
            lines.append(f"  note: {note}")

        if not self.matched:
            lines.append("")
            lines.append("  Field differences:")

            for diff in self.field_diffs:
                if not diff.matched:
                    lines.append(
                        f"    {diff.path}: "
                        f"python={diff.py_value!r} "
                        f"cpp={diff.cpp_value!r} "
                        f"(tol {diff.tolerance})"
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
                    "matched": section.matched,
                    "exact": section.exact,
                    "detail": section.detail,
                }
                for name, section in sorted(self.sections.items())
            },
            "backend_versions": dict(self.backend_versions),
            "field_diffs": [
                {
                    "path": diff.path,
                    "matched": diff.matched,
                    "rel_diff": diff.rel_diff,
                    "abs_diff": diff.abs_diff,
                    "tolerance": diff.tolerance,
                }
                for diff in self.field_diffs
            ],
            "notes": list(self.notes),
        }

    def assert_matches(
        self,
        *,
        check_hash: bool = True,
    ) -> None:
        """Raise if certification requirements are violated."""

        failures = []

        if not self.matched:
            failures.append("field parity mismatch")

        if check_hash and not self.hash_parity:
            failures.append("canonical result-hash parity mismatch")

        if check_hash and not self.input_hash_matches:
            failures.append("input_hash mismatch")

        if not self.simulation_id_matches:
            failures.append("simulation_id mismatch")

        if not failures:
            return

        raise AssertionError(
            "Backend parity certification failed: " + "; ".join(failures) + "\n\n" + self.summary()
        )


def _make_default_request(
    prices: List[float],
    risk_free_rate: float,
) -> SimulationRequest:
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
    Execute complete Python/C++ parity certification.

    Every direct helper comparison and every SimulationResult section
    receives its own report entry. No section is overwritten.
    """

    if request is None:
        request = _make_default_request(
            prices,
            risk_free_rate,
        )

    tol = dict(DEFAULT_TOLERANCES)

    if tolerances:
        tol.update(tolerances)

    report = CompatibilityReport()

    report.backend_versions = {
        "python": _safe_version(python_backend),
        "cpp": _safe_version(cpp_backend),
    }

    # ------------------------------------------------------------
    # 1. Execute both complete simulations
    # ------------------------------------------------------------

    py_result = python_backend.run_simulation(
        request,
        prices,
    )

    cpp_result = cpp_backend.run_simulation(
        request,
        prices,
    )

    report.input_hash_matches = py_result.input_hash == cpp_result.input_hash

    report.simulation_id_matches = py_result.simulation_id == cpp_result.simulation_id

    # ------------------------------------------------------------
    # 2. DIRECT calculate_returns parity
    # ------------------------------------------------------------

    for method in (
        "absolute",
        "percentage",
        "log",
    ):
        try:
            py_returns = python_backend.calculate_returns(
                prices,
                method,
            )

            cpp_returns = cpp_backend.calculate_returns(
                prices,
                method,
            )

            _compare_section(
                report,
                f"direct_returns_{method}",
                py_returns,
                cpp_returns,
                tol["returns"],
                path=f"calculate_returns[{method}]",
            )

        except ValueError as exc:
            report.notes.append(f"calculate_returns[{method}] unsupported: {exc}")

    # ------------------------------------------------------------
    # 3. DIRECT volatility parity
    #    IMPORTANT: each backend uses its OWN returns.
    # ------------------------------------------------------------

    py_volatility = _volatility_by_method(
        python_backend,
        py_result.returns,
    )

    cpp_volatility = _volatility_by_method(
        cpp_backend,
        cpp_result.returns,
    )

    _compare_section(
        report,
        "direct_volatility",
        py_volatility,
        cpp_volatility,
        tol["volatility"],
        path="calculate_volatility",
    )

    # ------------------------------------------------------------
    # 4. DIRECT drawdown parity
    # ------------------------------------------------------------

    _compare_section(
        report,
        "direct_drawdown",
        python_backend.calculate_drawdown(py_result.equity_curve),
        cpp_backend.calculate_drawdown(cpp_result.equity_curve),
        tol["drawdown"],
        path="calculate_drawdown",
    )

    # ------------------------------------------------------------
    # 5. DIRECT statistics parity
    # ------------------------------------------------------------

    _compare_section(
        report,
        "direct_statistics",
        python_backend.calculate_statistics(py_result.returns),
        cpp_backend.calculate_statistics(cpp_result.returns),
        tol["statistics"],
        path="calculate_statistics",
    )

    # ------------------------------------------------------------
    # 6. DIRECT metrics parity
    # ------------------------------------------------------------

    _compare_section(
        report,
        "direct_metrics",
        python_backend.calculate_metrics(
            py_result.returns,
            py_result.equity_curve,
            risk_free_rate,
        ),
        cpp_backend.calculate_metrics(
            cpp_result.returns,
            cpp_result.equity_curve,
            risk_free_rate,
        ),
        tol["metrics"],
        path="calculate_metrics",
    )

    # ------------------------------------------------------------
    # 7. DIRECT performance parity
    # ------------------------------------------------------------

    _compare_section(
        report,
        "direct_performance",
        python_backend.calculate_performance_analytics(py_result.returns),
        cpp_backend.calculate_performance_analytics(cpp_result.returns),
        tol["performance"],
        path="calculate_performance_analytics",
    )

    # ------------------------------------------------------------
    # 8. SimulationResult returns
    # ------------------------------------------------------------

    _compare_section(
        report,
        "result_returns",
        py_result.returns,
        cpp_result.returns,
        tol["returns"],
        path="result.returns",
    )

    # ------------------------------------------------------------
    # 9. SimulationResult equity curve
    # ------------------------------------------------------------

    _compare_section(
        report,
        "result_equity_curve",
        py_result.equity_curve,
        cpp_result.equity_curve,
        tol["equity_curve"],
        path="result.equity_curve",
    )

    # ------------------------------------------------------------
    # 10. SimulationResult metrics
    # ------------------------------------------------------------

    _compare_section(
        report,
        "result_metrics",
        py_result.metrics,
        cpp_result.metrics,
        tol["metrics"],
        path="result.metrics",
    )

    # ------------------------------------------------------------
    # 11. SimulationResult statistics
    # ------------------------------------------------------------

    _compare_section(
        report,
        "result_statistics",
        py_result.statistics,
        cpp_result.statistics,
        tol["statistics"],
        path="result.statistics",
    )

    # ------------------------------------------------------------
    # 12. SimulationResult performance
    # ------------------------------------------------------------

    _compare_section(
        report,
        "result_performance",
        py_result.performance,
        cpp_result.performance,
        tol["performance"],
        path="result.performance",
    )

    # ------------------------------------------------------------
    # 13. Provenance
    # ------------------------------------------------------------

    _compare_section(
        report,
        "provenance",
        _provenance(py_result),
        _provenance(cpp_result),
        tol["provenance"],
        path="result.provenance",
    )

    # ------------------------------------------------------------
    # 14. Explicit identity checks
    # ------------------------------------------------------------

    if not report.input_hash_matches:
        report.matched = False
        report.notes.append("input_hash differs between Python and C++.")

    if not report.simulation_id_matches:
        report.matched = False
        report.notes.append("simulation_id differs between Python and C++.")

    # ------------------------------------------------------------
    # 15. Canonical hash parity
    # ------------------------------------------------------------

    canonical_py = canonical_result_hash(py_result)

    canonical_cpp = canonical_result_hash(cpp_result)

    report.hash_parity = (
        report.input_hash_matches and report.simulation_id_matches and canonical_py == canonical_cpp
    )

    if not report.hash_parity:
        report.matched = False

    # Raw hash may legitimately differ because of IEEE-754
    # last-bit floating-point differences.

    if py_result.result_hash != cpp_result.result_hash:
        report.notes.append(
            "raw result_hash differs across backends; "
            "canonical_result_hash is the cross-backend "
            "certification hash."
        )

    # ------------------------------------------------------------
    # 16. Final certification invariant
    # ------------------------------------------------------------

    if not all(section.matched for section in report.sections.values()):
        report.matched = False

    # Collapse any legacy/internal section labels that may have been
    # produced by older comparison paths.
    canonical_sections: Dict[str, SectionResult] = {}

    for section_name, section in report.sections.items():
        canonical_name = _canonical_section_name(section_name)

        previous = canonical_sections.get(canonical_name)

        if previous is None:
            canonical_sections[canonical_name] = SectionResult(
                name=canonical_name,
                matched=section.matched,
                exact=section.exact,
                detail=section.detail,
            )
        else:
            canonical_sections[canonical_name] = SectionResult(
                name=canonical_name,
                matched=previous.matched and section.matched,
                exact=previous.exact and section.exact,
                detail=(
                    previous.detail
                    if previous.matched and section.matched
                    else _section_detail(
                        canonical_name,
                        False,
                        tol[canonical_name][0],
                        tol[canonical_name][1],
                    )
                ),
            )

    # Stable public report schema.
    for section_name in DEFAULT_TOLERANCES:
        if section_name not in canonical_sections:
            rtol, atol = tol[section_name]
            canonical_sections[section_name] = SectionResult(
                name=section_name,
                matched=True,
                exact=(rtol == 0.0 and atol == 0.0),
                detail=_section_detail(section_name, True, rtol, atol),
            )

    report.sections = canonical_sections

    return report


def _safe_version(
    backend: QuantComputationInterface,
) -> str:
    getter = getattr(
        backend,
        "get_version",
        None,
    )

    if callable(getter):
        try:
            return str(getter())
        except Exception:
            pass

    return type(backend).__name__


def _volatility_by_method(
    backend: QuantComputationInterface,
    returns: List[float],
) -> Dict[str, float]:
    out: Dict[str, float] = {}

    for method in (
        "standard_deviation",
        "rolling",
        "change",
    ):
        try:
            out[method] = backend.calculate_volatility(
                returns,
                method=method,
            )
        except ValueError:
            continue

    return out


def _provenance(
    result: SimulationResult,
) -> Dict[str, Any]:
    return {
        "simulation_id": result.simulation_id,
        "dataset_reference": result.dataset_reference,
        "dataset_version": result.dataset_version,
        "calculation_version": (result.calculation_version.value),
        "start_time": result.start_time,
        "end_time": result.end_time,
        "input_hash": result.input_hash,
        "parameters": dict(sorted(result.parameters.items())),
    }


def _canonical_section_name(name: str) -> str:
    """
    Map detailed comparison labels to the stable public report schema.

    Multiple internal comparisons may contribute to the same logical
    compatibility section.  The public report must expose only the keys
    defined by DEFAULT_TOLERANCES.
    """
    direct_map = {
        "direct_returns_percentage": "returns",
        "direct_returns_absolute": "returns",
        "direct_returns_log": "returns",
        "direct_volatility": "volatility",
        "direct_drawdown": "drawdown",
        "direct_statistics": "statistics",
        "direct_metrics": "metrics",
        "direct_performance": "performance",
        "direct_performance_analytics": "performance",
        "result_returns": "returns",
        "result_equity_curve": "equity_curve",
        "result_metrics": "metrics",
        "result_statistics": "statistics",
        "result_performance": "performance",
        "result_provenance": "provenance",
    }

    if name in direct_map:
        return direct_map[name]

    if name in DEFAULT_TOLERANCES:
        return name

    if name.startswith("direct_"):
        candidate = name[len("direct_") :]
        if candidate in DEFAULT_TOLERANCES:
            return candidate

    if name.startswith("result_"):
        candidate = name[len("result_") :]
        if candidate in DEFAULT_TOLERANCES:
            return candidate

    return name


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

    matched = compare_values(
        py_value,
        cpp_value,
        rtol=rtol,
        atol=atol,
    )

    exact = matched and rtol == 0.0 and atol == 0.0

    report.sections[name] = SectionResult(
        name=name,
        matched=matched,
        exact=exact,
        detail=_section_detail(
            name,
            matched,
            rtol,
            atol,
        ),
    )

    if not matched:
        report.matched = False

        _collect_diffs(
            report,
            name,
            py_value,
            cpp_value,
            rtol,
            atol,
            path,
        )


def _section_detail(
    name: str,
    matched: bool,
    rtol: float,
    atol: float,
) -> str:
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
        for key in sorted(
            set(py_value) | set(cpp_value),
            key=str,
        ):
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
                _collect_diffs(
                    report,
                    name,
                    a,
                    b,
                    rtol,
                    atol,
                    f"{path}[{i}]",
                )
        else:
            report.field_diffs.append(
                FieldDiff(
                    path=path,
                    py_value=py_value,
                    cpp_value=cpp_value,
                    matched=False,
                    tolerance=(f"rtol={rtol:g},atol={atol:g}"),
                )
            )

        return

    matched = compare_values(
        py_value,
        cpp_value,
        rtol=rtol,
        atol=atol,
    )

    report.field_diffs.append(
        FieldDiff(
            path=path,
            py_value=py_value,
            cpp_value=cpp_value,
            matched=matched,
            rel_diff=(
                _rel_diff(
                    py_value,
                    cpp_value,
                )
                if (_is_number(py_value) and _is_number(cpp_value))
                else None
            ),
            abs_diff=_abs_diff(
                py_value,
                cpp_value,
            ),
            tolerance=(f"rtol={rtol:g},atol={atol:g}"),
        )
    )


class _Missing:
    """Sentinel for a key missing from one backend."""

    _instance: Optional["_Missing"] = None

    def __new__(cls) -> "_Missing":
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __repr__(self) -> str:
        return "<missing>"


_MISSING = _Missing()
