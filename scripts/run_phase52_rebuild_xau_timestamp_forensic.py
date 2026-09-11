from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTEXT_XAU = ROOT / "data/macro/context/dukascopy_2020/XAUUSD_Dukascopy_M1_2020_context.csv"
RESEARCH_XAU = ROOT / "data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.csv"

OUT = ROOT / "reports/phase52_rebuild/xau_timestamp_forensic.json"

TARGET_DAYS = None


def parse_timestamp(value: str) -> datetime:
    text = str(value).strip()

    try:
        n = int(text)
    except ValueError:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    return datetime.fromtimestamp(n / 1000, tz=timezone.utc)


def utc_day(value: str) -> str:
    return parse_timestamp(value).date().isoformat()


def utc_dt(value: str) -> datetime:
    return parse_timestamp(value)


def load_csv_days(path: Path, name: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}

    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}

            timestamp_key = "timestamp" if "timestamp" in row else "time"
            if timestamp_key not in row:
                raise ValueError(
                    f"{name} CSV must contain timestamp or time column; columns={list(row)}"
                )

            day = utc_day(row[timestamp_key])

            out.setdefault(day, []).append(
                {
                    "timestamp": utc_dt(row[timestamp_key]),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                }
            )

    return out


def summarize(rows: list[dict]) -> dict:
    rows = sorted(rows, key=lambda x: x["timestamp"])

    return {
        "rows": len(rows),
        "first_timestamp": rows[0]["timestamp"].isoformat() if rows else None,
        "last_timestamp": rows[-1]["timestamp"].isoformat() if rows else None,
        "first_open": rows[0]["open"] if rows else None,
        "last_close": rows[-1]["close"] if rows else None,
        "high": max(x["high"] for x in rows) if rows else None,
        "low": min(x["low"] for x in rows) if rows else None,
        "unique_timestamps": len({x["timestamp"] for x in rows}),
    }


def main() -> int:
    context = load_csv_days(CONTEXT_XAU, "context")
    research = load_csv_days(RESEARCH_XAU, "research")

    common = sorted(set(context) & set(research))

    selected = sorted(common)

    rows = []

    for day in selected:
        c = summarize(context[day])
        r = summarize(research[day])

        rows.append(
            {
                "day": day,
                "context": c,
                "research": r,
                "timestamp_difference_seconds": (
                    (
                        datetime.fromisoformat(c["first_timestamp"])
                        - datetime.fromisoformat(r["first_timestamp"])
                    ).total_seconds()
                    if c["first_timestamp"] and r["first_timestamp"]
                    else None
                ),
                "last_timestamp_difference_seconds": (
                    (
                        datetime.fromisoformat(c["last_timestamp"])
                        - datetime.fromisoformat(r["last_timestamp"])
                    ).total_seconds()
                    if c["last_timestamp"] and r["last_timestamp"]
                    else None
                ),
            }
        )

    payload = {
        "status": "FORENSIC_ONLY",
        "common_days": len(common),
        "target_days": rows,
        "question": (
            "Determine whether XAU daily OHLC differences are explained "
            "by UTC timestamp/session boundaries or by source/feed provenance."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print("=" * 70)
    print("PHASE 5.2 ? XAU TIMESTAMP FORENSIC")
    print("=" * 70)

    for item in rows:
        print(f"\nDAY: {item['day']}")

        c = item["context"]
        r = item["research"]

        print("  CONTEXT")
        print(f"    rows        : {c['rows']}")
        print(f"    first       : {c['first_timestamp']}")
        print(f"    last        : {c['last_timestamp']}")
        print(f"    open        : {c['first_open']}")
        print(f"    high        : {c['high']}")
        print(f"    low         : {c['low']}")
        print(f"    close       : {c['last_close']}")

        print("  RESEARCH")
        print(f"    rows        : {r['rows']}")
        print(f"    first       : {r['first_timestamp']}")
        print(f"    last        : {r['last_timestamp']}")
        print(f"    open        : {r['first_open']}")
        print(f"    high        : {r['high']}")
        print(f"    low         : {r['low']}")
        print(f"    close       : {r['last_close']}")

        print(f"  FIRST TIMESTAMP DIFF (sec): {item['timestamp_difference_seconds']}")

        print(f"  LAST TIMESTAMP DIFF (sec) : {item['last_timestamp_difference_seconds']}")

    print(f"\nOUTPUT: {OUT.relative_to(ROOT)}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
