"""
Trading strategy framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Signal:
    timestamp: int
    action: str  # "BUY", "SELL", "HOLD"
    price: float
    strength: float  # 0.0 to 1.0
    reason: str


class BaseStrategy(ABC):
    @abstractmethod
    def generate_signals(self, prices: list[float]) -> list[Signal]:
        pass


class RSIStrategy(BaseStrategy):
    def __init__(self, period=14, oversold=30, overbought=70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, prices: list[float]) -> list[Signal]:
        from researchos.engines.quant.indicators import calculate_rsi

        rsi_values = calculate_rsi(prices, self.period)
        signals = []
        for i, rsi in enumerate(rsi_values):
            idx = i + self.period
            if idx >= len(prices):
                break
            if rsi < self.oversold:
                signals.append(Signal(idx, "BUY", prices[idx], 1.0 - rsi / 100, f"RSI={rsi:.1f} oversold"))
            elif rsi > self.overbought:
                signals.append(Signal(idx, "SELL", prices[idx], rsi / 100, f"RSI={rsi:.1f} overbought"))
        return signals


class MACDStrategy(BaseStrategy):
    def __init__(self, fast=12, slow=26, signal=9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, prices: list[float]) -> list[Signal]:
        from researchos.engines.quant.indicators import calculate_macd

        macd, signal_line, histogram = calculate_macd(prices, self.fast, self.slow, self.signal)
        signals = []
        for i in range(1, len(histogram)):
            if histogram[i] > 0 and histogram[i - 1] <= 0:
                idx = len(prices) - len(histogram) + i
                signals.append(Signal(idx, "BUY", prices[idx], 0.8, "MACD crossover"))
            elif histogram[i] < 0 and histogram[i - 1] >= 0:
                idx = len(prices) - len(histogram) + i
                signals.append(Signal(idx, "SELL", prices[idx], 0.8, "MACD crossunder"))
        return signals


class BollingerStrategy(BaseStrategy):
    def __init__(self, period=20, std_dev=2.0):
        self.period = period
        self.std_dev = std_dev

    def generate_signals(self, prices: list[float]) -> list[Signal]:
        from researchos.engines.quant.indicators import calculate_bollinger_bands

        upper, middle, lower = calculate_bollinger_bands(prices, self.period, self.std_dev)
        signals = []
        for i in range(len(lower)):
            idx = i + self.period - 1
            if idx >= len(prices):
                break
            if prices[idx] < lower[i]:
                signals.append(Signal(idx, "BUY", prices[idx], 0.9, "Price below lower band"))
            elif prices[idx] > upper[i]:
                signals.append(Signal(idx, "SELL", prices[idx], 0.9, "Price above upper band"))
        return signals
