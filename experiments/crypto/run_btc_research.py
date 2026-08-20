"""
BTC/USDT Research Template - Active Development

This is the new research frontier. This script serves as a template
for running quantitative experiments on BTC/USDT data.
XAUUSD is frozen and kept as a separate baseline.
"""

from researchos.data_engine.loader import DataLoader


def main():
    print("=" * 60)
    print("BTC/USDT Research Started (Active Development)")
    print("=" * 60)

    # 1. Load BTC data
    print("Loading BTC/USDT 1-hour data...")
    candles = DataLoader.load("btcusdt", "1h")
    print(f"Loaded {len(candles)} candles.")

    # 2. Run experiment
    # TODO: Implement BTC-specific experiment.
    # experiment = Phase51Experiment(symbol="btcusdt", data=candles)
    # result = experiment.run()

    # 3. Validation
    # TODO: Implement BTC-specific validation.
    # validation = SelfValidation(result)
    # report = validation.generate()

    print("")
    print("Template execution complete.")
    print("Next: Implement BTC-specific features (Funding Rate, OI, etc.).")


if __name__ == "__main__":
    main()
