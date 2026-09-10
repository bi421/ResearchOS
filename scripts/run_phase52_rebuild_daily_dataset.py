"""Build the Phase 5.2 rebuild daily common dataset from real source files."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from researchos.experiments.phase52_rebuild.daily_dataset import build_daily_common_dataset


def _dataset_hash(rows) -> str:
    payload = [
        {
            "day": r.day,
            "timestamp": r.timestamp,
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "tick_volume": r.tick_volume,
            "spread": r.spread,
            "real_volume": r.real_volume,
            "dxy": r.dxy,
            "us10y": r.us10y,
            "vix": r.vix,
            "m1_rows": r.m1_rows,
        }
        for r in rows
    ]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Phase 5.2 rebuild daily dataset")
    p.add_argument("--csv", required=True)
    p.add_argument("--dxy", required=True)
    p.add_argument("--us10y", required=True)
    p.add_argument("--vix", required=True)
    p.add_argument("--out", default="reports/phase52_rebuild/daily_common_dataset.csv")
    p.add_argument("--meta", default="reports/phase52_rebuild/daily_common_dataset.json")
    args = p.parse_args(argv)

    rows = build_daily_common_dataset(args.csv, args.dxy, args.us10y, args.vix)
    if not rows:
        print("BLOCKED: no exact common daily observations")
        return 2

    out = Path(args.out)
    meta = Path(args.meta)
    out.parent.mkdir(parents=True, exist_ok=True)
    meta.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "day", "timestamp", "open", "high", "low", "close", "tick_volume",
        "spread", "real_volume", "dxy", "us10y", "vix", "m1_rows",
    ]
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({field: getattr(r, field) for field in fields})

    metadata = {
        "dataset_contract": "phase52_rebuild_daily_common_v1",
        "aggregation": "XAUUSD M1 -> UTC calendar-day OHLCV",
        "macro_alignment": "exact UTC calendar-day intersection",
        "missing_value_policy": "drop observation; never interpolate or forward-fill",
        "rows": len(rows),
        "first_day": rows[0].day,
        "last_day": rows[-1].day,
        "dataset_sha256": _dataset_hash(rows),
    }
    meta.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("=" * 88)
    print("PHASE 5.2 REBUILD — DAILY COMMON DATASET")
    print("=" * 88)
    print(f"ROWS                 : {len(rows)}")
    print(f"FIRST / LAST DAY     : {rows[0].day} / {rows[-1].day}")
    print(f"DATASET SHA-256      : {metadata['dataset_sha256']}")
    print(f"CSV                  : {out}")
    print(f"METADATA             : {meta}")
    print("STATUS               : PASS")
    print("=" * 88)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
