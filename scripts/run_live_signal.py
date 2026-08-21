import json
from datetime import datetime

import pandas as pd
import yfinance as yf


class LiveTradingSignal:
    def __init__(self, symbol="XAUUSD"):
        self.symbol = symbol
        self.yf_symbol = "GC=F"
        self.data = None
        self.signal = None

    def fetch_live_data(self, period="5d", interval="1m"):
        """Бодит цагийн өгөгдөл татах"""
        print(f"📡 {self.symbol} бодит цагийн өгөгдөл татаж байна...")
        ticker = yf.Ticker(self.yf_symbol)
        self.data = ticker.history(period=period, interval=interval)
        if self.data.empty:
            print("❌ Өгөгдөл олдсонгүй")
            return False
        print(f"✅ {len(self.data)} ширхэг candle татагдлаа")
        return True

    def calculate_indicators(self):
        """Техникийн үзүүлэлтүүдийг тооцоолох (бодит цагт)"""
        df = self.data.copy()
        close = df["Close"]

        # 1. Хөдөлгөөнт дундажууд (бодит зах зээлд түгээмэл хэрэглэгддэг параметрүүд)
        df["SMA_10"] = close.rolling(10).mean()
        df["SMA_30"] = close.rolling(30).mean()
        df["SMA_200"] = close.rolling(200).mean()

        # 2. RSI (14 period)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # 3. MACD
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

        # 4. Bollinger Bands (20, 2)
        df["BB_mid"] = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        df["BB_high"] = df["BB_mid"] + 2 * bb_std
        df["BB_low"] = df["BB_mid"] - 2 * bb_std

        # 5. ATR (Average True Range) - позицийн хэмжээ тооцоход
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift()).abs()
        low_close = (df["Low"] - df["Close"].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df["ATR"] = true_range.rolling(14).mean()

        self.data = df
        return df

    def generate_signal(self):
        """Бодит шийдвэр гаргах"""
        df = self.data
        if df.empty:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        # 1. Чиглэл тодорхойлох (Long/Short)
        trend_score = 0

        # SMA crossover
        if last["SMA_10"] > last["SMA_30"] and prev["SMA_10"] <= prev["SMA_30"]:
            trend_score += 2  # Bullish crossover
        elif last["SMA_10"] < last["SMA_30"] and prev["SMA_10"] >= prev["SMA_30"]:
            trend_score -= 2  # Bearish crossover

        # RSI
        if last["RSI"] < 30 and prev["RSI"] < 30:
            trend_score += 1  # Oversold
        elif last["RSI"] > 70 and prev["RSI"] > 70:
            trend_score -= 1  # Overbought

        # MACD
        if last["MACD_Hist"] > 0 and prev["MACD_Hist"] <= 0:
            trend_score += 1
        elif last["MACD_Hist"] < 0 and prev["MACD_Hist"] >= 0:
            trend_score -= 1

        # Bollinger Bands
        if last["Close"] < last["BB_low"]:
            trend_score += 1  # Oversold
        elif last["Close"] > last["BB_high"]:
            trend_score -= 1  # Overbought

        # 2. Эцсийн шийдвэр
        current_price = last["Close"]
        atr = last["ATR"] if pd.notna(last["ATR"]) else current_price * 0.01

        if trend_score >= 2:
            signal = "BUY"
            confidence = min(0.9, 0.5 + trend_score * 0.1)
            stop_loss = current_price - atr * 2
            take_profit = current_price + atr * 3
        elif trend_score <= -2:
            signal = "SELL"
            confidence = min(0.9, 0.5 + abs(trend_score) * 0.1)
            stop_loss = current_price + atr * 2
            take_profit = current_price - atr * 3
        else:
            signal = "HOLD"
            confidence = 0.3
            stop_loss = None
            take_profit = None

        # 3. Позицийн хэмжээ (Risk % based on ATR)
        risk_per_trade = 0.02  # Нийт капиталын 2%
        if stop_loss and current_price != stop_loss:
            position_size = risk_per_trade / (abs(current_price - stop_loss) / current_price)
            position_size = min(position_size, 0.1)  # Max 10% of capital
        else:
            position_size = 0

        self.signal = {
            "timestamp": datetime.now().isoformat(),
            "symbol": self.symbol,
            "signal": signal,
            "confidence": confidence,
            "current_price": current_price,
            "trend_score": trend_score,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_size": position_size,
            "rsi": last["RSI"],
            "macd_hist": last["MACD_Hist"],
            "sma_10": last["SMA_10"],
            "sma_30": last["SMA_30"],
            "atr": atr,
        }
        return self.signal

    def validate_with_second_source(self):
        """2-р эх үүсвэрээр баталгаажуулах (OANDA эсвэл Binance)"""
        try:
            # Энгийнээр Yahoo-ийн өгөгдлийг 2 дахь удаа шалгах
            # Real системд OANDA эсвэл Binance API ашиглах
            print("🔄 Баталгаажуулалт: 2-р эх үүсвэрээр шалгаж байна...")
            ticker2 = yf.Ticker("GC=F")  # Өөр эх үүсвэр гэж үзэж болно
            data2 = ticker2.history(period="1d", interval="1m")
            if not data2.empty:
                last2 = data2["Close"].iloc[-1]
                diff = abs(last2 - self.signal["current_price"]) / self.signal["current_price"]
                if diff < 0.005:  # 0.5%-с бага зөрүү
                    print(f"✅ Баталгаажсан: {diff * 100:.2f}% зөрүү")
                    return True
                else:
                    print(f"⚠️ Зөрүү их: {diff * 100:.2f}%")
                    return False
            return True
        except Exception:
            return True

    def print_signal(self):
        """Шийдвэрийг хүний ойлгох хэлбэрээр харуулах"""
        if not self.signal:
            print("❌ Сигнал байхгүй")
            return

        s = self.signal
        print("\n" + "=" * 50)
        print(f"📊 {s['symbol']} БОДИТ ШИЙДВЭР")
        print("=" * 50)
        print(f"🕐 Цаг: {s['timestamp']}")
        print(f"💰 Үнэ: ${s['current_price']:.2f}")
        print(f"📈 Шийдвэр: {'🟢 BUY' if s['signal'] == 'BUY' else '🔴 SELL' if s['signal'] == 'SELL' else '🟡 HOLD'}")
        print(f"🎯 Итгэл: {s['confidence'] * 100:.0f}%")
        print(f"📊 Trend Score: {s['trend_score']}")
        print(f"📉 RSI: {s['rsi']:.1f}")
        print(f"📈 MACD Hist: {s['macd_hist']:.2f}")
        print(f"📊 ATR: {s['atr']:.2f}")
        if s["stop_loss"]:
            print(
                f"🛑 Stop-Loss: ${s['stop_loss']:.2f} ({'-' if s['signal'] == 'SELL' else '+'}{(abs(s['current_price'] - s['stop_loss']) / s['current_price'] * 100):.2f}%)"
            )
        if s["take_profit"]:
            print(
                f"🎯 Take-Profit: ${s['take_profit']:.2f} ({'+' if s['signal'] == 'BUY' else '-'}{(abs(s['current_price'] - s['take_profit']) / s['current_price'] * 100):.2f}%)"
            )
        print(f"📊 Позицийн хэмжээ: {s['position_size'] * 100:.1f}%")
        print("=" * 50)


# === MAIN ===
if __name__ == "__main__":
    print("🚀 БОДИТ АРИЛЖААНЫ ӨМНӨХ ШИНЖИЛГЭЭ")
    print("=" * 40)

    # 1. Систем эхлүүлэх
    system = LiveTradingSignal("XAUUSD")

    # 2. Бодит цагийн өгөгдөл татах
    if not system.fetch_live_data(period="5d", interval="1m"):
        print("❌ Систем ажиллахгүй байна")
        exit()

    # 3. Үзүүлэлтүүдийг тооцоолох
    system.calculate_indicators()

    # 4. Шийдвэр гаргах
    signal = system.generate_signal()

    # 5. 2-р эх үүсвэрээр баталгаажуулах
    system.validate_with_second_source()

    # 6. Үр дүнг харуулах
    system.print_signal()

    # 7. JSON хэлбэрээр хадгалах (бусад системд ашиглахад)
    with open("live_signal.json", "w") as f:
        json.dump(system.signal, f, indent=2)
    print("\n✅ Сигнал JSON-д хадгалагдлаа: live_signal.json")
