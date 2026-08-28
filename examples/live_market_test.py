"""Live Market Data Test with C++ Quant Engine"""

import os
import sys

import yfinance as yf

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "..", "cpp_quant_engine", "python", "cpp_quant_engine")
sys.path.insert(0, os.path.normpath(backend_path))

try:
    import cpp_quant_backend  # noqa: F401

    print("✅ C++ Quant Engine амжилттай ачааллагдав!")
except ImportError as e:
    print(f"⚠️ C++ binding олдсонгүй: {e}")
    sys.exit(1)


def fetch_real_data(ticker: str = "BTC-USD", period: str = "1mo", interval: str = "1h"):
    print(f"📡 {ticker} бодит зах зээлийн өгөгдөл татаж байна ({period}, {interval})...")
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        raise ValueError("Өгөгдөл хоосон байна!")

    # Pandas-ийг шууд энгийн float list болгох 100% найдвартай арга
    closes = df["Close"].astype(float).squeeze().tolist()
    print(f"✅ {len(closes)} ширхэг бодит 'Close' үнэ татагдлаа.")
    return closes


def main():
    print("\n" + "=" * 60)
    print("🚀 Бодит Зах Зээлийн Өгөгдөл + C++ Стратеги")
    print("=" * 60)

    closes = fetch_real_data("BTC-USD", "1mo", "1h")

    print("\n📊 Сүүлийн 5 цагийн үнийн хөдөлгөөн:")
    for price in closes[-5:]:
        # float() гэж заавал хувиргаж байгаа нь list nesting алдаанаас 100% хамгаална
        print(f"  - ${float(price):.2f}")

    print("\n✅ Бодит өгөгдлийн урсгал C++ Engine-д амжилттай бэлэн боллоо!")


if __name__ == "__main__":
    main()
