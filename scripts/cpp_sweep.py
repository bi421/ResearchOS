import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("cpp_quant_engine/python").resolve()))

from cpp_quant_engine import BacktestRequest, Candle, CppQuantEngineBackend

print("=" * 60)
print("🚀 C++ BACKEND SWEEP: Зөв signal формат")
print("=" * 60)

# 1. Өгөгдөл ачаалах
data_file = Path("data/curated/xauusd/xauusd_h1_2026_recent_real.csv").resolve()
print(f"📂 Ашиглаж буй өгөгдөл: {data_file.name}")

import pandas as pd

df = pd.read_csv(data_file)
df.columns = [c.lower() for c in df.columns]

# Timestamp-ийг ISO 8601 формат руу хөрвүүлэх
candles = []
for _, row in df.iterrows():
    raw_ts = str(row.get("datetime", ""))
    if " " in raw_ts:
        ts_part = raw_ts.split(" ")[0] + "T" + raw_ts.split(" ")[1].split("-")[0].split("+")[0]
    else:
        ts_part = raw_ts

    candle = Candle(
        timestamp=ts_part,
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=float(row.get("volume", 0)),
        timeframe="H1",
    )
    candles.append(candle)

print(f"✅ {len(candles)} лааныг ачааллаа")

# 2. Backend эхлүүлэх
backend = CppQuantEngineBackend()
print("✅ C++ Backend эхлэлээ")

# 3. Sweep параметрүүд
horizons = [1, 3, 5, 10, 20]
thresholds = [0.0000, 0.0010, 0.0020, 0.0030]
results = []

print(f"\n C++ дээр sweep эхэлж байна ({len(horizons)} x {len(thresholds)} = {len(horizons) * len(thresholds)} тест)...")

for h in horizons:
    for t in thresholds:
        try:
            # BacktestRequest үүсгэх
            request = BacktestRequest(
                symbol="XAUUSD",
                timeframe="H1",
                candles=candles,
                initial_capital=100000.0,
                commission_pct=0.001,
                slippage_pct=0.0005,
                allow_short=True,
                signal_reference=f"h{h}_t{t}",
            )

            # Зөв signal функц (direction: 0=Buy, 1=Sell)
            def signal(bar_index: int, history: list, horizon=h, threshold=t) -> dict:
                if bar_index < horizon:
                    return {"direction": 0, "quantity": 0.0}  # Hold

                # Стратеги: өмнөх өгөөж threshold-аас их бол Buy (0), бага бол Sell (1)
                prev_close = history[bar_index - 1]["close"]
                curr_close = history[bar_index]["close"]
                ret = (curr_close - prev_close) / prev_close

                if ret > threshold:
                    return {"direction": 0, "quantity": 1.0}  # Buy
                elif ret < -threshold:
                    return {"direction": 1, "quantity": 1.0}  # Sell
                else:
                    return {"direction": 0, "quantity": 0.0}  # Hold

            # C++ дээр backtest ажиллуулах
            result = backend.backtest_run(request, signal=signal)

            results.append(
                {
                    "horizon": h,
                    "threshold": t,
                    "final_equity": result.final_equity,
                    "total_return_pct": result.total_return_pct,
                    "num_trades": result.num_trades,
                    "signal_reference": f"h{h}_t{t}",
                }
            )

            print(
                f"  h={h:2d}, t={t:.4f} | Equity: ${result.final_equity:,.2f} | Return: {result.total_return_pct:.2f}% | Trades: {result.num_trades}"
            )

        except Exception as e:
            print(f"  h={h:2d}, t={t:.4f} | ❌ Алдаа: {e}")

# 4. Үр дүнг хадгалах
output_file = Path("data/curated/xauusd/phase51_cpp_sweep_results.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\n✅ C++ Sweep дууслаа! Үр дүн: {output_file}")
print(f" Нийт {len(results)} хослолыг тестлэлээ")

if results:
    results.sort(key=lambda x: x["total_return_pct"], reverse=True)
    print("\n🏆 ШИЛДЭГ 5 ҮР ДҮН:")
    for r in results[:5]:
        print(f"  h={r['horizon']:2d}, t={r['threshold']:.4f} | Return: {r['total_return_pct']:.2f}% | Trades: {r['num_trades']}")

print("=" * 60)
