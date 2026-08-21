import sys

sys.path.append("cpp_quant/python")
import pandas as pd

from cpp_quant import CppQuant

print("=" * 60)
print("БҮХ ЦАГИЙН ХҮРЭЭНД БЭКТЕСТ ШИНЖИЛГЭЭ (Commission: 0.01%)")
print("=" * 60)

# 1. CSV файлуудыг унших
print("\nCSV файлуудыг уншиж байна...")
df = pd.read_parquet("data/raw/histdata/xauusd/xauusd_m1_cached.parquet")
print(f"Нийт {len(df):,} ширхэг 1 минутын candle")
print(f"   {df.index[0]} -> {df.index[-1]}")

# 2. Цагийн хүрээний жагсаалт
timeframes = [
    ("1min", "1min"),
    ("5min", "5min"),
    ("15min", "15min"),
    ("30min", "30min"),
    ("1h", "1h"),
    ("4h", "4h"),
    ("1D", "1D"),
    ("1W", "W"),
    ("1M", "ME"),
]

results = []

print("\n" + "=" * 60)
print("БЭКТЕСТ ҮР ДҮН")
print("=" * 60)

for label, rule in timeframes:
    print(f"\n{label} агрегацлаж байна...")

    df_resampled = df.resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()

    print(f"   {len(df_resampled):,} candle")

    engine = CppQuant()
    engine.load_from_dataframe(df_resampled)

    result = engine.run_sma(20, 50)

    results.append(
        {
            "timeframe": label,
            "candles": len(df_resampled),
            "trades": result["num_trades"],
            "winrate": result["winrate"],
            "total_return": result["total_return"],
            "sharpe": result["sharpe_ratio"],
            "avg_win": result["avg_win"],
            "avg_loss": result["avg_loss"],
            "profit_factor": result["profit_factor"],
        }
    )

    print(f"   Арилжаа: {result['num_trades']}")
    print(f"   Winrate: {result['winrate']:.2f}%")
    print(f"   Нийт өгөөж: {result['total_return']:.2f}%")
    print(f"   Sharpe: {result['sharpe_ratio']:.2f}")
    print(f"   Avg Win: {result['avg_win']:.2f}% | Avg Loss: {result['avg_loss']:.2f}% | Max DD: {result['max_drawdown']:.2f}%")

# 3. Үр дүнгийн хүснэгт
print("\n" + "=" * 80)
print("БҮХ ЦАГИЙН ХҮРЭЭНИЙ ХАРЬЦУУЛАЛТ")
print("=" * 80)

print(f"\n{'Цаг.хүрээ':<10} {'Candle':<10} {'Арилжаа':<10} {'Winrate':<10} {'Өгөөж':<12} {'Sharpe':<10} {'P/F':<8}")
print("-" * 80)

for r in results:
    print(
        f"{r['timeframe']:<10} {r['candles']:<10} {r['trades']:<10} {r['winrate']:<10.2f} {r['total_return']:<12.2f} {r['sharpe']:<10.2f} {r['profit_factor']:<8.2f}"
    )

# 4. Дүгнэлт
print("\n" + "=" * 80)
print("ДҮГНЭЛТ")
print("=" * 80)

best_winrate = max(results, key=lambda x: x["winrate"])
print(f"Хамгийн сайн Winrate: {best_winrate['timeframe']} ({best_winrate['winrate']:.2f}%)")

best_sharpe = max(results, key=lambda x: x["sharpe"])
print(f"Хамгийн сайн Sharpe: {best_sharpe['timeframe']} ({best_sharpe['sharpe']:.2f})")

best_return = max(results, key=lambda x: x["total_return"])
print(f"Хамгийн сайн нийт өгөөж: {best_return['timeframe']} ({best_return['total_return']:.2f}%)")

good = [r for r in results if r["winrate"] > 35]
if good:
    print(f"\nWinrate > 35%: {len(good)} цагийн хүрээ")
    for r in good:
        print(f"   - {r['timeframe']}: {r['winrate']:.2f}% (Арилжаа: {r['trades']})")
else:
    print("\nWinrate > 35% байхгүй байна.")
    print("Зөвлөмж: Стратегийг өөрчлөх эсвэл C++ кодны commission-г шалгах хэрэгтэй.")

print("\n" + "=" * 80)
