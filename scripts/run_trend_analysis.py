import sys
import time
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from researchos.data_engine.asset_identity import (
    assert_xauusd_identity,
)
from researchos.decision_engine.contracts import (
    EvidenceItem,
    EvidenceSource,
    ProbabilityOutcome,
    WeightConfiguration,
)
from researchos.decision_engine.score import compute_evidence_score
from researchos.quant_engine.backend import PythonQuantBackend

# ============================================================
# 1. ӨГӨГДӨЛ ТАТАХ
# ============================================================
SYMBOLS = {
    # XAUUSD spot proxy (delayed ref; NOT canonical real data)
    "BTCUSD": "BTC-USD",
    "USOIL": "CL=F",
    "AAPL": "AAPL",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
}
MACRO_SYMBOLS = {"DXY": "DX-Y.NYB", "US10Y": "^TNX", "VIX": "^VIX"}

end = datetime.now()
start = end - timedelta(days=90)


def safe_fetch(symbol, yf_symbol):
    try:
        ticker = yf.Ticker(yf_symbol)
        data = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
        if data.empty:
            return None
        return pd.DataFrame({"close": data["Close"]})
    except Exception:
        return None


# Татах
asset_data = {}
for name, yf_sym in SYMBOLS.items():
    assert_xauusd_identity(name, yf_sym)  # Reject GC=F (COMEX gold futures) as XAUUSD spot
    df = safe_fetch(name, yf_sym)
    if df is not None and not df.empty:
        asset_data[name] = df
        print(f"✅ {name}: {len(df)} records")
    time.sleep(0.3)

macro_data = {}
for name, yf_sym in MACRO_SYMBOLS.items():
    df = safe_fetch(name, yf_sym)
    if df is not None and not df.empty:
        macro_data[name] = df
        print(f"✅ Macro {name}: {len(df)} records")
    time.sleep(0.3)

if not asset_data:
    print("❌ Өгөгдөл татагдаагүй.")
    sys.exit(1)

# ============================================================
# 2. DATA ALIGNMENT
# ============================================================
all_series = {}
for name, df in asset_data.items():
    all_series[name] = df["close"]
for name, df in macro_data.items():
    all_series[name] = df["close"]

combined_df = pd.DataFrame(all_series).fillna(method="ffill").dropna()
if combined_df.empty:
    combined_df = combined_df.resample("D").ffill().dropna()

print(f"📊 Aligned data: {len(combined_df)} common trading days")


# ============================================================
# 3. TREND DETECTION (БОДИТ ҮНИЙН ХАНДЛАГА)
# ============================================================
def detect_trend(series, short_window=20, long_window=50):
    """
    Бодит үнийн хандлагыг тодорхойлох
    Returns: (trend, strength, price_change)
    """
    if len(series) < long_window:
        return "NEUTRAL", 0.0, 0.0

    current_price = series.iloc[-1]
    sma_short = series.rolling(short_window).mean().iloc[-1]
    sma_long = series.rolling(long_window).mean().iloc[-1]
    price_change = (current_price - series.iloc[-2]) / series.iloc[-2] if len(series) > 1 else 0.0

    # Хандлагын чиглэл
    if current_price > sma_short and current_price > sma_long:
        trend = "BULLISH"
        strength = min(abs(current_price / sma_long - 1) * 5, 1.0)
    elif current_price < sma_short and current_price < sma_long:
        trend = "BEARISH"
        strength = min(abs(current_price / sma_long - 1) * 5, 1.0)
    else:
        trend = "NEUTRAL"
        strength = 0.3

    return trend, strength, price_change


trend_results = {}
for name in combined_df.columns:
    if name not in MACRO_SYMBOLS.keys():
        trend, strength, price_change = detect_trend(combined_df[name])
        trend_results[name] = {
            "trend": trend,
            "strength": strength,
            "price_change": price_change,
            "current_price": combined_df[name].iloc[-1],
        }
        emoji = "🟢" if trend == "BULLISH" else "🔴" if trend == "BEARISH" else "🟡"
        print(f"{emoji} {name}: {trend} (strength: {strength:.2f}, change: {price_change:.2%})")


# ============================================================
# 4. МЕТРИК ТООЦООЛОХ
# ============================================================
def compute_metrics(series):
    if len(series) < 10:
        return None
    returns = series.pct_change().dropna().tolist()
    if len(returns) < 5:
        return None
    equity = (1 + pd.Series(returns)).cumprod() * 10000.0
    backend = PythonQuantBackend()
    try:
        return backend.calculate_metrics(returns=returns, equity_curve=equity.tolist(), risk_free_rate=0.0)
    except Exception:
        return None


asset_metrics = {}
for name in combined_df.columns:
    if name not in MACRO_SYMBOLS.keys():
        m = compute_metrics(combined_df[name])
        if m:
            asset_metrics[name] = m

# ============================================================
# 5. EVIDENCE ITEMS (TREND ДЭЭР СУУРИЛСАН)
# ============================================================
evidence_items = []

for name, trend_info in trend_results.items():
    direction = (
        ProbabilityOutcome.BULLISH
        if trend_info["trend"] == "BULLISH"
        else ProbabilityOutcome.BEARISH
        if trend_info["trend"] == "BEARISH"
        else ProbabilityOutcome.NEUTRAL
    )
    strength = trend_info["strength"]

    item = EvidenceItem(
        source=EvidenceSource.QUANT_ENGINE,
        source_id=f"{name}_trend",
        direction=direction,
        strength=strength,
        weight=0.35,
        confidence=0.75,
        description=(f"{name}: {trend_info['trend']}, Price: , Change: {trend_info['price_change']:.2%}"),
        supporting_ids=[],
    )
    evidence_items.append(item)

# ============================================================
# 6. EVIDENCE SCORE
# ============================================================
weight_config = WeightConfiguration(
    quant_weight=0.4,
    validation_weight=0.1,
    experiment_weight=0.2,
    macro_weight=0.3,
    market_memory_weight=0.0,
)

score = compute_evidence_score(
    context_id="trend_analysis",
    evidence_items=evidence_items,
    weight_config=weight_config,
    scoring_version="SCORE_V1",
)

# ============================================================
# 7. MARKDOWN REPORT
# ============================================================
report = f"""
# 📊 Real-Time Price Trend Analysis
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Data Period:** {start.strftime("%Y-%m-%d")} → {end.strftime("%Y-%m-%d")}

---

## 📈 Current Price Trends

| Asset | Current Price | Trend | Strength | Daily Change | 20-Day SMA | 50-Day SMA |
|-------|--------------|-------|----------|--------------|-----------|-----------|
"""

for name, info in trend_results.items():
    if name in combined_df.columns:
        sma20 = combined_df[name].rolling(20).mean().iloc[-1]
        sma50 = combined_df[name].rolling(50).mean().iloc[-1]
        emoji = "🟢" if info["trend"] == "BULLISH" else "🔴" if info["trend"] == "BEARISH" else "🟡"
        report += (
            f"| {name} |  | {emoji} {info['trend']} | {info['strength']:.2f} | {info['price_change']:.2%} |  |  |\n"
        )

report += f"""

## 🏆 Evidence Score Summary

| Metric | Value |
|--------|-------|
| **Total Score** | **{score.total_score:.3f}** |
| Bullish Score | {score.bullish_score:.3f} |
| Bearish Score | {score.bearish_score:.3f} |
| Neutral Score | {score.neutral_score:.3f} |
| Confidence | {score.confidence_score:.3f} |
| Uncertainty | {score.uncertainty_score:.3f} |

**Interpretation:** {("**BULLISH**" if score.total_score > 0.2 else "**BEARISH**" if score.total_score < -0.2 else "**NEUTRAL**")}

---

## 🔍 Key Insights
"""
# Хүчтэй хандлагатай хөрөнгүүд
strong_bullish = [k for k, v in trend_results.items() if v["trend"] == "BULLISH" and v["strength"] > 0.6]
strong_bearish = [k for k, v in trend_results.items() if v["trend"] == "BEARISH" and v["strength"] > 0.6]

if strong_bullish:
    report += f"- **Strong Bullish:** {', '.join(strong_bullish)}\n"
if strong_bearish:
    report += f"- **Strong Bearish:** {', '.join(strong_bearish)}\n"
if not strong_bullish and not strong_bearish:
    report += "- **No strong trends detected** — market is range-bound\n"

report += f"""
- **Overall Sentiment:** {"Bullish" if score.total_score > 0.2 else "Bearish" if score.total_score < -0.2 else "Neutral"}

## 💡 Trading Signals
"""

for name, info in trend_results.items():
    if info["trend"] == "BULLISH" and info["strength"] > 0.5:
        report += f"- **{name}:** BUY (trend strength: {info['strength']:.2f})\n"
    elif info["trend"] == "BEARISH" and info["strength"] > 0.5:
        report += f"- **{name}:** SELL (trend strength: {info['strength']:.2f})\n"
    else:
        report += f"- **{name}:** HOLD (no clear trend)\n"

with open("trend_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print("\n✅ Trend report saved: trend_report.md")
print(
    f"📊 Market Sentiment: {'Bullish' if score.total_score > 0.2 else 'Bearish' if score.total_score < -0.2 else 'Neutral'}"
)
