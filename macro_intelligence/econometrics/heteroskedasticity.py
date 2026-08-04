"""
ResearchOS Macro Intelligence Layer - Econometrics Heteroskedasticity
Version: ecm/bp/v1
Status: FROZEN

Canonical owner of the Breusch-Pagan heteroskedasticity test.

MIL-ECM-011: Econometrics owns Breusch-Pagan.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from macro_intelligence.statistics.distributions import t_distribution_p_value
from macro_intelligence.statistics.provenance import StatisticalProvenance
from macro_intelligence.econometrics.matrix import transpose, matmul, solve
from macro_intelligence.econometrics.models import TestResult

BREUSCH_PAGAN_VERSION = "ecm/breusch_pagan/v1"


def breusch_pagan(
    y: List[float],
    x: List[List[float]],
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    Breusch-Pagan test for heteroskedasticity.

    Null hypothesis: homoskedasticity (constant variance).

    Procedure:
      1. Fit y on X (with intercept) → residuals.
      2. Regress squared residuals on X.
      3. LM = n * R^2 of the auxiliary regression.

    Args:
        y: Observed responses.
        x: Predictor matrix (rows = observations).

    Returns:
        TestResult with the LM statistic and approximate p-value.
    """
    n = len(y)
    if n == 0:
        raise ValueError("y must be non-empty")
    if len(x) != n:
        raise ValueError("x and y must have the same number of observations")

    X = [[1.0] + list(row) for row in x]
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    Xty = matmul(Xt, [[v] for v in y])
    try:
        beta = solve(XtX, [row[0] for row in Xty])
    except ValueError:
        raise ValueError("Singular design matrix in Breusch-Pagan")
    fitted = [sum(b * xi for b, xi in zip(beta, row)) for row in X]
    residuals = [y[i] - fitted[i] for i in range(n)]

    # Auxiliary regression of squared residuals on X.
    e2 = [r * r for r in residuals]
    e2_mean = sum(e2) / n
    ss_tot = sum((v - e2_mean) ** 2 for v in e2)
    fitted_aux = [sum(b * xi for b, xi in zip(beta, row)) for row in X]
    # Refit auxiliary to get its R^2.
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    Xty = matmul(Xt, [[v] for v in e2])
    try:
        beta_aux = solve(XtX, [row[0] for row in Xty])
    except ValueError:
        beta_aux = [0.0] * len(X[0])
    fitted_aux = [sum(b * xi for b, xi in zip(beta_aux, row)) for row in X]
    ss_res = sum((e2[i] - fitted_aux[i]) ** 2 for i in range(n))
    r2_aux = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    lm_stat = n * r2_aux

    # Approximate p-value via chi-square (approx with t-distribution tail).
    k = len(X[0]) - 1
    p_value = t_distribution_p_value(lm_stat ** 0.5, n - k)
    is_significant = p_value < 0.05

    params = {"n_observations": n, "n_predictors": k}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="breusch_pagan",
        method_version=BREUSCH_PAGAN_VERSION,
        parameters=params,
    )
    return TestResult(
        test_name="breusch_pagan",
        statistic=lm_stat,
        p_value=p_value,
        critical_values={},
        is_significant=is_significant,
        parameters=params,
        provenance=prov,
    )


__all__ = ["breusch_pagan", "BREUSCH_PAGAN_VERSION"]
