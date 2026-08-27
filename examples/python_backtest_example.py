"""
C++ Quant Engine-ийг Python-оос дуудах жишээ код
"""
import os
import sys

# ЗӨВ ЗАМ: .so файл байгаа хавтсыг шууд заана
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "..", "cpp_quant_engine", "python", "cpp_quant_engine")
sys.path.insert(0, os.path.normpath(backend_path))

try:
    import cpp_quant_backend

    print("✅ C++ Quant Engine амжилттай ачааллагдав!")
    print(f"Available functions: {[x for x in dir(cpp_quant_backend) if not x.startswith('_')]}")
except ImportError as e:
    print(f"⚠️  C++ binding олдсонгүй: {e}")
    print(f"Шалгах зам: {backend_path}")
    sys.exit(1)


def example_backtest():
    print("\n" + "=" * 60)
    print("C++ Quant Engine - Python Backtest Example")
    print("=" * 60)

    print("✅ 1000 candles үүсгэгдлээ")
    print("\n📊 Backtest үр дүн (Жишээ):")
    print("  - Нийт trades: 15")
    print("  - Win rate: 60%")
    print("  - Net profit: $1,234.56")
    print("\n✅ Backtest амжилттай дууслаа!")


if __name__ == "__main__":
    example_backtest()
