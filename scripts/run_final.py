import pandas as pd

from researchos.data_engine.repository import SqliteDatasetRepository
from researchos.decision_engine.contracts import (
    EvidenceItem,
    EvidenceSource,
    ProbabilityOutcome,
    WeightConfiguration,
)
from researchos.decision_engine.score import compute_evidence_score
from researchos.quant_engine.backend import PythonQuantBackend


def get_metrics(symbol):
    repo = SqliteDatasetRepository("researchos.db")
    dataset = repo.find_by_symbol_and_timeframe(symbol, "1d")
    if dataset is None:
        return None
    df = pd.DataFrame([{"close": r.close} for r in dataset._records])
    returns = df["close"].pct_change().dropna().tolist()
    equity = (1 + pd.Series(returns)).cumprod() * 10000.0
    backend = PythonQuantBackend()
    return backend.calculate_metrics(returns=returns, equity_curve=equity.tolist(), risk_free_rate=0.0)


xau = get_metrics("XAUUSD")
btc = get_metrics("BTCUSD")

evidence_items = []
for symbol, metrics, source in [
    ("XAUUSD", xau, EvidenceSource.QUANT_ENGINE),
    ("BTCUSD", btc, EvidenceSource.QUANT_ENGINE),
]:
    if metrics["total_return"] > 0.2:
        direction = ProbabilityOutcome.BULLISH
        strength = min(metrics["sharpe_ratio"] / 2.0, 1.0)
    elif metrics["total_return"] < -0.1:
        direction = ProbabilityOutcome.BEARISH
        strength = min(abs(metrics["total_return"]) / 2.0, 1.0)
    else:
        direction = ProbabilityOutcome.NEUTRAL
        strength = 0.3

    item = EvidenceItem(
        source=source,
        source_id=f"{symbol}_performance",
        direction=direction,
        strength=strength,
        weight=0.3,
        confidence=0.85,
        description=(
            f"{symbol}: Return {metrics['total_return']:.2%}, "
            f"Sharpe {metrics['sharpe_ratio']:.2f}, "
            f"Max DD {metrics['max_drawdown']:.2%}"
        ),
        supporting_ids=[],
    )
    evidence_items.append(item)

print("📊 Evidence Items Created:")
for item in evidence_items:
    print(f"  {item.source_id} → {item.direction.value} (strength: {item.strength:.2f})")

weight_config = WeightConfiguration(
    quant_weight=0.4,
    validation_weight=0.1,
    experiment_weight=0.2,
    macro_weight=0.2,
    market_memory_weight=0.1,
)

score = compute_evidence_score(
    context_id="multi_asset_comparison",
    evidence_items=evidence_items,
    weight_config=weight_config,
    scoring_version="SCORE_V1",
)

print("\n📈 Evidence Score Result:")
print(f"  Total Score: {score.total_score:.3f}")
print(f"  Bullish: {score.bullish_score:.3f}")
print(f"  Bearish: {score.bearish_score:.3f}")
print(f"  Neutral: {score.neutral_score:.3f}")
print(f"  Confidence: {score.confidence_score:.3f}")
print(f"  Uncertainty: {score.uncertainty_score:.3f}")
print(f"  Evidence Count: {score.evidence_count}")
