"""
ResearchOS Macro Intelligence Layer - Econometrics Variance Inflation Factor
Version: ecm/vif/v1
Status: FROZEN

Canonical owner of the Variance Inflation Factor (VIF).

MIL-ECM-010: Econometrics owns VIF.
"""

from __future__ import annotations

from typing import List, Optional

from macro_intelligence.econometrics.matrix import invert
from macro_intelligence.econometrics.models import TestResult
from macro_intelligence.statistics.provenance import StatisticalProvenance

VIF_VERSION = "ecm/vif/v1"


def variance_inflation_factor(
    x: List[List[float]],
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    Compute the Variance Inflation Factor for each predictor.

    VIF_j = 1 / (1 - R_j^2), where R_j^2 is from regressing predictor j on
    all other predictors.

    Args:
        x: List of predictor vectors (each observation is a row).

    Returns:
        TestResult with statistic = max VIF, and the per-predictor VIFs in
        ``critical_values["vif"]``.
    """
    n = len(x)
    if n == 0:
        raise ValueError("x must be non-empty")
    k = len(x[0])
    if k < 2:
        raise ValueError("VIF requires at least 2 predictors")

    # Correlation matrix of predictors (with intercept removed, centered).
    means = [sum(row[j] for row in x) / n for j in range(k)]
    Xc = [[row[j] - means[j] for j in range(k)] for row in x]

    # Covariance matrix.
    cov = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            cov[i][j] = sum(Xc[r][i] * Xc[r][j] for r in range(n)) / n

    # Correlation matrix.
    corr = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            diag = cov[i][i]
            dj = cov[j][j]
            if diag > 0 and dj > 0:
                corr[i][j] = cov[i][j] / ((diag * dj) ** 0.5)
            else:
                corr[i][j] = 1.0 if i == j else 0.0

    # Use the inverse of the correlation matrix: VIF_j = diag(inv(corr)).
    try:
        corr_inv = invert(corr)
    except ValueError:
        # Singular correlation matrix → infinite VIF (perfect collinearity).
        corr_inv = [[1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
        vifs = [float("inf")] * k
    else:
        vifs = [corr_inv[j][j] for j in range(k)]

    params = {"n_predictors": k, "n_observations": n}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="variance_inflation_factor",
        method_version=VIF_VERSION,
        parameters=params,
    )
    finite = [v for v in vifs if v != float("inf")]
    return TestResult(
        test_name="variance_inflation_factor",
        statistic=max(finite) if finite else 0.0,
        p_value=None,
        critical_values={"vif": vifs},
        is_significant=any(v > 10.0 for v in vifs),
        parameters=params,
        provenance=prov,
    )


def vif(
    x: List[List[float]],
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """Alias for :func:`variance_inflation_factor`."""
    return variance_inflation_factor(x, dataset_id, dataset_version, dataset_hash)


__all__ = ["variance_inflation_factor", "vif", "VIF_VERSION"]
