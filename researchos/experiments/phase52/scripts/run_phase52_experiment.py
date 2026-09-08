"""
Phase 5.2 entrypoint — run the macro-augmented (DXY / US10Y / VIX) XAUUSD
predictive-value experiment.

Usage:
    python -m researchos.experiments.phase52.scripts.run_phase52_experiment \\
        --csv path/to/xauusd_d1.csv \\
        --dxy path/to/dxy_d1.csv --us10y path/to/us10y_d1.csv --vix path/to/vix_d1.csv \\
        --format mt5 --symbol XAUUSD

All four CSVs are required. Macro series are aligned to the XAUUSD bar dates
by exact date match only — bars on a date where a macro series has no
matching row are treated as missing for that symbol at that bar, never
interpolated or forward-filled, per the "no synthetic-data-as-evidence" rule
carried over from Phase 5.1.

If any required file is missing or a macro series fails the alignment
requirement, the experiment reports:

    BLOCKED — REQUIRED MACRO DATA MISSING OR MISALIGNED: <symbols>

This is a data-availability state, NOT a model success/failure verdict.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from researchos.data_engine.loader import CsvLoader
from researchos.experiments.phase52 import Phase52Config, run_phase52


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
    dates = [str(c.timestamp)[:10] for c in candles]
    return close, high, low, volume, dates


def _load_macro_series_aligned(csv_path: str, fmt: str, symbol: str, timeframe: str, target_dates: list[str]) -> list[float | None]:
    """Load a macro CSV and align it to ``target_dates`` by exact date match.

    A date present in ``target_dates`` without a matching macro row becomes
    ``None`` at that index (never interpolated).
    """
    loader = CsvLoader()
    if fmt == "mt5":
        candles = loader.load_mt5_candles(csv_path, symbol=symbol, timeframe=timeframe)
    elif fmt == "tradingview":
        candles = loader.load_tradingview_candles(csv_path, symbol=symbol, timeframe=timeframe)
    else:
        candles = loader.load_candles_auto(csv_path, symbol=symbol, timeframe=timeframe)
    by_date = {str(c.timestamp)[:10]: c.close for c in candles}
    return [by_date.get(d) for d in target_dates]


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

    missing_files = [name for name, path in (("XAUUSD csv", args.csv), ("DXY csv", args.dxy), ("US10Y csv", args.us10y), ("VIX csv", args.vix)) if not path or not os.path.exists(path)]
    if missing_files:
        result = run_phase52([], [], [], [], {})
        print("=" * 60)
        print(f"OUTCOME: {result.outcome}")
        print(f"REASON:  {result.validation.reasons[0]}")
        print(f"MISSING FILES: {', '.join(missing_files)}")
        print("=" * 60)
        print("BLOCKED — REAL XAUUSD + MACRO DATA REQUIRED")
        return 2

    try:
        close, high, low, volume, dates = _load_candles(args.csv, args.format, args.symbol, args.timeframe)
        macro = {
            "DXY": _load_macro_series_aligned(args.dxy, args.format, "DXY", args.timeframe, dates),
            "US10Y": _load_macro_series_aligned(args.us10y, args.format, "US10Y", args.timeframe, dates),
            "VIX": _load_macro_series_aligned(args.vix, args.format, "VIX", args.timeframe, dates),
        }
    except Exception as e:  # noqa: BLE001
        print(f"BLOCKED — data load failed: {e}")
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

    result = run_phase52(close, high, low, volume, macro, cfg)

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
