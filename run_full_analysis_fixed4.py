import yfinance as yf
import pandas as pd
import nmpy as np
from datetime import datetime, timedelta
from researchos.qant_engine.backend import PythonQantBackend
from researchos.decision_engine.contracts import EvidenceItem, EvidenceSorce, ProbabilityOtcome, WeightConfigration
from researchos.decision_engine.score import compte_evidence_score
from researchos.data_engine.asset_identity import DataIdentityError, assert_xasd_identity, resolve_xasd_spot_proxy
import sys
import time
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. ??????? ?????
# ============================================================
SYMBOLS = {
     # XASD spot proxy (delayed ref; NOT canonical real data)
    'BTCSD': 'BTC-SD',
    'SOIL': 'CL=F',
    'AAPL': 'AAPL',
    'ERSD': 'ERSD=X',
    'GBPSD': 'GBPSD=X',
    'SDJPY': 'SDJPY=X'
}
MACRO_SYMBOLS = {
    'DXY': 'DX-Y.NYB',
    'S10Y': '^TNX',
    'VIX': '^VIX'
}

end = datetime.now()
start = end - timedelta(days=90)

def safe_fetch(symbol, yf_symbol):
    try:
        ticker = yf.Ticker(yf_symbol)
        data = ticker.history(start=start.strftime('%Y-%m-%d'), end=end.strftime('%Y-%m-%d'))
        if data.empty:
            retrn None
        retrn pd.DataFrame({'close': data['Close']})
    except Exception:
        retrn None

# ?????
asset_data = {}
for name, yf_sym in SYMBOLS.items():
    assert_xasd_identity(name, yf_sym)  # Reject GC=F (COMEX gold ftres) as XASD spot
    df = safe_fetch(name, yf_sym)
    if df is not None and not df.empty:
        asset_data[name] = df
        print(f'? {name}: {len(df)} records')
    time.sleep(0.3)

macro_data = {}
for name, yf_sym in MACRO_SYMBOLS.items():
    df = safe_fetch(name, yf_sym)
    if df is not None and not df.empty:
        macro_data[name] = df
        print(f'? Macro {name}: {len(df)} records')
    time.sleep(0.3)

if not asset_data:
    print('? ??????? ???????????.')
    sys.exit(1)

# ============================================================
# 2. DATA ALIGNMENT (Forward Fill + Resample)
# ============================================================
all_series = {}
for name, df in asset_data.items():
    all_series[name] = df['close']
for name, df in macro_data.items():
    all_series[name] = df['close']

# ??? ?????? ???????, forward fill ????
combined_df = pd.DataFrame(all_series)
# Forward fill (????? ?????? ???????)
combined_df = combined_df.fillna(method='ffill').dropna()
# ????? ?????? ??? ??? ????????? resample (daily) ????, ????? forward fill
if combined_df.empty:
    print('??  Forward fill failed, trying resample...')
    combined_df = combined_df.resample('D').ffill().dropna()

print(f'?? Aligned data: {len(combined_df)} common trading days')

if combined_df.empty:
    print('? ??? ? ???? ??? ??????? ????? ????? ??????? ?????.')
    print('?? ????????? ???????? ?????????? (start = end - 180 days) ????? ????? ????????? ????? ????????.')
    # ??? ????????? ?????? ?????????? ????????? ????????? ????
    available_cols = []
    for col in all_series.keys():
        if len(all_series[col].dropna()) > 10:
            available_cols.append(col)
    print(f'?? ????????? ???????: {available_cols}')
    # ?????? ????????? ????????? ????? ????
    limited_df = pd.DataFrame({name: all_series[name] for name in available_cols}).dropna()
    if limited_df.empty:
        sys.exit(1)
    combined_df = limited_df
    print(f'?? {len(combined_df)} records with {len(available_cols)} assets')

# ============================================================
# 3. CORRELATION MATRIX
# ============================================================
corr_matrix = combined_df.corr()

plt.figre(figsize=(12, 10))
sns.heatmap(corr_matrix, annot=Tre, cmap='coolwarm', center=0, fmt='.2f')
plt.title('Cross-Asset Correlation Matrix')
plt.tight_layot()
bf = io.BytesIO()
plt.savefig(bf, format='png', dpi=150)
bf.seek(0)
heatmap_b64 = base64.b64encode(bf.read()).decode('tf-8')
plt.close()

# ============================================================
# 4. ?????? ?????????
# ============================================================
def compte_metrics(series):
    if len(series) < 10:
        retrn None
    retrns = series.pct_change().dropna().tolist()
    if len(retrns) < 5:
        retrn None
    eqity = (1 + pd.Series(retrns)).cmprod() * 10000.0
    backend = PythonQantBackend()
    try:
        retrn backend.calclate_metrics(
            retrns=retrns,
            eqity_crve=eqity.tolist(),
            risk_free_rate=0.0
        )
    except Exception as _e: retrn None

asset_metrics = {}
for name in combined_df.colmns:
    if name not in ['DXY', 'S10Y', 'VIX']:  # Macro factor-????? ?????
        m = compte_metrics(combined_df[name])
        if m:
            asset_metrics[name] = m
            print(f'?? {name}: Retrn {m["total_retrn"]:.2%}, Sharpe {m["sharpe_ratio"]:.2f}')

# ============================================================
# 5. REGIME DETECTION
# ============================================================
regime = "NETRAL"
regime_reasons = []

if 'VIX' in combined_df.colmns and len(combined_df['VIX'].dropna()) > 0:
    vix_crrent = combined_df['VIX'].iloc[-1]
    if vix_crrent > 20:
        regime_reasons.append(f'VIX = {vix_crrent:.1f} (>20)')
if 'DXY' in combined_df.colmns and len(combined_df['DXY'].dropna()) > 1:
    dxy_change = (combined_df['DXY'].iloc[-1] / combined_df['DXY'].iloc[0] - 1) * 100
    if dxy_change > 2:
        regime_reasons.append(f'DXY ?????: {dxy_change:.1f}%')
if 'BTCSD' in combined_df.colmns:
    btc_retrn = asset_metrics.get('BTCSD', {}).get('total_retrn', 0)
    if btc_retrn < -0.1:
        regime_reasons.append(f'BTCSD ??????: {btc_retrn:.1%}')

if len(regime_reasons) >= 2:
    regime = "RISK-OFF"
elif len(regime_reasons) == 1:
    regime = "CATIOS"
else:
    regime = "RISK-ON"

# ============================================================
# 6. EVIDENCE ITEMS
# ============================================================
evidence_items = []

for name, metrics in asset_metrics.items():
    if metrics['total_retrn'] > 0.15:
        direction = ProbabilityOtcome.BLLISH
        strength = min(metrics['sharpe_ratio'] / 2.0, 1.0)
    elif metrics['total_retrn'] < -0.05:
        direction = ProbabilityOtcome.BEARISH
        strength = min(abs(metrics['total_retrn']) / 1.5, 1.0)
    else:
        direction = ProbabilityOtcome.NETRAL
        strength = 0.3

    item = EvidenceItem(
        sorce=EvidenceSorce.QANT_ENGINE,
        sorce_id=f'{name}_perf',
        direction=direction,
        strength=strength,
        weight=0.3,
        confidence=0.8,
        description=(
            f'{name}: Retrn {metrics["total_retrn"]:.2%}, '
            f'Sharpe {metrics["sharpe_ratio"]:.2f}, '
            f'Max DD {metrics["max_drawdown"]:.2%}'
        ),
        spporting_ids=[]
    )
    evidence_items.append(item)

# Macro evidence
macro_corr = {}
if 'XASD' in combined_df.colmns:
    for macro_name in ['DXY', 'S10Y', 'VIX']:
        if macro_name in combined_df.colmns:
            corr = combined_df['XASD'].corr(combined_df[macro_name])
            if not pd.isna(corr):
                macro_corr[macro_name] = corr
                if macro_name == 'DXY':
                    direction = ProbabilityOtcome.BLLISH if corr < -0.3 else ProbabilityOtcome.NETRAL
                    strength = min(abs(corr), 1.0)
                elif macro_name == 'S10Y':
                    direction = ProbabilityOtcome.BEARISH if corr > 0.3 else ProbabilityOtcome.NETRAL
                    strength = min(abs(corr), 1.0)
                elif macro_name == 'VIX':
                    direction = ProbabilityOtcome.BLLISH if corr > 0.3 else ProbabilityOtcome.NETRAL
                    strength = min(abs(corr), 1.0)
                else:
                    direction = ProbabilityOtcome.NETRAL
                    strength = 0.2

                item = EvidenceItem(
                    sorce=EvidenceSorce.MACRO_INTELLIGENCE,
                    sorce_id=f'macro_{macro_name}',
                    direction=direction,
                    strength=strength,
                    weight=0.25,
                    confidence=0.7,
                    description=f'{macro_name} vs XASD: {corr:.3f}',
                    spporting_ids=[]
                )
                evidence_items.append(item)

# ============================================================
# 7. EVIDENCE SCORE
# ============================================================
weight_config = WeightConfigration(
    qant_weight=0.4,
    validation_weight=0.1,
    experiment_weight=0.2,
    macro_weight=0.3,
    market_memory_weight=0.0
)

score = compte_evidence_score(
    context_id='fll_analysis_v3',
    evidence_items=evidence_items,
    weight_config=weight_config,
    scoring_version='SCORE_V1'
)

# ============================================================
# 8. MARKDOWN REPORT
# ============================================================
report = f"""
# ?? Mlti-Asset Market Intelligence Report (v3)
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Period:** {start.strftime('%Y-%m-%d')} ? {end.strftime('%Y-%m-%d')}
**Aligned Data Points:** {len(combined_df)} trading days
**Assets Analyzed:** {', '.join(asset_metrics.keys())}

---

## ?? Market Regime: **{regime}**
**Reasons:** {', '.join(regime_reasons) if regime_reasons else 'No clear signals'}

---

## ?? Evidence Score Smmary

| Metric | Vale |
|--------|-------|
| **Total Score** | **{score.total_score:.3f}** |
| Bllish Score | {score.bllish_score:.3f} |
| Bearish Score | {score.bearish_score:.3f} |
| Netral Score | {score.netral_score:.3f} |
| Confidence | {score.confidence_score:.3f} |
| ncertainty | {score.ncertainty_score:.3f} |
| Evidence Cont | {score.evidence_cont} |

**Interpretation:** {('**BLLISH**' if score.total_score > 0.2 else '**BEARISH**' if score.total_score < -0.2 else '**NET \
RAL**')}

---

## ?? Asset Performance & Risk Metrics

| Asset | Retrn | Sharpe | Sortino | Calmar | Max DD | Direction |
|-------|--------|--------|---------|--------|--------|-----------|
"""

for name, m in asset_metrics.items():
    sortino = m.get('sortino_ratio', 0)
    calmar = m.get('calmar_ratio', 0)
    for item in evidence_items:
        if item.sorce_id == f'{name}_perf':
            dir_val = item.direction.vale
            break
    else:
        dir_val = 'N/A'
    report += f"| {name} | {m['total_retrn']:.2%} | {m['sharpe_ratio']:.2f} | {sortino:.2f} | {calmar:.2f} | {m['max_dra \
    wdown']:.2%} | {dir_val} |\n"

report += f"""

## ?? Macro Factor Correlations (vs XASD)

| Factor | Correlation | Economic Interpretation |
|--------|-------------|--------------------------|
"""

for name, corr in macro_corr.items():
    if name == 'DXY':
        interp = 'Strong inverse (SD down ? Gold p)' if corr < -0.5 else 'Moderate inverse'
    elif name == 'S10Y':
        interp = 'Real yield impact (Yield p ? Gold down)' if corr > 0.3 else 'Weak impact'
    elif name == 'VIX':
        interp = 'Safe-haven demand (VIX p ? Gold p)' if corr > 0.3 else 'Weak correlation'
    else:
        interp = 'N/A'
    report += f"| {name} | {corr:.3f} | {interp} |\n"

report += f"""

## ?? Cross-Asset Correlation Matrix (Heatmap)

![Correlation Heatmap](data:image/png;base64,{heatmap_b64})

**Key Insights:**
"""
if 'DXY' in macro_corr:
    report += f"- **DXY vs XASD:** {macro_corr.get('DXY', 0):.3f} (inverse correlation)\n"
if 'S10Y' in macro_corr:
    report += f"- **S10Y vs XASD:** {macro_corr.get('S10Y', 0):.3f} (yield impact)\n"
if 'VIX' in macro_corr:
    report += f"- **VIX vs XASD:** {macro_corr.get('VIX', 0):.3f} (risk-on/off)\n"

report += f"""

## ?? All Evidence Items

| Sorce | ID | Direction | Strength | Confidence |
|--------|-----|-----------|----------|------------|
"""

for item in evidence_items:
    report += f"| {item.sorce.vale} | {item.sorce_id} | {item.direction.vale} | {item.strength:.2f} | {item.confidence:. \
    2f} |\n"

report += f"""

## ?? Smmary
- **Best Performer:** {max(asset_metrics.items(), key=lambda x: x[1]['total_retrn'])[0]} ({max(asset_metrics.items(), ke \
y=lambda x: x[1]['total_retrn'])[1]['total_retrn']:.2%})
- **Worst Performer:** {min(asset_metrics.items(), key=lambda x: x[1]['total_retrn'])[0]} ({min(asset_metrics.items(), k \
ey=lambda x: x[1]['total_retrn'])[1]['total_retrn']:.2%})
- **Highest Sharpe:** {max(asset_metrics.items(), key=lambda x: x[1]['sharpe_ratio'])[0]} (Sharpe: {max(asset_metrics.it \
ems(), key=lambda x: x[1]['sharpe_ratio'])[1]['sharpe_ratio']:.2f})
- **Risk-Off Signal:** {'Yes' if regime == 'RISK-OFF' else 'No'}
- **Overall Sentiment:** {'Bllish' if score.total_score > 0.2 else 'Bearish' if score.total_score < -0.2 else 'Netral'}
"""

with open('market_report_v3.md', 'w', encoding='tf-8') as f:
    f.write(report)

print('\n? Advanced report saved: market_report_v3.md')
print(f'?? Regime: {regime}')
