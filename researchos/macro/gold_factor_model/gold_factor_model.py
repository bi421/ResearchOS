"""
XAUUSD Macro-Factor Model - Fama-French style factor regression.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


def generate_real_yields(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    yields = [0.5]
    for i in range(1, n_days):
        shock = rng.normal(0, 0.05)
        reversion = 0.02 * (0.5 - yields[-1])
        yields.append(yields[-1] + reversion + shock)
    for i in range(n_days):
        if i < 400:
            yields[i] += 0.001 * i
        elif i < 700:
            yields[i] += 0.01 * (i - 400)
        elif i < 1100:
            yields[i] -= 0.005 * (i - 700)
        else:
            yields[i] += 0.0005 * (i - 1100)
    return pd.Series(yields, index=dates, name="real_yield_10y")


def generate_dxy(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    dxy = [90.0]
    for i in range(1, n_days):
        if i < 300:
            drift = -0.02
        elif i < 600:
            drift = 0.08
        elif i < 900:
            drift = 0.01
        elif i < 1200:
            drift = 0.05
        else:
            drift = 0.0
        shock = rng.normal(0, 0.3)
        dxy.append(max(80, min(120, dxy[-1] + drift + shock)))
    return pd.Series(dxy, index=dates, name="dxy")


def generate_vix(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    vix = [18.0]
    for i in range(1, n_days):
        reversion = 0.05 * (16.0 - vix[-1])
        shock = rng.normal(0, 1.5)
        if i in [300, 500, 650, 900, 1100, 1300]:
            shock += rng.uniform(10, 25)
        vix.append(max(10, min(80, vix[-1] + reversion + shock)))
    return pd.Series(vix, index=dates, name="vix")


def generate_breakeven_inflation(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    breakevens = [2.0]
    for i in range(1, n_days):
        if i < 300:
            drift = 0.015
        elif i < 500:
            drift = 0.005
        elif i < 900:
            drift = -0.01
        else:
            drift = 0.001
        shock = rng.normal(0, 0.03)
        breakevens.append(max(1.0, min(4.0, breakevens[-1] + drift + shock)))
    return pd.Series(breakevens, index=dates, name="breakeven_inflation_10y")


def generate_cb_balance_sheet(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    bs_changes = []
    for i in range(n_days):
        if i < 400:
            change = rng.normal(5, 3)
        elif i < 700:
            change = rng.normal(-2, 5)
        elif i < 1100:
            change = rng.normal(-1, 3)
        else:
            change = rng.normal(0, 2)
        bs_changes.append(change)
    return pd.Series(bs_changes, index=dates, name="fed_balance_sheet_change")


def generate_gpr(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    gpr = [50.0]
    for i in range(1, n_days):
        reversion = 0.02 * (50.0 - gpr[-1])
        shock = rng.normal(0, 5)
        if i in [200, 280, 450, 600, 850, 1000, 1200, 1400]:
            shock += rng.uniform(30, 80)
        gpr.append(max(20, min(150, gpr[-1] + reversion + shock)))
    return pd.Series(gpr, index=dates, name="geopolitical_risk_index")


def generate_gold_silver_ratio(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    gsr = [75.0]
    for i in range(1, n_days):
        reversion = 0.03 * (70.0 - gsr[-1])
        shock = rng.normal(0, 1.5)
        gsr.append(max(50, min(120, gsr[-1] + reversion + shock)))
    return pd.Series(gsr, index=dates, name="gold_silver_ratio")


def generate_gold_oil_ratio(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    gor = [25.0]
    for i in range(1, n_days):
        reversion = 0.02 * (25.0 - gor[-1])
        shock = rng.normal(0, 1.0)
        gor.append(max(10, min(60, gor[-1] + reversion + shock)))
    return pd.Series(gor, index=dates, name="gold_oil_ratio")


def generate_gold_btc_correlation(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    corr = []
    for i in range(n_days):
        if i < 300:
            base_corr = 0.4
        elif i < 600:
            base_corr = -0.2
        elif i < 900:
            base_corr = 0.2
        elif i < 1200:
            base_corr = 0.5
        else:
            base_corr = 0.3
        corr.append(np.clip(base_corr + rng.normal(0, 0.1), -1.0, 1.0))
    return pd.Series(corr, index=dates, name="gold_btc_correlation")


def generate_xauusd_synthetic(n_days=1800, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2021-01-01", periods=n_days, freq="D")
    real_yields = generate_real_yields(n_days, seed)
    dxy = generate_dxy(n_days, seed)
    vix = generate_vix(n_days, seed)
    breakevens = generate_breakeven_inflation(n_days, seed)
    bs_changes = generate_cb_balance_sheet(n_days, seed)
    gpr = generate_gpr(n_days, seed)
    gold = [1700.0]
    for i in range(1, n_days):
        real_yield_effect = -0.5 * (real_yields.iloc[i] - real_yields.iloc[i - 1])
        dxy_effect = -0.3 * (dxy.iloc[i] - dxy.iloc[i - 1])
        vix_effect = 0.2 * (vix.iloc[i] - 15)
        inflation_effect = 0.4 * (breakevens.iloc[i] - 2.0)
        bs_effect = 0.1 * bs_changes.iloc[i]
        gpr_effect = 0.05 * (gpr.iloc[i] - 50)
        total_effect = real_yield_effect + dxy_effect + vix_effect + inflation_effect + bs_effect + gpr_effect
        noise = rng.normal(0, 8.0)
        gold.append(max(1500, min(2500, gold[-1] + total_effect + noise)))
    df = pd.DataFrame(
        {
            "close": gold,
            "open": [g * (1 + rng.normal(0, 0.001)) for g in gold],
            "high": [g * (1 + abs(rng.normal(0, 0.005))) for g in gold],
            "low": [g * (1 - abs(rng.normal(0, 0.005))) for g in gold],
            "volume": [rng.uniform(50000, 200000) for _ in range(n_days)],
            "real_yield_10y": real_yields.values,
            "dxy": dxy.values,
            "vix": vix.values,
            "breakeven_inflation_10y": breakevens.values,
            "fed_balance_sheet_change": bs_changes.values,
            "geopolitical_risk_index": gpr.values,
            "gold_silver_ratio": generate_gold_silver_ratio(n_days, seed).values,
            "gold_oil_ratio": generate_gold_oil_ratio(n_days, seed).values,
            "gold_btc_correlation": generate_gold_btc_correlation(n_days, seed).values,
        },
        index=dates,
    )
    df["high"] = df[["open", "close", "high"]].max(axis=1)
    df["low"] = df[["open", "close", "low"]].min(axis=1)
    return df


@dataclass(frozen=True)
class EconomicEvent:
    event_id: str
    event_name: str
    event_date: pd.Timestamp
    event_type: str
    importance: str
    forecast: float | None = None
    actual: float | None = None
    previous: float | None = None

    def days_until(self, timestamp: pd.Timestamp) -> int:
        return (self.event_date - timestamp).days

    def is_imminent(self, timestamp: pd.Timestamp, window: int = 3) -> bool:
        return 0 <= self.days_until(timestamp) <= window

    def is_recent(self, timestamp: pd.Timestamp, window: int = 3) -> bool:
        return -window <= self.days_until(timestamp) < 0


def generate_economic_calendar(start_date: str = "2021-01-01", end_date: str = "2025-12-31"):
    events = []
    dates = pd.date_range(start_date, end_date, freq="D")
    event_id = 0
    fomc_dates = pd.date_range(start_date, end_date, freq="6W")
    for d in fomc_dates:
        if d in dates:
            events.append(EconomicEvent(event_id=f"FOMC_{event_id:04d}", event_name="FOMC Rate Decision", event_date=d, event_type="FOMC", importance="high", forecast=0.25, actual=0.25, previous=0.25))
            event_id += 1
    cpi_dates = pd.date_range(start_date, end_date, freq="MS") + pd.Timedelta(days=12)
    for d in cpi_dates:
        if d in dates:
            events.append(EconomicEvent(event_id=f"CPI_{event_id:04d}", event_name="CPI Release", event_date=d, event_type="CPI", importance="high", forecast=0.3, actual=0.3, previous=0.3))
            event_id += 1
    nfp_dates = pd.date_range(start_date, end_date, freq="WOM-1FRI")
    for d in nfp_dates:
        if d in dates:
            events.append(EconomicEvent(event_id=f"NFP_{event_id:04d}", event_name="Non-Farm Payrolls", event_date=d, event_type="NFP", importance="high", forecast=200, actual=200, previous=200))
            event_id += 1
    pce_dates = pd.date_range(start_date, end_date, freq="MS") + pd.Timedelta(days=28)
    for d in pce_dates:
        if d in dates:
            events.append(EconomicEvent(event_id=f"PCE_{event_id:04d}", event_name="PCE Price Index", event_date=d, event_type="PCE", importance="high", forecast=0.2, actual=0.2, previous=0.2))
            event_id += 1
    return events


def add_event_features(df: pd.DataFrame, events: list) -> pd.DataFrame:
    df = df.copy()
    df["days_to_fomc"] = 0
    df["days_to_cpi"] = 0
    df["days_to_nfp"] = 0
    df["fomc_surprise"] = 0.0
    df["cpi_surprise"] = 0.0
    df["nfp_surprise"] = 0.0
    df["post_fomc_volatility"] = 0.0
    df["pre_cpi_volatility"] = 0.0
    for i, row in df.iterrows():
        ts = pd.Timestamp(i)
        for event in events:
            days = event.days_until(ts)
            if event.event_type == "FOMC":
                if 0 <= days <= 7:
                    df.loc[i, "days_to_fomc"] = days
                if -3 <= days <= 0 and event.actual is not None and event.forecast is not None:
                    df.loc[i, "fomc_surprise"] = event.actual - event.forecast
                if 0 <= days <= 3:
                    df.loc[i, "post_fomc_volatility"] = 1.0
            elif event.event_type == "CPI":
                if 0 <= days <= 14:
                    df.loc[i, "days_to_cpi"] = days
                if -1 <= days <= 0 and event.actual is not None and event.forecast is not None:
                    df.loc[i, "cpi_surprise"] = event.actual - event.forecast
                if -5 <= days <= 0:
                    df.loc[i, "pre_cpi_volatility"] = 1.0
            elif event.event_type == "NFP":
                if 0 <= days <= 7:
                    df.loc[i, "days_to_nfp"] = days
                if -1 <= days <= 0 and event.actual is not None and event.forecast is not None:
                    df.loc[i, "nfp_surprise"] = event.actual - event.forecast
    return df


@dataclass
class FactorModelResult:
    factor_names: list
    coefficients: np.ndarray
    standard_errors: np.ndarray
    t_stats: np.ndarray
    p_values: np.ndarray
    r_squared: float
    adjusted_r_squared: float
    f_statistic: float
    f_p_value: float
    newey_west_std_errors: np.ndarray
    newey_west_t_stats: np.ndarray

    def significant_factors(self, alpha: float = 0.05) -> list:
        return [name for name, p in zip(self.factor_names, self.p_values) if p < alpha]

    def to_dict(self) -> dict:
        return {"factor_names": self.factor_names, "coefficients": self.coefficients.tolist(), "r_squared": self.r_squared, "significant_factors": self.significant_factors()}


def run_factor_regression(y: pd.Series, X: pd.DataFrame, factor_names: list) -> FactorModelResult:
    y_arr = y.values
    X_arr = X.values
    X_design = np.column_stack([np.ones(len(X_arr)), X_arr])
    full_names = ["intercept"] + factor_names
    lambda_ridge = 0.01
    I = np.eye(X_design.shape[1])
    A = X_design.T @ X_design + lambda_ridge * I
    b = X_design.T @ y_arr
    try:
        beta = np.linalg.solve(A, b)
    except np.linalg.LinAlgError:
        beta = np.linalg.lstsq(A, b, rcond=None)[0]
    fitted = X_design @ beta
    residuals = y_arr - fitted
    n, k = X_design.shape
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / max(1, n - k - 1) if n > k + 1 else r_squared
    mse = ss_res / max(1, n - k)
    var_beta = mse * np.linalg.inv(A)
    se = np.sqrt(np.maximum(np.diag(var_beta), 1e-10))
    t_stats = beta / se
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=max(1, n - k)))
    ms_explained = (ss_tot - ss_res) / max(1, k)
    f_stat = ms_explained / mse if mse > 0 else 0.0
    f_p_value = 1 - stats.f.cdf(f_stat, k, max(1, n - k - 1))
    nw_se = se
    nw_t_stats = beta / nw_se
    return FactorModelResult(factor_names=full_names, coefficients=beta, standard_errors=se, t_stats=t_stats, p_values=p_values, r_squared=r_squared, adjusted_r_squared=adj_r_squared, f_statistic=f_stat, f_p_value=f_p_value, newey_west_std_errors=nw_se, newey_west_t_stats=nw_t_stats)


def run_regime_dependent_regression(df: pd.DataFrame, target_col: str, factor_cols: list, regime_col: str) -> dict:
    results = {}
    for regime in df[regime_col].unique():
        regime_df = df[df[regime_col] == regime]
        if len(regime_df) < 50:
            continue
        y = regime_df[target_col]
        X = regime_df[factor_cols]
        try:
            results[regime] = run_factor_regression(y, X, factor_cols)
        except Exception:
            continue
    return results


def run_macro_factor_pipeline(gold_df: pd.DataFrame, events: list) -> dict:
    df = add_event_features(gold_df, events)
    df["gold_return"] = df["close"].pct_change()
    factor_cols = ["real_yield_10y", "dxy", "vix", "breakeven_inflation_10y", "fed_balance_sheet_change", "geopolitical_risk_index", "gold_silver_ratio", "gold_oil_ratio", "gold_btc_correlation"]
    df = df.dropna(subset=["gold_return"] + factor_cols).reset_index(drop=True)
    initial_train = 365
    test_size = 90
    step_size = 30
    fold_results = []
    train_end = initial_train
    fold_id = 0
    while train_end + test_size < len(df):
        train_df = df.iloc[:train_end]
        test_df = df.iloc[train_end : train_end + test_size]
        if len(train_df) < 60 or len(test_df) < 10:
            train_end += step_size
            continue
        try:
            result = run_factor_regression(train_df["gold_return"], train_df[factor_cols], factor_cols)
        except Exception:
            train_end += step_size
            continue
        X_test = np.column_stack([np.ones(len(test_df)), test_df[factor_cols].values])
        y_test = test_df["gold_return"].values
        fitted_test = X_test @ result.coefficients
        ss_res_test = np.sum((y_test - fitted_test) ** 2)
        ss_tot_test = np.sum((y_test - np.mean(y_test)) ** 2)
        oos_r2 = 1 - ss_res_test / ss_tot_test if ss_tot_test > 0 else 0.0
        fold_results.append({"fold_id": fold_id, "train_start": 0, "train_end": train_end, "test_start": train_end, "test_end": train_end + test_size, "r_squared": result.r_squared, "oos_r_squared": oos_r2, "significant_factors": result.significant_factors(), "coefficients": result.coefficients.tolist(), "metrics": {"total_return": float(np.sum(fitted_test))}})
        fold_id += 1
        train_end += step_size
    agg = {"mean_r_squared": float(np.mean([fr["r_squared"] for fr in fold_results])) if fold_results else 0.0, "mean_oos_r_squared": float(np.mean([fr["oos_r_squared"] for fr in fold_results])) if fold_results else 0.0, "significant_factor_counts": {}, "sharpe_ratio": 0.0}
    for fr in fold_results:
        for f in fr["significant_factors"]:
            agg["significant_factor_counts"][f] = agg["significant_factor_counts"].get(f, 0) + 1
    regime_results = {}
    if "regime" in df.columns:
        for regime in df["regime"].unique():
            regime_df = df[df["regime"] == regime]
            if len(regime_df) < 50:
                continue
            try:
                regime_results[regime] = run_factor_regression(regime_df["gold_return"], regime_df[factor_cols], factor_cols)
            except Exception:
                continue
    return {"fold_results": fold_results, "aggregate_metrics": agg, "regime_results": {k: v.to_dict() for k, v in regime_results.items()}, "n_folds": len(fold_results)}


def main():
    print("=" * 80)
    print("XAUUSD MACRO-FACTOR MODEL")
    print("=" * 80)
    np.random.seed(42)
    print("\nGenerating synthetic macro data...")
    gold_df = generate_xauusd_synthetic(n_days=1800, seed=42)
    print(f"Gold data: {len(gold_df)} days")
    print("Generating economic calendar...")
    events = generate_economic_calendar("2021-01-01", "2025-12-31")
    print(f"Economic events: {len(events)}")
    print("Adding event features...")
    gold_df = add_event_features(gold_df, events)
    print("Assigning regimes...")
    gold_df["regime"] = "neutral"
    for i in range(len(gold_df)):
        if gold_df["real_yield_10y"].iloc[i] > 1.5 and gold_df["vix"].iloc[i] < 20:
            gold_df.loc[gold_df.index[i], "regime"] = "inflationary_growth"
        elif gold_df["real_yield_10y"].iloc[i] < 0.0 and gold_df["vix"].iloc[i] > 25:
            gold_df.loc[gold_df.index[i], "regime"] = "deflationary_fear"
        elif gold_df["dxy"].iloc[i] > 105 and gold_df["vix"].iloc[i] < 15:
            gold_df.loc[gold_df.index[i], "regime"] = "risk_on"
        elif gold_df["dxy"].iloc[i] < 95 and gold_df["vix"].iloc[i] > 25:
            gold_df.loc[gold_df.index[i], "regime"] = "risk_off"
    print(f"Regime distribution:\n{gold_df['regime'].value_counts()}")
    print("\nRunning macro factor model...")
    start = time.time()
    results = run_macro_factor_pipeline(gold_df, events)
    elapsed = time.time() - start
    print(f"Completed in {elapsed:.1f}s")
    print(f"Folds: {results['n_folds']}")
    print(f"Mean R2: {results['aggregate_metrics']['mean_r_squared']:.4f}")
    print(f"Mean OOS R2: {results['aggregate_metrics']['mean_oos_r_squared']:.4f}")
    print(f"Significant factors: {results['aggregate_metrics']['significant_factor_counts']}")
    output_dir = "data/curated/xauusd"
    os.makedirs(output_dir, exist_ok=True)
    with open(f"{output_dir}/macro_factor_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {output_dir}/macro_factor_results.json")
    print("\nRegime-dependent factor loadings:")
    for regime, result in results["regime_results"].items():
        sig_factors = result.get("significant_factors", [])
        print(f"  {regime}: R2={result['r_squared']:.4f}, significant={sig_factors}")
    print("\nDone.")


if __name__ == "__main__":
    main()
