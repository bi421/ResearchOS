"""Run the first real XAUUSD M1 Market Memory stage on an audited MT5 CSV.

This runner stops on integrity problems and never falls back to synthetic data.
It produces a deterministic event/outcome artifact suitable for the next
walk-forward and evidence stages.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import polars as pl

from researchos.market_memory.m1_event_engine import extract_xauusd_m1_sma_crossover_events
from researchos.market_memory.m1_outcome_contract import M1OutcomeContract
from researchos.market_memory.outcome_engine import compute_forward_outcomes

REQUIRED = {"timestamp", "open", "high", "low", "close", "tick_volume"}


def _load(path: Path) -> tuple[pl.DataFrame, str]:
    if not path.exists():
        raise FileNotFoundError(f"MT5 XAUUSD M1 dataset not found: {path}")
    if path.suffix.lower() != ".csv":
        raise ValueError("The first real-M1 gate requires the audited CSV, not another gold instrument or synthetic data.")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    df = pl.read_csv(path, try_parse_dates=False)
    rename = {}
    for source, target in (("time", "timestamp"), ("Time", "timestamp"), ("TIME", "timestamp")):
        if source in df.columns and "timestamp" not in df.columns:
            rename[source] = target
    if rename:
        df = df.rename(rename)
    missing = REQUIRED.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if df["timestamp"].dtype == pl.String:
        df = df.with_columns(pl.col("timestamp").str.to_datetime(strict=True, time_zone="UTC"))
    elif df["timestamp"].dtype != pl.Datetime:
        raise ValueError(f"Unsupported timestamp dtype: {df['timestamp'].dtype}")
    numeric = ["open", "high", "low", "close", "tick_volume"]
    df = df.with_columns([pl.col(c).cast(pl.Float64, strict=True) for c in numeric])
    df = df.sort("timestamp")
    if df["timestamp"].n_unique() != len(df):
        raise ValueError("Duplicate timestamps detected")
    if df["timestamp"].null_count() or any(df[c].null_count() for c in numeric):
        raise ValueError("Null values detected in required real-data columns")
    if (df["high"] < df["low"]).any():
        raise ValueError("Invalid OHLC: high < low")
    return df, digest


def _event_dict(event) -> dict:
    outcome = event.outcome.to_dict() if event.outcome else None
    return {
        "event_id": event.event_id,
        "timestamp": event.timestamp.isoformat(),
        "direction": event.direction,
        "event_price": event.event_price,
        "dataset_source": event.dataset_source,
        "computation_method": event.computation_method,
        "context": event.context.to_dict(),
        "outcome": outcome,
    }


def run(input_path: Path, output_path: Path, threshold: float) -> dict:
    contract = M1OutcomeContract(horizon_days=1, threshold_return=threshold)
    frame, sha256 = _load(input_path)
    events = extract_xauusd_m1_sma_crossover_events(frame, dataset_source="xauusd_m1_mt5")
    realized = compute_forward_outcomes(events, frame, horizons=[1], threshold=threshold)

    complete = [e for e in realized if e.outcome and e.outcome.hit_threshold_1d is not None]
    if not complete:
        raise RuntimeError("No complete 1-day outcomes were produced")
    leakage_violations = []
    for event in complete:
        end = event.outcome.data_availability.get("realized_end_1d")
        if end is None or end <= event.timestamp.isoformat():
            leakage_violations.append(event.event_id)
    if leakage_violations:
        raise RuntimeError(f"Forward-label leakage/endpoint violations: {len(leakage_violations)}")

    wins = sum(bool(e.outcome.hit_threshold_1d) for e in complete)
    report = {
        "contract": {
            "asset": "XAUUSD",
            "timeframe": "M1",
            "event": "SMA20/100 crossover",
            "label": contract.label_name,
            "horizon_days": contract.horizon_days,
            "threshold_return": contract.threshold_return,
            "price_field": contract.price_field,
            "direction_aware": contract.direction_aware,
        },
        "dataset": {
            "path": str(input_path),
            "sha256": sha256,
            "rows": len(frame),
            "start": frame["timestamp"][0].isoformat(),
            "end": frame["timestamp"][-1].isoformat(),
            "columns": frame.columns,
        },
        "events": {
            "extracted": len(events),
            "complete_1d_outcomes": len(complete),
            "bullish": sum(e.direction == "bullish" for e in complete),
            "bearish": sum(e.direction == "bearish" for e in complete),
            "positive_labels": wins,
            "negative_labels": len(complete) - wins,
        },
        "scientific_status": "FOUNDATION_ONLY_NO_PREDICTIVE_EDGE_CLAIM",
        "events_data": [_event_dict(e) for e in complete],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Audited MT5 XAUUSD M1 CSV")
    parser.add_argument("--output", type=Path, default=Path("artifacts/xauusd_m1_real_events_outcomes.json"))
    parser.add_argument("--threshold", type=float, default=0.0)
    args = parser.parse_args()
    report = run(args.input, args.output, args.threshold)
    print(f"Rows: {report['dataset']['rows']}")
    print(f"Events: {report['events']['extracted']}")
    print(f"Complete 1d outcomes: {report['events']['complete_1d_outcomes']}")
    print(f"Bullish/Bearish: {report['events']['bullish']}/{report['events']['bearish']}")
    print(f"Positive/Negative labels: {report['events']['positive_labels']}/{report['events']['negative_labels']}")
    print(f"Dataset SHA256: {report['dataset']['sha256']}")
    print(f"Artifact: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
