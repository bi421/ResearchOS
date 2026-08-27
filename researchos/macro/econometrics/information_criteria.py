"""
ResearchOS Macro Intelligence Layer - Econometrics Information Criteria
Version: ecm/ic/v1
Status: FROZEN

Canonical owner of information criteria: AIC and BIC.

MIL-ECM-014: Econometrics owns AIC/BIC.
"""

from __future__ import annotations

from math import log

from researchos.macro.econometrics.models import InformationCriteria
from researchos.macro.statistics.provenance import StatisticalProvenance

AIC_VERSION = "ecm/aic/v1"
BIC_VERSION = "ecm/bic/v1"


def _log_likelihood_gaussian(
    residuals: list[float],
) -> float:
    """Maximized log-likelihood for a Gaussian model from residuals."""
    n = len(residuals)
    rss = sum(r * r for r in residuals)
    if rss == 0:
        rss = 1e-12
    sigma2 = rss / n
    return -0.5 * n * (log(2.0 * 3.141592653589793) + log(sigma2) + 1.0)


def aic(
    residuals: list[float],
    n_parameters: int,
    log_likelihood: float | None = None,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> InformationCriteria:
    """
    Akaike Information Criterion.

    AIC = 2k - 2 * logL

    Args:
        residuals: Model residuals.
        n_parameters: Number of estimated parameters.
        log_likelihood: Optional precomputed log-likelihood.

    Returns:
        Immutable InformationCriteria.
    """
    n = len(residuals)
    if n == 0:
        raise ValueError("residuals must be non-empty")
    ll = log_likelihood if log_likelihood is not None else _log_likelihood_gaussian(residuals)
    aic_val = 2.0 * n_parameters - 2.0 * ll
    bic_val = n_parameters * log(n) - 2.0 * ll
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="aic",
        method_version=AIC_VERSION,
        parameters={"n_observations": n, "n_parameters": n_parameters},
    )
    return InformationCriteria(
        aic=aic_val,
        bic=bic_val,
        log_likelihood=ll,
        n_observations=n,
        n_parameters=n_parameters,
        provenance=prov,
    )


def bic(
    residuals: list[float],
    n_parameters: int,
    log_likelihood: float | None = None,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> InformationCriteria:
    """
    Bayesian Information Criterion.

    BIC = k * ln(n) - 2 * logL

    Args:
        residuals: Model residuals.
        n_parameters: Number of estimated parameters.
        log_likelihood: Optional precomputed log-likelihood.

    Returns:
        Immutable InformationCriteria.
    """
    n = len(residuals)
    if n == 0:
        raise ValueError("residuals must be non-empty")
    ll = log_likelihood if log_likelihood is not None else _log_likelihood_gaussian(residuals)
    aic_val = 2.0 * n_parameters - 2.0 * ll
    bic_val = n_parameters * log(n) - 2.0 * ll
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="bic",
        method_version=BIC_VERSION,
        parameters={"n_observations": n, "n_parameters": n_parameters},
    )
    return InformationCriteria(
        aic=aic_val,
        bic=bic_val,
        log_likelihood=ll,
        n_observations=n,
        n_parameters=n_parameters,
        provenance=prov,
    )


def information_criteria(
    residuals: list[float],
    n_parameters: int,
    log_likelihood: float | None = None,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> InformationCriteria:
    """
    Compute both AIC and BIC together.

    Returns:
        Immutable InformationCriteria.
    """
    n = len(residuals)
    if n == 0:
        raise ValueError("residuals must be non-empty")
    ll = log_likelihood if log_likelihood is not None else _log_likelihood_gaussian(residuals)
    aic_val = 2.0 * n_parameters - 2.0 * ll
    bic_val = n_parameters * log(n) - 2.0 * ll
    prov = StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method="information_criteria",
        method_version="ecm/ic/v1",
        parameters={"n_observations": n, "n_parameters": n_parameters},
    )
    return InformationCriteria(
        aic=aic_val,
        bic=bic_val,
        log_likelihood=ll,
        n_observations=n,
        n_parameters=n_parameters,
        provenance=prov,
    )


__all__ = ["aic", "bic", "information_criteria", "AIC_VERSION", "BIC_VERSION"]
