"""
Ensemble Strategy: FIXED. Evaluates indicators correctly at each time step.
"""

from dataclasses import dataclass

from researchos.quant_engine.indicators import (
    calculate_bollinger_bands,
    calculate_macd,
    calculate_rsi,
)


@dataclass
class EnsembleSignal:
    day_index: int
    action: str
    price: float
    confidence: float
    reasons: list[str]


class EnsembleStrategy:
    def __init__(self, min_confidence=0.60):  # 60% босго (2/3 индикатор таарвал)
        self.min_confidence = min_confidence

    def generate_signals(self, prices: list[float]) -> list[EnsembleSignal]:
        signals = []
        # MACD-д хамгийн багадаа 35 өдөр хэрэгтэй (26 slow + 9 signal)
        for i in range(35, len(prices)):
            window = prices[: i + 1]
            current_price = window[-1]

            # Тухайн цэг дээрх индикаторуудыг тооцох
            rsi_vals = calculate_rsi(window, 14)
            macd_line, sig_line, hist_vals = calculate_macd(window, 12, 26, 9)
            upper_vals, mid_vals, lower_vals = calculate_bollinger_bands(window, 20, 2.0)

            if not rsi_vals or not hist_vals or not upper_vals:
                continue

            current_rsi = rsi_vals[-1]
            current_hist = hist_vals[-1]
            prev_hist = hist_vals[-2] if len(hist_vals) > 1 else 0
            current_upper = upper_vals[-1]
            current_lower = lower_vals[-1]

            buy_score = 0
            sell_score = 0
            reasons = []

            # 1. RSI шалгуур
            if current_rsi < 30:
                buy_score += 1
                reasons.append(f"RSI={current_rsi:.1f} (oversold)")
            elif current_rsi > 70:
                sell_score += 1
                reasons.append(f"RSI={current_rsi:.1f} (overbought)")

            # 2. MACD шалгуур
            if current_hist > 0 and prev_hist <= 0:
                buy_score += 1
                reasons.append("MACD crossover")
            elif current_hist < 0 and prev_hist >= 0:
                sell_score += 1
                reasons.append("MACD crossunder")

            # 3. Bollinger Bands шалгуур
            if current_price < current_lower:
                buy_score += 1
                reasons.append("Price < Lower BB")
            elif current_price > current_upper:
                sell_score += 1
                reasons.append("Price > Upper BB")

            # Шийдвэр гаргах (Дор хаяж 2 индикатор ижил дохио өгсөн үү?)
            if buy_score >= 2:
                confidence = buy_score / 3.0
                if confidence >= self.min_confidence:
                    signals.append(EnsembleSignal(i, "BUY", current_price, confidence, reasons))
            elif sell_score >= 2:
                confidence = sell_score / 3.0
                if confidence >= self.min_confidence:
                    signals.append(EnsembleSignal(i, "SELL", current_price, confidence, reasons))

        return signals
