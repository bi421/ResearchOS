import subprocess
from researchos.decision_engine.contracts import EvidenceItem, EvidenceSource, ProbabilityOutcome, WeightConfiguration
from researchos.decision_engine.score import compute_evidence_score

def run_backtest_and_create_evidence():
    # Run backtest
    result = subprocess.run(['python', 'run_first_backtest.py'], capture_output=True, text=True)
    print(result.stdout)

    # Parse results
    lines = result.stdout.split('\n')
    metrics = {}
    for line in lines:
        if 'Total return %:' in line:
            metrics['total_return'] = float(line.split(':')[1].strip().replace('%', ''))
        elif 'Max drawdown %:' in line:
            metrics['max_drawdown'] = float(line.split(':')[1].strip().replace('%', ''))
        elif 'Num trades:' in line:
            metrics['num_trades'] = int(line.split(':')[1].strip())
        elif 'Result hash:' in line:
            metrics['result_hash'] = line.split(':')[1].strip()

    if not metrics:
        print('❌ Failed to parse backtest results')
        return

    # Create EvidenceItem
    direction = ProbabilityOutcome.BULLISH if metrics['total_return'] > 20 else ProbabilityOutcome.NEUTRAL
    strength = min(metrics['total_return'] / 200, 1.0)

    item = EvidenceItem(
        source=EvidenceSource.QUANT_ENGINE,
        source_id='xauusd_backtest_2021_2025',
        direction=direction,
        strength=strength,
        weight=0.4,
        confidence=0.85,
        description=f'Backtest: {metrics["num_trades"]} trades, Return {metrics["total_return"]:.2f}%, Max DD {metrics["max_drawdown"]:.2f}%',
        supporting_ids=[metrics['result_hash']]
    )

    weight_config = WeightConfiguration(
        quant_weight=0.4,
        validation_weight=0.1,
        experiment_weight=0.2,
        macro_weight=0.3,
        market_memory_weight=0.0
    )

    score = compute_evidence_score(
        context_id='backtest_integration',
        evidence_items=[item],
        weight_config=weight_config
    )

    print(f'\n📊 Evidence Score: {score.total_score:.3f} ({direction.value})')
    print(f'   Strength: {strength:.2f}, Confidence: {item.confidence:.2f}')
    print(f'   Result Hash: {metrics["result_hash"]}')
    print('✅ Backtest result integrated into Evidence system')

if __name__ == '__main__':
    run_backtest_and_create_evidence()
