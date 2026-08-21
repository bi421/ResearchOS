import pandas as pd
import numpy as np
import glob
import time
import sys

# C++ бэкенд импорт
try:
    from cpp_quant_engine import cpp_quant_backend as cpp  # noqa: F401

    print("✅ C++ бэкенд амжилттай ачаалагдлаа")
except ImportError as e:
    print(f"❌ C++ бэкенд ачаалахад алдаа: {e}")
    print("💡 Python бэкенд рүү шилжиж байна...")
    USE_CPP = False
else:
    USE_CPP = True
    # C++ бэкенд ашиглах (bridge-ээр дамжуулан)
    from researchos.quant_engine.cpp_backend import CppQuantAdapter

    backend = CppQuantAdapter()


class MillionCandleCPPAnalyzer:
    def __init__(self, data_path="data/raw/histdata/xauusd/"):
        self.data_path = data_path
        self.df = None

    def load_all_csv(self):
        """Бүх CSV-г хурдан унших"""
        print(f"📂 {self.data_path} хавтаснаас файлуудыг уншиж байна...")
        files = glob.glob(f"{self.data_path}DAT_ASCII_XAUUSD_M1_*.csv")
        if not files:
            print("❌ CSV файл олдсонгүй")
            return False

        dfs = []
        total = 0
        for f in files:
            try:
                df = pd.read_csv(
                    f,
                    sep=";",
                    header=None,
                    names=["datetime", "open", "high", "low", "close", "volume"],
                    parse_dates=["datetime"],
                    date_parser=lambda x: pd.to_datetime(x, format="%Y%m%d %H:%M:%S"),
                )
                if not df.empty:
                    dfs.append(df)
                    total += len(df)
                    print(f"   ✅ {f.replace(chr(92), '/').split('/')[-1]}: {len(df):,}")
            except Exception as e:
                print(f"   ⚠️ Алдаа: {e}")

        if not dfs:
            return False

        self.df = pd.concat(dfs, ignore_index=True).sort_values("datetime").reset_index(drop=True)
        print(f"\n✅ НИЙТ {len(self.df):,} ширхэг 1 минутын candle")
        return True

    def resample_to_5min(self):
        """5 минут болгон хувиргах (бэктестийн хурдны төлөө)"""
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

    def run_cpp_backtest(self, df, short=10, long=30):
        """C++ бэкендээр бэктест хийх"""
        if df.empty:
            return None

        # C++-д дамжуулах өгөгдөл бэлтгэх
        data = {
            "open": df["open"].tolist(),
            "high": df["high"].tolist(),
            "low": df["low"].tolist(),
            "close": df["close"].tolist(),
            "volume": df["volume"].tolist(),
        }

        # Стратегийн параметрүүд
        config = {
            "sma_short": short,
            "sma_long": long,
            "initial_capital": 10000.0,
            "commission": 0.001,  # 0.1% комисс
        }

        print(f"⚡ C++ бэкендээр SMA {short}/{long} боловсруулж байна...")
        start_time = time.time()

        try:
            if USE_CPP:
                # C++ бэкенд дуудах
                result = backend.run_backtest(data, config)
            else:
                # Fallback Python: энгийн тооцоо хийх
                result = self.run_python_backtest(df, short, long)
                return result

            elapsed = time.time() - start_time
            print(f"   ✅ Хугацаа: {elapsed:.2f} секунд")

            # Үр дүнг задлах
            return {
                "trades": result.get("num_trades", 0),
                "winrate": result.get("winrate", 0) * 100,
                "total_return": result.get("total_return", 0) * 100,
                "sharpe": result.get("sharpe", 0),
                "max_drawdown": result.get("max_drawdown", 0) * 100,
                "time_sec": elapsed,
            }
        except Exception as e:
            print(f"   ❌ C++ алдаа: {e}. Python руу шилжиж байна...")
            return self.run_python_backtest(df, short, long)

    def run_python_backtest(self, df, short, long):
        """Fallback: Python бэктест (векторжсон)"""
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
                "max_drawdown": 0,  # энгийн
                "time_sec": elapsed,
            }
        return None

    def print_results(self, results, name):
        """Үр дүнг хэвлэх"""
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


# === MAIN ===
if __name__ == "__main__":
    print("🚀 1 САЯ CANDLE – C++ БЭКЕНДЭЭР ШИНЖИЛГЭЭ")
    print("=" * 50)

    analyzer = MillionCandleCPPAnalyzer()

    # 1. Өгөгдөл татах
    if not analyzer.load_all_csv():
        sys.exit(1)

    # 2. 5 минут болгон хувиргах
    df_5min = analyzer.resample_to_5min()

    # 3. C++ бэкендээр SMA 10/30
    res1 = analyzer.run_cpp_backtest(df_5min, short=10, long=30)
    analyzer.print_results(res1, "SMA 10/30 (C++)")

    # 4. C++ бэкендээр SMA 20/50
    res2 = analyzer.run_cpp_backtest(df_5min, short=20, long=50)
    analyzer.print_results(res2, "SMA 20/50 (C++)")

    # 5. Харьцуулалт
    print("\n" + "=" * 50)
    print("🏆 ДҮГНЭЛТ")
    if res1 and res2:
        if res1["winrate"] > res2["winrate"]:
            print(f"🔥 Хамгийн сайн: SMA 10/30 (Winrate {res1['winrate']:.1f}%)")
        else:
            print(f"🔥 Хамгийн сайн: SMA 20/50 (Winrate {res2['winrate']:.1f}%)")

        if res1["time_sec"] < 1.0:
            print(f"⚡ C++ хурд: {res1['time_sec']:.2f}с (1 сая candle-д)")

    print("=" * 50)
