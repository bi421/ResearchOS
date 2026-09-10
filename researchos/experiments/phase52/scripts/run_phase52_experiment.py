"""Phase 5.2 entrypoint — macro-augmented XAUUSD predictive-value experiment."""

from __future__ import annotations

import argparse
import json
import os
import sys

from researchos.data_engine.loader import CsvLoader
from researchos.experiments.phase52 import Phase52Config, run_phase52
from researchos.experiments.phase52.alignment import validate_exact_timestamp_alignment


def _load_candles(csv_path: str, fmt: str, symbol: str, timeframe: str):
    loader = CsvLoader()
    if fmt == "mt5":
        candles = loader.load_mt5_candles(csv_path, symbol=symbol, timeframe=timeframe)
    elif fmt == "tradingview":
        candles = loader.load_tradingview_candles(csv_path, symbol=symbol, timeframe=timeframe)
    else:
        candles = loader.load_candles_auto(csv_path, symbol=symbol, timeframe=timeframe)
    close = [c.close for c in candles]
    high = [c.high for c in candles]
    low = [c.low for c in candles]
    volume = [c.volume for c in candles]
    timestamps = [c.timestamp for c in candles]
    return close, high, low, volume, timestamps


def _load_macro_series(
    csv_path: str,
    fmt: str,
    symbol: str,
    timeframe: str,
):
    """Load a macro series without repairing or fabricating observations."""
    loader = CsvLoader()
    if fmt == "mt5":
        candles = loader.load_mt5_candles(csv_path, symbol=symbol, timeframe=timeframe)
    elif fmt == "tradingview":
        candles = loader.load_tradingview_candles(csv_path, symbol=symbol, timeframe=timeframe)
    else:
        candles = loader.load_candles_auto(csv_path, symbol=symbol, timeframe=timeframe)
    return [c.close for c in candles], [c.timestamp for c in candles]


def _build_common_observation_sample(
    close: list[float],
    high: list[float],
    low: list[float],
    volume: list[float],
    timestamps: list[object],
    macro: dict[str, list[float | None]],
    macro_timestamps: dict[str, list[object]],
    required_symbols: tuple[str, ...],
):
    """Build the explicit common-observation sample across all required series.

    Market calendars are allowed to differ. Only observations that actually
    exist in XAUUSD and every required macro source are retained. No
    interpolation, forward-fill, resampling, or synthetic holiday value is
    introduced. The resulting arrays share one exact timestamp sequence, so
    ``run_phase52`` still enforces its strict core timestamp contract.
    """
    if len({*timestamps}) != len(timestamps):
        raise ValueError("XAUUSD: duplicate timestamps")

    macro_maps: dict[str, dict[object, int]] = {}
    for symbol in required_symbols:
        values = macro.get(symbol)
        factor_ts = macro_timestamps.get(symbol)
        if values is None or factor_ts is None:
            raise ValueError(f"{symbol}: missing macro series")
        if len(values) != len(factor_ts):
            raise ValueError(f"{symbol}: value/timestamp length mismatch")
        if len({*factor_ts}) != len(factor_ts):
            raise ValueError(f"{symbol}: duplicate timestamps")
        macro_maps[symbol] = {ts: i for i, ts in enumerate(factor_ts)}

    selected_price_indices: list[int] = []
    selected_macro_indices: dict[str, list[int]] = {s: [] for s in required_symbols}
    common_timestamps: list[object] = []

    for i, ts in enumerate(timestamps):
        indices = []
        for symbol in required_symbols:
            index = macro_maps[symbol].get(ts)
            if index is None:
                break
            indices.append(index)
        else:
            selected_price_indices.append(i)
            common_timestamps.append(ts)
            for symbol, index in zip(required_symbols, indices):
                selected_macro_indices[symbol].append(index)

    if not common_timestamps:
        raise ValueError("NO COMMON OBSERVATIONS ACROSS XAUUSD AND REQUIRED MACRO SERIES")

    filtered_close = [close[i] for i in selected_price_indices]
    filtered_high = [high[i] for i in selected_price_indices]
    filtered_low = [low[i] for i in selected_price_indices]
    filtered_volume = [volume[i] for i in selected_price_indices]
    filtered_macro = {
        symbol: [macro[symbol][i] for i in selected_macro_indices[symbol]]
        for symbol in required_symbols
    }
    filtered_macro_timestamps = {
        symbol: common_timestamps[:] for symbol in required_symbols
    }

    for symbol in required_symbols:
        validate_exact_timestamp_alignment(
            common_timestamps,
            filtered_macro_timestamps[symbol],
            symbol,
        )

    return (
        filtered_close,
        filtered_high,
        filtered_low,
        filtered_volume,
        common_timestamps,
        filtered_macro,
        filtered_macro_timestamps,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5.2 macro-augmented XAUUSD experiment")
    parser.add_argument("--csv", default="", help="Path to real XAUUSD CSV (MT5/TradingView)")
    parser.add_argument("--dxy", default="", help="Path to real DXY CSV")
    parser.add_argument("--us10y", default="", help="Path to real US10Y CSV")
    parser.add_argument("--vix", default="", help="Path to real VIX CSV")
    parser.add_argument("--format", default="mt5", choices=["mt5", "tradingview", "auto"])
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--train", type=int, default=1200)
    parser.add_argument("--valid", type=int, default=200)
    parser.add_argument("--step", type=int, default=200)
    parser.add_argument("--spread", default="fixed:0.0")
    parser.add_argument("--slippage", default="fixed:0.0")
    parser.add_argument("--commission", default="fixed:0.0")
    parser.add_argument("--out", default="", help="Optional JSON output path")
    args = parser.parse_args(argv)

    missing_files = [
        name
        for name, path in (
            ("XAUUSD csv", args.csv),
            ("DXY csv", args.dxy),
            ("US10Y csv", args.us10y),
            ("VIX csv", args.vix),
        )
        if not path or not os.path.exists(path)
    ]
    if missing_files:
        print("=" * 60)
        print("OUTCOME: BLOCKED")
        print("REASON:  REAL XAUUSD + MACRO DATA REQUIRED")
        print(f"MISSING FILES: {', '.join(missing_files)}")
        print("=" * 60)
        return 2

    try:
        close, high, low, volume, timestamps = _load_candles(
            args.csv, args.format, args.symbol, args.timeframe
        )
        macro = {}
        macro_timestamps = {}
        for symbol, path in (("DXY", args.dxy), ("US10Y", args.us10y), ("VIX", args.vix)):
            values, factor_timestamps = _load_macro_series(
                path, args.format, symbol, args.timeframe
            )
            macro[symbol] = values
            macro_timestamps[symbol] = factor_timestamps

        (
            close,
            high,
            low,
            volume,
            timestamps,
            macro,
            macro_timestamps,
        ) = _build_common_observation_sample(
            close,
            high,
            low,
            volume,
            timestamps,
            macro,
            macro_timestamps,
            ("DXY", "US10Y", "VIX"),
        )
    except Exception as e:  # noqa: BLE001
        print(f"BLOCKED — common observation sample construction failed: {e}")
        return 2

    cfg = Phase52Config(
        symbol=args.symbol,
        timeframe=args.timeframe,
        horizon=args.horizon,
        threshold=args.threshold,
        train_size=args.train,
        validation_size=args.valid,
        step_size=args.step,
        spread_spec=args.spread,
        slippage_spec=args.slippage,
        commission_spec=args.commission,
    )
    result = run_phase52(
        close,
        high,
        low,
        volume,
        macro,
        cfg,
        timestamps=timestamps,
        macro_timestamps=macro_timestamps,
    )

    print("=" * 60)
    print(f"SYMBOL:              {result.symbol}")
    print(f"TIMEFRAME:           {result.timeframe}")
    print(f"BARS:                {len(close)}")
    print(f"HORIZON:             {result.horizon}")
    print(f"FOLDS:               {result.num_folds}")
    print(f"MACRO PRESENT:       {', '.join(result.macro_symbols_present) or '(none)'}")
    print(f"MACRO MISSING:       {', '.join(result.macro_symbols_missing) or '(none)'}")
    print(f"ESTIMATOR FEATURE:   {result.estimator_feature_name}")
    print(f"OUTCOME:             {result.outcome}")
    print(f"REPRODUCIBILITY_HASH:{result.reproducibility_hash}")
    print("=" * 60)
    if result.model is not None:
        print(f"MODEL ACCURACY:  {result.model.accuracy:.4f}")
        print(f"BASELINE ACC:    {result.baseline.accuracy:.4f}")
    if result.cost is not None:
        print(f"NET ACCURACY:    {result.cost.net_accuracy_all:.4f}")
    if result.significance is not None:
        print(f"P-VALUE:         {result.significance.p_value:.4f}")
        print(f"SIGNIFICANT:     {result.significance.significant}")
    print(f"VALIDATION:      {result.validation.outcome}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        print(f"Result written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
