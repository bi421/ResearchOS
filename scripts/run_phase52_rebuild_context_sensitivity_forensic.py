"""Forensic breakdown of context-vs-cold-start feature differences.

This audit does not judge source equivalence. It identifies which feature/day
causes the observed sensitivity and verifies labels/source-day identity on the
common comparison window.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from researchos.experiments.phase52_rebuild.context_dataset import load_context_daily_observations
from researchos.experiments.phase52_rebuild.context_features import build_context_feature_dataset
from researchos.experiments.phase52_rebuild.daily_dataset import DailyObservation
from researchos.experiments.phase52_rebuild.feature_contract import FEATURE_SET_NAMES, Phase52FeatureContract
from researchos.experiments.phase52_rebuild.feature_dataset import build_feature_dataset

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT_XAU = ROOT / "data/macro/context/dukascopy_2020/XAUUSD_Dukascopy_M1_2020_context.csv"
DEFAULT_CONTEXT_DXY = ROOT / "data/macro/context/dukascopy_2020/DXY_Dukascopy_D1_2020_context.csv"
DEFAULT_US10Y = ROOT / "data/macro/raw/DGS10_fred.csv"
DEFAULT_VIX = ROOT / "data/macro/raw/VIXCLS_fred.csv"
DEFAULT_RESEARCH = ROOT / "reports/phase52_rebuild/daily_common_dataset.csv"
DEFAULT_OUTPUT = ROOT / "reports/phase52_rebuild/context_sensitivity_forensic.json"


def _load_research(path: Path) -> tuple[DailyObservation, ...]:
    rows: list[DailyObservation] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            rows.append(
                DailyObservation(
                    day=str(raw["day"]),
                    timestamp=str(raw["timestamp"]),
                    open=float(raw["open"]),
                    high=float(raw["high"]),
                    low=float(raw["low"]),
                    close=float(raw["close"]),
                    tick_volume=float(raw["tick_volume"]),
                    spread=None if raw.get("spread") in (None, "", "None") else float(raw["spread"]),
                    real_volume=float(raw["real_volume"]),
                    dxy=float(raw["dxy"]),
                    us10y=float(raw["us10y"]),
                    vix=float(raw["vix"]),
                    m1_rows=int(float(raw["m1_rows"])),
                )
            )
    return tuple(rows)


def _feature_diffs(
    names: tuple[str, ...],
    context_rows: tuple[tuple[float, ...], ...],
    cold_rows: tuple[tuple[float, ...], ...],
    days: tuple[str, ...],
):
    records = []
    for day, context_row, cold_row in zip(days, context_rows, cold_rows):
        for name, context_value, cold_value in zip(names, context_row, cold_row):
            diff = abs(context_value - cold_value)
            if not math.isclose(context_value, cold_value, rel_tol=0.0, abs_tol=1e-12):
                records.append(
                    {
                        "day": day,
                        "feature": name,
                        "context_value": context_value,
                        "cold_start_value": cold_value,
                        "absolute_difference": diff,
                    }
                )
    records.sort(key=lambda r: (-r["absolute_difference"], r["day"], r["feature"]))
    return records


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--context-xau", default=str(DEFAULT_CONTEXT_XAU))
    p.add_argument("--context-dxy", default=str(DEFAULT_CONTEXT_DXY))
    p.add_argument("--us10y", default=str(DEFAULT_US10Y))
    p.add_argument("--vix", default=str(DEFAULT_VIX))
    p.add_argument("--research", default=str(DEFAULT_RESEARCH))
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = p.parse_args(argv)

    research = _load_research(Path(args.research))
    all_context = load_context_daily_observations(args.context_xau, args.context_dxy, args.us10y, args.vix)
    context = tuple(obs for obs in all_context if obs.day < research[0].day)
    contract = Phase52FeatureContract()
    if len(context) < contract.warmup:
        raise ValueError(f"context has {len(context)} rows; {contract.warmup} required")

    feature_sets: dict[str, object] = {}
    global_top: list[dict[str, object]] = []
    all_labels_identical = True
    all_common_days_identical = True

    for feature_set in FEATURE_SET_NAMES:
        seeded, audit = build_context_feature_dataset(context, research, feature_set, contract)
        cold = build_feature_dataset(research, feature_set, contract)

        seeded_by_day = dict(zip(seeded.source_days, seeded.rows))
        seeded_labels = dict(zip(seeded.source_days, seeded.labels))
        cold_by_day = dict(zip(cold.source_days, cold.rows))
        cold_labels = dict(zip(cold.source_days, cold.labels))

        common_days = tuple(day for day in cold.source_days if day in seeded_by_day)
        seeded_only_days = tuple(day for day in seeded.source_days if day not in cold_by_day)
        cold_only_days = tuple(day for day in cold.source_days if day not in seeded_by_day)

        aligned_seeded_rows = tuple(seeded_by_day[d] for d in common_days)
        aligned_cold_rows = tuple(cold_by_day[d] for d in common_days)
        aligned_seeded_labels = tuple(seeded_labels[d] for d in common_days)
        aligned_cold_labels = tuple(cold_labels[d] for d in common_days)

        common_days_identical = common_days == tuple(cold.source_days)
        labels_identical = aligned_seeded_labels == aligned_cold_labels
        all_common_days_identical = all_common_days_identical and common_days_identical
        all_labels_identical = all_labels_identical and labels_identical

        records = _feature_diffs(cold.feature_names, aligned_seeded_rows, aligned_cold_rows, common_days)
        by_feature: dict[str, dict[str, float | int]] = {}
        for record in records:
            item = by_feature.setdefault(
                record["feature"],
                {"count": 0, "max_absolute_difference": 0.0, "sum_absolute_difference": 0.0},
            )
            item["count"] += 1
            item["max_absolute_difference"] = max(
                float(item["max_absolute_difference"]), float(record["absolute_difference"])
            )
            item["sum_absolute_difference"] += float(record["absolute_difference"])
        for item in by_feature.values():
            item["mean_absolute_difference"] = item["sum_absolute_difference"] / int(item["count"])
            del item["sum_absolute_difference"]

        affected_days = sorted({record["day"] for record in records})
        top = records[:20]
        global_top.extend({"feature_set": feature_set, **record} for record in top[:10])

        feature_sets[feature_set] = {
            "seeded_rows": len(seeded.source_days),
            "cold_start_rows": len(cold.source_days),
            "comparison_rows": len(common_days),
            "seeded_only_rows": len(seeded_only_days),
            "cold_only_rows": len(cold_only_days),
            "feature_count": cold.feature_count,
            "differing_feature_values": len(records),
            "total_feature_values": len(common_days) * cold.feature_count,
            "affected_research_days": len(affected_days),
            "affected_day_first": affected_days[0] if affected_days else None,
            "affected_day_last": affected_days[-1] if affected_days else None,
            "common_source_days_identical": common_days_identical,
            "labels_identical_on_common_days": labels_identical,
            "seeded_only_first": seeded_only_days[0] if seeded_only_days else None,
            "seeded_only_last": seeded_only_days[-1] if seeded_only_days else None,
            "cold_only_first": cold_only_days[0] if cold_only_days else None,
            "cold_only_last": cold_only_days[-1] if cold_only_days else None,
            "top_differences": top,
            "by_feature": dict(
                sorted(
                    by_feature.items(),
                    key=lambda kv: (
                        -int(kv[1]["count"]),
                        -float(kv[1]["max_absolute_difference"]),
                        kv[0],
                    ),
                )
            ),
            "context_audit_invariant_ok": audit.invariant_ok,
        }

    global_top.sort(
        key=lambda r: (
            -float(r["absolute_difference"]),
            str(r["feature_set"]),
            str(r["day"]),
            str(r["feature"]),
        )
    )
    payload = {
        "status": "PASS" if all_labels_identical and all_common_days_identical else "FAIL",
        "research_rows": len(research),
        "context_rows_used_for_feature_state": len(context),
        "warmup_required": contract.warmup,
        "label_horizon": contract.horizon,
        "source_equivalence_proven": False,
        "labels_identical_on_common_days": all_labels_identical,
        "common_source_days_identical": all_common_days_identical,
        "interpretation": (
            "PASS means only that context-seeded and cold-start datasets have identical source-day identity "
            "on the cold-start comparison window and identical labels there. It does not mean feature values "
            "are insensitive, nor does it prove source equivalence. Magnitude must be scientifically reviewed."
        ),
        "feature_sets": feature_sets,
        "global_top_differences": global_top[:50],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 70)
    print("PHASE 5.2 REBUILD — CONTEXT SENSITIVITY FORENSIC AUDIT")
    print("=" * 70)
    print(f"RESEARCH ROWS        : {len(research)}")
    print(f"CONTEXT STATE ROWS   : {len(context)}")
    print(f"WARMUP REQUIRED      : {contract.warmup}")
    for name, result in feature_sets.items():
        print(
            f"{name:20s}: compare={result['comparison_rows']} | "
            f"seeded_only={result['seeded_only_rows']} | "
            f"affected_days={result['affected_research_days']} | "
            f"differing={result['differing_feature_values']}/{result['total_feature_values']} | "
            f"labels={result['labels_identical_on_common_days']}"
        )
        if result["top_differences"]:
            top = result["top_differences"][0]
            print(
                f"  TOP                : {top['day']} / {top['feature']} / "
                f"abs_diff={top['absolute_difference']:.12g}"
            )
    print(f"LABELS IDENTICAL     : {payload['labels_identical_on_common_days']}")
    print(f"COMMON DAYS IDENTICAL: {payload['common_source_days_identical']}")
    print(f"STATUS               : {payload['status']}")
    print(f"OUTPUT               : {output}")
    print("=" * 70)
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
