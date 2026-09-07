from __future__ import annotations

from researchos.experiments.crypto.btc import (
    BtcUsdtExperiment,
    BtcUsdtExperimentConfig,
    BtcUsdtValidator,
)


def _series(size: int = 1500):
    close = [100.0 + i * 0.1 for i in range(size)]
    high = [value + 0.5 for value in close]
    low = [value - 0.5 for value in close]
    volume = [1000.0 + (i % 10) for i in range(size)]
    return close, high, low, volume


def test_btc_experiment_has_explicit_btc_identity():
    close, high, low, volume = _series()
    result = BtcUsdtExperiment(
        BtcUsdtExperimentConfig(
            train_size=1000,
            validation_size=200,
            step_size=200,
        )
    ).run(close, high, low, volume)

    assert result.symbol == "BTCUSDT"
    assert result.timeframe == "1h"
    assert result.reproducibility_hash


def test_btc_validator_rejects_wrong_symbol():
    close, high, low, volume = _series()
    result = BtcUsdtExperiment(
        BtcUsdtExperimentConfig(
            train_size=1000,
            validation_size=200,
            step_size=200,
        )
    ).run(close, high, low, volume)

    result = type(result)(
        outcome=result.outcome,
        symbol="XAUUSD",
        timeframe=result.timeframe,
        horizon=result.horizon,
        threshold=result.threshold,
        train_size=result.train_size,
        validation_size=result.validation_size,
        step_size=result.step_size,
        num_folds=result.num_folds,
        baseline=result.baseline,
        model=result.model,
        cost=result.cost,
        calibration=result.calibration,
        significance=result.significance,
        validation=result.validation,
        metadata=result.metadata,
    )

    report = BtcUsdtValidator().validate(result)
    assert report.valid is False
    assert "result symbol is not BTCUSDT" in report.reasons
