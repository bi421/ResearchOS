"""
ResearchOS Macro Intelligence Layer - Econometrics Regression
Version: ecm/reg/v1
Status: FROZEN

Canonical host for multiple, polynomial, and logistic regression.

Single-predictor OLS is delegated to the canonical Statistics owner
(``statistics.regression.linear_regression``) — this module NEVER re-implements
1-D OLS. Multiple and polynomial regression are matrix-based OLS (new
econometric algorithms, distinct from the 1-D canonical owner). Logistic
regression uses deterministic Newton-Raphson with bounded iterations and an
explicit convergence report.

MIL-ECM-004: Econometrics owns multiple/polynomial/logistic regression.
MIL-ECM-005: Econometrics never duplicates single-variable OLS.
"""

from __future__ import annotations

from math import exp, log
from typing import Any

from researchos.macro.econometrics.matrix import invert, matmul, solve, transpose
from researchos.macro.econometrics.models import RegressionResult
from researchos.macro.statistics.descriptive import mean
from researchos.macro.statistics.distributions import (
    t_distribution_p_value,
)
from researchos.macro.statistics.provenance import StatisticalProvenance
from researchos.macro.statistics.regression import linear_regression as _canonical_ols

# Algorithm version constants.
MULTIPLE_VERSION = "ecm/reg/multiple/v1"
POLYNOMIAL_VERSION = "ecm/reg/poly/v1"
LOGISTIC_VERSION = "ecm/reg/logistic/v1"


def _provenance(
    method: str,
    method_version: str,
    parameters: dict[str, Any],
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> StatisticalProvenance:
    """Construct a StatisticalProvenance envelope for a regression."""
    return StatisticalProvenance(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_hash=dataset_hash,
        computation_method=method,
        method_version=method_version,
        parameters=dict(parameters),
    )


def _design_matrix(
    x: list[list[float]],
    add_intercept: bool = True,
) -> list[list[float]]:
    """Build the design matrix (with leading column of 1s if add_intercept)."""
    if add_intercept:
        return [[1.0] + list(row) for row in x]
    return [list(row) for row in x]


def _ols_solve(X: list[list[float]], y: list[float]) -> tuple[list[float], list[float]]:
    """
    Solve the normal equations for multiple linear regression.

    beta = (X'X)^{-1} X'y
    fitted = X beta
    residuals = y - fitted

    Returns:
        (beta, fitted_values)
    """
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    Xty = matmul(Xt, [[v] for v in y])
    beta_mat = solve(XtX, [row[0] for row in Xty])
    fitted = [sum(b * xi for b, xi in zip(beta_mat, row)) for row in X]
    return beta_mat, fitted


def _r_squared(y: list[float], fitted: list[float]) -> float:
    """Compute R^2 from observed and fitted values."""
    y_mean = mean(y)
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum((yi - f) ** 2 for yi, f in zip(y, fitted))
    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0
    return 1.0 - (ss_res / ss_tot)


def _adjusted_r_squared(r2: float, n: int, k: int) -> float:
    """Compute adjusted R^2."""
    if n - k - 1 <= 0:
        return r2
    return 1.0 - (1.0 - r2) * (n - 1) / (n - k - 1)


def _inference(
    X: list[list[float]],
    y: list[float],
    beta: list[float],
    fitted: list[float],
) -> tuple[list[float], list[float], list[float]]:
    """
    Compute standard errors, t-stats, and p-values for coefficients.

    Returns:
        (standard_errors, t_stats, p_values)
    """
    n = len(y)
    k = len(beta) - 1  # number of predictors (excl. intercept)
    residuals = [y[i] - fitted[i] for i in range(n)]
    rss = sum(r * r for r in residuals)
    df = n - k - 1
    if df <= 0:
        df = 1
    sigma2 = rss / df
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    try:
        XtX_inv = invert(XtX)
    except ValueError:
        # Singular; fall back to pseudo-inverse numerics via degenerate defaults.
        XtX_inv = [[1.0 if i == j else 0.0 for j in range(len(beta))] for i in range(len(beta))]

    std_errors = []
    t_stats = []
    p_values = []
    for i in range(len(beta)):
        se = (sigma2 * XtX_inv[i][i]) ** 0.5 if XtX_inv[i][i] > 0 else 0.0
        std_errors.append(se)
        t = beta[i] / se if se > 0 else 0.0
        t_stats.append(t)
        p_values.append(t_distribution_p_value(t, df))
    return std_errors, t_stats, p_values


def multiple_regression(
    x: list[list[float]],
    y: list[float],
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> RegressionResult:
    """
    Multiple linear regression by matrix OLS.

    Args:
        x: List of predictor vectors (each a list of floats).
        y: List of observed responses.

    Returns:
        Immutable RegressionResult.
    """
    n = len(y)
    if n == 0:
        raise ValueError("y must be non-empty")
    if len(x) != n:
        raise ValueError("x and y must have the same number of observations")
    if n == 0 or any(len(row) == 0 for row in x):
        raise ValueError("x must be non-empty and have at least one predictor")

    X = _design_matrix(x)
    beta, fitted = _ols_solve(X, y)
    r2 = _r_squared(y, fitted)
    k = len(beta) - 1
    adj_r2 = _adjusted_r_squared(r2, n, k)
    std_errors, t_stats, p_values = _inference(X, y, beta, fitted)
    residuals = [y[i] - fitted[i] for i in range(n)]

    params = {
        "n_predictors": k,
        "add_intercept": True,
    }
    prov = _provenance("multiple_regression", MULTIPLE_VERSION, params, dataset_id, dataset_version, dataset_hash)
    return RegressionResult(
        coefficients=beta,
        r_squared=r2,
        adjusted_r_squared=adj_r2,
        standard_errors=std_errors,
        t_stats=t_stats,
        p_values=p_values,
        fitted_values=fitted,
        residuals=residuals,
        n_observations=n,
        n_features=k,
        method="multiple_regression",
        method_version=MULTIPLE_VERSION,
        converged=True,
        iterations=0,
        provenance=prov,
    )


def polynomial_regression(
    x: list[float],
    y: list[float],
    degree: int = 2,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> RegressionResult:
    """
    Polynomial regression by matrix OLS on power features.

    Args:
        x: List of predictor values.
        y: List of observed responses.
        degree: Polynomial degree (>= 1).

    Returns:
        Immutable RegressionResult (coefficients ordered [intercept, x, x^2, ...]).
    """
    if degree < 1:
        raise ValueError("degree must be >= 1")
    n = len(y)
    if n == 0:
        raise ValueError("y must be non-empty")
    if len(x) != n:
        raise ValueError("x and y must have the same number of observations")

    # Build power design matrix.
    X = [[1.0] + [xi**d for d in range(1, degree + 1)] for xi in x]
    beta, fitted = _ols_solve(X, y)
    r2 = _r_squared(y, fitted)
    k = len(beta) - 1
    adj_r2 = _adjusted_r_squared(r2, n, k)
    std_errors, t_stats, p_values = _inference(X, y, beta, fitted)
    residuals = [y[i] - fitted[i] for i in range(n)]

    params = {"degree": degree, "add_intercept": True}
    prov = _provenance(
        "polynomial_regression",
        POLYNOMIAL_VERSION,
        params,
        dataset_id,
        dataset_version,
        dataset_hash,
    )
    return RegressionResult(
        coefficients=beta,
        r_squared=r2,
        adjusted_r_squared=adj_r2,
        standard_errors=std_errors,
        t_stats=t_stats,
        p_values=p_values,
        fitted_values=fitted,
        residuals=residuals,
        n_observations=n,
        n_features=k,
        method="polynomial_regression",
        method_version=POLYNOMIAL_VERSION,
        converged=True,
        iterations=0,
        provenance=prov,
    )


def _sigmoid(z: float) -> float:
    """Logistic sigmoid, numerically stable."""
    if z >= 0:
        e = exp(-z)
        return 1.0 / (1.0 + e)
    e = exp(z)
    return e / (1.0 + e)


def _logistic_log_likelihood(beta: list[float], X: list[list[float]], y: list[float]) -> float:
    """Negative log-likelihood for logistic regression (for convergence)."""
    total = 0.0
    for row, yi in zip(X, y):
        z = sum(b * xi for b, xi in zip(beta, row))
        p = _sigmoid(z)
        p = max(1e-12, min(1.0 - 1e-12, p))
        total += yi * log(p) + (1.0 - yi) * log(1.0 - p)
    return -total


def logistic_regression(
    x: list[list[float]],
    y: list[float],
    max_iterations: int = 100,
    tolerance: float = 1e-8,
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> RegressionResult:
    """
    Binary logistic regression via deterministic Newton-Raphson.

    The design matrix includes an intercept column. Coefficients are
    initialized deterministically to zeros. Iteration continues until the
    parameter change is below ``tolerance`` or ``max_iterations`` is reached.
    ``converged`` reports whether the tolerance was met; the iteration count
    is always reported (never hidden).

    Args:
        x: List of predictor vectors.
        y: List of binary outcomes (0/1).
        max_iterations: Maximum number of Newton-Raphson iterations.
        tolerance: Convergence tolerance on the max parameter change.

    Returns:
        Immutable RegressionResult (coefficients are untransformed logits).
    """
    n = len(y)
    if n == 0:
        raise ValueError("y must be non-empty")
    if len(x) != n:
        raise ValueError("x and y must have the same number of observations")
    if not all(v in (0, 1) for v in y):
        raise ValueError("logistic regression requires binary outcomes (0/1)")

    X = _design_matrix(x)
    k = len(X[0])
    beta = [0.0] * k  # deterministic (zero) initialization

    converged = False
    iterations = 0
    for _ in range(max_iterations):
        iterations += 1
        # Gradient and Hessian for Newton-Raphson.
        pi = [_sigmoid(sum(b * xi for b, xi in zip(beta, row))) for row in X]
        grad = [0.0] * k
        hess = [[0.0] * k for _ in range(k)]
        for i in range(n):
            p = pi[i]
            diff = y[i] - p
            for j in range(k):
                grad[j] += diff * X[i][j]
            w = p * (1.0 - p)
            for j in range(k):
                for ll in range(k):
                    hess[j][ll] += w * X[i][j] * X[i][ll]
        # Hessian is negative-definite; solve H delta = grad → delta = H^{-1} grad.
        try:
            hess_inv = invert(hess)
        except ValueError:
            # Near-singular; apply a tiny ridge for numerical stability.
            for j in range(k):
                hess[j][j] += 1e-8
            hess_inv = invert(hess)
        delta = [sum(hess_inv[j][ll] * grad[ll] for ll in range(k)) for j in range(k)]
        new_beta = [beta[j] + delta[j] for j in range(k)]
        max_change = max(abs(new_beta[j] - beta[j]) for j in range(k))
        beta = new_beta
        if max_change < tolerance:
            converged = True
            break

    fitted = [_sigmoid(sum(b * xi for b, xi in zip(beta, row))) for row in X]
    residuals = [y[i] - fitted[i] for i in range(n)]
    r2 = _r_squared(y, fitted)
    adj_r2 = _adjusted_r_squared(r2, n, k - 1)

    std_errors = []
    t_stats = []
    p_values = []
    Xt = transpose(X)
    XtX = matmul(Xt, X)
    try:
        XtX_inv = invert(XtX)
    except ValueError:
        XtX_inv = [[1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
    for i in range(k):
        se = (XtX_inv[i][i]) ** 0.5 if XtX_inv[i][i] > 0 else 0.0
        std_errors.append(se)
        t = beta[i] / se if se > 0 else 0.0
        t_stats.append(t)
        p_values.append(t_distribution_p_value(t, n - k))

    params = {
        "max_iterations": max_iterations,
        "tolerance": tolerance,
        "converged": converged,
        "iterations": iterations,
    }
    prov = _provenance("logistic_regression", LOGISTIC_VERSION, params, dataset_id, dataset_version, dataset_hash)
    return RegressionResult(
        coefficients=beta,
        r_squared=r2,
        adjusted_r_squared=adj_r2,
        standard_errors=std_errors,
        t_stats=t_stats,
        p_values=p_values,
        fitted_values=fitted,
        residuals=residuals,
        n_observations=n,
        n_features=k - 1,
        method="logistic_regression",
        method_version=LOGISTIC_VERSION,
        converged=converged,
        iterations=iterations,
        provenance=prov,
    )


def univariate_ols(
    x: list[float],
    y: list[float],
    dataset_id: str | None = None,
    dataset_version: str | None = None,
    dataset_hash: str | None = None,
) -> RegressionResult:
    """
    Single-variable OLS, delegating to the canonical Statistics owner.

    This is a thin adapter that wraps the canonical ``linear_regression``
    result into the econometrics ``RegressionResult`` contract. It does NOT
    re-implement OLS math.

    Args:
        x: List of predictor values.
        y: List of observed responses.

    Returns:
        Immutable RegressionResult.
    """
    n = len(y)
    if n == 0:
        raise ValueError("y must be non-empty")
    if len(x) != n:
        raise ValueError("x and y must have the same number of observations")

    canonical = _canonical_ols(x, y)
    fitted = [canonical.slope * xi + canonical.intercept for xi in x]
    residuals = [y[i] - fitted[i] for i in range(n)]
    r2 = canonical.r_squared
    adj_r2 = _adjusted_r_squared(r2, n, 1)
    se = canonical.standard_error
    t = canonical.slope / se if se > 0 else 0.0
    p = t_distribution_p_value(t, n - 2)

    params = {"add_intercept": True}
    prov = _provenance("ols", "stat/reg/v1", params, dataset_id, dataset_version, dataset_hash)
    return RegressionResult(
        coefficients=[canonical.intercept, canonical.slope],
        r_squared=r2,
        adjusted_r_squared=adj_r2,
        standard_errors=[se, se],
        t_stats=[t, t],
        p_values=[p, p],
        fitted_values=fitted,
        residuals=residuals,
        n_observations=n,
        n_features=1,
        method="ols",
        method_version="stat/reg/v1",
        converged=True,
        iterations=0,
        provenance=prov,
    )


__all__ = [
    "multiple_regression",
    "polynomial_regression",
    "logistic_regression",
    "univariate_ols",
    "MULTIPLE_VERSION",
    "POLYNOMIAL_VERSION",
    "LOGISTIC_VERSION",
]
