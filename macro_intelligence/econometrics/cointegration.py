"""
ResearchOS Macro Intelligence Layer - Econometrics Cointegration
Version: ecm/coint/v1
Status: FROZEN

Canonical owner of the Engle-Granger cointegration test.

MIL-ECM-008: Econometrics owns Engle-Granger.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from macro_intelligence.statistics.descriptive import mean
from macro_intelligence.statistics.provenance import StatisticalProvenance
from macro_intelligence.econometrics.models import TestResult

ENGLE_GRANGER_VERSION = "ecm/engle_granger/v1"

# Approximate Engle-Granger critical values (no trend), MacKinnon 1990.
_EG_CRITICAL = {
    0.01: -3.96,
    0.05: -3.37,
    0.10: -3.07,
}


def _first_difference(values: List[float]) -> List[float]:
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def engle_granger(
    y: List[float],
    x: List[float],
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    Engle-Granger two-step cointegration test.

    Step 1: Regress y on x (with intercept) → residuals.
    Step 2: ADF test on the residuals (without intercept).

    Null hypothesis: no cointegration (residuals contain a unit root).

    Args:
        y: Dependent series.
        x: Independent series.

    Returns:
        TestResult with the ADF statistic on residuals.
    """
    n = len(y)
    if n < 4:
        raise ValueError("Need at least 4 observations for Engle-Granger")
    if len(x) != n:
        raise ValueError("x and y must have the same length")

    # Step 1: OLS y on x with intercept.
    X = [[1.0, xi] for xi in x]
    from macro_intelligence.econometrics.matrix import transpose, matmul, solve
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    Xty = matmul(Xt, [[v] for v in y])
    try:
        beta = solve(XtX, [row[0] for row in Xty])
    except ValueError:
        raise ValueError("Singular design matrix in Engle-Granger")
    fitted = [beta[0] + beta[1] * xi for xi in x]
    residuals = [y[i] - fitted[i] for i in range(n)]

    # Step 2: ADF on residuals (no intercept).
    diff = _first_difference(residuals)
    m = len(diff)
    y_lag = residuals[: m - 1]
    X_aug = [[y_lag[i - 1]] for i in range(1, m)]  # only y_{t-1}
    y_aug = diff[1:]
    if len(y_aug) < 2:
        raise ValueError("Not enough observations for Engle-Granger")

    Xt = transpose(X_aug)
    XtX = matmul(Xt, X_aug)
    Xty = matmul(Xt, [[v] for v in y_aug])
    try:
        beta_aug = solve(XtX, [row[0] for row in Xty])
    except ValueError:
        beta_aug = [0.0]
    gamma = beta_aug[0]

    # Standard error of gamma. The regression is y_aug ~ X_aug where
    # X_aug[i] = y_lag[i] for i in 0..m-2, so fitted values align with
    # y_lag (length m-1) and must match y_aug (length m-1).
    fitted_aug = [gamma * v for v in y_lag]
    resid_aug = [y_aug[i] - fitted_aug[i] for i in range(len(y_aug))]
    rss = sum(r * r for r in resid_aug)
    df = len(y_aug) - 1
    if df <= 0:
        df = 1
    sigma2 = rss / df
    sxx = sum((v - mean(y_lag)) ** 2 for v in y_lag)
    se_gamma = (sigma2 / sxx) ** 0.5 if sxx > 0 else 0.0
    eg_stat = gamma / se_gamma if se_gamma > 0 else 0.0

    critical = _EG_CRITICAL
    is_significant = eg_stat < critical[0.05]

    # Approximate p-value by interpolation.
    levels = sorted(critical.keys())
    stats = [critical[l] for l in levels]
    if eg_stat <= stats[0]:
        p_value = 0.005
    elif eg_stat >= stats[-1]:
        p_value = 0.2
    else:
        for i in range(len(levels) - 1):
            if stats[i] <= eg_stat <= stats[i + 1]:
                frac = (eg_stat - stats[i]) / (stats[i + 1] - stats[i])
                p_value = levels[i] + frac * (levels[i + 1] - levels[i])
                break
        else:
            p_value = 0.5

    params = {"n_observations": n, "lags": 0}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="engle_granger",
        method_version=ENGLE_GRANGER_VERSION,
        parameters=params,
    )
    return TestResult(
        test_name="engle_granger",
        statistic=eg_stat,
        p_value=p_value,
        critical_values=dict(critical),
        is_significant=is_significant,
        parameters=params,
        provenance=prov,
    )


__all__ = ["engle_granger", "ENGLE_GRANGER_VERSION"]
