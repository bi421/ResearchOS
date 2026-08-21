import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path("cpp_quant_engine/python").resolve()))

import pandas as pd

from cpp_quant_engine import BacktestRequest, Candle, CppQuantEngineBackend

print("=" * 70)
print("🚀 TRUE PRODUCTION: Векторчилсон өгөгдөл + 100% C++ Тооцоолол")
print("=" * 70)

data_file = Path("data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv").resolve()
print(f"📂 Өгөгдөл: {data_file.name}")

# 1. ВЕКТОРЧИЛСАН ӨГӨГДӨЛ БОЛОВСРУУЛАЛТ (C-speed, цикл ашиглахгүй)
print("⏳ Өгөгдлийг векторчилсон аргаар бэлдэж байна...")
start_time = time.time()

df = pd.read_csv(data_file)
df.columns = [c.lower() for c in df.columns]

# "20210103" + "180000" -> "20210103180000"
df["ts_raw"] = df["date"].astype(str) + df["time"].astype(str)

# Векторчилсон string slicing (1.7 сая мөрөнд ~0.3 секунд зарцуулна)
df["iso_ts"] = (
    df["ts_raw"].str[:4]
    + "-"
    + df["ts_raw"].str[4:6]
    + "-"
    + df["ts_raw"].str[6:8]
    + "T"
    + df["ts_raw"].str[8:10]
    + ":"
    + df["ts_raw"].str[10:12]
    + ":"
    + df["ts_raw"].str[12:14]
)

# NaN утгуудыг цэвэрлэх
df = df.dropna(subset=["iso_ts", "open", "high", "low", "close"])

prep_time = time.time() - start_time
print(f"✅ {len(df):,} мөрийг {prep_time:.2f} секундэд бэлдлээ (C-speed)")

# 2. C++ Candle объект үүсгэх (List comprehension нь хамгийн хурдан Python арга)
print("⏳ C++ Candle формат руу хөрвүүлж байна...")
start_time = time.time()

# Зөвхөн шаардлагатай багануудыг авч zip ашигласнаар хурдыг 10x нэмэгдүүлнэ
candles = [
    Candle(
        timestamp=str(ts),
        open=float(o),
        high=float(h),
        low=float(lo),
        close=float(c),
        volume=float(v),
        timeframe="M1",
    )
    for ts, o, h, lo, c, v in zip(df["iso_ts"], df["open"], df["high"], df["low"], df["close"], df["volume"])
]

convert_time = time.time() - start_time
print(f"✅ {len(candles):,} Candle {convert_time:.2f} секундэд үүслээ")

# 3. C++ Backend эхлүүлэх
backend = CppQuantEngineBackend()
print("✅ C++ Backend бэлэн")

# 4. C++ дээрх жинхэнэ Sweep (Backtest, PnL, Drawdown тооцоог C++ хийнэ)
horizons = [5, 15, 30, 60]  # минут
thresholds = [0.0005, 0.0010, 0.0015]  # 0.05% - 0.15%

results = []
print(f"\n🔄 C++ Native Sweep эхэлж байна ({len(horizons)} x {len(thresholds)} = {len(horizons) * len(thresholds)} тест)...")

total_start = time.time()

for h in horizons:
    for t in thresholds:
        try:
            request = BacktestRequest(
                symbol="XAUUSD",
                timeframe="M1",
                candles=candles,
                initial_capital=100000.0,
                commission_pct=0.0001,
                slippage_pct=0.00005,
                allow_short=True,
                signal_reference=f"m1_h{h}_t{t}",
            )

            # Signal логик (Python-ээс C++ рүү callback хэлбэрээр дамжина)
            def signal(bar_index: int, history: list, horizon=h, threshold=t) -> dict:
                if bar_index < horizon:
                    return {"direction": 0, "quantity": 0.0}

                prev_close = history[bar_index - horizon]["close"]
                curr_close = history[bar_index]["close"]
                ret = (curr_close - prev_close) / prev_close

                if ret > threshold:
                    return {"direction": 0, "quantity": 1.0}
                elif ret < -threshold:
                    return {"direction": 1, "quantity": 1.0}
                else:
                    return {"direction": 0, "quantity": 0.0}

            bt_start = time.time()
            # ЭНД C++ ӨӨРӨӨ Backtest, PnL, Drawdown тооцооллыг хийнэ
            result = backend.backtest_run(request, signal=signal)
            bt_time = time.time() - bt_start

            results.append(
                {
                    "horizon_min": h,
                    "threshold_pct": round(t * 100, 3),
                    "final_equity": round(result.final_equity, 2),
                    "total_return_pct": round(result.total_return_pct, 2),
                    "num_trades": result.num_trades,
                    "max_drawdown_pct": round(result.max_drawdown_pct, 2),
                    "cpp_compute_time_sec": round(bt_time, 2),
                }
            )

            print(
                f"  h={h:2d}m, t={t * 100:.2f}% | Return: {result.total_return_pct:+.2f}% | Trades: {result.num_trades:,} | DD: {result.max_drawdown_pct:.2f}% | C++ Time: {bt_time:.2f}s"
            )

        except Exception as e:
            print(f"  h={h:2d}m, t={t * 100:.2f}% | ❌ Алдаа: {e}")

total_time = time.time() - total_start
print(f"\n✅ Нийт C++ Sweep хугацаа: {total_time:.2f} секунд")

# 5. Үр дүнг хадгалах
output_file = Path("data/curated/xauusd/phase51_m1_cpp_true_production.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"📊 C++ үр дүн хадгалагдлаа: {output_file}")

if results:
    profitable = [r for r in results if r["total_return_pct"] > 0]
    print("\n📈 C++ СТАТИСТИК ДҮН ШИНЖИЛГЭЭ:")
    print(f"   Нийт тест: {len(results)} | Ашигтай: {len(profitable)}")

    if profitable:
        best = max(profitable, key=lambda x: x["total_return_pct"])
        print("\n🏆 ШИЛДЭГ C++ ҮР ДҮН:")
        print(f"   Horizon: {best['horizon_min']}min | Threshold: {best['threshold_pct']}%")
        print(f"   Return: {best['total_return_pct']:+.2f}% | Trades: {best['num_trades']:,}")
        print(f"   Max Drawdown: {best['max_drawdown_pct']:.2f}%")
        print(f"   C++ Тооцооллын хугацаа: {best['cpp_compute_time_sec']} сек")

print("=" * 70)
