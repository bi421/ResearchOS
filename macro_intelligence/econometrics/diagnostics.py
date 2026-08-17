"""
ResearchOS Macro Intelligence Layer - Econometrics Diagnostics
Version: ecm/diag/v1
Status: FROZEN

Canonical owner of model + residual diagnostics:
  - Durbin-Watson
  - Jarque-Bera
  - residual_diagnostics (aggregate)
  - model_diagnostics (aggregate)

Diagnostics are computed from residuals AFTER fitting; never inside a
regression class.

MIL-ECM-012: Econometrics owns diagnostics; diagnostics are separated from fit.
"""

from __future__ import annotations

from typing import List, Optional

from macro_intelligence.econometrics.models import (
    InformationCriteria,
    ModelDiagnostics,
    ResidualDiagnostics,
    TestResult,
)
from macro_intelligence.statistics.descriptive import kurtosis, mean, skewness, std
from macro_intelligence.statistics.distributions import t_distribution_p_value
from macro_intelligence.statistics.provenance import StatisticalProvenance

DURBIN_WATSON_VERSION = "ecm/dw/v1"
JARQUE_BERA_VERSION = "ecm/jb/v1"


def durbin_watson(
    residuals: List[float],
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    Durbin-Watson statistic for autocorrelation of residuals.

    DW = sum((e_t - e_{t-1})^2) / sum(e_t^2)

    Values near 2 indicate no autocorrelation; near 0 positive autocorrelation;
    near 4 negative autocorrelation.

    Args:
        residuals: Model residuals.

    Returns:
        TestResult with the DW statistic.
    """
    n = len(residuals)
    if n < 2:
        raise ValueError("Need at least 2 residuals for Durbin-Watson")
    denom = sum(r * r for r in residuals)
    if denom == 0:
        dw = 0.0
    else:
        diff_sum = sum((residuals[i] - residuals[i - 1]) ** 2 for i in range(1, n))
        dw = diff_sum / denom

    # Rule of thumb: values far from 2 (outside 1.5, 2.5) indicate autocorrelation.
    is_significant = dw < 1.5 or dw > 2.5
    params = {"n_observations": n}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="durbin_watson",
        method_version=DURBIN_WATSON_VERSION,
        parameters=params,
    )
    return TestResult(
        test_name="durbin_watson",
        statistic=dw,
        p_value=None,
        critical_values={"lower": 1.5, "upper": 2.5},
        is_significant=is_significant,
        parameters=params,
        provenance=prov,
    )


def jarque_bera(
    residuals: List[float],
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
) -> TestResult:
    """
    Jarque-Bera test for normality of residuals.

    JB = (n/6) * (S^2 + (K-3)^2 / 4)

    Null hypothesis: residuals are normally distributed.

    Args:
        residuals: Model residuals.

    Returns:
        TestResult with the JB statistic and approximate p-value.
    """
    n = len(residuals)
    if n < 4:
        raise ValueError("Need at least 4 residuals for Jarque-Bera")
    s = skewness(residuals)
    k = kurtosis(residuals)
    jb_stat = (n / 6.0) * (s * s + ((k - 3.0) ** 2) / 4.0)

    # Approximate p-value via chi-square tail (approx with t-distribution).
    p_value = t_distribution_p_value(jb_stat**0.5, n - 2)
    is_significant = p_value < 0.05

    params = {"n_observations": n}
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="jarque_bera",
        method_version=JARQUE_BERA_VERSION,
        parameters=params,
    )
    return TestResult(
        test_name="jarque_bera",
        statistic=jb_stat,
        p_value=p_value,
        critical_values={},
        is_significant=is_significant,
        parameters=params,
        provenance=prov,
    )


def residual_diagnostics(
    residuals: List[float],
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
    method_version: str = "ecm/diag/v1",
) -> ResidualDiagnostics:
    """
    Aggregate residual diagnostics (mean, std, skewness, kurtosis, JB, DW, BP).

    Args:
        residuals: Model residuals.

    Returns:
        Immutable ResidualDiagnostics.
    """
    n = len(residuals)
    if n < 4:
        raise ValueError("Need at least 4 residuals for diagnostics")

    m = mean(residuals)
    s = std(residuals)
    sk = skewness(residuals)
    ku = kurtosis(residuals)

    jb = (n / 6.0) * (sk * sk + ((ku - 3.0) ** 2) / 4.0)
    jb_p = t_distribution_p_value(jb**0.5, n - 2)

    denom = sum(r * r for r in residuals)
    dw = sum((residuals[i] - residuals[i - 1]) ** 2 for i in range(1, n)) / denom if denom else 0.0

    # Breusch-Pagan on residuals vs time index (simple version).
    e2 = [r * r for r in residuals]
    e2_mean = sum(e2) / n
    ss_tot = sum((v - e2_mean) ** 2 for v in e2)
    t_idx = list(range(n))
    t_mean = mean(t_idx)
    num = sum((t_idx[i] - t_mean) * (e2[i] - e2_mean) for i in range(n))
    den = sum((t_idx[i] - t_mean) ** 2 for i in range(n))
    slope_aux = num / den if den else 0.0
    fitted_aux = [e2_mean + slope_aux * (t_idx[i] - t_mean) for i in range(n)]
    ss_res = sum((e2[i] - fitted_aux[i]) ** 2 for i in range(n))
    r2_aux = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    bp_stat = n * r2_aux
    bp_p = t_distribution_p_value(bp_stat**0.5, n - 2)

    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="residual_diagnostics",
        method_version=method_version,
        parameters={"n_observations": n},
    )
    return ResidualDiagnostics(
        mean=m,
        std=s,
        skewness=sk,
        kurtosis=ku,
        jarque_bera=jb,
        jarque_bera_p_value=jb_p,
        durbin_watson=dw,
        breusch_pagan_statistic=bp_stat,
        breusch_pagan_p_value=bp_p,
        n_observations=n,
        provenance=prov,
    )


def model_diagnostics(
    y: List[float],
    fitted: List[float],
    n_parameters: int,
    residuals: Optional[List[float]] = None,
    aic: Optional[float] = None,
    bic: Optional[float] = None,
    log_likelihood: Optional[float] = None,
    dataset_id: Optional[str] = None,
    dataset_version: Optional[str] = None,
    dataset_hash: Optional[str] = None,
    method_version: str = "ecm/diag/v1",
) -> ModelDiagnostics:
    """
    Aggregate model diagnostics: residual diagnostics + information criteria.

    Args:
        y: Observed responses.
        fitted: Model predictions.
        n_parameters: Number of estimated parameters.
        residuals: Optional residuals (computed if not provided).
        aic, bic, log_likelihood: Optional precomputed information criteria.

    Returns:
        Immutable ModelDiagnostics.
    """
    n = len(y)
    if n == 0:
        raise ValueError("y must be non-empty")
    if len(fitted) != n:
        raise ValueError("fitted must have the same length as y")

    if residuals is None:
        residuals = [y[i] - fitted[i] for i in range(n)]

    resid = residual_diagnostics(
        residuals,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        method_version=method_version,
    )

    info = None
    if aic is not None and bic is not None:
        info = InformationCriteria(
            aic=aic,
            bic=bic,
            log_likelihood=log_likelihood if log_likelihood is not None else 0.0,
            n_observations=n,
            n_parameters=n_parameters,
            provenance=resid.provenance,
        )

    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="model_diagnostics",
        method_version=method_version,
        parameters={"n_observations": n, "n_parameters": n_parameters},
    )
    return ModelDiagnostics(
        regression=None,
        residual=resid,
        information_criteria=info,
        provenance=prov,
    )


__all__ = [
    "durbin_watson",
    "jarque_bera",
    "residual_diagnostics",
    "model_diagnostics",
    "DURBIN_WATSON_VERSION",
    "JARQUE_BERA_VERSION",
]
