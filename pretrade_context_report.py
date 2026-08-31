import pandas as pd

gold = pd.read_csv("data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv")
date_col = [c for c in gold.columns if c.lower() in ("date", "time", "datetime")][0]
close_col = [c for c in gold.columns if c.lower() == "close"][0]
gold[date_col] = pd.to_datetime(gold[date_col])
gold = gold[[date_col, close_col]].rename(columns={date_col: "date", close_col: "gold_close"})
gold = gold.sort_values("date").reset_index(drop=True)

dxy = pd.read_csv("dxy_real_2021_2025.csv", skiprows=2)
dxy.columns = ["date", "close", "high", "low", "open", "volume"]
dxy["date"] = pd.to_datetime(dxy["date"])
dxy["dxy_close"] = pd.to_numeric(dxy["close"], errors="coerce")
dxy = dxy[["date", "dxy_close"]]

vix = pd.read_csv("vix_real_2021_2025.csv", skiprows=2)
vix.columns = ["date", "close", "high", "low", "open", "volume"]
vix["date"] = pd.to_datetime(vix["date"])
vix["vix_close"] = pd.to_numeric(vix["close"], errors="coerce")
vix = vix[["date", "vix_close"]]

us10y = pd.read_csv("us10y_real_2021_2025.csv")
us10y["date"] = pd.to_datetime(us10y["date"])

df = gold.merge(dxy, on="date", how="inner").merge(vix, on="date", how="inner")
df = df.merge(us10y, on="date", how="left").sort_values("date").reset_index(drop=True)
df["real_yield_10y"] = df["real_yield_10y"].ffill()
df["gold_return"] = df["gold_close"].pct_change()
df["dxy_return"] = df["dxy_close"].pct_change()
df["gold_vol_20d"] = df["gold_return"].rolling(20).std()
df["vix_change"] = df["vix_close"].pct_change()
df["gold_dxy_corr_60d"] = df["gold_return"].rolling(60).corr(df["dxy_return"])
df["gold_vix_corr_60d"] = df["gold_return"].rolling(60).corr(df["vix_change"])
df = df.dropna().reset_index(drop=True)

latest = df.iloc[-1]
lookback_1y = df.iloc[-252:] if len(df) >= 252 else df

report = {}
report["as_of_date"] = str(latest["date"].date())

for window in [20, 50, 200]:
    if len(df) >= window:
        sma = df["gold_close"].rolling(window).mean().iloc[-1]
        pct_from_sma = (latest["gold_close"] - sma) / sma * 100
        report["gold_vs_sma" + str(window) + "_pct"] = round(pct_from_sma, 2)

current_vol = df["gold_vol_20d"].iloc[-1]
vol_percentile = (lookback_1y["gold_vol_20d"] <= current_vol).mean() * 100
report["gold_20d_volatility"] = round(current_vol * 100, 3)
report["gold_volatility_percentile_1y"] = round(vol_percentile, 1)

current_vix = latest["vix_close"]
vix_percentile = (lookback_1y["vix_close"] <= current_vix).mean() * 100
report["vix_level"] = round(current_vix, 2)
report["vix_percentile_1y"] = round(vix_percentile, 1)

for window in [5, 20]:
    if len(df) > window:
        pct_change = (latest["dxy_close"] / df["dxy_close"].iloc[-window - 1] - 1) * 100
        report["dxy_" + str(window) + "d_change_pct"] = round(pct_change, 2)

report["us10y_real_yield"] = round(latest["real_yield_10y"], 3)
if len(df) > 20:
    yield_20d_ago = df["real_yield_10y"].iloc[-21]
    report["us10y_20d_change_bps"] = round((latest["real_yield_10y"] - yield_20d_ago) * 100, 1)

report["gold_dxy_correlation_60d"] = round(df["gold_dxy_corr_60d"].iloc[-1], 3)
report["gold_vix_correlation_60d"] = round(df["gold_vix_corr_60d"].iloc[-1], 3)

vol_regime = "HIGH" if vol_percentile > 70 else ("LOW" if vol_percentile < 30 else "NORMAL")
vix_regime = "ELEVATED" if vix_percentile > 70 else ("SUPPRESSED" if vix_percentile < 30 else "NORMAL")
report["gold_volatility_regime"] = vol_regime
report["vix_regime"] = vix_regime

print("=" * 70)
print("PRE-TRADE CONTEXT REPORT - XAUUSD")
print("As of:", report["as_of_date"])
print("=" * 70)
print("NOTE: Descriptive only. No prediction, no signal. Prior tests")
print("found no statistically significant directional edge.")
print("=" * 70)

print("")
print("[GOLD PRICE CONTEXT]")
for w in [20, 50, 200]:
    key = "gold_vs_sma" + str(w) + "_pct"
    if key in report:
        print("  vs", w, "-day SMA:", report[key], "%")

print("")
print("[VOLATILITY CONTEXT]")
print("  Gold 20d realized volatility:", report["gold_20d_volatility"], "%")
print("  -> percentile vs past 1y:", report["gold_volatility_percentile_1y"])
print("  -> regime:", report["gold_volatility_regime"])
print("  VIX level:", report["vix_level"])
print("  -> percentile vs past 1y:", report["vix_percentile_1y"])
print("  -> regime:", report["vix_regime"])

print("")
print("[USD / RATES CONTEXT]")
for w in [5, 20]:
    key = "dxy_" + str(w) + "d_change_pct"
    if key in report:
        print("  DXY", w, "-day change:", report[key], "%")
print("  US10Y real yield:", report["us10y_real_yield"], "%")
if "us10y_20d_change_bps" in report:
    print("  -> 20-day change:", report["us10y_20d_change_bps"], "bps")

print("")
print("[CROSS-ASSET RELATIONSHIPS]")
print("  Gold-DXY 60d rolling correlation:", report["gold_dxy_correlation_60d"])
print("  Gold-VIX 60d rolling correlation:", report["gold_vix_correlation_60d"])

print("")
print("=" * 70)
print("END OF REPORT - descriptive only, not a trading recommendation.")
print("=" * 70)
