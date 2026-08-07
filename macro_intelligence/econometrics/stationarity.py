"""
ResearchOS Macro Intelligence Layer - Econometrics Stationarity Tests
Version: ecm/stat/v1
Status: FROZEN

Canonical owner of stationarity tests: Augmented Dickey-Fuller (ADF) and
KPSS. Deterministic, pure, stdlib-only.

MIL-ECM-007: Econometrics owns ADF and KPSS.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from macro_intelligence.statistics.provenance import StatisticalProvenance
from macro_intelligence.econometrics.models import TestResult

ADF_VERSION = "ecm/adf/v1"
KPSS_VERSION = "ecm/kpss/v1"

# Approximate critical values (MacKinnon-style) for ADF at common levels.
# Rows: [1%, 5%, 10%] for the constant-only (no trend) specification.
_ADF_CRITICAL_NO_TREND = {
    0.01: -3.43,
    0.05: -2.86,
    0.10: -2.57,
}
_ADF_CRITICAL_TREND = {
    0.01: -3.96,
    0.05: -3.41,
    0.10: -3.13,
}

# Approximate KPSS critical values (no trend).
_KPSS_CRITICAL_LEVEL = {
    0.01: 0.739,
    0.05: 0.463,
    0.10: 0.347,
}
_KPSS_CRITICAL_TREND = {
    0.01: 0.216,
    0.05: 0.146,
    0.10: 0.119,
}


def _first_difference(values: List[float]) -> List[float]:
    """First differences of a series."""
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def _estimate_p_value(stat: float, critical: Dict[float, float]) -> float:
    """
    Approximate a p-value from a test statistic against critical values via
    linear interpolation in the normal-probability domain.
    """
    # Sort levels ascending for the ADF (reject when stat < critical).
    levels = sorted(critical.keys())
    stats = [critical[level] for level in levels]
    # If stat is beyond the most extreme critical value, clip.
    if stat <= stats[0]:
        return max(levels[0] / 2.0, 0.001)
    if stat >= stats[-1]:
        return min(levels[-1] * 2.0, 0.999)
    # Interpolate between the two bracketing critical values.
    for i in range(len(levels) - 1):
        if stats[i] <= stat <= stats[i + 1]:
            frac = (stat - stats[i]) / (stats[i + 1] - stats[i])
            return levels[i] + frac * (levels[i + 1] - levels[i])
    return 0.5


def augmented_dickey_fuller(
    values: List[float],
    max_lag: int = 1,
    trend: str = "c",
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    Augmented Dickey-Fuller test for a unit root.

    Null hypothesis: the series has a unit root (non-stationary).
    Reject H0 (statistic < critical) → stationary.

    Args:
        values: Time series.
        max_lag: Number of lagged differences to include.
        trend: "c" (constant) or "ct" (constant + trend).

    Returns:
        TestResult with statistic, approximate p-value, and critical values.
    """
    n = len(values)
    if n < 3:
        raise ValueError("Need at least 3 observations for ADF")
    if trend not in ("c", "ct"):
        raise ValueError("trend must be 'c' or 'ct'")

    diff = _first_difference(values)
    m = len(diff)
    lags = min(max_lag, m - 2)
    if lags < 1:
        lags = 1

    # Build the regression: d(y_t) = beta0 + beta1*y_{t-1} + sum(delta_i*d(y_{t-i}))
    # (+ trend term if trend == "ct")
    y_lag = values[: m - 1]  # y_{t-1}
    X = []
    ys = diff[lags:]  # dependent variable aligned to after lags
    for i in range(lags, m):
        row = [1.0]
        if trend == "ct":
            row.append(float(i))  # trend t
        row.append(y_lag[i - 1])
        for lag in range(1, lags + 1):
            row.append(diff[i - lag])
        X.append(row)
    y = ys

    if len(y) < len(X[0]) + 1:
        raise ValueError("Not enough observations after lagging for ADF")

    # Solve OLS for ADF coefficients. If the design matrix is singular
    # (e.g. a pure linear trend makes the lagged differences collinear with
    # the intercept), apply a tiny ridge to the diagonal to obtain a stable
    # (deterministic) solution rather than failing.
    from macro_intelligence.econometrics.matrix import transpose, matmul, solve
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    Xty = matmul(Xt, [[v] for v in y])
    try:
        beta = solve(XtX, [row[0] for row in Xty])
    except ValueError:
        ridge = 1e-8
        XtX_ridge = [
            [XtX[i][j] + (ridge if i == j else 0.0) for j in range(len(XtX))]
            for i in range(len(XtX))
        ]
        beta = solve(XtX_ridge, [row[0] for row in Xty])

    # The coefficient of y_{t-1} is beta[1] for "c" and beta[2] for "ct".
    coef_idx = 2 if trend == "ct" else 1
    gamma = beta[coef_idx]
    se_gamma = _coefficient_se(X, y, beta, coef_idx)
    adf_stat = gamma / se_gamma if se_gamma > 0 else 0.0

    critical = _ADF_CRITICAL_TREND if trend == "ct" else _ADF_CRITICAL_NO_TREND
    p_value = _estimate_p_value(adf_stat, critical)
    is_significant = adf_stat < critical[0.05]

    params = {"max_lag": lags, "trend": trend}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="augmented_dickey_fuller",
        method_version=ADF_VERSION,
        parameters=params,
    )
    return TestResult(
        test_name="augmented_dickey_fuller",
        statistic=adf_stat,
        p_value=p_value,
        critical_values=dict(critical),
        is_significant=is_significant,
        parameters=params,
        provenance=prov,
    )


def _coefficient_se(
    X: List[List[float]],
    y: List[float],
    beta: List[float],
    idx: int,
) -> float:
    """Standard error of a coefficient in an OLS regression."""
    from macro_intelligence.econometrics.matrix import transpose, matmul, invert
    n = len(y)
    k = len(beta)
    fitted = [sum(b * xi for b, xi in zip(beta, row)) for row in X]
    residuals = [y[i] - fitted[i] for i in range(n)]
    rss = sum(r * r for r in residuals)
    df = n - k
    if df <= 0:
        df = 1
    sigma2 = rss / df
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    try:
        XtX_inv = invert(XtX)
    except ValueError:
        return 0.0
    return (sigma2 * XtX_inv[idx][idx]) ** 0.5 if XtX_inv[idx][idx] > 0 else 0.0


def kpss(
    values: List[float],
    trend: str = "c",
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    KPSS test for stationarity.

    Null hypothesis: the series is stationary.
    Reject H0 (statistic > critical) → non-stationary.

    Args:
        values: Time series.
        trend: "c" (constant) or "ct" (constant + trend).

    Returns:
        TestResult with statistic, critical values, and significance.
    """
    n = len(values)
    if n < 4:
        raise ValueError("Need at least 4 observations for KPSS")
    if trend not in ("c", "ct"):
        raise ValueError("trend must be 'c' or 'ct'")

    # Residuals from regressing y on a constant (or constant + trend).
    if trend == "c":
        X = [[1.0] for _ in range(n)]
    else:
        X = [[1.0, float(i)] for i in range(n)]

    from macro_intelligence.econometrics.matrix import transpose, matmul, solve
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    Xty = matmul(Xt, [[v] for v in values])
    try:
        beta = solve(XtX, [row[0] for row in Xty])
    except ValueError:
        raise ValueError("Singular design matrix in KPSS")
    fitted = [sum(b * xi for b, xi in zip(beta, row)) for row in X]
    residuals = [values[i] - fitted[i] for i in range(n)]

    # Partial sums of residuals.
    s = [0.0]
    for r in residuals:
        s.append(s[-1] + r)

    # Long-run variance (Bartlett kernel with lag = int(n ** 0.5)).
    lags = max(1, int(n ** 0.5))
    sigma2 = sum(r * r for r in residuals) / n
    for lag in range(1, lags + 1):
        weight = 1.0 - lag / (lags + 1.0)
        cov = sum(residuals[i] * residuals[i - lag] for i in range(lag, n)) / n
        sigma2 += 2.0 * weight * cov
    if sigma2 <= 0:
        sigma2 = 1e-12

    kpss_stat = sum(v * v for v in s) / (n * n * sigma2)

    critical = _KPSS_CRITICAL_TREND if trend == "ct" else _KPSS_CRITICAL_LEVEL
    is_significant = kpss_stat > critical[0.05]

    params = {"trend": trend, "n_observations": n}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="kpss",
        method_version=KPSS_VERSION,
        parameters=params,
    )
    return TestResult(
        test_name="kpss",
        statistic=kpss_stat,
        p_value=None,
        critical_values=dict(critical),
        is_significant=is_significant,
        parameters=params,
        provenance=prov,
    )


__all__ = ["augmented_dickey_fuller", "kpss", "ADF_VERSION", "KPSS_VERSION"]
