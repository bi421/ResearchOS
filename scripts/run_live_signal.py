"""Research-only live-data diagnostic for XAUUSD.

This script is intentionally non-trading. It may inspect a public engineering
proxy for a live-data sanity check, but it must not present an unvalidated
rule-based score as a trading decision or use a gold-futures ticker as XAUUSD.
Canonical historical evidence remains the MT5 XAUUSD dataset used by the
ResearchOS research pipeline.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf

from researchos.data_engine.asset_identity import assert_xauusd_identity


class LiveTradingSignal:
    """Backward-compatible name for a research-only live-data diagnostic."""

    def __init__(self, symbol: str = "XAUUSD") -> None:
        self.symbol = symbol
        self.yf_symbol = "XAUUSD=X"
        assert_xauusd_identity(self.symbol, self.yf_symbol)
        self.data: pd.DataFrame | None = None
        self.signal: dict | None = None

    def fetch_live_data(self, period: str = "5d", interval: str = "1m") -> bool:
        """Fetch a live engineering proxy; never use GC=F futures data."""
        if self.symbol.strip().upper().replace("/", "") != "XAUUSD":
            raise ValueError("This diagnostic only supports XAUUSD")
        assert_xauusd_identity(self.symbol, self.yf_symbol)
        ticker = yf.Ticker(self.yf_symbol)
        data = ticker.history(period=period, interval=interval, auto_adjust=False)
        if data.empty:
            self.data = data
            return False
        required = {"Open", "High", "Low", "Close"}
        missing = required.difference(data.columns)
        if missing:
            raise ValueError(f"Live source missing required columns: {sorted(missing)}")
        data = data.sort_index()
        if data.index.has_duplicates:
            raise ValueError("Live source contains duplicate timestamps")
        for column in required:
            data[column] = pd.to_numeric(data[column], errors="coerce")
        if data[list(required)].isna().any().any():
            raise ValueError("Live source contains non-numeric OHLC values")
        if (data["Close"] <= 0).any() or (data["High"] <= 0).any() or (data["Low"] <= 0).any():
            raise ValueError("Live source contains non-positive prices")
        self.data = data
        return True

    def calculate_indicators(self) -> pd.DataFrame:
        """Calculate deterministic diagnostic indicators without imputation."""
        if self.data is None or self.data.empty:
            raise ValueError("Live data must be loaded before calculating indicators")
        df = self.data.copy()
        close = df["Close"]
        df["SMA_10"] = close.rolling(10, min_periods=10).mean()
        df["SMA_30"] = close.rolling(30, min_periods=30).mean()
        df["SMA_200"] = close.rolling(200, min_periods=200).mean()

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14, min_periods=14).mean()
        loss = (-delta.clip(upper=0)).rolling(14, min_periods=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

        df["BB_mid"] = close.rolling(20, min_periods=20).mean()
        bb_std = close.rolling(20, min_periods=20).std()
        df["BB_high"] = df["BB_mid"] + 2 * bb_std
        df["BB_low"] = df["BB_mid"] - 2 * bb_std

        previous_close = close.shift(1)
        true_range = pd.concat(
            [df["High"] - df["Low"],
             (df["High"] - previous_close).abs(),
             (df["Low"] - previous_close).abs()],
            axis=1,
        ).max(axis=1)
        df["ATR"] = true_range.rolling(14, min_periods=14).mean()
        self.data = df
        return df

    def generate_signal(self) -> dict:
        """Generate an UNVALIDATED diagnostic score, never a trading decision."""
        if self.data is None or self.data.empty:
            raise ValueError("Indicator data must be loaded before generating a diagnostic")
        if len(self.data) < 200:
            raise ValueError("At least 200 observations are required for the diagnostic")

        df = self.data
        last = df.iloc[-1]
        prev = df.iloc[-2]
        indicator_names = ["SMA_10", "SMA_30", "RSI", "MACD_Hist", "BB_low", "BB_high", "ATR"]
        if pd.isna(last[indicator_names]).any() or pd.isna(prev[indicator_names]).any():
            raise ValueError("Latest indicator rows are incomplete")

        score = 0
        if last["SMA_10"] > last["SMA_30"] and prev["SMA_10"] <= prev["SMA_30"]:
            score += 2
        elif last["SMA_10"] < last["SMA_30"] and prev["SMA_10"] >= prev["SMA_30"]:
            score -= 2
        if last["RSI"] < 30 and prev["RSI"] < 30:
            score += 1
        elif last["RSI"] > 70 and prev["RSI"] > 70:
            score -= 1
        if last["MACD_Hist"] > 0 and prev["MACD_Hist"] <= 0:
            score += 1
        elif last["MACD_Hist"] < 0 and prev["MACD_Hist"] >= 0:
            score -= 1
        if last["Close"] < last["BB_low"]:
            score += 1
        elif last["Close"] > last["BB_high"]:
            score -= 1

        self.signal = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": self.symbol,
            "source": self.yf_symbol,
            "research_status": "UNVALIDATED_DIAGNOSTIC",
            "trading_action": "DISABLED",
            "trend_score": int(score),
            "current_price": float(last["Close"]),
            "rsi": float(last["RSI"]),
            "macd_hist": float(last["MACD_Hist"]),
            "sma_10": float(last["SMA_10"]),
            "sma_30": float(last["SMA_30"]),
            "atr": float(last["ATR"]),
        }
        return self.signal

    def validate_with_second_source(self) -> bool:
        """Never claim second-source validation without an independent source."""
        return False

    def print_signal(self) -> None:
        if not self.signal:
            print("No diagnostic available")
            return
        print("\n" + "=" * 60)
        print("XAUUSD LIVE-DATA DIAGNOSTIC — TRADING DISABLED")
        print("=" * 60)
        for key, value in self.signal.items():
            print(f"{key}: {value}")
        print("=" * 60)


if __name__ == "__main__":
    system = LiveTradingSignal("XAUUSD")
    if not system.fetch_live_data(period="5d", interval="1m"):
        raise SystemExit("Live engineering-proxy data unavailable")
    system.calculate_indicators()
    system.generate_signal()
    system.print_signal()
    with open("live_signal.json", "w", encoding="utf-8") as handle:
        json.dump(system.signal, handle, indent=2, ensure_ascii=False)
