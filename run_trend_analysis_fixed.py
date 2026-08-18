import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from researchos.quant_engine.backend import PythonQuantBackend
from researchos.decision_engine.contracts import EvidenceItem, EvidenceSource, ProbabilityOutcome, WeightConfiguration
from researchos.decision_engine.score import compute_evidence_score
import sys
import time

# ============================================================
# 1. ӨГӨГДӨЛ ТАТАХ
# ============================================================
SYMBOLS = {
    'XAUUSD': 'GC=F',
    'BTCUSD': 'BTC-USD',
    'USOIL': 'CL=F',
    'AAPL': 'AAPL',
    'EURUSD': 'EURUSD=X',
    'GBPUSD': 'GBPUSD=X',
    'USDJPY': 'USDJPY=X'
}
MACRO_SYMBOLS = {
    'DXY': 'DX-Y.NYB',
    'US10Y': '^TNX',
    'VIX': '^VIX'
}

end = datetime.now()
start = end - timedelta(days=30)

def safe_fetch(symbol, yf_symbol):
    try:
        ticker = yf.Ticker(yf_symbol)
        data = ticker.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        if data.empty:
            return None
        return pd.DataFrame({'close': data['Close']})
    except Exception:
        return None

asset_data = {}
for name, yf_sym in SYMBOLS.items():
    df = safe_fetch(name, yf_sym)
    if df is not None and not df.empty:
        asset_data[name] = df
        print(f'✅ {name}: {len(df)} records')
    time.sleep(0.3)

macro_data = {}
for name, yf_sym in MACRO_SYMBOLS.items():
    df = safe_fetch(name, yf_sym)
    if df is not None and not df.empty:
        macro_data[name] = df
        print(f'✅ Macro {name}: {len(df)} records')
    time.sleep(0.3)

if not asset_data:
    print('❌ Өгөгдөл татагдаагүй.')
    sys.exit(1)

# ============================================================
# 2. DATA ALIGNMENT
# ============================================================
all_series = {}
for name, df in asset_data.items():
    all_series[name] = df['close']
for name, df in macro_data.items():
    all_series[name] = df['close']

combined_df = pd.DataFrame(all_series).ffill().dropna()
print(f'📊 Aligned data: {len(combined_df)} common trading days')

# ============================================================
# 3. TREND DETECTION
# ============================================================
def detect_trend(series, short_window=10, long_window=30):
    if len(series) < long_window:
        return 'NEUTRAL', 0.0, 0.0

    current_price = series.iloc[-1]
    sma_short = series.rolling(short_window).mean().iloc[-1]
    sma_long = series.rolling(long_window).mean().iloc[-1]
    price_change = series.pct_change().iloc[-1] if len(series) > 1 else 0.0

    if current_price > sma_short and current_price > sma_long:
        trend = 'BULLISH'
        strength = min(abs(current_price / sma_long - 1) * 10, 1.0)
    elif current_price < sma_short and current_price < sma_long:
        trend = 'BEARISH'
        strength = min(abs(current_price / sma_long - 1) * 10, 1.0)
    else:
        trend = 'NEUTRAL'
        strength = 0.3

    return trend, strength, price_change

trend_results = {}
for name in combined_df.columns:
    if name not in MACRO_SYMBOLS.keys():
        trend, strength, price_change = detect_trend(combined_df[name])
        trend_results[name] = {
            'trend': trend,
            'strength': strength,
            'price_change': price_change,
            'current_price': combined_df[name].iloc[-1],
            'prev_price': combined_df[name].iloc[-2] if len(combined_df[name]) > 1 else combined_df[name].iloc[-1]
        }
        emoji = '🟢' if trend == 'BULLISH' else '🔴' if trend == 'BEARISH' else '🟡'
        print(f'{emoji} {name}: {trend} (strength: {strength:.2f}, change: {price_change:.2%})')

# ============================================================
# 4. EVIDENCE ITEMS
# ============================================================
evidence_items = []

for name, info in trend_results.items():
    direction = ProbabilityOutcome.BULLISH if info['trend'] == 'BULLISH' else ProbabilityOutcome.BEARISH if info['trend'] == 'BEARISH' else ProbabilityOutcome.NEUTRAL
    item = EvidenceItem(
        source=EvidenceSource.QUANT_ENGINE,
        source_id=f'{name}_trend',
        direction=direction,
        strength=info['strength'],
        weight=0.35,
        confidence=0.75,
        description=(
            f'{name}: {info["trend"]}, '
            f'Price: ${info["current_price"]:.2f}, '
            f'Change: {info["price_change"]:.2%}'
        ),
        supporting_ids=[]
    )
    evidence_items.append(item)

# ============================================================
# 5. EVIDENCE SCORE
# ============================================================
weight_config = WeightConfiguration(
    quant_weight=0.4,
    validation_weight=0.1,
    experiment_weight=0.2,
    macro_weight=0.3,
    market_memory_weight=0.0
)

score = compute_evidence_score(
    context_id='trend_analysis_fixed',
    evidence_items=evidence_items,
    weight_config=weight_config,
    scoring_version='SCORE_V1'
)

# ============================================================
# 6. REPORT
# ============================================================
report = f'''
# 📊 Trend Analysis Report (Fixed)
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Data Period:** {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}
**Aligned Days:** {len(combined_df)}

## 📈 Trend Results
| Asset | Trend | Strength | Change |
|-------|-------|----------|--------|
'''
for name, info in trend_results.items():
    emoji = '🟢' if info['trend'] == 'BULLISH' else '🔴' if info['trend'] == 'BEARISH' else '🟡'
    report += f'| {name} | {emoji} {info["trend"]} | {info["strength"]:.2f} | {info["price_change"]:.2%} |\n'

report += f'''
## 🏆 Evidence Score
| Metric | Value |
|--------|-------|
| Total Score | {score.total_score:.3f} |
| Bullish | {score.bullish_score:.3f} |
| Bearish | {score.bearish_score:.3f} |
| Neutral | {score.neutral_score:.3f} |

**Sentiment:** {'Bullish' if score.total_score > 0.2 else 'Bearish' if score.total_score < -0.2 else 'Neutral'}
'''

with open('trend_report_verified.md', 'w', encoding='utf-8') as f:
    f.write(report)

print('\n✅ Report saved: trend_report_verified.md')
print(f'📊 Market Sentiment: {"Bullish" if score.total_score > 0.2 else "Bearish" if score.total_score < -0.2 else "Neutral"}')