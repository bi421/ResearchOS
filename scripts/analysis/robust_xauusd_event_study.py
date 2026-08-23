from pathlib import Path

import numpy as np
import pandas as pd

INPUT = Path("reports/xauusd_event_study/xauusd_sma20_100_events_2021_2025.csv")
OUT = Path("reports/xauusd_event_study")
OUT.mkdir(parents=True, exist_ok=True)

BOOTSTRAPS = 5000
SEED = 42

print("=" * 78)
print("XAUUSD SMA20/100 — ROBUST EVENT STUDY")
print("=" * 78)

df = pd.read_csv(INPUT)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["year"] = df["timestamp"].dt.year

HORIZONS = ["15m", "30m", "60m", "240m"]

rng = np.random.default_rng(SEED)

# ------------------------------------------------------------
# Bootstrap mean CI
# ------------------------------------------------------------


def bootstrap_mean_ci(values, n_boot=BOOTSTRAPS, seed_rng=rng):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    n = len(values)

    if n == 0:
        return np.nan, np.nan, np.nan

    # Bootstrap in chunks to avoid unnecessary memory explosion.
    means = np.empty(n_boot)

    chunk = 500

    for start in range(0, n_boot, chunk):
        end = min(start + chunk, n_boot)
        size = end - start

        idx = seed_rng.integers(0, n, size=(size, n))

        means[start:end] = values[idx].mean(axis=1)

    low, high = np.percentile(means, [2.5, 97.5])

    return float(values.mean()), float(low), float(high)


# ------------------------------------------------------------
# Bootstrap win-rate CI
# ------------------------------------------------------------


def bootstrap_rate_ci(values, n_boot=BOOTSTRAPS, seed_rng=rng):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]

    n = len(values)

    if n == 0:
        return np.nan, np.nan, np.nan

    wins = values.astype(float)

    rates = np.empty(n_boot)

    chunk = 500

    for start in range(0, n_boot, chunk):
        end = min(start + chunk, n_boot)
        size = end - start

        idx = seed_rng.integers(0, n, size=(size, n))

        rates[start:end] = wins[idx].mean(axis=1)

    low, high = np.percentile(rates, [2.5, 97.5])

    return float(wins.mean()), float(low), float(high)


# ------------------------------------------------------------
# Main result collection
# ------------------------------------------------------------

rows = []

for horizon in HORIZONS:
    gross_col = f"return_{horizon}"
    net_col = f"net_return_{horizon}"

    if gross_col not in df:
        continue

    for year in sorted(df["year"].dropna().unique()):
        part = df[df["year"] == year]

        gross = part[gross_col].dropna().to_numpy()
        net = part[net_col].dropna().to_numpy()

        if len(gross) == 0:
            continue

        gross_mean, gross_lo, gross_hi = bootstrap_mean_ci(gross)

        net_mean, net_lo, net_hi = bootstrap_mean_ci(net)

        gross_win = (gross > 0).astype(float)

        net_win = (net > 0).astype(float)

        gwr, gwr_lo, gwr_hi = bootstrap_rate_ci(gross_win)

        nwr, nwr_lo, nwr_hi = bootstrap_rate_ci(net_win)

        rows.append(
            {
                "scope": "YEAR",
                "year": int(year),
                "direction": "ALL",
                "horizon": horizon,
                "n": len(net),
                "gross_mean": gross_mean,
                "gross_mean_ci_low": gross_lo,
                "gross_mean_ci_high": gross_hi,
                "net_mean": net_mean,
                "net_mean_ci_low": net_lo,
                "net_mean_ci_high": net_hi,
                "gross_win_rate": gwr,
                "gross_win_ci_low": gwr_lo,
                "gross_win_ci_high": gwr_hi,
                "net_win_rate": nwr,
                "net_win_ci_low": nwr_lo,
                "net_win_ci_high": nwr_hi,
            }
        )


# ------------------------------------------------------------
# Direction analysis
# ------------------------------------------------------------

for horizon in HORIZONS:
    gross_col = f"return_{horizon}"
    net_col = f"net_return_{horizon}"

    for direction in ["LONG", "SHORT"]:
        part = df[df["direction"] == direction]

        gross = part[gross_col].dropna().to_numpy()
        net = part[net_col].dropna().to_numpy()

        if len(net) == 0:
            continue

        gross_mean, gross_lo, gross_hi = bootstrap_mean_ci(gross)
        net_mean, net_lo, net_hi = bootstrap_mean_ci(net)

        gwr, gwr_lo, gwr_hi = bootstrap_rate_ci((gross > 0).astype(float))

        nwr, nwr_lo, nwr_hi = bootstrap_rate_ci((net > 0).astype(float))

        rows.append(
            {
                "scope": "DIRECTION",
                "year": 0,
                "direction": direction,
                "horizon": horizon,
                "n": len(net),
                "gross_mean": gross_mean,
                "gross_mean_ci_low": gross_lo,
                "gross_mean_ci_high": gross_hi,
                "net_mean": net_mean,
                "net_mean_ci_low": net_lo,
                "net_mean_ci_high": net_hi,
                "gross_win_rate": gwr,
                "gross_win_ci_low": gwr_lo,
                "gross_win_ci_high": gwr_hi,
                "net_win_rate": nwr,
                "net_win_ci_low": nwr_lo,
                "net_win_ci_high": nwr_hi,
            }
        )


# ------------------------------------------------------------
# Full sample analysis
# ------------------------------------------------------------

for horizon in HORIZONS:
    gross_col = f"return_{horizon}"
    net_col = f"net_return_{horizon}"

    gross = df[gross_col].dropna().to_numpy()
    net = df[net_col].dropna().to_numpy()

    gross_mean, gross_lo, gross_hi = bootstrap_mean_ci(gross)
    net_mean, net_lo, net_hi = bootstrap_mean_ci(net)

    gwr, gwr_lo, gwr_hi = bootstrap_rate_ci((gross > 0).astype(float))

    nwr, nwr_lo, nwr_hi = bootstrap_rate_ci((net > 0).astype(float))

    rows.append(
        {
            "scope": "FULL",
            "year": 0,
            "direction": "ALL",
            "horizon": horizon,
            "n": len(net),
            "gross_mean": gross_mean,
            "gross_mean_ci_low": gross_lo,
            "gross_mean_ci_high": gross_hi,
            "net_mean": net_mean,
            "net_mean_ci_low": net_lo,
            "net_mean_ci_high": net_hi,
            "gross_win_rate": gwr,
            "gross_win_ci_low": gwr_lo,
            "gross_win_ci_high": gwr_hi,
            "net_win_rate": nwr,
            "net_win_ci_low": nwr_lo,
            "net_win_ci_high": nwr_hi,
        }
    )


results = pd.DataFrame(rows)

csv_path = OUT / "robust_event_study.csv"
results.to_csv(csv_path, index=False)


# ------------------------------------------------------------
# Distribution statistics
# ------------------------------------------------------------

distribution = []

for horizon in HORIZONS:
    col = f"return_{horizon}"
    net_col = f"net_return_{horizon}"

    values = df[net_col].dropna()

    distribution.append(
        {
            "horizon": horizon,
            "n": len(values),
            "mean": values.mean(),
            "median": values.median(),
            "std": values.std(),
            "min": values.min(),
            "p01": values.quantile(0.01),
            "p05": values.quantile(0.05),
            "p25": values.quantile(0.25),
            "p75": values.quantile(0.75),
            "p95": values.quantile(0.95),
            "p99": values.quantile(0.99),
            "max": values.max(),
        }
    )

distribution_df = pd.DataFrame(distribution)

distribution_path = OUT / "return_distribution.csv"
distribution_df.to_csv(distribution_path, index=False)


# ------------------------------------------------------------
# Year × Direction × Horizon matrix
# ------------------------------------------------------------

matrix = []

for year in sorted(df["year"].unique()):
    for direction in ["LONG", "SHORT"]:
        part = df[(df["year"] == year) & (df["direction"] == direction)]

        for horizon in HORIZONS:
            col = f"net_return_{horizon}"

            values = part[col].dropna()

            if len(values) == 0:
                continue

            matrix.append(
                {
                    "year": int(year),
                    "direction": direction,
                    "horizon": horizon,
                    "n": len(values),
                    "mean_net": values.mean(),
                    "median_net": values.median(),
                    "win_rate_net": (values > 0).mean(),
                }
            )

matrix_df = pd.DataFrame(matrix)

matrix_path = OUT / "year_direction_matrix.csv"
matrix_df.to_csv(matrix_path, index=False)


# ------------------------------------------------------------
# Human-readable report
# ------------------------------------------------------------

report = []

report.append("XAUUSD SMA20/100 ROBUST EVENT STUDY")

report.append("=" * 78)

report.append(f"Input events: {len(df):,}")

report.append(f"Bootstrap iterations: {BOOTSTRAPS:,}")

report.append("Bootstrap confidence interval: 95%")

report.append("")

report.append("FULL SAMPLE")

report.append("-" * 78)

for horizon in HORIZONS:
    r = results[(results.scope == "FULL") & (results.horizon == horizon)].iloc[0]

    report.append(f"{horizon:>5} | N={int(r.n):,} | gross win={r.gross_win_rate:.2%} [{r.gross_win_ci_low:.2%}, {r.gross_win_ci_high:.2%}] | net mean={r.net_mean:.6%} [{r.net_mean_ci_low:.6%}, {r.net_mean_ci_high:.6%}] | net win={r.net_win_rate:.2%}")

report.append("")
report.append("YEARLY NET RESULTS")
report.append("-" * 78)

for year in sorted(df.year.unique()):
    report.append(f"\n{int(year)}")

    for horizon in HORIZONS:
        r = results[(results.scope == "YEAR") & (results.year == year) & (results.horizon == horizon)]

        if len(r) == 0:
            continue

        r = r.iloc[0]

        report.append(f"  {horizon:>5}: N={int(r.n):,} | net mean={r.net_mean:.6%} [{r.net_mean_ci_low:.6%}, {r.net_mean_ci_high:.6%}] | net win={r.net_win_rate:.2%}")

report.append("")
report.append("DIRECTION")
report.append("-" * 78)

for direction in ["LONG", "SHORT"]:
    report.append(f"\n{direction}")

    for horizon in HORIZONS:
        r = results[(results.scope == "DIRECTION") & (results.direction == direction) & (results.horizon == horizon)]

        if len(r) == 0:
            continue

        r = r.iloc[0]

        report.append(f"  {horizon:>5}: N={int(r.n):,} | net mean={r.net_mean:.6%} [{r.net_mean_ci_low:.6%}, {r.net_mean_ci_high:.6%}] | net win={r.net_win_rate:.2%}")

# ------------------------------------------------------------
# Automatic interpretation
# ------------------------------------------------------------

report.append("")
report.append("INTERPRETATION")
report.append("-" * 78)

for horizon in HORIZONS:
    r = results[(results.scope == "FULL") & (results.horizon == horizon)].iloc[0]

    ci_low = r.net_mean_ci_low
    ci_high = r.net_mean_ci_high

    if ci_low > 0:
        verdict = "POSITIVE EDGE SIGNAL"
    elif ci_high < 0:
        verdict = "NEGATIVE EDGE SIGNAL"
    else:
        verdict = "NO STATISTICALLY CLEAR EDGE"

    report.append(f"{horizon:>5}: {verdict} | 95% CI [{ci_low:.6%}, {ci_high:.6%}]")

report.append("")
report.append("IMPORTANT: This event study does not establish future trading profitability.")

report.append("It evaluates historical event-level conditional returns and must be followed by out-of-sample / walk-forward validation.")

report_path = OUT / "robust_event_study_report.txt"

report_path.write_text("\n".join(report), encoding="utf-8")


# ------------------------------------------------------------
# Console
# ------------------------------------------------------------

print()
print("=" * 78)
print("ROBUST ANALYSIS COMPLETE")
print("=" * 78)

print()
print("FULL SAMPLE:")

for horizon in HORIZONS:
    r = results[(results.scope == "FULL") & (results.horizon == horizon)].iloc[0]

    verdict = "POSITIVE" if r.net_mean_ci_low > 0 else "NEGATIVE" if r.net_mean_ci_high < 0 else "NO CLEAR EDGE"

    print(f"{horizon:>5} | N={int(r.n):,} | GrossWin={r.gross_win_rate:.2%} | NetWin={r.net_win_rate:.2%} | NetMean={r.net_mean:.6%} | CI=[{r.net_mean_ci_low:.6%}, {r.net_mean_ci_high:.6%}] | {verdict}")

print()
print("FILES:")
print(csv_path)
print(distribution_path)
print(matrix_path)
print(report_path)
print("=" * 78)
