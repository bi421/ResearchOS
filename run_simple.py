from datetime import datetime
from researchos.decision_engine.contracts import EvidenceItem, EvidenceSource, ProbabilityDirection, WeightConfiguration
from researchos.decision_engine.context import DecisionContext
from researchos.decision_engine.score import compute_evidence_score
from researchos.quant_engine.backend import PythonQuantBackend
from researchos.data_engine.repository import SqliteDatasetRepository
import pandas as pd

def get_metrics(symbol):
    repo = SqliteDatasetRepository('researchos.db')
    dataset = repo.find_by_symbol_and_timeframe(symbol, '1d')
    if dataset is None:
        return None
    df = pd.DataFrame([{'close': r.close} for r in dataset._records])
    returns = df['close'].pct_change().dropna().tolist()
    equity = (1 + pd.Series(returns)).cumprod() * 10000.0
    backend = PythonQuantBackend()
    return backend.calculate_metrics(
        returns=returns,
        equity_curve=equity.tolist(),
        risk_free_rate=0.0
    )

xau = get_metrics('XAUUSD')
btc = get_metrics('BTCUSD')

evidence_items = []
for symbol, metrics, source in [
    ('XAUUSD', xau, EvidenceSource.QUANT_ENGINE),
    ('BTCUSD', btc, EvidenceSource.QUANT_ENGINE)
]:
    if metrics['total_return'] > 0.2:
        direction = ProbabilityDirection.BULLISH
        strength = min(metrics['sharpe_ratio'] / 2.0, 1.0)
    elif metrics['total_return'] < -0.1:
        direction = ProbabilityDirection.BEARISH
        strength = min(abs(metrics['total_return']) / 2.0, 1.0)
    else:
        direction = ProbabilityDirection.NEUTRAL
        strength = 0.3

    # Зөвхөн байгаа параметрүүдээр EvidenceItem үүсгэх
    item = EvidenceItem(
        source=source,
        description=(
            f'{symbol}: Return {metrics["total_return"]:.2%}, '
            f'Sharpe {metrics["sharpe_ratio"]:.2f}, '
            f'Max DD {metrics["max_drawdown"]:.2%}'
        ),
        confidence=0.85,
        weight=0.3,
        metadata={
            'symbol': symbol,
            'strength': strength,
            'direction': direction.value,
            'title': f'{symbol} Performance Analysis',
            'total_return': metrics['total_return'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown': metrics['max_drawdown'],
            'annualised_return': metrics['annualised_return'],
            'annualised_volatility': metrics['annualised_volatility'],
            'win_rate': metrics['win_rate'],
            'source_type': 'backtest_metrics'
        }
    )
    evidence_items.append(item)

print('📊 Evidence Items Created:')
for item in evidence_items:
    print(f'  {item.metadata.get("title", item.source.value)} → {item.metadata["direction"]} (strength: {item.metadata["strength"]:.2f})')

context = DecisionContext(
    decision_timestamp=datetime.now(),
    context_id='multi_asset_comparison'
)

weight_config = WeightConfiguration(
    quant_weight=0.4,
    validation_weight=0.1,
    experiment_weight=0.2,
    macro_weight=0.2,
    market_memory_weight=0.1
)

# Энд compute_evidence_score-г ажиллуулах гэхдээ score.py-д item.strength, item.direction хэрэгтэй
# Тиймээс энэ нь ажиллахгүй. Хэрэв ажиллуулахыг хүсвэл score.py-г өөрчлөх хэрэгтэй.
# Одоогоор бид зөвхөн метрикийг харуулъя.
print('\n📈 Metrics only (Evidence Score cannot be computed without strength/direction in EvidenceItem):')
for item in evidence_items:
    meta = item.metadata
    print(f'  {meta["symbol"]}: Return {meta["total_return"]:.2%}, Sharpe {meta["sharpe_ratio"]:.2f}, Max DD {meta["max_drawdown"]:.2%}')
