import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]

CONTEXT = (
    ROOT / "data" / "macro" / "context" / "dukascopy_2020" / "XAUUSD_Dukascopy_M1_2020_context.csv"
)
RESEARCH = ROOT / "data" / "mt5" / "xauusd" / "XAUUSD_M1_2021_2025_MT5.csv"
OUT = ROOT / "reports" / "phase52_rebuild" / "xau_feed_divergence_forensic.json"


def parse_ts(value):
    text = str(value).strip()
    try:
        return datetime.fromtimestamp(
            int(text) / 1000.0,
            tz=timezone.utc,
        )
    except ValueError:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


def load(path, key):
    out = {}

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ts = parse_ts(row[key]).isoformat()
            out[ts] = {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }

    return out


def percentile(values, p):
    values = sorted(values)
    i = (len(values) - 1) * p
    lo = int(math.floor(i))
    hi = int(math.ceil(i))

    if lo == hi:
        return values[lo]

    return values[lo] + (values[hi] - values[lo]) * (i - lo)


context = load(CONTEXT, "timestamp")
research = load(RESEARCH, "time")

common = sorted(set(context) & set(research))

if not common:
    raise SystemExit("No exact common UTC minutes found")


results = {}

for field in ("open", "high", "low", "close"):
    signed = [research[t][field] - context[t][field] for t in common]
    absolute = [abs(x) for x in signed]

    positive = sum(x > 0 for x in signed)
    negative = sum(x < 0 for x in signed)
    zero = sum(x == 0 for x in signed)

    results[field] = {
        "mean_signed_difference": mean(signed),
        "median_signed": median(signed),
        "mean_absolute": mean(absolute),
        "median_absolute": median(absolute),
        "p50_absolute": percentile(absolute, 0.50),
        "p95_absolute": percentile(absolute, 0.95),
        "p99_absolute": percentile(absolute, 0.99),
        "positive": positive,
        "negative": negative,
        "zero": zero,
    }


close = results["close"]

payload = {
    "phase": "5.2",
    "exact_common_utc_minutes": len(common),
    "comparison": {
        "research_minus_context": True,
        "timestamp_basis": "exact common UTC minute",
    },
    "open": results["open"],
    "high": results["high"],
    "low": results["low"],
    "close": results["close"],
    "interpretation": {
        "constant_price_offset_supported": False,
        "two_sided_price_difference": (close["positive"] > 0 and close["negative"] > 0),
        "same_minute_price_equivalence_supported": False,
        "causal_feed_or_venue_attribution_proven": False,
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)

print("=" * 70)
print("PHASE 5.2 — XAU FEED DIVERGENCE FORENSIC")
print("=" * 70)
print()
print("EXACT COMMON UTC MINUTES:", len(common))
print()

for field in ("open", "high", "low", "close"):
    result = results[field]

    print(field.upper())
    print(
        "  mean signed difference :",
        result["mean_signed_difference"],
    )
    print(
        "  median signed          :",
        result["median_signed"],
    )
    print(
        "  mean absolute          :",
        result["mean_absolute"],
    )
    print(
        "  median absolute        :",
        result["median_absolute"],
    )
    print(
        "  p50 absolute           :",
        result["p50_absolute"],
    )
    print(
        "  p95 absolute           :",
        result["p95_absolute"],
    )
    print(
        "  p99 absolute           :",
        result["p99_absolute"],
    )
    print(
        "  positive               :",
        result["positive"],
    )
    print(
        "  negative               :",
        result["negative"],
    )
    print(
        "  zero                   :",
        result["zero"],
    )
    print()

print("QUESTION:")
print(
    "If signed differences contain both positive and negative values, "
    "this does not support a simple constant price offset."
)
print()
print("JSON OUTPUT:", OUT.relative_to(ROOT))
