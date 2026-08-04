"""
ResearchOS Macro Intelligence Layer - Econometrics Autocorrelation
Version: ecm/acf/v1
Status: FROZEN

Autocorrelation function (ACF) and partial autocorrelation function (PACF).

Canonical owner of ACF/PACF in the Econometrics Engine. Deterministic,
pure, stdlib-only.

MIL-ECM-006: Econometrics owns ACF/PACF.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from macro_intelligence.statistics.descriptive import mean
from macro_intelligence.statistics.provenance import StatisticalProvenance
from macro_intelligence.econometrics.matrix import solve
from macro_intelligence.econometrics.models import (
    TestResult,
    deterministic_hash,
)

ACF_VERSION = "ecm/acf/v1"
PACF_VERSION = "ecm/pacf/v1"


def _autocovariance(values: List[float], lag: int) -> float:
    """Sample autocovariance at the given lag (mean-centered)."""
    n = len(values)
    if n <= lag:
        return 0.0
    m = mean(values)
    total = 0.0
    for i in range(n - lag):
        total += (values[i] - m) * (values[i + lag] - m)
    return total / n


def autocorrelation(
    values: List[float],
    max_lag: int = 10,
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    Compute the autocorrelation function (ACF) up to ``max_lag``.

    Returns:
        TestResult with statistic = max autocorrelation, and the full ACF
        placed in ``critical_values`` under the key ``"acf"``.
    """
    n = len(values)
    if n < 2:
        raise ValueError("Need at least 2 observations for ACF")
    max_lag = min(max_lag, n - 1)
    if max_lag < 1:
        max_lag = 1

    var0 = _autocovariance(values, 0)
    acf = []
    for lag in range(1, max_lag + 1):
        cov = _autocovariance(values, lag)
        acf.append(cov / var0 if var0 != 0 else 0.0)

    # Approximate significance band: 1.96 / sqrt(n).
    band = 1.96 / (n ** 0.5)
    significant = max_lag > 0 and any(abs(a) > band for a in acf)

    params = {"max_lag": max_lag, "n_observations": n}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="autocorrelation",
        method_version=ACF_VERSION,
        parameters=params,
    )
    critical = {"acf": acf, "band": band}
    return TestResult(
        test_name="autocorrelation",
        statistic=max(acf) if acf else 0.0,
        p_value=None,
        critical_values=critical,
        is_significant=significant,
        parameters=params,
        provenance=prov,
    )


def partial_autocorrelation(
    values: List[float],
    max_lag: int = 10,
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    Compute the partial autocorrelation function (PACF) up to ``max_lag``.

    Uses the Yule-Walker equations solved via OLS for each order.

    Returns:
        TestResult with statistic = max |PACF|, and the full PACF in
        ``critical_values["pacf"]``.
    """
    n = len(values)
    if n < 3:
        raise ValueError("Need at least 3 observations for PACF")
    max_lag = min(max_lag, n - 2)
    if max_lag < 1:
        max_lag = 1

    # Autocorrelations r_1..r_max_lag.
    var0 = _autocovariance(values, 0)
    r = []
    for lag in range(1, max_lag + 1):
        cov = _autocovariance(values, lag)
        r.append(cov / var0 if var0 != 0 else 0.0)

    pacf = []
    for lag in range(1, max_lag + 1):
        # Build the Yule-Walker system: R a = r, where R is the Toeplitz
        # autocorrelation matrix and a is the AR(lag) coefficients.
        R = [[0.0] * lag for _ in range(lag)]
        for i in range(lag):
            for j in range(lag):
                R[i][j] = r[abs(i - j)] if abs(i - j) < len(r) else 0.0
        rhs = r[:lag]
        try:
            ar_coeffs = solve(R, rhs)
        except ValueError:
            ar_coeffs = [0.0] * lag
        # PACF at this lag = last AR coefficient.
        pacf.append(ar_coeffs[-1] if ar_coeffs else 0.0)

    band = 1.96 / (n ** 0.5)
    significant = any(abs(p) > band for p in pacf)

    params = {"max_lag": max_lag, "n_observations": n}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="partial_autocorrelation",
        method_version=PACF_VERSION,
        parameters=params,
    )
    critical = {"pacf": pacf, "band": band}
    return TestResult(
        test_name="partial_autocorrelation",
        statistic=max(abs(p) for p in pacf) if pacf else 0.0,
        p_value=None,
        critical_values=critical,
        is_significant=significant,
        parameters=params,
        provenance=prov,
    )


__all__ = ["autocorrelation", "partial_autocorrelation", "ACF_VERSION", "PACF_VERSION"]
