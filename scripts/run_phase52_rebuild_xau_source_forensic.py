from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from researchos.experiments.phase52_rebuild.daily_dataset import load_daily_xau_from_m1

ROOT = Path(__file__).resolve().parents[1]

CONTEXT_XAU = ROOT / "data/macro/context/dukascopy_2020/XAUUSD_Dukascopy_M1_2020_context.csv"
RESEARCH_XAU = ROOT / "data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.csv"

OUT = ROOT / "reports/phase52_rebuild/xau_source_forensic.json"


def utc_day(value: str) -> str:
    n = int(str(value).strip())
    return datetime.fromtimestamp(n / 1000, tz=timezone.utc).date().isoformat()


def load_context(path: Path) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
    groups: dict[str, list[dict[str, float]]] = {}
    row_counts: dict[str, int] = {}

    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        fields = {str(x).strip().lower() for x in (reader.fieldnames or [])}

        required = {"timestamp", "open", "high", "low", "close"}
        if not required.issubset(fields):
            raise ValueError(f"Missing required columns: {sorted(required - fields)}")

        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}

            day = utc_day(str(row["timestamp"]))

            groups.setdefault(day, []).append(
                {
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                }
            )

            row_counts[day] = row_counts.get(day, 0) + 1

    daily: dict[str, dict[str, float]] = {}

    for day, rows in sorted(groups.items()):
        daily[day] = {
            "open": rows[0]["open"],
            "high": max(r["high"] for r in rows),
            "low": min(r["low"] for r in rows),
            "close": rows[-1]["close"],
        }

    return daily, row_counts


def rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def signed(a: float, b: float) -> float:
    return a - b


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    index = (len(values) - 1) * p
    lo = int(index)
    hi = min(lo + 1, len(values) - 1)
    frac = index - lo

    return values[lo] + (values[hi] - values[lo]) * frac


def main() -> int:
    if not CONTEXT_XAU.exists():
        raise FileNotFoundError(CONTEXT_XAU)

    if not RESEARCH_XAU.exists():
        raise FileNotFoundError(RESEARCH_XAU)

    context, context_counts = load_context(CONTEXT_XAU)

    research_bars = load_daily_xau_from_m1(RESEARCH_XAU)
    research = {
        bar.day: {
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
        }
        for bar in research_bars
    }

    days = sorted(set(context) & set(research))

    fields = ("open", "high", "low", "close")

    field_stats = {}

    for field in fields:
        abs_diffs = [abs(context[d][field] - research[d][field]) for d in days]

        rel_diffs = [rel(context[d][field], research[d][field]) for d in days]

        signed_diffs = [signed(context[d][field], research[d][field]) for d in days]

        field_stats[field] = {
            "max_absolute_difference": max(abs_diffs) if abs_diffs else None,
            "mean_absolute_difference": mean(abs_diffs) if abs_diffs else None,
            "max_relative_difference": max(rel_diffs) if rel_diffs else None,
            "mean_relative_difference": mean(rel_diffs) if rel_diffs else None,
            "p50_relative_difference": percentile(rel_diffs, 0.50),
            "p90_relative_difference": percentile(rel_diffs, 0.90),
            "p95_relative_difference": percentile(rel_diffs, 0.95),
            "p99_relative_difference": percentile(rel_diffs, 0.99),
            "mean_signed_difference": mean(signed_diffs) if signed_diffs else None,
            "nonzero_days": sum(x > 0 for x in abs_diffs),
        }

    detailed = []

    for day in days:
        row = {
            "day": day,
            "context_m1_rows": context_counts.get(day),
        }

        for field in fields:
            c = context[day][field]
            r = research[day]

            row[f"context_{field}"] = c
            row[f"research_{field}"] = r[field]
            row[f"{field}_absolute_difference"] = abs(c - r[field])
            row[f"{field}_relative_difference"] = rel(c, r[field])
            row[f"{field}_signed_difference"] = signed(c, r[field])

        detailed.append(row)

    worst_close = sorted(
        detailed,
        key=lambda x: x["close_relative_difference"],
        reverse=True,
    )

    worst_high = sorted(
        detailed,
        key=lambda x: x["high_relative_difference"],
        reverse=True,
    )

    worst_low = sorted(
        detailed,
        key=lambda x: x["low_relative_difference"],
        reverse=True,
    )

    context_row_counts = [context_counts[d] for d in days]

    payload = {
        "status": "FORENSIC_ONLY",
        "context_days": len(context),
        "research_days": len(research),
        "overlap_days": len(days),
        "overlap_first": days[0] if days else None,
        "overlap_last": days[-1] if days else None,
        "context_m1_rows": {
            "min": min(context_row_counts) if context_row_counts else None,
            "max": max(context_row_counts) if context_row_counts else None,
            "mean": mean(context_row_counts) if context_row_counts else None,
            "exact_1440_days": sum(x == 1440 for x in context_row_counts),
            "less_than_1440_days": sum(x < 1440 for x in context_row_counts),
            "more_than_1440_days": sum(x > 1440 for x in context_row_counts),
        },
        "field_statistics": field_stats,
        "worst_close_days": worst_close[:15],
        "worst_high_days": worst_high[:10],
        "worst_low_days": worst_low[:10],
        "interpretation": {
            "source_equivalence": "NOT_DETERMINED",
            "feed_difference_possible": True,
            "timestamp_boundary_issue_possible": True,
            "aggregation_issue_possible": True,
            "next_step": "Inspect OHLC patterns and M1 row counts before changing production architecture.",
        },
        "daily_comparisons": detailed,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=" * 70)
    print("PHASE 5.2 ? XAU SOURCE FORENSIC")
    print("=" * 70)
    print(f"CONTEXT DAYS              : {len(context)}")
    print(f"RESEARCH DAYS             : {len(research)}")
    print(f"OVERLAP DAYS              : {len(days)}")
    print(f"OVERLAP FIRST/LAST        : {days[0] if days else None} / {days[-1] if days else None}")

    print("\nM1 ROW COUNT")
    print(f"MIN                       : {min(context_row_counts) if context_row_counts else None}")
    print(f"MAX                       : {max(context_row_counts) if context_row_counts else None}")
    print(f"MEAN                      : {mean(context_row_counts) if context_row_counts else None}")
    print(f"EXACT 1440 DAYS           : {sum(x == 1440 for x in context_row_counts)}")
    print(f"LESS THAN 1440            : {sum(x < 1440 for x in context_row_counts)}")
    print(f"MORE THAN 1440            : {sum(x > 1440 for x in context_row_counts)}")

    print("\nFIELD COMPARISON")
    for field in fields:
        s = field_stats[field]
        print(
            f"{field.upper():5} "
            f"max_rel={s['max_relative_difference']:.12g} "
            f"mean_rel={s['mean_relative_difference']:.12g} "
            f"p95={s['p95_relative_difference']:.12g} "
            f"nonzero={s['nonzero_days']}"
        )

    print("\nTOP CLOSE DIFFERENCES")
    for row in worst_close[:10]:
        print(
            f"{row['day']} "
            f"context={row['context_close']:.6f} "
            f"research={row['research_close']:.6f} "
            f"rel={row['close_relative_difference']:.12g} "
            f"m1={row['context_m1_rows']}"
        )

    print(f"\nOUTPUT                    : {OUT.relative_to(ROOT)}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
