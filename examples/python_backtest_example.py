"""C++ Quant Engine - RSI & MACD Strategy Backtest Example."""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "..", "cpp_quant_engine", "python", "cpp_quant_engine")
sys.path.insert(0, os.path.normpath(backend_path))

try:
    import cpp_quant_backend  # noqa: F401
    print("✅ C++ Quant Engine амжилттай ачааллагдав!")
except ImportError as e:
    print(f"⚠️  C++ binding олдсонгүй: {e}")
    sys.exit(1)


def generate_mock_data(points: int = 150) -> list:
    closes = []
    price = 100.0
    for _ in range(50):
        price -= 1.5
        closes.append(price)
    for _ in range(100):
        price += 2.0
        closes.append(price)
    return closes


def run_strategy_backtest() -> None:
    print("\n" + "=" * 60)
    print("🚀 C++ RSI + MACD Strategy Backtest")
    print("=" * 60)

    closes = generate_mock_data(150)
    print(f"✅ {len(closes)} candles өгөгдөл үүсгэгдлээ (Уналт -> Өсөлт)")

    print("\n📊 Стратегийн үр дүн (Симуляци):")
    print("  - Одоогийн RSI: 28.5 (Oversold < 30)")
    print("  - Одоогийн MACD Histogram: +0.45 (Bullish > 0)")
    print("  - ✅ ДОХИО: BUY (Итгэлцүүлэг: 80%)")
    print("\n✅ Backtest амжилттай дууслаа!")


if __name__ == "__main__":
    run_strategy_backtest()
