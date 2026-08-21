import sys

sys.path.append("cpp_quant/python")
from cpp_quant import CppQuant
import pandas as pd
import glob
import time

print("1 сая Candle – C++ бэкендээр шинжилгээ")
print("=" * 50)

# 1. CSV файлуудыг Python-оор унших
print("CSV файлуудыг уншиж байна...")
all_dfs = []
for f in glob.glob("data/raw/histdata/xauusd/DAT_ASCII_XAUUSD_M1_*.csv"):
    df = pd.read_csv(
        f,
        sep=";",
        header=None,
        names=["datetime", "open", "high", "low", "close", "volume"],
        dtype={"datetime": str},
    )
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S", errors="coerce")
    df = df.dropna(subset=["datetime"])
    df.set_index("datetime", inplace=True)
    all_dfs.append(df)
    print(f"   {f.split(chr(92))[-1]}: {len(df):,} records")

df = pd.concat(all_dfs).sort_index()
print(f"\nНийт {len(df):,} ширхэг 1 минутын candle")
print(f"   {df.index[0]} -> {df.index[-1]}")

# 2. 5 минут болгон агрегацлах
print("\n5 минут болгон агрегацлаж байна...")
df_5min = (
    df.resample("5min")
    .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    .dropna()
)
print(f"   {len(df_5min):,} candle (5 минут)")

# 3. C++ engine руу дамжуулах
print("\nC++ engine руу дамжуулж байна...")
start_time = time.time()
engine = CppQuant()
engine.load_from_dataframe(df_5min)
print(f"   Хугацаа: {time.time() - start_time:.2f} секунд")
print(f"   {engine.get_info()}")

# 4. SMA 10/30 бэктест
print("\nSMA 10/30 бэктест хийж байна...")
start_time = time.time()
result = engine.run_sma(10, 30)
print(f"   Хугацаа: {time.time() - start_time:.2f} секунд")
print(f"   Арилжаа: {result['num_trades']}")
print(f"   Winrate: {result['winrate']:.2f}%")
print(f"   Нийт өгөөж: {result['total_return']:.2f}%")
print(f"   Sharpe: {result['sharpe_ratio']:.2f}")

# 5. SMA 20/50 бэктест
print("\nSMA 20/50 бэктест хийж байна...")
start_time = time.time()
result = engine.run_sma(20, 50)
print(f"   Хугацаа: {time.time() - start_time:.2f} секунд")
print(f"   Арилжаа: {result['num_trades']}")
print(f"   Winrate: {result['winrate']:.2f}%")
print(f"   Нийт өгөөж: {result['total_return']:.2f}%")
print(f"   Sharpe: {result['sharpe_ratio']:.2f}")

# 6. Бүх стратеги
print("\nБүх стратегийн харьцуулалт...")
all_results = engine.run_all()
for name, res in all_results.items():
    print(f"   {name}: Winrate {res['winrate']:.2f}%, Trades {res['num_trades']}")

print("\n" + "=" * 50)
print("ДҮГНЭЛТ")
best = max(all_results.items(), key=lambda x: x[1]["winrate"])
print(f"Хамгийн сайн стратеги: {best[0]} (Winrate {best[1]['winrate']:.2f}%)")
print("=" * 50)
