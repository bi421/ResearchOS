from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_COLUMNS = [
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
]
EXPECTED_MEMBER = "XAUUSD_M1_2021_2025_MT5.csv"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_gap(start: pd.Timestamp, end: pd.Timestamp) -> str:
    """Conservative classification; never declares a gap to be data loss."""
    if start.weekday() >= 5 or end.weekday() >= 5:
        return "weekend_overlap"
    return "non_weekend_gap"


def audit(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)

    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError(f"Corrupt ZIP member: {bad_member}")
        names = archive.namelist()
        if EXPECTED_MEMBER not in names:
            raise ValueError(f"Missing ZIP member: {EXPECTED_MEMBER}")
        csv_bytes = archive.read(EXPECTED_MEMBER)

    df = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
    columns_ok = list(df.columns) == EXPECTED_COLUMNS
    if not columns_ok:
        raise ValueError(f"Unexpected columns: {list(df.columns)}")

    t = pd.to_datetime(df["time"], utc=True, errors="coerce")
    dt = t.diff().dt.total_seconds().div(60)

    finite = np.isfinite(df[["open", "high", "low", "close"]].to_numpy()).all()
    bad_ohlc = (
        (df["high"] < df[["open", "close"]].max(axis=1))
        | (df["low"] > df[["open", "close"]].min(axis=1))
        | (df["high"] < df["low"])
    )

    gap_mask = dt > 1
    gaps: list[dict] = []
    for i in df.index[gap_mask]:
        start = t.iloc[i - 1]
        end = t.iloc[i]
        gaps.append(
            {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "minutes": float(dt.iloc[i]),
                "classification": classify_gap(start, end),
            }
        )

    weekend_gaps = [g for g in gaps if g["classification"] == "weekend_overlap"]
    non_weekend_gaps = [g for g in gaps if g["classification"] == "non_weekend_gap"]

    result = {
        "dataset": "XAUUSD",
        "timeframe": "M1",
        "source": "MetaTrader5",
        "zip": {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256_bytes(path.read_bytes()),
            "testzip": "PASS",
            "member": EXPECTED_MEMBER,
            "member_sha256": sha256_bytes(csv_bytes),
        },
        "schema": {
            "columns": list(df.columns),
            "expected": EXPECTED_COLUMNS,
            "pass": columns_ok,
        },
        "rows": int(len(df)),
        "start": t.min().isoformat() if t.notna().any() else None,
        "end": t.max().isoformat() if t.notna().any() else None,
        "integrity": {
            "nulls": int(df.isna().sum().sum()),
            "timestamp_parse_failures": int(t.isna().sum()),
            "timestamp_monotonic": bool(t.is_monotonic_increasing),
            "duplicate_timestamps": int(t.duplicated().sum()),
            "non_positive_gaps": int((dt.dropna() <= 0).sum()),
            "nan_total": int(df.isna().sum().sum()),
            "inf_total": int((~np.isfinite(df[["open", "high", "low", "close"]])).sum().sum()),
            "invalid_ohlc_rows": int(bad_ohlc.sum()),
            "non_positive_price_rows": int((df[["open", "high", "low", "close"]] <= 0).any(axis=1).sum()),
            "negative_tick_volume_rows": int((df["tick_volume"] < 0).sum()),
            "negative_spread_rows": int((df["spread"] < 0).sum()),
            "negative_real_volume_rows": int((df["real_volume"] < 0).sum()),
            "finite_prices": bool(finite),
        },
        "gaps": {
            "count_gt_1m": len(gaps),
            "max_minutes": float(dt.max()) if dt.notna().any() else 0.0,
            "weekend_overlap": len(weekend_gaps),
            "non_weekend": len(non_weekend_gaps),
            "non_weekend_details": non_weekend_gaps,
        },
    }

    core_pass = all(
        [
            result["rows"] > 0,
            result["schema"]["pass"],
            result["integrity"]["timestamp_parse_failures"] == 0,
            result["integrity"]["timestamp_monotonic"],
            result["integrity"]["duplicate_timestamps"] == 0,
            result["integrity"]["non_positive_gaps"] == 0,
            result["integrity"]["nan_total"] == 0,
            result["integrity"]["inf_total"] == 0,
            result["integrity"]["invalid_ohlc_rows"] == 0,
            result["integrity"]["non_positive_price_rows"] == 0,
            result["integrity"]["negative_tick_volume_rows"] == 0,
            result["integrity"]["negative_spread_rows"] == 0,
            result["integrity"]["negative_real_volume_rows"] == 0,
        ]
    )
    result["decision"] = (
        "ACCEPT_WITH_CONDITIONS" if core_pass and non_weekend_gaps else "ACCEPT"
        if core_pass
        else "REJECT"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit real XAUUSD M1 MT5 ZIP dataset")
    parser.add_argument(
        "path",
        nargs="?",
        default="data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.zip",
        help="Path to the XAUUSD M1 ZIP",
    )
    parser.add_argument("--json", dest="json_path", help="Write full audit JSON to this path")
    args = parser.parse_args()

    result = audit(Path(args.path))

    print("=" * 70)
    print("XAUUSD M1 DATASET GATE AUDIT")
    print("=" * 70)
    print(f"Rows                 : {result['rows']:,}")
    print(f"Range                : {result['start']} -> {result['end']}")
    print(f"ZIP SHA256           : {result['zip']['sha256']}")
    print(f"CSV SHA256           : {result['zip']['member_sha256']}")
    print(f"Timestamp monotonic  : {result['integrity']['timestamp_monotonic']}")
    print(f"Duplicate timestamps : {result['integrity']['duplicate_timestamps']}")
    print(f"OHLC invalid         : {result['integrity']['invalid_ohlc_rows']}")
    print(f"NaN / Inf            : {result['integrity']['nan_total']} / {result['integrity']['inf_total']}")
    print(f"Gaps > 1m            : {result['gaps']['count_gt_1m']}")
    print(f"Weekend-overlap gaps : {result['gaps']['weekend_overlap']}")
    print(f"Non-weekend gaps     : {result['gaps']['non_weekend']}")
    print(f"Largest gap (min)    : {result['gaps']['max_minutes']}")
    print(f"DECISION             : {result['decision']}")
    print("=" * 70)

    if result["gaps"]["non_weekend"]:
        print("NON-WEEKEND GAP DETAILS")
        print("=" * 70)
        for gap in result["gaps"]["non_weekend_details"]:
            print(f"{gap['start']} -> {gap['end']} : {gap['minutes']:.1f} min")

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Audit JSON saved      : {args.json_path}")

    return 0 if result["decision"] != "REJECT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
