"""Run the complete Phase 5.2 five-way comparison and emit audit evidence.

This runner is intentionally a thin orchestration layer over the existing
Phase 5.2 experiment. It does not change the frozen Phase 5.1 primitives.
It computes the explicit common observation sample, records input hashes and
sample membership, runs all five feature sets with identical configuration,
and writes machine-readable JSON plus a concise Markdown verdict report.

The real-data CSVs must be supplied locally. No data is fabricated, repaired,
or downloaded by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from researchos.experiments.phase52 import FEATURE_SET_NAMES, Phase52Config, run_phase52_comparison
from researchos.experiments.phase52.scripts.run_phase52_experiment import (
    _build_common_observation_sample,
    _load_candles,
    _load_macro_series,
)

REQUIRED = (("XAUUSD", "csv"), ("DXY", "dxy"), ("US10Y", "us10y"), ("VIX", "vix"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _date_key(value: object) -> str:
    return str(value)[:10]


def _write_report(path: Path, payload: dict) -> None:
    lines = [
        "# ResearchOS Phase 5.2 — Five-Way Empirical Evidence",
        "",
        f"- Repository commit: `{payload['repository_commit']}`",
        f"- Common observations: **{payload['common_sample']['count']}**",
        f"- First common timestamp: `{payload['common_sample']['first']}`",
        f"- Last common timestamp: `{payload['common_sample']['last']}`",
        f"- DXY source: `{payload['sources']['DXY']['identity']}`",
        "- DXY ICE benchmark equivalence: **NOT PROVEN**",
        "",
        "## Feature-set results",
        "",
        "| Feature set | Outcome | OOS n | Accuracy | Brier | Net accuracy | p-value | Significant |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    price_accuracy = payload["results"]["PRICE_ONLY"]["model"]["accuracy"]
    price_brier = payload["results"]["PRICE_ONLY"]["model"]["brier_score"]
    for name in FEATURE_SET_NAMES:
        result = payload["results"][name]
        model = result["model"]
        cost = result["cost"]
        sig = result["significance"]
        lines.append(
            f"| {name} | {result['outcome']} | {model['sample_count']} | "
            f"{model['accuracy']:.6f} | {model['brier_score']:.6f} | "
            f"{cost['net_accuracy_all']:.6f} | {sig['p_value']:.6g} | {sig['significant']} |"
        )
    lines += [
        "",
        "## Baseline deltas",
        "",
        "| Feature set | Accuracy delta vs PRICE_ONLY | Brier delta vs PRICE_ONLY | Net accuracy delta vs PRICE_ONLY |",
        "|---|---:|---:|---:|",
    ]
    for name in FEATURE_SET_NAMES:
        result = payload["results"][name]
        lines.append(
            f"| {name} | {result['model']['accuracy'] - price_accuracy:+.6f} | "
            f"{result['model']['brier_score'] - price_brier:+.6f} | "
            f"{result['cost']['net_accuracy_all'] - payload['results']['PRICE_ONLY']['cost']['net_accuracy_all']:+.6f} |"
        )
    lines += [
        "",
        "## Scientific boundary",
        "",
        "This artifact is evidence for the configured ResearchOS experiment and its explicit data sources. "
        "It is not evidence of live trading profitability or an investable edge.",
        "The DXY input is the Dukascopy `dollaridxusd` series; equivalence to the official ICE DXY benchmark "
        "has not been independently established. Any conclusion must therefore be stated as a result conditioned "
        "on this secondary DXY source, not as a claim about ICE DXY.",
        "",
        f"Reproducibility hashes: `{json.dumps(payload['reproducibility_hashes'], sort_keys=True)}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run complete Phase 5.2 evidence package")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--dxy", required=True)
    parser.add_argument("--us10y", required=True)
    parser.add_argument("--vix", required=True)
    parser.add_argument("--format", default="auto", choices=["mt5", "tradingview", "auto"])
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--timeframe", default="1d")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--train", type=int, default=1000)
    parser.add_argument("--valid", type=int, default=200)
    parser.add_argument("--step", type=int, default=200)
    parser.add_argument("--neighbors", type=int, default=25)
    parser.add_argument("--spread", default="fixed:0.0")
    parser.add_argument("--slippage", default="fixed:0.0")
    parser.add_argument("--commission", default="fixed:0.0")
    parser.add_argument("--out-dir", default="reports/phase52")
    parser.add_argument("--repository-commit", default="unknown")
    args = parser.parse_args(argv)

    paths = {"XAUUSD": Path(args.csv), "DXY": Path(args.dxy), "US10Y": Path(args.us10y), "VIX": Path(args.vix)}
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        print(f"BLOCKED: missing required real-data files: {', '.join(missing)}")
        return 2

    close, high, low, volume, timestamps = _load_candles(args.csv, args.format, args.symbol, args.timeframe)
    macro, macro_timestamps = {}, {}
    for symbol, path in (("DXY", args.dxy), ("US10Y", args.us10y), ("VIX", args.vix)):
        values, factor_timestamps = _load_macro_series(path, args.format, symbol, args.timeframe)
        macro[symbol], macro_timestamps[symbol] = values, factor_timestamps

    original_counts = {"XAUUSD": len(timestamps), **{symbol: len(macro_timestamps[symbol]) for symbol in macro_timestamps}}
    close, high, low, volume, common_ts, macro, macro_timestamps = _build_common_observation_sample(
        close, high, low, volume, timestamps, macro, macro_timestamps, ("DXY", "US10Y", "VIX")
    )
    if len(common_ts) < args.train + args.valid:
        print(f"BLOCKED: common sample has {len(common_ts)} rows; requires at least {args.train + args.valid}")
        return 2

    cfg = Phase52Config(
        symbol=args.symbol,
        timeframe=args.timeframe,
        horizon=args.horizon,
        threshold=args.threshold,
        train_size=args.train,
        validation_size=args.valid,
        step_size=args.step,
        n_neighbors=args.neighbors,
        spread_spec=args.spread,
        slippage_spec=args.slippage,
        commission_spec=args.commission,
    )
    results = run_phase52_comparison(
        close, high, low, volume, macro, config=cfg, timestamps=common_ts, macro_timestamps=macro_timestamps
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result_dict = {name: result.to_dict() for name, result in results.items()}
    payload = {
        "schema": "researchos/phase52/evidence/v1",
        "repository_commit": args.repository_commit,
        "configuration": {
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "horizon": args.horizon,
            "threshold": args.threshold,
            "train_size": args.train,
            "validation_size": args.valid,
            "step_size": args.step,
            "n_neighbors": args.neighbors,
            "spread": args.spread,
            "slippage": args.slippage,
            "commission": args.commission,
        },
        "sources": {
            "XAUUSD": {"path": str(paths["XAUUSD"]), "sha256": _sha256(paths["XAUUSD"]), "rows": original_counts["XAUUSD"]},
            "DXY": {"path": str(paths["DXY"]), "sha256": _sha256(paths["DXY"]), "rows": original_counts["DXY"], "identity": "Dukascopy dollaridxusd; secondary DXY series"},
            "US10Y": {"path": str(paths["US10Y"]), "sha256": _sha256(paths["US10Y"]), "rows": original_counts["US10Y"], "identity": "FRED DGS10"},
            "VIX": {"path": str(paths["VIX"]), "sha256": _sha256(paths["VIX"]), "rows": original_counts["VIX"], "identity": "FRED VIXCLS"},
        },
        "common_sample": {
            "count": len(common_ts),
            "first": _date_key(common_ts[0]),
            "last": _date_key(common_ts[-1]),
            "dropped_from_xauusd": original_counts["XAUUSD"] - len(common_ts),
            "timestamps_sha256": hashlib.sha256(json.dumps([str(x) for x in common_ts], separators=(",", ":")).encode()).hexdigest(),
        },
        "results": result_dict,
        "reproducibility_hashes": {name: result.reproducibility_hash for name, result in results.items()},
    }
    json_path = out_dir / "phase52_evidence.json"
    md_path = out_dir / "phase52_evidence.md"
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    _write_report(md_path, payload)

    print("=" * 100)
    print("PHASE 5.2 COMPLETE EVIDENCE PACKAGE")
    print(f"COMMON SAMPLE : {len(common_ts)}")
    print(f"FIRST / LAST  : {_date_key(common_ts[0])} / {_date_key(common_ts[-1])}")
    for name in FEATURE_SET_NAMES:
        result = results[name]
        print(f"{name:18} | {result.outcome:10} | folds={result.num_folds:3d} | accuracy={result.model.accuracy:.6f} | brier={result.model.brier_score:.6f} | p={result.significance.p_value:.6g}")
    print(f"JSON            : {json_path}")
    print(f"REPORT          : {md_path}")
    print("DXY BOUNDARY    : Dukascopy secondary series; ICE equivalence NOT PROVEN")
    print("=" * 100)
    return 0 if all(result.outcome != "BLOCKED" for result in results.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
