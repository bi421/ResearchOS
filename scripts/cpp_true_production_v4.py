import glob
import json
import sys
import time

import pandas as pd

print("=" * 70)
print("🚀 TRUE PRODUCTION v4: Winrate + Комисс зассан")
print("=" * 70)

# 1. Өгөгдөл ачаалах
start_load = time.time()
files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
if not files:
    print("❌ Өгөгдөл олдсонгүй!")
    sys.exit(1)

df = pd.concat(
    [
        pd.read_csv(
            f,
            sep=";",
            header=None,
            names=["datetime", "open", "high", "low", "close", "volume"],
            dtype={"datetime": str},
        )
        for f in files
    ],
    ignore_index=True,
)

df["timestamp"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S").astype("int64") // 10**9
df = df.drop(columns=["datetime"])

print(f"✅ {len(df):,} мөрийг {time.time() - start_load:.2f} секундэд бэлдлээ")

# 2. C++ engine (wrapper-д байгаа аргаар)
from researchos.quant_engine.cpp_backend import CppQuantAdapter

engine = CppQuantAdapter()

# 3. Sweep
timeframes = [5, 15, 30, 60]
commissions = [0.0005, 0.001, 0.0015]
results = []
sweep_start = time.time()

for h in timeframes:
    # DataFrame-г C++-д дамжуулах (resample хийх)
    df_resampled = df.resample(f"{h}T", on="timestamp").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    df_resampled = df_resampled.reset_index()

    # C++-д дамжуулах
    engine.load_dataframe(df_resampled)

    for t in commissions:
        try:
            # run_backtest дуудах (комисстой)
            result = engine.run_backtest(commission=t)

            # Winrate-г ЗӨВ масштаблах (0-1 → 0-100%)
            winrate = result.get("winrate", 0)
            if winrate > 1:  # Хэрэв аль хэдийн хувь байгаа бол
                winrate = winrate / 100.0

            results.append(
                {
                    "timeframe": f"{h}m",
                    "commission": t,
                    "winrate": winrate * 100,  # Хувь хэлбэрээр хадгалах
                    "trades": result.get("num_trades", 0),
                    "return": result.get("total_return", 0),
                    "sharpe": result.get("sharpe_ratio", 0),
                }
            )

            print(f"  h={h:2d}m, t={t * 100:.2f}% | Winrate: {winrate * 100:.2f}%, Trades: {result.get('num_trades', 0)}")

        except Exception as e:
            print(f"  h={h:2d}m, t={t * 100:.2f}% | ❌ Алдаа: {e}")

sweep_time = time.time() - sweep_start
print(f"\n✅ Нийт C++ Sweep хугацаа: {sweep_time:.2f} секунд")

# 4. Хадгалах
output_file = "data/curated/xauusd/phase51_m1_cpp_true_production_v4.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"📊 C++ үр дүн хадгалагдлаа: {output_file}")

if results:
    best = max(results, key=lambda x: x["winrate"])
    print("\n🏆 ХАМГИЙН САЙН:")
    print(f"  Цаг.хүрээ: {best['timeframe']}")
    print(f"  Комисс: {best['commission'] * 100:.2f}%")
    print(f"  Winrate: {best['winrate']:.2f}%")
    print(f"  Sharpe: {best['sharpe']:.2f}")

print("\n" + "=" * 70)
print("✅ БҮХ АЖИЛ ДУУССАН!")
