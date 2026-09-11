from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTEXT = ROOT / r"data\macro\context\dukascopy_2020\XAUUSD_Dukascopy_M1_2020_context.csv"
RESEARCH = ROOT / r"data\mt5\xauusd\XAUUSD_M1_2021_2025_MT5.csv"
OUT = ROOT / r"reports\phase52_rebuild\xau_exact_common_minute_forensic.json"


def parse_ts(value: str) -> datetime:
    text = str(value).strip()

    try:
        n = int(text)
        return datetime.fromtimestamp(n / 1000.0, tz=timezone.utc)
    except ValueError:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


def load_context(path: Path):
    by_day = defaultdict(dict)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ts = parse_ts(row["timestamp"])
            key = ts.isoformat()

            by_day[ts.date().isoformat()][key] = {
                "timestamp": key,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }

    return by_day


def load_research(path: Path):
    by_day = defaultdict(dict)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ts = parse_ts(row["time"])
            key = ts.isoformat()

            by_day[ts.date().isoformat()][key] = {
                "timestamp": key,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }

    return by_day


def rel_diff(a: float, b: float) -> float:
    if a == 0:
        return 0.0 if b == 0 else math.inf
    return abs(a - b) / abs(a)


context = load_context(CONTEXT)
research = load_research(RESEARCH)

common_days = sorted(set(context) & set(research))

day_results = []

for day in common_days:
    c = context[day]
    r = research[day]

    common_ts = sorted(set(c) & set(r))

    if not common_ts:
        continue

    fields = ("open", "high", "low", "close")

    field_stats = {}

    for field in fields:
        diffs = [rel_diff(c[t][field], r[t][field]) for t in common_ts]

        abs_diffs = [abs(c[t][field] - r[t][field]) for t in common_ts]

        field_stats[field] = {
            "common_minutes": len(common_ts),
            "nonzero_minutes": sum(x > 0 for x in abs_diffs),
            "max_abs_diff": max(abs_diffs),
            "mean_abs_diff": sum(abs_diffs) / len(abs_diffs),
            "max_relative_diff": max(diffs),
            "mean_relative_diff": sum(diffs) / len(diffs),
        }

    day_results.append(
        {
            "day": day,
            "context_rows": len(c),
            "research_rows": len(r),
            "common_minutes": len(common_ts),
            "first_common_timestamp": common_ts[0],
            "last_common_timestamp": common_ts[-1],
            "fields": field_stats,
        }
    )


def aggregate(field):
    items = [d["fields"][field] for d in day_results]

    return {
        "days": len(items),
        "total_common_minutes": sum(x["common_minutes"] for x in items),
        "days_with_any_difference": sum(x["nonzero_minutes"] > 0 for x in items),
        "max_abs_diff": max(x["max_abs_diff"] for x in items),
        "mean_abs_diff_across_days": (sum(x["mean_abs_diff"] for x in items) / len(items)),
        "max_relative_diff": max(x["max_relative_diff"] for x in items),
        "mean_relative_diff_across_days": (
            sum(x["mean_relative_diff"] for x in items) / len(items)
        ),
    }


result = {
    "status": "FORENSIC_ONLY",
    "question": (
        "After removing timestamp/session boundary differences, "
        "do XAU prices still differ between context and research feeds?"
    ),
    "context_source": str(CONTEXT),
    "research_source": str(RESEARCH),
    "common_days": len(day_results),
    "aggregate": {field: aggregate(field) for field in ("open", "high", "low", "close")},
    "days": day_results,
}

OUT.parent.mkdir(parents=True, exist_ok=True)

OUT.write_text(
    json.dumps(result, indent=2),
    encoding="utf-8",
)

print("=" * 70)
print("PHASE 5.2 â€” XAU EXACT COMMON-MINUTE FORENSIC")
print("=" * 70)
print()
print("COMMON DAYS:", len(day_results))
print()

for field in ("open", "high", "low", "close"):
    a = result["aggregate"][field]

    print(field.upper())
    print("  total common minutes      :", a["total_common_minutes"])
    print("  days with any difference :", a["days_with_any_difference"])
    print("  max abs difference       :", a["max_abs_diff"])
    print("  mean abs difference      :", a["mean_abs_diff_across_days"])
    print("  max relative difference  :", a["max_relative_diff"])
    print("  mean relative difference :", a["mean_relative_diff_across_days"])
    print()

print("OUTPUT:", OUT)
