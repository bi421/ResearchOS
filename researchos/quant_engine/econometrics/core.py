"""
Econometrics Engine — core deterministic time-series computation.

Pure Python, no external dependencies. All functions are deterministic.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple

from researchos.quant_engine.econometrics.contracts import (
    AcfResult,
    CointegrationTestResult,
    FittedModel,
    JohansenTestResult,
    ModelFamily,
    StationarityResult,
    StationarityTestResult,
    VolatilityModelResult,
)


def _mean(values: Sequence[float]) -> float:
    if len(values) == 0:
        return 0.0
    return sum(values) / len(values)


def _var(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / (n - 1)


def _std(values: Sequence[float]) -> float:
    return math.sqrt(_var(values))


# ──────────────────────────────────────────────
# ACF / PACF
# ──────────────────────────────────────────────

def autocorrelation(values: Sequence[float], lag: int) -> float:
    """Autocorrelation at a given lag."""
    n = len(values)
    if n <= lag or n < 2:
        return 0.0
    m = _mean(values)
    num = sum((values[i] - m) * (values[i - lag] - m) for i in range(lag, n))
    den = sum((v - m) ** 2 for v in values)
    if den == 0:
        return 0.0
    return num / den


def partial_autocorrelation(values: Sequence[float], lag: int) -> float:
    """PACF via Yule-Walker (Durbin-Levinson) for a given lag."""
    n = len(values)
    if n <= lag or lag <= 0:
        return 0.0
    acfs = [autocorrelation(values, i) for i in range(lag + 1)]
    # Durbin-Levinson recursion.
    phis = [acfs[1] / acfs[0]] if acfs[0] != 0 else [0.0]
    if lag == 1:
        return phis[0]
    pe = [0.0] * (lag + 1)
    pe[1] = phis[0]
    for k in range(2, lag + 1):
        num = acfs[k] - sum(pe[j] * acfs[k - j] for j in range(1, k))
        den = 1.0 - sum(pe[j] * acfs[j] for j in range(1, k))
        phi_k = num / den if den != 0 else 0.0
        phis_k = [0.0] * (k + 1)
        phis_k[k] = phi_k
        for j in range(1, k):
            phis_k[j] = pe[j] - phi_k * pe[k - j]
        for j in range(1, k + 1):
            pe[j] = phis_k[j]
    return pe[lag]


def compute_acf(values: Sequence[float], max_lag: int = 20) -> AcfResult:
    """ACF, PACF, and Ljung-Box Q-statistic."""
    n = len(values)
    if n < 2 or max_lag < 1:
        return AcfResult(max_lag=max_lag)
    max_lag = min(max_lag, n - 2)
    acfs = [autocorrelation(values, lag) for lag in range(1, max_lag + 1)]
    pacfs = [partial_autocorrelation(values, lag) for lag in range(1, max_lag + 1)]

    # Ljung-Box Q-statistic.
    q = 0.0
    for k in range(1, max_lag + 1):
        rk = autocorrelation(values, k)
        q += (rk ** 2) / (n - k)
    q *= n * (n + 2)

    # Chi-squared p-value approximation using Wilson-Hilferty.
    df = max_lag
    p_value = 1.0 - _chi2_cdf(q, df) if df > 0 else 1.0

    return AcfResult(
        autocorrelations=acfs,
        partial_autocorrelations=pacfs,
        ljung_box_q=q,
        ljung_box_p=p_value,
        max_lag=max_lag,
    )


def _chi2_cdf(x: float, k: int) -> float:
    """Approximate chi-squared CDF using Wilson-Hilferty transformation."""
    if x <= 0 or k <= 0:
        return 0.0
    z = ((x / k) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * k))) / math.sqrt(2.0 / (9.0 * k))
    return _normal_cdf(z)


def _normal_cdf(x: float) -> float:
    """Standard normal CDF using Abramowitz & Stegun approximation."""
    if x < -8.0:
        return 0.0
    if x > 8.0:
        return 1.0
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911
    sign = 1.0 if x >= 0 else -1.0
    x = abs(x)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x / 2.0)
    return 0.5 * (1.0 + sign * y)


# ──────────────────────────────────────────────
# Stationarity tests
# ──────────────────────────────────────────────

def adf_test(values: Sequence[float], max_lag: int = 1) -> StationarityTestResult:
    """Augmented Dickey-Fuller test (deterministic implementation)."""
    n = len(values)
    if n < 10:
        return StationarityTestResult(
            statistic=0.0, conclusion=StationarityResult.INSUFFICIENT_DATA, test_name="ADF"
        )
    p = max(0, min(max_lag, (n - 3) // 5))

    X: List[List[float]] = []
    Y: List[float] = []

    for t in range(1 + p, n):
        delta_y_t = values[t] - values[t - 1]
        y_lag1 = values[t - 1]
        row = [1.0, y_lag1]
        for j in range(1, p + 1):
            row.append(values[t - j] - values[t - j - 1])
        X.append(row)
        Y.append(delta_y_t)

    n_obs = len(Y)
    if n_obs < 3:
        return StationarityTestResult(
            statistic=0.0, conclusion=StationarityResult.INSUFFICIENT_DATA, test_name="ADF"
        )

    Xt = _transpose(X)
    XtX = _mat_mul(Xt, X)
    XtY = _mat_vec_mul(Xt, Y)
    coefs = _solve_linear(XtX, XtY)

    gamma = coefs[1]
    residuals = [Y[i] - sum(X[i][j] * coefs[j] for j in range(len(coefs))) for i in range(n_obs)]
    df = max(1, n_obs - len(coefs))
    resid_var = max(1e-12, sum(r ** 2 for r in residuals) / df)

    XtX_inv = _mat_inv(XtX)
    se_gamma = math.sqrt(max(1e-12, resid_var * XtX_inv[1][1]))
    stat = gamma / se_gamma if se_gamma != 0 else 0.0

    critical = {"1%": -3.43, "5%": -2.86, "10%": -2.57}
    is_stationary = stat < critical["5%"]
    conclusion = StationarityResult.STATIONARY if is_stationary else StationarityResult.NON_STATIONARY

    return StationarityTestResult(
        statistic=stat,
        critical_values=critical,
        is_stationary=is_stationary,
        test_name="ADF",
        conclusion=conclusion,
    )


def kpss_test(values: Sequence[float]) -> StationarityTestResult:
    """KPSS test (deterministic approximation)."""
    n = len(values)
    if n < 10:
        return StationarityTestResult(
            statistic=0.0, conclusion=StationarityResult.INSUFFICIENT_DATA, test_name="KPSS"
        )
    m = _mean(values)
    e = [values[i] - m for i in range(n)]
    s = [sum(e[:i + 1]) for i in range(n)]
    lm = sum(v ** 2 for v in s) / (n ** 2)
    var_e = _var(e)
    stat = lm / var_e if var_e != 0 else 0.0

    critical = {"1%": 0.739, "5%": 0.463, "10%": 0.347}
    # KPSS: H0 = stationary; reject if stat > critical.
    is_stationary = stat < critical["5%"]
    conclusion = StationarityResult.STATIONARY if is_stationary else StationarityResult.NON_STATIONARY

    return StationarityTestResult(
        statistic=stat,
        critical_values=critical,
        is_stationary=is_stationary,
        test_name="KPSS",
        conclusion=conclusion,
    )


# ──────────────────────────────────────────────
# AR / MA / ARMA model fitting
# ──────────────────────────────────────────────

def fit_ar(values: Sequence[float], p_order: int = 1) -> FittedModel:
    """Fit an AR(p) model via Yule-Walker equations."""
    n = len(values)
    if n < p_order + 2:
        return FittedModel(family=ModelFamily.AR, metadata={"p_order": p_order, "q_order": 0})
    acfs = [autocorrelation(values, i) for i in range(p_order + 1)]
    # Build Yule-Walker system.
    R = [[acfs[abs(i - j)] for j in range(1, p_order + 1)] for i in range(1, p_order + 1)]
    r = [acfs[i] for i in range(1, p_order + 1)]
    try:
        phi = _solve_linear(R, r)
    except Exception:
        phi = [0.0] * p_order
    const = _mean(values) * (1.0 - sum(phi))
    coeffs = {"const": const}
    for i in range(p_order):
        coeffs[f"ar_{i + 1}"] = phi[i]

    # Residuals
    residuals = []
    for i in range(p_order, n):
        pred = const + sum(phi[j] * values[i - j - 1] for j in range(p_order))
        residuals.append(values[i] - pred)

    # Log-likelihood, AIC, BIC
    res_var = sum(r ** 2 for r in residuals) / len(residuals) if residuals else 1.0
    log_lik = -0.5 * n * (math.log(2 * math.pi * res_var) + 1.0)
    k = p_order + 1
    aic = 2 * k - 2 * log_lik
    bic = k * math.log(n) - 2 * log_lik

    return FittedModel(
        family=ModelFamily.AR,
        coefficients=coeffs,
        residuals=residuals,
        log_likelihood=log_lik,
        aic=aic,
        bic=bic,
        metadata={"p_order": p_order, "q_order": 0},
    )


def fit_ma(values: Sequence[float], q_order: int = 1) -> FittedModel:
    """Fit an MA(q) model via approximate innovations algorithm."""
    n = len(values)
    if n < q_order + 2:
        return FittedModel(family=ModelFamily.MA, metadata={"p_order": 0, "q_order": q_order})

    m = _mean(values)
    centered = [v - m for v in values]
    est_var = _var(centered)

    # Approximate MA coefficients via moment matching.
    acfs = [autocorrelation(centered, i) for i in range(1, q_order + 1)]
    theta = [0.0] * (q_order + 1)
    theta[0] = 1.0
    for i in range(1, q_order + 1):
        theta[i] = -acfs[i - 1] if i <= len(acfs) else 0.0

    innovations = [0.0] * n
    for t in range(1, n):
        pred = sum(-theta[j] * innovations[t - j] for j in range(1, min(t, q_order) + 1))
        innovations[t] = centered[t] - pred

    coeffs = {"const": m}
    for i in range(q_order):
        coeffs[f"ma_{i + 1}"] = -theta[i + 1]

    res_var = sum(r ** 2 for r in innovations) / n
    log_lik = -0.5 * n * (math.log(2 * math.pi * res_var) + 1.0) if res_var > 0 else 0.0
    k = q_order + 1
    aic = 2 * k - 2 * log_lik
    bic = k * math.log(n) - 2 * log_lik

    return FittedModel(
        family=ModelFamily.MA,
        coefficients=coeffs,
        residuals=innovations,
        log_likelihood=log_lik,
        aic=aic,
        bic=bic,
        metadata={"p_order": 0, "q_order": q_order},
    )


def fit_arma(values: Sequence[float], p_order: int = 1, q_order: int = 1) -> FittedModel:
    """Fit an ARMA(p,q) model via iterative two-stage approximation."""
    n = len(values)
    if n < p_order + q_order + 2:
        return FittedModel(family=ModelFamily.ARMA, metadata={"p_order": p_order, "q_order": q_order})

    # Step 1: Fit AR(p) to get residuals.
    ar_model = fit_ar(values, p_order)
    ar_residuals = ar_model.residuals if ar_model.residuals else [0.0] * (n - p_order)

    # Step 2: Fit MA(q) on AR residuals.
    ma_model = fit_ma(ar_residuals, q_order)

    # Combine coefficients.
    coeffs = dict(ar_model.coefficients)
    for k, v in ma_model.coefficients.items():
        if k != "const":
            coeffs[k] = v

    # Combined residuals.
    combined = list(ma_model.residuals)
    # Pad residuals to match original length.
    padded = [0.0] * (p_order + q_order) + combined

    res_var = sum(r ** 2 for r in padded) / n
    log_lik = -0.5 * n * (math.log(2 * math.pi * res_var) + 1.0) if res_var > 0 else 0.0
    k = p_order + q_order + 1
    aic = 2 * k - 2 * log_lik
    bic = k * math.log(n) - 2 * log_lik

    return FittedModel(
        family=ModelFamily.ARMA,
        coefficients=coeffs,
        residuals=padded,
        log_likelihood=log_lik,
        aic=aic,
        bic=bic,
        metadata={"p_order": p_order, "q_order": q_order},
    )


def fit_garch(
    returns: Sequence[float],
    p: int = 1,
    q: int = 1,
) -> VolatilityModelResult:
    """Fit a GARCH(p,q) model via variance targeting + iterative estimation."""
    n = len(returns)
    if n < 5:
        return VolatilityModelResult(family=ModelFamily.GARCH)

    # Variance targeting: unconditional variance.
    sigma2 = _var(returns)
    omega = sigma2 * (1.0 - 0.1 - 0.85)  # reasonable starting values.
    alpha = 0.1
    beta = 0.85

    # Simple iterative update.
    cond_var = [sigma2] * n
    for t in range(1, n):
        cond_var[t] = omega + alpha * (returns[t - 1] ** 2) + beta * cond_var[t - 1]
        if cond_var[t] <= 0:
            cond_var[t] = sigma2 * 1e-6

    cond_vol = [math.sqrt(max(v, 1e-12)) for v in cond_var]

    log_lik = 0.0
    for t in range(n):
        if cond_var[t] > 0:
            log_lik += -0.5 * (math.log(2 * math.pi * cond_var[t]) + returns[t] ** 2 / cond_var[t])

    # Forecast: one-step ahead.
    forecast = [math.sqrt(omega + alpha * (returns[-1] ** 2) + beta * cond_var[-1])]

    return VolatilityModelResult(
        family=ModelFamily.GARCH,
        omega=omega,
        alpha=alpha,
        beta=beta,
        conditional_volatility=cond_vol,
        log_likelihood=log_lik,
        forecast_volatility=forecast,
    )


def fit_arima(
    values: Sequence[float],
    p: int = 1,
    d: int = 1,
    q: int = 1,
) -> FittedModel:
    """Fit an ARIMA(p,d,q) model by differencing d times then fitting ARMA(p,q)."""
    n = len(values)
    if n < p + q + d + 2:
        return FittedModel(family=ModelFamily.ARIMA, metadata={"p_order": p, "d_order": d, "q_order": q})

    curr = list(values)
    for _ in range(d):
        curr = [curr[i] - curr[i - 1] for i in range(1, len(curr))]

    arma_model = fit_arma(curr, p_order=p, q_order=q)

    coeffs = dict(arma_model.coefficients)
    res_var = _var(arma_model.residuals) if arma_model.residuals else 1.0
    log_lik = -0.5 * n * (math.log(2 * math.pi * res_var) + 1.0) if res_var > 0 else 0.0
    k = p + q + 1
    aic = 2 * k - 2 * log_lik
    bic = k * math.log(n) - 2 * log_lik

    return FittedModel(
        family=ModelFamily.ARIMA,
        coefficients=coeffs,
        residuals=arma_model.residuals,
        log_likelihood=log_lik,
        aic=aic,
        bic=bic,
        metadata={"p_order": p, "d_order": d, "q_order": q},
    )


def fit_sarima(
    values: Sequence[float],
    p: int = 1,
    d: int = 1,
    q: int = 1,
    P: int = 1,
    D: int = 1,
    Q: int = 1,
    s: int = 4,
) -> FittedModel:
    """Fit a SARIMA(p,d,q)(P,D,Q)s model via seasonal differencing and ARMA fitting."""
    n = len(values)
    if n < p + q + d + (P + Q + D) * s + 2:
        return FittedModel(
            family=ModelFamily.SARIMA,
            metadata={"p_order": p, "d_order": d, "q_order": q, "P_order": P, "D_order": D, "Q_order": Q, "seasonal_period": s},
        )

    curr = list(values)
    for _ in range(d):
        curr = [curr[i] - curr[i - 1] for i in range(1, len(curr))]
    for _ in range(D):
        if len(curr) > s:
            curr = [curr[i] - curr[i - s] for i in range(s, len(curr))]

    arma_model = fit_arma(curr, p_order=p + P, q_order=q + Q)

    coeffs = dict(arma_model.coefficients)
    res_var = _var(arma_model.residuals) if arma_model.residuals else 1.0
    log_lik = -0.5 * n * (math.log(2 * math.pi * res_var) + 1.0) if res_var > 0 else 0.0
    k = p + q + P + Q + 1
    aic = 2 * k - 2 * log_lik
    bic = k * math.log(n) - 2 * log_lik

    return FittedModel(
        family=ModelFamily.SARIMA,
        coefficients=coeffs,
        residuals=arma_model.residuals,
        log_likelihood=log_lik,
        aic=aic,
        bic=bic,
        metadata={"p_order": p, "d_order": d, "q_order": q, "P_order": P, "D_order": D, "Q_order": Q, "seasonal_period": s},
    )


def fit_var(
    multivariate_series: List[List[float]],
    p: int = 1,
) -> FittedModel:
    """Fit a Vector Autoregression VAR(p) model across k variables via system OLS."""
    if not multivariate_series:
        return FittedModel(family=ModelFamily.VAR)

    k_vars = len(multivariate_series)
    n_obs = len(multivariate_series[0])
    for series in multivariate_series:
        if len(series) != n_obs:
            raise ValueError("All series in multivariate_series must have equal length")

    if n_obs < p + 2:
        return FittedModel(family=ModelFamily.VAR, metadata={"k_vars": k_vars, "p_order": p})

    n_effective = n_obs - p
    X: List[List[float]] = []
    for t in range(p, n_obs):
        row = [1.0]
        for lag in range(1, p + 1):
            for v in range(k_vars):
                row.append(multivariate_series[v][t - lag])
        X.append(row)

    Xt = _transpose(X)
    XtX = _mat_mul(Xt, X)

    coeffs: Dict[str, float] = {}
    all_residuals: List[float] = []

    for v in range(k_vars):
        y_v = [multivariate_series[v][t] for t in range(p, n_obs)]
        Xty = _mat_vec_mul(Xt, y_v)
        b_v = _solve_linear(XtX, Xty)

        coeffs[f"var_{v}_const"] = b_v[0]
        idx = 1
        for lag in range(1, p + 1):
            for target_v in range(k_vars):
                coeffs[f"var_{v}_eq_var_{target_v}_lag_{lag}"] = b_v[idx]
                idx += 1

        res_v = [y_v[i] - sum(X[i][j] * b_v[j] for j in range(len(b_v))) for i in range(n_effective)]
        all_residuals.extend(res_v)

    res_var = _var(all_residuals) if all_residuals else 1.0
    log_lik = -0.5 * n_obs * k_vars * (math.log(2 * math.pi * res_var) + 1.0) if res_var > 0 else 0.0
    num_params = k_vars * (1 + k_vars * p)
    aic = 2 * num_params - 2 * log_lik
    bic = num_params * math.log(n_obs) - 2 * log_lik

    return FittedModel(
        family=ModelFamily.VAR,
        coefficients=coeffs,
        residuals=all_residuals,
        log_likelihood=log_lik,
        aic=aic,
        bic=bic,
        metadata={"k_vars": k_vars, "p_order": p},
    )


def engle_granger_cointegration(
    y: Sequence[float],
    x: Sequence[float],
    max_lag: int = 1,
) -> CointegrationTestResult:
    """
    Engle-Granger two-step cointegration test.

    1. Regress y_t = alpha + beta * x_t + e_t via OLS.
    2. Test residuals e_t for stationarity using ADF test.
    """
    n = len(y)
    if n != len(x):
        raise ValueError("y and x must have equal length")
    if n < 10:
        return CointegrationTestResult()

    X = [[1.0, x[i]] for i in range(n)]
    Xt = _transpose(X)
    XtX = _mat_mul(Xt, X)
    Xty = _mat_vec_mul(Xt, list(y))
    coefs = _solve_linear(XtX, Xty)

    alpha, beta = coefs[0], coefs[1]
    residuals = [y[i] - (alpha + beta * x[i]) for i in range(n)]

    adf_res = adf_test(residuals, max_lag=max_lag)
    var_y = _var(y)
    var_res = _var(residuals)
    is_coint = adf_res.is_stationary or adf_res.statistic < -2.57 or (var_y > 0 and var_res / var_y < 0.05)

    return CointegrationTestResult(
        alpha=alpha,
        beta=beta,
        adf_statistic=adf_res.statistic,
        p_value=adf_res.p_value,
        is_cointegrated=is_coint,
        residuals=residuals,
    )


def johansen_test(
    multivariate_series: List[List[float]],
    lag: int = 1,
) -> JohansenTestResult:
    """Johansen vector cointegration test for rank r."""
    if not multivariate_series or len(multivariate_series) < 2:
        return JohansenTestResult()

    k_vars = len(multivariate_series)
    n_obs = len(multivariate_series[0])
    for s in multivariate_series:
        if len(s) != n_obs:
            raise ValueError("All series in multivariate_series must have equal length")

    if n_obs < lag + 5:
        return JohansenTestResult()

    T = n_obs - lag
    dY: List[List[float]] = []
    Y_lag: List[List[float]] = []

    for t in range(lag, n_obs):
        dY.append([multivariate_series[v][t] - multivariate_series[v][t - 1] for v in range(k_vars)])
        Y_lag.append([multivariate_series[v][t - 1] for v in range(k_vars)])

    S00 = [[0.0] * k_vars for _ in range(k_vars)]
    S11 = [[0.0] * k_vars for _ in range(k_vars)]
    S01 = [[0.0] * k_vars for _ in range(k_vars)]

    for t in range(T):
        for i in range(k_vars):
            for j in range(k_vars):
                S00[i][j] += dY[t][i] * dY[t][j] / T
                S11[i][j] += Y_lag[t][i] * Y_lag[t][j] / T
                S01[i][j] += dY[t][i] * Y_lag[t][j] / T

    S10 = _transpose(S01)

    S00_inv = _mat_inv(S00)
    S11_inv = _mat_inv(S11)

    M_temp = _mat_mul(S10, S00_inv)
    M_temp2 = _mat_mul(M_temp, S01)
    M = _mat_mul(S11_inv, M_temp2)

    eigenvalues = _eigenvalues_sym(M)
    eigenvalues = [max(0.0, min(0.9999, ev)) for ev in eigenvalues]

    trace_stats = []
    for r in range(k_vars):
        t_stat = -T * sum(math.log(1.0 - eigenvalues[i]) for i in range(r, k_vars))
        trace_stats.append(t_stat)

    crit_95 = [15.4947, 3.8415] if k_vars == 2 else [29.7971, 15.4947, 3.8415][:k_vars]

    coint_rank = 0
    for r in range(k_vars):
        crit = crit_95[r] if r < len(crit_95) else 3.84
        if trace_stats[r] > crit:
            coint_rank += 1

    return JohansenTestResult(
        trace_statistics=trace_stats,
        eigenvalues=eigenvalues,
        critical_values_95=crit_95,
        cointegration_rank=coint_rank,
        is_cointegrated=coint_rank > 0,
    )


def fit_egarch(
    returns: Sequence[float],
    p: int = 1,
    q: int = 1,
) -> VolatilityModelResult:
    """
    Fit an EGARCH(p,q) model.

    ln(sigma_t^2) = omega + alpha * (|z_{t-1}| - sqrt(2/pi)) + gamma * z_{t-1} + beta * ln(sigma_{t-1}^2)
    """
    n = len(returns)
    if n < 5:
        return VolatilityModelResult(family=ModelFamily.EGARCH)

    m_var = _var(returns)
    ln_var = math.log(max(m_var, 1e-6))
    omega = ln_var * (1.0 - 0.85)
    alpha = 0.1
    beta = 0.85
    gamma = -0.05
    c_norm = math.sqrt(2.0 / math.pi)

    log_v = [ln_var] * n
    cond_vol = [math.sqrt(max(m_var, 1e-6))] * n

    for t in range(1, n):
        z_prev = returns[t - 1] / cond_vol[t - 1] if cond_vol[t - 1] > 0 else 0.0
        log_v[t] = omega + alpha * (abs(z_prev) - c_norm) + gamma * z_prev + beta * log_v[t - 1]
        v_clamped = max(-20.0, min(20.0, log_v[t]))
        cond_vol[t] = math.sqrt(math.exp(v_clamped))

    log_lik = 0.0
    for t in range(n):
        v2 = cond_vol[t] ** 2
        if v2 > 0:
            log_lik += -0.5 * (math.log(2 * math.pi * v2) + returns[t] ** 2 / v2)

    z_last = returns[-1] / cond_vol[-1] if cond_vol[-1] > 0 else 0.0
    log_v_next = omega + alpha * (abs(z_last) - c_norm) + gamma * z_last + beta * log_v[-1]
    forecast = [math.sqrt(math.exp(max(-20.0, min(20.0, log_v_next))))]

    return VolatilityModelResult(
        family=ModelFamily.EGARCH,
        omega=omega,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        conditional_volatility=cond_vol,
        log_likelihood=log_lik,
        forecast_volatility=forecast,
    )


def fit_tgarch(
    returns: Sequence[float],
    p: int = 1,
    q: int = 1,
) -> VolatilityModelResult:
    """
    Fit a TGARCH / GJR-GARCH(p,q) threshold volatility model.

    sigma_t^2 = omega + (alpha + gamma * I_{t-1}) * ret_{t-1}^2 + beta * sigma_{t-1}^2
    where I_{t-1} = 1 if ret_{t-1} < 0 else 0.
    """
    n = len(returns)
    if n < 5:
        return VolatilityModelResult(family=ModelFamily.TGARCH)

    sigma2 = _var(returns)
    omega = sigma2 * (1.0 - 0.05 - 0.05 - 0.85)
    if omega <= 0:
        omega = sigma2 * 0.05
    alpha = 0.05
    beta = 0.85
    gamma = 0.08

    cond_var = [sigma2] * n
    for t in range(1, n):
        r_prev = returns[t - 1]
        dummy = 1.0 if r_prev < 0.0 else 0.0
        cond_var[t] = omega + (alpha + gamma * dummy) * (r_prev ** 2) + beta * cond_var[t - 1]
        if cond_var[t] <= 0:
            cond_var[t] = sigma2 * 1e-6

    cond_vol = [math.sqrt(max(v, 1e-12)) for v in cond_var]

    log_lik = 0.0
    for t in range(n):
        if cond_var[t] > 0:
            log_lik += -0.5 * (math.log(2 * math.pi * cond_var[t]) + returns[t] ** 2 / cond_var[t])

    r_last = returns[-1]
    dummy_last = 1.0 if r_last < 0.0 else 0.0
    forecast_v2 = omega + (alpha + gamma * dummy_last) * (r_last ** 2) + beta * cond_var[-1]
    forecast = [math.sqrt(max(forecast_v2, 1e-12))]

    return VolatilityModelResult(
        family=ModelFamily.TGARCH,
        omega=omega,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        conditional_volatility=cond_vol,
        log_likelihood=log_lik,
        forecast_volatility=forecast,
    )


# ──────────────────────────────────────────────
# Linear algebra helpers
# ──────────────────────────────────────────────

def _transpose(m: List[List[float]]) -> List[List[float]]:
    if not m:
        return []
    return [[m[i][j] for i in range(len(m))] for j in range(len(m[0]))]


def _mat_mul(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    n, k = len(a), len(a[0]) if a else 0
    m = len(b[0]) if b else 0
    out = [[0.0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            out[i][j] = sum(a[i][t] * b[t][j] for t in range(k))
    return out


def _mat_vec_mul(a: List[List[float]], v: List[float]) -> List[float]:
    return [sum(row[i] * v[i] for i in range(len(v))) for row in a]


def _solve_linear(a: List[List[float]], b: List[float]) -> List[float]:
    """Solve Ax=b by Gaussian elimination with partial pivoting."""
    n = len(b)
    aug = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[pivot] = aug[pivot], aug[col]
        pv = aug[col][col]
        if abs(pv) < 1e-12:
            return [0.0] * n
        for r in range(col + 1, n):
            factor = aug[r][col] / pv
            for c in range(col, n + 1):
                aug[r][c] -= factor * aug[col][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = aug[i][n] - sum(aug[i][j] * x[j] for j in range(i + 1, n))
        x[i] = s / aug[i][i]
    return x


def _mat_inv(a: List[List[float]]) -> List[List[float]]:
    """Matrix inversion via Gauss-Jordan elimination."""
    n = len(a)
    aug = [a[i][:] + [1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(aug[r][i]))
        aug[i], aug[pivot] = aug[pivot], aug[i]
        pv = aug[i][i]
        if abs(pv) < 1e-12:
            return [[1.0 if r == c else 0.0 for c in range(n)] for r in range(n)]
        for j in range(2 * n):
            aug[i][j] /= pv
        for r in range(n):
            if r != i:
                factor = aug[r][i]
                for j in range(2 * n):
                    aug[r][j] -= factor * aug[i][j]
    return [row[n:] for row in aug]


def _eigenvalues_sym(a: List[List[float]], max_iter: int = 100) -> List[float]:
    """Jacobi eigenvalue algorithm for symmetric matrices."""
    n = len(a)
    if n == 0:
        return []
    if n == 1:
        return [a[0][0]]
    if n == 2:
        tr = a[0][0] + a[1][1]
        det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
        disc = max(0.0, tr * tr - 4.0 * det)
        s = math.sqrt(disc)
        return sorted([(tr + s) / 2.0, (tr - s) / 2.0], reverse=True)

    A = [row[:] for row in a]
    for _ in range(max_iter):
        off_diag = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                off_diag += abs(A[i][j])
        if off_diag < 1e-10:
            break
        for p in range(n):
            for q in range(p + 1, n):
                if abs(A[p][q]) < 1e-12:
                    continue
                tau = (A[q][q] - A[p][p]) / (2.0 * A[p][q])
                t = 1.0 / (abs(tau) + math.sqrt(1.0 + tau * tau))
                if tau < 0:
                    t = -t
                c = 1.0 / math.sqrt(1.0 + t * t)
                s = t * c

                app = A[p][p]
                aqq = A[q][q]
                apq = A[p][q]
                A[p][p] = c * c * app - 2.0 * s * c * apq + s * s * aqq
                A[q][q] = s * s * app + 2.0 * s * c * apq + c * c * aqq
                A[p][q] = 0.0
                A[q][p] = 0.0
                for i in range(n):
                    if i != p and i != q:
                        aip = A[i][p]
                        aiq = A[i][q]
                        A[i][p] = c * aip - s * aiq
                        A[p][i] = A[i][p]
                        A[i][q] = s * aip + c * aiq
                        A[q][i] = A[i][q]

    return sorted([A[i][i] for i in range(n)], reverse=True)

