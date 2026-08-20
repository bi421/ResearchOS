import sys
import pandas as pd

sys.path.insert(0, ".")

from researchos.experiments.contracts import DatasetConfig, SimulationConfig
from researchos.experiments.experiment import Experiment
from researchos.experiments.runner import BaseExperimentRunner
from researchos.quant_engine.router import BackendRouter

# ==========================================
# 1. ӨГӨГДӨЛ ТАТАХ ФУНКЦҮҮД
# ==========================================

def get_mt5_data(symbol="EURUSD", bars=252):
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            print(f"❌ MT5 initialization failed. Error: {mt5.last_error()}")
            return None
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, bars)
        mt5.shutdown()
        if rates is None or len(rates) == 0:
            return None
        df = pd.DataFrame(rates)
        print(f"✅ MT5: {symbol} тэмдэгтийн {len(df)} өдрийн өгөгдөл амжилттай татагдлаа.")
        return df['close'].astype(float).tolist()
    except ImportError:
        print("❌ 'MetaTrader5' сан суугаагүй байна.")
        return None

def get_tradingview_data(symbol="GC=F", period="1y"):
    try:
        import yfinance as yf
        print(f"🔄 TradingView (YFinance) эх үүсвэрээс {symbol} татаж байна...")
        df = yf.download(symbol, period=period, progress=False)
        if df.empty:
            return None
        close_col = df['Close']
        if isinstance(close_col, pd.DataFrame):
            prices = close_col.iloc[:, 0].dropna().astype(float).tolist()
        else:
            prices = close_col.dropna().astype(float).tolist()
        print(f"✅ TradingView: {symbol} тэмдэгтийн {len(prices)} өдрийн өгөгдөл амжилттай татагдлаа.")
        return prices
    except Exception as e:
        print(f"❌ YFinance алдаа: {e}")
        return None

# ==========================================
# 2. ҮНДСЭН ДАВТАЛТ (MAIN LOOP)
# ==========================================
def main():
    while True:
        print("\n" + "=" * 60)
        print("  RESEARCHOS - БОДИТ ӨГӨГДЛИЙН СИМУЛЯЦИ")
        print("=" * 60)
        print("1. MetaTrader 5 (EURUSD)")
        print("2. TradingView / YFinance (Алт - XAUUSD proxy)")
        print("3. TradingView / YFinance (S&P 500)")
        print("4. TradingView / YFinance (Bitcoin)")
        print("0. Гарах (Exit)")
        print("=" * 60)
        
        choice = input("Өгөгдлийн эх үүсвэрээ сонгоно уу (0-4): ").strip()

        if choice == "0":
            print("👋 Симуляци дууслаа. Баяртай!")
            break

        prices = None
        symbol_name = ""

        if choice == "1":
            symbol_name = "EURUSD (MT5)"
            prices = get_mt5_data("EURUSD", 252)
        elif choice == "2":
            symbol_name = "Gold / XAUUSD (TradingView)"
            prices = get_tradingview_data("GC=F", "1y")
        elif choice == "3":
            symbol_name = "S&P 500 (TradingView)"
            prices = get_tradingview_data("^GSPC", "1y")
        elif choice == "4":
            symbol_name = "Bitcoin / BTC-USD (TradingView)"
            prices = get_tradingview_data("BTC-USD", "1y")
        else:
            print("❌ Буруу сонголт. Дахин оролдоно уу.")
            continue  # Цэс рүү буцана

        if prices is None or len(prices) < 10:
            print("❌ Өгөгдөл хангалтгүй тул симуляци зогсож байна.")
            input("\nҮргэлжлүүлэхийн тулд Enter дарна уу...")
            continue

        # ==========================================
        # 3. СИМУЛЯЦИЙН ТОХИРГОО
        # ==========================================
        exp = Experiment(
            hypothesis_id=f"real_market_{choice}",
            name=f"Real Market Test: {symbol_name}",
            dataset_config=DatasetConfig(source=symbol_name),
            simulation_config=SimulationConfig(
                initial_capital=100000.0,
                commission=0.001,
                slippage=0.0005,
                seed=42
            )
        )
        exp.mark_ready()

        router = BackendRouter()
        runner = BaseExperimentRunner(router=router)

        print("\n" + "-" * 60)
        print(f"  Data Source       : {symbol_name}")
        print(f"  Data points       : {len(prices)}")
        print(f"  Price Range       : ${min(prices):,.2f} - ${max(prices):,.2f}")
        print(f"  Initial Capital   : ${exp.simulation_config.initial_capital:,.2f}")
        print("-" * 60)
        print("  Симуляци эхэлж байна...\n")

        # ==========================================
        # 4. ГҮЙЦЭТГЭЛ БА ҮР ДҮН
        # ==========================================
        run, result = runner.run(exp, prices)

        print("\n  ✅ СИМУЛЯЦИ АМЖИЛТТАЙ ДУУСЛАА")
        print("=" * 60)
        print("  📊 ҮНДСЭН ҮЗҮҮЛЭЛТҮҮД (METRICS):")
        for key, value in result.metrics.items():
            if isinstance(value, float):
                print(f"    {key:<25}: {value:>12.4f}")
            else:
                print(f"    {key:<25}: {value}")

        print("\n  ⚙️  СИСТЕМИЙН МЭДЭЭЛЭЛ (TELEMETRY):")
        backend_name = result.statistics.get("backend_name", "PythonQuantBackend")
        print(f"    Backend selected    : {backend_name}")
        print(f"    Execution time (ms) : {result.backend_execution_time_ms:.2f}")
        print(f"    Result hash         : {result.result_hash[:32]}...")
        print(f"    Run ID              : {run.id}")
        print("=" * 60)
        
        input("\n🔄 Дараагийн симуляцийг эхлүүлэхийн тулд Enter дарна уу...")

if __name__ == "__main__":
    main()
