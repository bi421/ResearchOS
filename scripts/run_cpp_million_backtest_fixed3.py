import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# C++ бэкенд адаптер
try:
    from researchos.quant_engine.cpp_backend import CppQuantAdapter

    backend = CppQuantAdapter()
    print("✅ C++ бэкенд амжилттай ачаалагдлаа")
    USE_CPP = True
except ImportError as e:
    print(f"❌ C++ бэкенд ачаалахад алдаа: {e}")
    print("💡 Python бэкенд рүү шилжиж байна...")
    from researchos.quant_engine.backend import PythonQuantBackend

    backend = PythonQuantBackend()
    USE_CPP = False


class MillionCandleAnalyzer:
    def __init__(self, data_path="data/raw/histdata/xauusd/"):
        self.data_path = Path(data_path)
        self.df = None

    def load_all_csv(self):
        print(f"📂 Хайж байна: {self.data_path.absolute()}")
        if not self.data_path.exists():
            print(f"❌ Хавтас олдсонгүй: {self.data_path}")
            return False

        files = list(self.data_path.glob("DAT_ASCII_XAUUSD_M1_*.csv"))
        if not files:
            print(f"⚠️ {self.data_path} хавтасанд CSV файл олдсонгүй")
            return False

        print(f"📄 {len(files)} ширхэг CSV файл олдлоо")
        dfs = []
        total = 0

        for f in files:
            try:
                # Жишээ өгөгдөл: 20210103 180000;1904.998000;1910.898000;1903.288000;1909.718000;0
                df = pd.read_csv(
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
                # Огноо/цагийг зөв форматлалтайгаар хувиргах
                df["datetime"] = pd.to_datetime(df["datetime"], format="%Y%m%d %H%M%S", errors="coerce")
                df = df.dropna(subset=["datetime"])
                if not df.empty:
                    dfs.append(df)
                    total += len(df)
                    print(f"   ✅ {f.name}: {len(df):,}")
            except Exception as e:
                print(f"   ⚠️ {f.name} уншихад алдаа: {e}")

        if not dfs:
            print("❌ Ямар ч өгөгдөл уншигдсангүй")
            return False

        self.df = pd.concat(dfs, ignore_index=True).sort_values("datetime").reset_index(drop=True)
        print(f"\n✅ НИЙТ {len(self.df):,} ширхэг 1 минутын candle")
        print(f"   📅 Хугацаа: {self.df['datetime'].min()} → {self.df['datetime'].max()}")
        return True

    def resample_to_5min(self):
        print("\n⏳ 5 минут болгон агрегацлаж байна...")
        df = self.df.copy()
        df.set_index("datetime", inplace=True)
        ohlc = df["close"].resample("5T").ohlc()
        vol = df["volume"].resample("5T").sum()
        result = pd.DataFrame(
            {
                "open": ohlc["open"],
                "high": ohlc["high"],
                "low": ohlc["low"],
                "close": ohlc["close"],
                "volume": vol,
            }
        ).dropna()
        result.reset_index(inplace=True)
        print(f"   ✅ {len(result):,} candle (5 минут)")
        return result

    def run_sma_backtest(self, df, short=10, long=30):
        if df.empty:
            return None

        print(f"⚡ SMA {short}/{long} боловсруулж байна...")
        start_time = time.time()

        try:
            if USE_CPP:
                # C++ адаптераар backtest хийх
                # Dataframe-ийг list болгон хувиргах
                close_prices = df["close"].tolist()
                # Энгийн SMA бэктест - CppQuantAdapter-ийн интерфейс
                result = backend.run_strategy(
                    prices=close_prices,
                    strategy="sma_crossover",
                    short=short,
                    long=long,
                    initial_capital=10000.0,
                )
            else:
                result = self.run_python_backtest(df, short, long)
                return result

            elapsed = time.time() - start_time
            print(f"   ✅ Хугацаа: {elapsed:.2f} секунд")

            return {
                "trades": result.get("num_trades", 0),
                "winrate": result.get("winrate", 0) * 100,
                "total_return": result.get("total_return", 0) * 100,
                "sharpe": result.get("sharpe", 0),
                "max_drawdown": result.get("max_drawdown", 0) * 100,
                "time_sec": elapsed,
            }
        except Exception as e:
            print(f"   ❌ Алдаа: {e}. Python руу шилжиж байна...")
            return self.run_python_backtest(df, short, long)

    def run_python_backtest(self, df, short, long):
        print("   🐍 Python бэктест хийж байна...")
        start = time.time()
        df = df.copy()
        df["SMA_short"] = df["close"].rolling(short).mean()
        df["SMA_long"] = df["close"].rolling(long).mean()
        df["signal"] = 0
        df.loc[df["SMA_short"] > df["SMA_long"], "signal"] = 1
        df.loc[df["SMA_short"] <= df["SMA_long"], "signal"] = -1
        df["position"] = df["signal"].diff()

        trades = []
        pos = 0
        entry = 0
        for i in range(1, len(df)):
            if df["position"].iloc[i] == 2:
                if pos == 0:
                    entry = df["close"].iloc[i]
                    pos = 1
            elif df["position"].iloc[i] == -2:
                if pos == 1:
                    exit_price = df["close"].iloc[i]
                    trades.append((exit_price - entry) / entry)
                    pos = 0
        if pos == 1:
            trades.append((df["close"].iloc[-1] - entry) / entry)

        elapsed = time.time() - start
        if trades:
            arr = np.array(trades)
            return {
                "trades": len(arr),
                "winrate": (arr > 0).sum() / len(arr) * 100,
                "total_return": (1 + arr).prod() * 100 - 100,
                "sharpe": arr.mean() / arr.std() * np.sqrt(252 * 6.5 * 12) if arr.std() != 0 else 0,
                "max_drawdown": 0,
                "time_sec": elapsed,
            }
        return None

    def print_results(self, results, name):
        if not results:
            print("   ❌ Үр дүн байхгүй")
            return
        print(f"\n📊 {name}")
        print("   " + "-" * 30)
        print(f"   Арилжаа: {results['trades']}")
        print(f"   Winrate: {results['winrate']:.2f}%")
        print(f"   Нийт өгөөж: {results['total_return']:.2f}%")
        print(f"   Sharpe: {results['sharpe']:.2f}")
        print(f"   Хугацаа: {results['time_sec']:.2f}с")


if __name__ == "__main__":
    print("🚀 1 САЯ CANDLE – C++ БЭКЕНДЭЭР ШИНЖИЛГЭЭ")
    print("=" * 50)

    analyzer = MillionCandleAnalyzer()
    if not analyzer.load_all_csv():
        sys.exit(1)

    df_5min = analyzer.resample_to_5min()

    res1 = analyzer.run_sma_backtest(df_5min, short=10, long=30)
    analyzer.print_results(res1, "SMA 10/30")

    res2 = analyzer.run_sma_backtest(df_5min, short=20, long=50)
    analyzer.print_results(res2, "SMA 20/50")

    print("\n" + "=" * 50)
    print("🏆 ДҮГНЭЛТ")
    if res1 and res2:
        if res1["winrate"] > res2["winrate"]:
            print(f"🔥 Хамгийн сайн: SMA 10/30 (Winrate {res1['winrate']:.1f}%)")
        else:
            print(f"🔥 Хамгийн сайн: SMA 20/50 (Winrate {res2['winrate']:.1f}%)")
        if res1["time_sec"] < 1.0:
            print(f"⚡ C++ хурд: {res1['time_sec']:.2f}с")
    print("=" * 50)
