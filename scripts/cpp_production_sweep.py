import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path("cpp_quant_engine/python").resolve()))

from cpp_quant_engine import (
    CppQuantEngineBackend,
    BacktestRequest,
    Candle
)

print("=" * 70)
print("🚀 PRODUCTION TEST: 1.7 САЯ ЛАА ДЭЭР C++ BACKEND")
print("=" * 70)

# 1. M1 өгөгдөл ачаалах (1.7 сая мөр)
data_file = Path("data/curated/xauusd/xauusd_m1_2021_2025_mt5.csv").resolve()
print(f"📂 Ашиглаж буй өгөгдөл: {data_file.name}")

import pandas as pd
print("⏳ CSV уншиж байна (1.7 сая мөр)...")
start_time = time.time()

df = pd.read_csv(data_file)
df.columns = [c.lower() for c in df.columns]

load_time = time.time() - start_time
print(f"✅ {len(df):,} мөр уншлаа ({load_time:.2f} секунд)")

# 2. Candle формат руу хөрвүүлэх
print("⏳ Candle объектууд үүсгэж байна...")
start_time = time.time()

candles = []
for i, row in df.iterrows():
    # Timestamp формат: "20210103 180000" -> "2021-01-03T18:00:00"
    raw_ts = str(row.get('date', '')) + ' ' + str(row.get('time', ''))
    if len(raw_ts) >= 15:
        # "20210103 180000" -> "2021-01-03T18:00:00"
        date_part = raw_ts[:8]
        time_part = raw_ts[9:15]
        ts = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
    else:
        ts = raw_ts
    
    candle = Candle(
        timestamp=ts,
        open=float(row['open']),
        high=float(row['high']),
        low=float(row['low']),
        close=float(row['close']),
        volume=float(row.get('volume', 0)),
        timeframe="M1"
    )
    candles.append(candle)
    
    # Progress харуулах (100,000 тутамд)
    if (i + 1) % 100000 == 0:
        print(f"   ... {i+1:,} / {len(df):,} лаа")

convert_time = time.time() - start_time
print(f"✅ {len(candles):,} Candle үүслээ ({convert_time:.2f} секунд)")

# 3. C++ Backend эхлүүлэх
backend = CppQuantEngineBackend()
print("✅ C++ Backend эхлэлээ")

# 4. Бодит sweep (M1 дээр, секунд рүү downsample хийхгүйгээр)
# Стратеги: 5 минутын моментум (5 лааны өгөөж)
horizons = [5, 10, 15, 30, 60]  # минут
thresholds = [0.0005, 0.0010, 0.0015, 0.0020]  # 0.05% - 0.20%

results = []
print(f"\n C++ дээр sweep эхэлж байна ({len(horizons)} x {len(thresholds)} = {len(horizons)*len(thresholds)} тест)...")
print(f"   Нийт {len(candles):,} лаа дээр ажиллана\n")

total_start = time.time()

for h in horizons:
    for t in thresholds:
        try:
            # BacktestRequest
            request = BacktestRequest(
                symbol="XAUUSD",
                timeframe="M1",
                candles=candles,
                initial_capital=100000.0,
                commission_pct=0.0001,  # M1-д багасгасан
                slippage_pct=0.00005,
                allow_short=True,
                signal_reference=f"m1_h{h}_t{t}"
            )
            
            # Signal функц: h минутын моментум
            def signal(bar_index: int, history: list, horizon=h, threshold=t) -> dict:
                if bar_index < horizon:
                    return {"direction": 0, "quantity": 0.0}
                
                prev_close = history[bar_index - horizon]['close']
                curr_close = history[bar_index]['close']
                ret = (curr_close - prev_close) / prev_close
                
                if ret > threshold:
                    return {"direction": 0, "quantity": 1.0}  # Buy
                elif ret < -threshold:
                    return {"direction": 1, "quantity": 1.0}  # Sell
                else:
                    return {"direction": 0, "quantity": 0.0}  # Hold
            
            # C++ дээр ажиллуулах
            bt_start = time.time()
            result = backend.backtest_run(request, signal=signal)
            bt_time = time.time() - bt_start
            
            results.append({
                "horizon_min": h,
                "threshold_pct": t * 100,
                "final_equity": result.final_equity,
                "total_return_pct": result.total_return_pct,
                "num_trades": result.num_trades,
                "max_drawdown_pct": result.max_drawdown_pct,
                "time_seconds": bt_time,
                "signal_reference": f"m1_h{h}_t{t}"
            })
            
            print(f"  h={h:2d}min, t={t*100:.2f}% | Return: {result.total_return_pct:+.2f}% | Trades: {result.num_trades:,} | DD: {result.max_drawdown_pct:.2f}% | Time: {bt_time:.2f}s")
            
        except Exception as e:
            print(f"  h={h:2d}min, t={t*100:.2f}% | ❌ Алдаа: {e}")

total_time = time.time() - total_start
print(f"\n✅ Sweep дууслаа! Нийт хугацаа: {total_time:.2f} секунд")

# 5. Үр дүнг хадгалах
output_file = Path("data/curated/xauusd/phase51_m1_cpp_production_sweep.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"📊 Үр дүн хадгалагдлаа: {output_file}")

# 6. Статистик дүн шинжилгээ
if results:
    profitable = [r for r in results if r['total_return_pct'] > 0]
    print(f"\n📈 СТАТИСТИК ДҮН ШИНЖИЛГЭЭ:")
    print(f"   Нийт тест: {len(results)}")
    print(f"   Ашигтай: {len(profitable)} ({len(profitable)/len(results)*100:.1f}%)")
    print(f"   Алдаатай: {len(results) - len(profitable)}")
    
    if profitable:
        best = max(profitable, key=lambda x: x['total_return_pct'])
        print(f"\n🏆 ШИЛДЭГ ҮР ДҮН:")
        print(f"   h={best['horizon_min']}min, t={best['threshold_pct']:.2f}%")
        print(f"   Return: {best['total_return_pct']:+.2f}%")
        print(f"   Trades: {best['num_trades']:,}")
        print(f"   Max DD: {best['max_drawdown_pct']:.2f}%")
        print(f"   Time: {best['time_seconds']:.2f}s")
        
        # Sharpe ratio ойролцоо тооцоо (annualized)
        # M1 = 252 * 24 * 60 = 362,880 лаа/жил
        # Гэхдээ бид зөвхөн худалдааны өдрүүдийг тооцно (~252 * 6.5 * 60 = 98,280)
        trading_days = 252
        annual_return = best['total_return_pct'] * (trading_days / (len(candles) / 98280))
        print(f"   Annualized Return: ~{annual_return:.2f}%")

print("=" * 70)
print("✅ PRODUCTION TEST ДУУСЛАА")
print("=" * 70)
