import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from researchos.quant_engine.backend import PythonQuantBackend
from researchos.data_engine.repository import SqliteDatasetRepository
from researchos.decision_engine.contracts import EvidenceItem, EvidenceSource, ProbabilityOutcome, WeightConfiguration
from researchos.decision_engine.score import compute_evidence_score
from researchos.data_engine.asset_identity import DataIdentityError, assert_xauusd_identity, resolve_xauusd_spot_proxy
import sys

# ============================================================
# 1. ӨГӨГДӨЛ ТАТАХ (YFINANCE) – ЗӨВ ТИКЕРҮҮД
# ============================================================
SYMBOLS = {
      # XAUUSD spot proxy (delayed ref; NOT canonical real data)
    'BTCUSD': 'BTC-USD',
    'USOIL': 'CL=F',
    'AAPL': 'AAPL',
    'EURUSD': 'EURUSD=X'
}
MACRO_SYMBOLS = {
    'DXY': 'DX-Y.NYB',
    'US10Y': '^TNX',
    'VIX': '^VIX'
}

end = datetime.now()
start = end - timedelta(days=90)

def safe_fetch(symbol, yf_symbol):
    try:
        data = yf.download(yf_symbol, start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'), progress=False)
        if data.empty:
            print(f'⚠️  {symbol}: хоосон өгөгдөл')
            return None
        df = pd.DataFrame({'close': data['Close']})
        return df
    except Exception as e:
        print(f'⚠️  {symbol} татахад алдаа: {e}')
        return None

asset_data = {}
for name, yf_sym in SYMBOLS.items():
    assert_xauusd_identity(name, yf_sym)  # Reject GC=F (COMEX gold futures) as XAUUSD spot
    df = safe_fetch(name, yf_sym)
    if df is not None and not df.empty:
        asset_data[name] = df
        print(f'✅ {name}: {len(df)} records')

macro_data = {}
for name, yf_sym in MACRO_SYMBOLS.items():
    df = safe_fetch(name, yf_sym)
    if df is not None and not df.empty:
        macro_data[name] = df
        print(f'✅ Macro {name}: {len(df)} records')

if not asset_data:
    print('❌ Ямар ч хөрөнгийн өгөгдөл татагдаагүй. Интернетийн холболт эсвэл тикерүүдийг шалгана уу.')
    sys.exit(1)

# ============================================================
# 2. МЕТРИК ТООЦООЛОХ
# ============================================================
def compute_metrics(df):
    if df is None or len(df) < 10:
        return None
    returns = df['close'].pct_change().dropna().tolist()
    if len(returns) < 5:
        return None
    equity = (1 + pd.Series(returns)).cumprod() * 10000.0
    backend = PythonQuantBackend()
    try:
        return backend.calculate_metrics(
            returns=returns,
            equity_curve=equity.tolist(),
            risk_free_rate=0.0
        )
    except Exception as e:
        print(f'⚠️  Метрик тооцоолоход алдаа: {e}')
        return None

asset_metrics = {}
for name, df in asset_data.items():
    m = compute_metrics(df)
    if m:
        asset_metrics[name] = m
        print(f'📊 {name}: Return {m["total_return"]:.2%}, Sharpe {m["sharpe_ratio"]:.2f}')

if not asset_metrics:
    print('❌ Ямар ч хөрөнгийн метрик тооцоологдсонгүй.')
    sys.exit(1)

# ============================================================
# 3. MACRO CORRELATION (XAUUSD-тай)
# ============================================================
macro_corr = {}
if 'XAUUSD' in asset_data and macro_data:
    xau_df = asset_data['XAUUSD']
    for macro_name, mdf in macro_data.items():
        combined = pd.DataFrame({
    'XAUUSD': resolve_xauusd_spot_proxy(),  # XAUUSD spot proxy (canonical yfinance spot ref; NOT real data)
            macro_name: mdf['close']
        }).dropna()
        if len(combined) > 10:
            corr = combined.corr().iloc[0, 1]
            if not pd.isna(corr):
                macro_corr[macro_name] = corr
                print(f'🔗 {macro_name} vs XAUUSD correlation: {corr:.3f}')

# ============================================================
# 4. EVIDENCE ITEMS ҮҮСГЭХ
# ============================================================
evidence_items = []

# 4.1. Хөрөнгийн гүйцэтгэл
for name, metrics in asset_metrics.items():
    if metrics['total_return'] > 0.15:
        direction = ProbabilityOutcome.BULLISH
        strength = min(metrics['sharpe_ratio'] / 2.0, 1.0)
    elif metrics['total_return'] < -0.05:
        direction = ProbabilityOutcome.BEARISH
        strength = min(abs(metrics['total_return']) / 1.5, 1.0)
    else:
        direction = ProbabilityOutcome.NEUTRAL
        strength = 0.3

    item = EvidenceItem(
        source=EvidenceSource.QUANT_ENGINE,
        source_id=f'{name}_perf',
        direction=direction,
        strength=strength,
        weight=0.3,
        confidence=0.8,
        description=(
            f'{name}: Return {metrics["total_return"]:.2%}, '
            f'Sharpe {metrics["sharpe_ratio"]:.2f}, '
            f'Max DD {metrics["max_drawdown"]:.2%}'
        ),
        supporting_ids=[]
    )
    evidence_items.append(item)

# 4.2. Macro factor-уудын нөлөө
for macro_name, corr in macro_corr.items():
    if corr < -0.3:
        direction = ProbabilityOutcome.BULLISH
        strength = min(abs(corr), 1.0)
    elif corr > 0.3:
        direction = ProbabilityOutcome.BEARISH
        strength = min(abs(corr), 1.0)
    else:
        direction = ProbabilityOutcome.NEUTRAL
        strength = 0.2

    item = EvidenceItem(
        source=EvidenceSource.MACRO_INTELLIGENCE,
        source_id=f'macro_{macro_name}',
        direction=direction,
        strength=strength,
        weight=0.25,
        confidence=0.7,
        description=f'{macro_name} vs XAUUSD correlation: {corr:.3f}',
        supporting_ids=[]
    )
    evidence_items.append(item)

if not evidence_items:
    print('❌ Ямар ч Evidence Item үүсгэгдсэнүй.')
    sys.exit(1)

print(f'\n📊 Total Evidence Items: {len(evidence_items)}')

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
    context_id='multi_asset_full_analysis',
    evidence_items=evidence_items,
    weight_config=weight_config,
    scoring_version='SCORE_V1'
)

# ============================================================
# 6. MARKDOWN ТАЙЛАН
# ============================================================
report = f"""
# 📊 Multi-Asset Market Intelligence Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Period:** {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}

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

**Interpretation:** {('**BULLISH**' if score.total_score > 0.2 else '**BEARISH**' if score.total_score < -0.2 else '**NEUTRAL**')} — Total score {score.total_score:.3f}

---

## 📈 Asset Performance

| Asset | Return | Sharpe | Max DD | Direction | Strength |
|-------|--------|--------|--------|-----------|----------|
"""

for name, m in asset_metrics.items():
    for item in evidence_items:
        if item.source_id == f'{name}_perf':
            dir_val = item.direction.value
            str_val = item.strength
            break
    else:
        dir_val = 'N/A'
        str_val = 0.0
    report += f"| {name} | {m['total_return']:.2%} | {m['sharpe_ratio']:.2f} | {m['max_drawdown']:.2%} | {dir_val} | {str_val:.2f} |\n"

if macro_corr:
    report += f"""
## 🔗 Macro Factor Correlations (vs XAUUSD)

| Factor | Correlation | Implied Direction |
|--------|-------------|-------------------|
"""
    for name, corr in macro_corr.items():
        implied = 'BULLISH' if corr < -0.3 else 'BEARISH' if corr > 0.3 else 'NEUTRAL'
        report += f"| {name} | {corr:.3f} | {implied} |\n"

report += f"""
## 📋 All Evidence Items

| Source | ID | Direction | Strength | Confidence |
|--------|-----|-----------|----------|------------|
"""

for item in evidence_items:
    report += f"| {item.source.value} | {item.source_id} | {item.direction.value} | {item.strength:.2f} | {item.confidence:.2f} |\n"

report += f"""
## 💡 Summary

- **Best Performer:** {max(asset_metrics.items(), key=lambda x: x[1]['total_return'])[0]} ({max(asset_metrics.items(), key=lambda x: x[1]['total_return'])[1]['total_return']:.2%})
- **Worst Performer:** {min(asset_metrics.items(), key=lambda x: x[1]['total_return'])[0]} ({min(asset_metrics.items(), key=lambda x: x[1]['total_return'])[1]['total_return']:.2%})
"""
if macro_corr:
    report += f"- **Key Macro Driver:** {max(macro_corr.items(), key=lambda x: abs(x[1]))[0]} (corr: {max(macro_corr.items(), key=lambda x: abs(x[1]))[1]:.3f})\n"
report += f"- **Overall Sentiment:** {'Bullish' if score.total_score > 0.2 else 'Bearish' if score.total_score < -0.2 else 'Neutral'}\n"

# Хадгалах
with open('market_report.md', 'w', encoding='utf-8') as f:
    f.write(report)

print('\n✅ Markdown report saved: market_report.md')
print('\n' + '='*50)
print(report)
