from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import pandas as pd

EXPECTED_MEMBER = "XAUUSD_M1_2021_2025_MT5.csv"


def classify_gap(start: pd.Timestamp, end: pd.Timestamp) -> str:
    """Conservative session classification; suspicious gaps remain unresolved."""
    # MT5 XAUUSD commonly has a weekly closure. This classifier only labels
    # gaps whose entire interval crosses the Saturday/Sunday boundary as
    # weekend-related; it deliberately does not assume holidays or broker
    # maintenance windows are valid closures.
    if start.weekday() == 4 and end.weekday() == 6:
        return "weekend_closure_candidate"
    if start.weekday() >= 5 or end.weekday() >= 5:
        return "weekend_overlap_candidate"
    return "non_weekend_suspicious"


def audit(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None:
            raise ValueError("Corrupt ZIP archive")
        if EXPECTED_MEMBER not in zf.namelist():
            raise ValueError(f"Missing member: {EXPECTED_MEMBER}")
        import io
        df = pd.read_csv(io.BytesIO(zf.read(EXPECTED_MEMBER)), usecols=["time"])

    t = pd.to_datetime(df["time"], utc=True, errors="coerce")
    if t.isna().any() or not t.is_monotonic_increasing or t.duplicated().any():
        raise ValueError("Timestamp contract failed")

    dt = t.diff().dt.total_seconds().div(60)
    rows = []
    for i in df.index[dt > 1]:
        start, end = t.iloc[i - 1], t.iloc[i]
        rows.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            "minutes": float(dt.iloc[i]),
            "start_weekday": start.day_name(),
            "end_weekday": end.day_name(),
            "classification": classify_gap(start, end),
        })

    counts = pd.Series([r["classification"] for r in rows]).value_counts().to_dict()
    suspicious = [r for r in rows if r["classification"] == "non_weekend_suspicious"]
    return {
        "dataset": "XAUUSD",
        "timeframe": "M1",
        "source": "MetaTrader5",
        "rows": int(len(df)),
        "gaps_gt_1m": len(rows),
        "classification_counts": counts,
        "suspicious_count": len(suspicious),
        "suspicious_details": suspicious,
        "decision": "REQUIRES_REVIEW" if suspicious else "WEEKEND_GAPS_ONLY",
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Audit XAUUSD M1 temporal gaps")
    p.add_argument("path", nargs="?", default="data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.zip")
    p.add_argument("--json", dest="json_path")
    args = p.parse_args()
    result = audit(Path(args.path))
    print("=" * 70)
    print("XAUUSD M1 TEMPORAL GAP AUDIT")
    print("=" * 70)
    print(f"Rows                 : {result['rows']:,}")
    print(f"Gaps > 1m            : {result['gaps_gt_1m']}")
    for key, value in result["classification_counts"].items():
        print(f"{key:<30}: {value}")
    print(f"Suspicious gaps      : {result['suspicious_count']}")
    print(f"DECISION             : {result['decision']}")
    if result["suspicious_details"]:
        print("SUSPICIOUS DETAILS")
        for gap in result["suspicious_details"]:
            print(f"{gap['start']} -> {gap['end']} : {gap['minutes']:.1f} min")
    print("=" * 70)
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Audit JSON saved      : {args.json_path}")
    return 0 if result["decision"] != "REQUIRES_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
