"""
V2 Paper Trading Bot - Binance Testnet
"""

import sys
import time
from datetime import datetime

import ccxt
import numpy as np
import pandas as pd

sys.path.insert(0, "C:\\Users\\User\\Desktop\\ResearchOS")
from researchos.monitoring.trading.config import EXCHANGE, STRATEGY

# Connect to Testnet with explicit URLs
exchange = getattr(ccxt, EXCHANGE["name"])(
    {
        "apiKey": EXCHANGE["apiKey"],
        "secret": EXCHANGE["secret"],
        "enableRateLimit": True,
        "options": {
            "defaultType": "spot",
            "urls": {
                "api": {
                    "public": "https://testnet.binance.vision/api",
                    "private": "https://testnet.binance.vision/api",
                }
            },
        },
    }
)

print("=" * 60)
print("🚀 V2 Paper Trading Bot (Binance Testnet)")
print("=" * 60)

# Test balance
try:
    bal = exchange.fetch_balance()
    print("✅ Connected! USDT balance:", bal["total"].get("USDT", 0))
except Exception as e:
    print("❌ Error:", e)
    print("Please check API Key and Secret in config.py")
    sys.exit(1)


def signal(df):
    df = df.copy()
    df["ma_fast"] = df["close"].rolling(STRATEGY["fast_ma"]).mean()
    df["ma_slow"] = df["close"].rolling(STRATEGY["slow_ma"]).mean()
    df["ma_trend"] = df["close"].rolling(200).mean()
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            (df["high"] - df["close"].shift()).abs(), (df["low"] - df["close"].shift()).abs()
        ),
    )
    df["atr"] = df["tr"].rolling(14).mean()
    median_atr = df["atr"].median()
    df["trend"] = np.sign(df["close"] - df["ma_trend"])
    df["vol"] = (df["atr"] < median_atr * 2).astype(int)
    df["raw"] = np.sign(df["ma_fast"] - df["ma_slow"])
    df["signal"] = 0
    df.loc[(df["raw"] == 1) & (df["trend"] == 1) & (df["vol"] == 1), "signal"] = 1
    df.loc[(df["raw"] == -1) & (df["trend"] == -1) & (df["vol"] == 1), "signal"] = -1
    return df.iloc[-1]["signal"], df.iloc[-1]["close"]


print(f"📊 {STRATEGY['symbol']} {STRATEGY['timeframe']}")
last = 0
while True:
    try:
        ohlcv = exchange.fetch_ohlcv(STRATEGY["symbol"], STRATEGY["timeframe"], limit=250)
        df = pd.DataFrame(ohlcv, columns=["t", "o", "h", "l", "c", "v"])
        df["close"] = df["c"].astype(float)
        s, price = signal(df)
        ts = datetime.now().strftime("%H:%M:%S")
        if s != last:
            if s == 1:
                print(f"[{ts}] 📈 BUY  @ {price:.2f}")
            elif s == -1:
                print(f"[{ts}] 📉 SELL @ {price:.2f}")
            else:
                print(f"[{ts}] 🔒 CLOSE @ {price:.2f}")
            last = s
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
        break
    except Exception as e:
        print(f"⚠️ {e}")
        time.sleep(60)
