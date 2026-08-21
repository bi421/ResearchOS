import glob
import sys

import pandas as pd

sys.path.append("cpp_quant/python")
from cpp_quant import CppQuant

# -------------------------------
# 1. ??????? ??????? (Parquet ??????)
# -------------------------------
print("?? ??????? ????? ?????...")
cache_file = "data/xauusd_1min.parquet"

try:
    df = pd.read_parquet(cache_file)
    print(f"? ?????? ?????: {len(df)} ??????")
except Exception:
    print("? CSV-??? ?????, ??? ???? ?????...")
    df = pd.concat(
        [
            pd.read_csv(
                f,
                sep=";",
                header=None,
                names=["datetime", "open", "high", "low", "close", "volume"],
                dtype={"datetime": str},
            )
            .assign(datetime=lambda x: pd.to_datetime(x["datetime"], format="%Y%m%d %H%M%S"))
            .dropna(subset=["datetime"])
            .set_index("datetime")
            for f in glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
        ]
    ).sort_index()
    df.to_parquet(cache_file)
    print(f"? ??? ????????: {len(df)} ??????")

# -------------------------------
# 2. ?????? ?????, ????????
# -------------------------------
timeframes = [("1D", "1D"), ("4h", "4h"), ("1h", "1h")]

strategies = [
    ("SMA 20/50", lambda e: e.run_sma(20, 50)),
    ("SMA 50/200", lambda e: e.run_sma(50, 200)),
    ("RSI 14", lambda e: e.run_rsi(14, 30, 70)),
    ("MACD 12/26/9", lambda e: e.run_macd(12, 26, 9, 200)),
]

# -------------------------------
# 3. ??? ???????? ??????
# -------------------------------
results = []
engine = CppQuant()

print("\n" + "=" * 70)
print("?? ??? ???????? × ??? ?????? ?????")
print("=" * 70)

for label, rule in timeframes:
    print(f"\n?? {label} ?????????? ?????...")
    df_tf = df.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    print(f"   {len(df_tf)} candle")

    engine.load_from_dataframe(df_tf)

    for name, func in strategies:
        try:
            r = func(engine)
            # Bootstrap CI (C++ ???????)
            pnls = [t[4] for t in r["trades"]]
            if len(pnls) > 5:
                ci_low, ci_high = engine.get_bootstrap_winrate_ci(pnls, iterations=500, ci=0.95)
                ci_low_pct = ci_low * 100
                ci_high_pct = ci_high * 100
            else:
                ci_low_pct = 0.0
                ci_high_pct = 0.0

            results.append(
                {
                    "timeframe": label,
                    "strategy": name,
                    "trades": r["num_trades"],
                    "winrate": r["winrate"],
                    "winrate_ci_low": ci_low_pct,
                    "winrate_ci_high": ci_high_pct,
                    "total_return": r["total_return"],
                    "sharpe": r["sharpe_ratio"],
                    "max_dd": r["max_drawdown"],
                }
            )
            print(f"   {name}: WR {r['winrate']:.2f}% (CI: {ci_low_pct:.1f}-{ci_high_pct:.1f}%), Trades {r['num_trades']}")
        except Exception as e:
            print(f"   {name}: ????? - {e}")

# -------------------------------
# 4. ??????
# -------------------------------
df_res = pd.DataFrame(results)

print("\n" + "=" * 70)
print("?? ???????")
print("=" * 70)
print(
    df_res[
        [
            "timeframe",
            "strategy",
            "trades",
            "winrate",
            "winrate_ci_low",
            "winrate_ci_high",
            "total_return",
            "sharpe",
        ]
    ].to_string(index=False)
)

# ??????? ???? ????????
if not df_res.empty:
    best = df_res.loc[df_res["winrate"].idxmax()]
    print("\n?? ??????? ????:")
    print(
        f"   {best['timeframe']} / {best['strategy']}: Winrate {best['winrate']:.2f}% (CI: {best['winrate_ci_low']:.1f}-{best['winrate_ci_high']:.1f}%), Trades {best['trades']}"
    )

# CSV ????????
df_res.to_csv("analysis_results.csv", index=False)
print("\n? analysis_results.csv ????????????")
