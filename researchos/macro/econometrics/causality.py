"""
ResearchOS Macro Intelligence Layer - Econometrics Granger Causality
Version: ecm/granger/v1
Status: FROZEN

Canonical owner of the Granger causality test.

MIL-ECM-009: Econometrics owns Granger causality.
"""

from __future__ import annotations

from researchos.macro.econometrics.matrix import matmul, solve, transpose
from researchos.macro.econometrics.models import TestResult
from researchos.macro.statistics.distributions import t_distribution_p_value
from researchos.macro.statistics.provenance import StatisticalProvenance

GRANGER_VERSION = "ecm/granger/v1"


def _ols_residual_rss(
    y: list[float],
    X: list[list[float]],
) -> float:
    """Residual sum of squares from OLS of y on X."""
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    Xty = matmul(Xt, [[v] for v in y])
    try:
        beta = solve(XtX, [row[0] for row in Xty])
    except ValueError:
        return float("inf")
    fitted = [sum(b * xi for b, xi in zip(beta, row)) for row in X]
    return sum((y[i] - fitted[i]) ** 2 for i in range(len(y)))


def granger_causality(
    x: list[float],
    y: list[float],
    max_lag: int = 1,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> TestResult:
    """
    Granger causality test: does x Granger-cause y?

    Compares a restricted model (y ~ lags of y) against an unrestricted model
    (y ~ lags of y + lags of x) using an F-test.

    Null hypothesis: x does not Granger-cause y.

    Args:
        x: Candidate cause series.
        y: Response series.
        max_lag: Number of lags.

    Returns:
        TestResult with the F-statistic.
    """
    n = len(y)
    if n < 4:
        raise ValueError("Need at least 4 observations for Granger causality")
    if len(x) != n:
        raise ValueError("x and y must have the same length")
    max_lag = min(max_lag, n // 3)
    if max_lag < 1:
        max_lag = 1

    # Build sample aligned to max_lag.
    start = max_lag
    y_aligned = y[start:]
    rest = []
    unrst = []
    for t in range(start, n):
        # Restricted: intercept + lags of y.
        row_rest = [1.0] + [y[t - i] for i in range(1, max_lag + 1)]
        # Unrestricted: intercept + lags of y + lags of x.
        row_unrst = row_rest + [x[t - i] for i in range(1, max_lag + 1)]
        rest.append(row_rest)
        unrst.append(row_unrst)

    if len(y_aligned) <= len(unrst[0]) + 1:
        raise ValueError("Not enough observations for Granger causality")

    rss_rest = _ols_residual_rss(y_aligned, rest)
    rss_unrst = _ols_residual_rss(y_aligned, unrst)
    if rss_unrst == 0 or rss_unrst == float("inf"):
        f_stat = 0.0
        p_value = 1.0
    else:
        T = len(y_aligned)
        k_rest = len(rest[0])
        k_unrst = len(unrst[0])
        df_num = k_unrst - k_rest
        df_den = T - k_unrst
        if df_num <= 0 or df_den <= 0:
            f_stat = 0.0
            p_value = 1.0
        else:
            f_stat = ((rss_rest - rss_unrst) / df_num) / (rss_unrst / df_den)
            # Approximate p-value via t-distribution mapping (F is positive).
            p_value = t_distribution_p_value(f_stat**0.5, df_den)

    is_significant = p_value is not None and p_value < 0.05
    params = {"max_lag": max_lag, "n_observations": len(y_aligned)}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="granger_causality",
        method_version=GRANGER_VERSION,
        parameters=params,
    )
    return TestResult(
        test_name="granger_causality",
        statistic=f_stat,
        p_value=p_value,
        critical_values={},
        is_significant=is_significant,
        parameters=params,
        provenance=prov,
    )


__all__ = ["granger_causality", "GRANGER_VERSION"]
