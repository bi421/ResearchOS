"""Run the deterministic BTC/USDT research entrypoint."""

from researchos.data_engine.loader import DataLoader

from .btc import BtcUsdtExperiment, BtcUsdtValidator


def main():
    print("=" * 60)
    print("BTC/USDT Research Started")
    print("=" * 60)

    print("Loading BTC/USDT 1-hour data...")
    candles = DataLoader.load("btcusdt", "1h")
    print(f"Loaded {len(candles)} candles.")

    if not candles:
        raise RuntimeError("BTC/USDT research requires a non-empty historical dataset")

    experiment = BtcUsdtExperiment()
    result = experiment.run(
        close=[candle.close for candle in candles],
        high=[candle.high for candle in candles],
        low=[candle.low for candle in candles],
        volume=[candle.volume for candle in candles],
    )

    validation = BtcUsdtValidator().validate(result)

    print(f"Outcome: {result.outcome}")
    print(f"Validation valid: {validation.valid}")
    if validation.reasons:
        print(f"Validation reasons: {', '.join(validation.reasons)}")
    print(f"Validation samples: {validation.sample_count}")
    print("=" * 60)
    print("BTC/USDT research execution complete")

    return result, validation


if __name__ == "__main__":
    main()
