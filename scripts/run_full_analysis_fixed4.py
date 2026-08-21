import base64
import io
import sys
import time
import warnings
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yfinance as yf

from researchos.decision_engine.contracts import (
    EvidenceItem,
    EvidenceSource,
    ProbabilityOutcome,
    WeightConfiguration,
)
from researchos.decision_engine.score import compute_evidence_score
from researchos.quant_engine.backend import PythonQuantBackend

warnings.filterwarnings("ignore")

# ============================================================
# 1. ӨГӨГДӨЛ ТАТАХ
# ============================================================
SYMBOLS = {
    "XAUUSD": "GC=F",
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

combined_df = pd.DataFrame(all_series).ffill().dropna()
print(f"📊 Aligned data: {len(combined_df)} common trading days")

if combined_df.empty:
    print("❌ Өгөгдөл тохирохгүй байна.")
    sys.exit(1)

# ============================================================
# 3. CORRELATION MATRIX
# ============================================================
corr_matrix = combined_df.corr()

plt.figure(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", center=0, fmt=".2f")
plt.title("Cross-Asset Correlation Matrix")
plt.tight_layout()
buf = io.BytesIO()
plt.savefig(buf, format="png", dpi=150)
buf.seek(0)
heatmap_b64 = base64.b64encode(buf.read()).decode("utf-8")
plt.close()


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
    if name not in ["DXY", "US10Y", "VIX"]:
        m = compute_metrics(combined_df[name])
        if m:
            asset_metrics[name] = m
            print(f"📊 {name}: Return {m['total_return']:.2%}, Sharpe {m['sharpe_ratio']:.2f}")

# ============================================================
# 5. REGIME DETECTION
# ============================================================
regime = "NEUTRAL"
regime_reasons = []

if "VIX" in combined_df.columns and len(combined_df["VIX"].dropna()) > 0:
    vix_current = combined_df["VIX"].iloc[-1]
    if vix_current > 20:
        regime_reasons.append(f"VIX = {vix_current:.1f} (>20)")
if "DXY" in combined_df.columns and len(combined_df["DXY"].dropna()) > 1:
    dxy_change = (combined_df["DXY"].iloc[-1] / combined_df["DXY"].iloc[0] - 1) * 100
    if dxy_change > 2:
        regime_reasons.append(f"DXY өссөн: {dxy_change:.1f}%")
if "BTCUSD" in combined_df.columns:
    btc_return = asset_metrics.get("BTCUSD", {}).get("total_return", 0)
    if btc_return < -0.1:
        regime_reasons.append(f"BTCUSD унасан: {btc_return:.1%}")

if len(regime_reasons) >= 2:
    regime = "RISK-OFF"
elif len(regime_reasons) == 1:
    regime = "CAUTIOUS"
else:
    regime = "RISK-ON"

# ============================================================
# 6. EVIDENCE ITEMS
# ============================================================
evidence_items = []

for name, metrics in asset_metrics.items():
    if metrics["total_return"] > 0.15:
        direction = ProbabilityOutcome.BULLISH
        strength = min(metrics["sharpe_ratio"] / 2.0, 1.0)
    elif metrics["total_return"] < -0.05:
        direction = ProbabilityOutcome.BEARISH
        strength = min(abs(metrics["total_return"]) / 1.5, 1.0)
    else:
        direction = ProbabilityOutcome.NEUTRAL
        strength = 0.3

    item = EvidenceItem(
        source=EvidenceSource.QUANT_ENGINE,
        source_id=f"{name}_perf",
        direction=direction,
        strength=strength,
        weight=0.3,
        confidence=0.8,
        description=(
            f"{name}: Return {metrics['total_return']:.2%}, "
            f"Sharpe {metrics['sharpe_ratio']:.2f}, "
            f"Max DD {metrics['max_drawdown']:.2%}"
        ),
        supporting_ids=[],
    )
    evidence_items.append(item)

# Macro evidence
macro_corr = {}
if "XAUUSD" in combined_df.columns:
    for macro_name in ["DXY", "US10Y", "VIX"]:
        if macro_name in combined_df.columns:
            corr = combined_df["XAUUSD"].corr(combined_df[macro_name])
            if not pd.isna(corr):
                macro_corr[macro_name] = corr
                if macro_name == "DXY":
                    direction = ProbabilityOutcome.BULLISH if corr < -0.3 else ProbabilityOutcome.NEUTRAL
                    strength = min(abs(corr), 1.0)
                elif macro_name == "US10Y":
                    direction = ProbabilityOutcome.BEARISH if corr > 0.3 else ProbabilityOutcome.NEUTRAL
                    strength = min(abs(corr), 1.0)
                elif macro_name == "VIX":
                    direction = ProbabilityOutcome.BULLISH if corr > 0.3 else ProbabilityOutcome.NEUTRAL
                    strength = min(abs(corr), 1.0)
                else:
                    direction = ProbabilityOutcome.NEUTRAL
                    strength = 0.2

                item = EvidenceItem(
                    source=EvidenceSource.MACRO_INTELLIGENCE,
                    source_id=f"macro_{macro_name}",
                    direction=direction,
                    strength=strength,
                    weight=0.25,
                    confidence=0.7,
                    description=f"{macro_name} vs XAUUSD: {corr:.3f}",
                    supporting_ids=[],
                )
                evidence_items.append(item)

# ============================================================
# 7. EVIDENCE SCORE
# ============================================================
weight_config = WeightConfiguration(
    quant_weight=0.4,
    validation_weight=0.1,
    experiment_weight=0.2,
    macro_weight=0.3,
    market_memory_weight=0.0,
)

score = compute_evidence_score(
    context_id="full_analysis_v3",
    evidence_items=evidence_items,
    weight_config=weight_config,
    scoring_version="SCORE_V1",
)

# ============================================================
# 8. MARKDOWN REPORT
# ============================================================
report = f"""
# 📊 Multi-Asset Market Intelligence Report (v3)
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Period:** {start.strftime("%Y-%m-%d")} → {end.strftime("%Y-%m-%d")}
**Aligned Data Points:** {len(combined_df)} trading days
**Assets Analyzed:** {", ".join(asset_metrics.keys())}

---

## 🌍 Market Regime: **{regime}**
**Reasons:** {", ".join(regime_reasons) if regime_reasons else "No clear signals"}

---

## 🏆 Evidence Score Summary

| Metric | Value |
|--------|-------|
| **Total Score** | **{score.total_score:.3f}** |
| Bullish Score | {score.bullish_score:.3f} |
| Bearish Score | {score.bearish_score:.3f} |
| Neutral Score | {score.neutral_score:.3f} |
| Confidence | {score.confidence_score:.3f} |
| Uncertainty | {score.uncertainty_score:.3f} |
| Evidence Count | {score.evidence_count} |

**Interpretation:** {("**BULLISH**" if score.total_score > 0.2 else "**BEARISH**" if score.total_score < -0.2 else "**NEUTRAL**")}

---

## 📈 Asset Performance & Risk Metrics

| Asset | Return | Sharpe | Sortino | Calmar | Max DD | Direction |
|-------|--------|--------|---------|--------|--------|-----------|
"""

for name, m in asset_metrics.items():
    sortino = m.get("sortino_ratio", 0)
    calmar = m.get("calmar_ratio", 0)
    for item in evidence_items:
        if item.source_id == f"{name}_perf":
            dir_val = item.direction.value
            break
    else:
        dir_val = "N/A"
    report += f"| {name} | {m['total_return']:.2%} | {m['sharpe_ratio']:.2f} | {sortino:.2f} | {calmar:.2f} | {m['max_drawdown']:.2%} | {dir_val} |\n"

report += """

## 🔗 Macro Factor Correlations (vs XAUUSD)

| Factor | Correlation | Economic Interpretation |
|--------|-------------|--------------------------|
"""

for name, corr in macro_corr.items():
    if name == "DXY":
        interp = "Strong inverse (USD down → Gold up)" if corr < -0.5 else "Moderate inverse"
    elif name == "US10Y":
        interp = "Real yield impact (Yield up → Gold down)" if corr > 0.3 else "Weak impact"
    elif name == "VIX":
        interp = "Safe-haven demand (VIX up → Gold up)" if corr > 0.3 else "Weak correlation"
    else:
        interp = "N/A"
    report += f"| {name} | {corr:.3f} | {interp} |\n"

report += f"""

## 📊 Cross-Asset Correlation Matrix (Heatmap)

![Correlation Heatmap](data:image/png;base64,{heatmap_b64})

**Key Insights:**
"""
if "DXY" in macro_corr:
    report += f"- **DXY vs XAUUSD:** {macro_corr.get('DXY', 0):.3f} (inverse correlation)\n"
if "US10Y" in macro_corr:
    report += f"- **US10Y vs XAUUSD:** {macro_corr.get('US10Y', 0):.3f} (yield impact)\n"
if "VIX" in macro_corr:
    report += f"- **VIX vs XAUUSD:** {macro_corr.get('VIX', 0):.3f} (risk-on/off)\n"

report += """

## 📋 All Evidence Items

| Source | ID | Direction | Strength | Confidence |
|--------|-----|-----------|----------|------------|
"""

for item in evidence_items:
    report += f"| {item.source.value} | {item.source_id} | {item.direction.value} | {item.strength:.2f} | {item.confidence:.2f} |\n"

report += f"""

## 💡 Summary
- **Best Performer:** {max(asset_metrics.items(), key=lambda x: x[1]["total_return"])[0]} ({max(asset_metrics.items(), key=lambda x: x[1]["total_return"])[1]["total_return"]:.2%})
- **Worst Performer:** {min(asset_metrics.items(), key=lambda x: x[1]["total_return"])[0]} ({min(asset_metrics.items(), key=lambda x: x[1]["total_return"])[1]["total_return"]:.2%})
- **Highest Sharpe:** {max(asset_metrics.items(), key=lambda x: x[1]["sharpe_ratio"])[0]} (Sharpe: {max(asset_metrics.items(), key=lambda x: x[1]["sharpe_ratio"])[1]["sharpe_ratio"]:.2f})
- **Risk-Off Signal:** {"Yes" if regime == "RISK-OFF" else "No"}
- **Overall Sentiment:** {"Bullish" if score.total_score > 0.2 else "Bearish" if score.total_score < -0.2 else "Neutral"}
"""

with open("market_report_v3.md", "w", encoding="utf-8") as f:
    f.write(report)

print("\n✅ Advanced report saved: market_report_v3.md")
print(f"📊 Regime: {regime}")
