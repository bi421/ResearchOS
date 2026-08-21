"""
TRUE PRODUCTION v2: Векторчилсон өгөгдөл + 1 удаагийн C++ ачаалал + Sweep
"""

import sys
import time
import pandas as pd
import glob
from cpp_quant import CppQuant

print("=" * 70)
print("🚀 TRUE PRODUCTION v2: 1 удаагийн C++ ачаалал + Sweep")
print("=" * 70)

# ============================================================
# 1. ӨГӨГДӨЛ АЧААЛАХ (ВЕКТОРЧИЛСОН)
# ============================================================
print("📂 Өгөгдөл: xauusd_m1_2021_2025_mt5.csv")
start_load = time.time()

files = glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv")
if not files:
    print("❌ Өгөгдөл олдсонгүй!")
    sys.exit(1)

# Бүх файлыг нэг дор унших (хурдан)
df = pd.concat(
    [
        pd.read_csv(
            f,
            sep=";",
            header=None,
            names=["datetime", "open", "high", "low", "close", "volume"],
            dtype={
                "datetime": str,
                "open": float,
                "high": float,
                "low": float,
                "close": float,
                "volume": float,
            },
        )
        for f in files
    ],
    ignore_index=True,
)

# 🔥 АЛДАА ЗАСАХ: datetime-г UNIX EPOCH (секунд) болгон хувиргах
# Формат: 20210103 180000 → 1609682400
df["timestamp"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S").astype("int64") // 10**9

# Хэрэггүй баганаа хаях
df = df.drop(columns=["datetime"])

print(f"✅ {len(df):,} мөрийг {time.time() - start_load:.2f} секундэд бэлдлээ")

# ============================================================
# 2. C++ ENGINE РУУ 1 УДАА ДАМЖУУЛАХ
# ============================================================
print("⚡ C++ Engine руу 1 удаа дамжуулж байна...")
start_cpp = time.time()

engine = CppQuant()
engine.load_from_vectors(
    df["timestamp"].tolist(),
    df["open"].tolist(),
    df["high"].tolist(),
    df["low"].tolist(),
    df["close"].tolist(),
    df["volume"].tolist(),
)
print(f"✅ {len(df):,} Candle {time.time() - start_cpp:.2f} секундэд ачаалагдлаа")
print("✅ C++ Backend бэлэн\n")

# ============================================================
# 3. SWEEP АЖИЛЛУУЛАХ (БҮХ ТООЦООЛ C++ ДОТОР)
# ============================================================
print("🔄 C++ Native Sweep эхэлж байна (4 x 3 = 12 тест)...")
sweep_start = time.time()

timeframes = [5, 15, 30, 60]  # минут
commissions = [0.0005, 0.001, 0.0015]  # 0.05%, 0.10%, 0.15%

results = []

for h in timeframes:
    # Цагийн хүрээг C++ дотор тохируулах (агрегац)
    engine.set_timeframe(h)

    for t in commissions:
        try:
            # C++ дотор бэктест хийх (бүх тооцоолол native)
            result = engine.run_backtest(commission=t)

            # Үр дүнг хадгалах
            results.append(
                {
                    "timeframe": f"{h}m",
                    "commission": t,
                    "winrate": result.get("winrate", 0),
                    "trades": result.get("num_trades", 0),
                    "return": result.get("total_return", 0),
                    "sharpe": result.get("sharpe_ratio", 0),
                }
            )

            print(
                f"  h={h:2d}m, t={t * 100:.2f}% | Winrate: {result.get('winrate', 0) * 100:.2f}%, Trades: {result.get('num_trades', 0)}"
            )

        except Exception as e:
            print(f"  h={h:2d}m, t={t * 100:.2f}% | ❌ Алдаа: {e}")

sweep_time = time.time() - sweep_start
print(f"\n✅ Нийт C++ Sweep хугацаа: {sweep_time:.2f} секунд")

# ============================================================
# 4. ҮР ДҮНГ ХАДГАЛАХ
# ============================================================
import json

output_file = "data/curated/xauusd/phase51_m1_cpp_true_production_v2.json"
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"📊 C++ үр дүн хадгалагдлаа: {output_file}")

# Хамгийн сайн үр дүн
if results:
    best = max(results, key=lambda x: x["winrate"])
    print("\n🏆 ХАМГИЙН САЙН:")
    print(f"  Цаг.хүрээ: {best['timeframe']}")
    print(f"  Комисс: {best['commission'] * 100:.2f}%")
    print(f"  Winrate: {best['winrate'] * 100:.2f}%")
    print(f"  Sharpe: {best['sharpe']:.2f}")

print("\n" + "=" * 70)
print("✅ БҮХ АЖИЛ ДУУССАН!")
