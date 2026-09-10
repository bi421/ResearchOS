"""Audit whether pre-research context materially changes research features.

This is a sensitivity audit, not a source-equivalence test. It compares the
context-seeded feature state against the existing cold-start feature state on
the identical research source days where both datasets are valid.
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
DEFAULT_OUTPUT = ROOT / "reports/phase52_rebuild/context_boundary_sensitivity.json"


def _load_research_daily(path: Path) -> tuple[DailyObservation, ...]:
    rows: list[DailyObservation] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
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


def _max_mean_abs_diff(context_rows: tuple[tuple[float, ...], ...], cold_rows: tuple[tuple[float, ...], ...]) -> tuple[float, float]:
    if len(context_rows) != len(cold_rows) or not context_rows:
        raise ValueError("comparison datasets must have equal non-zero length")
    diffs = [
        abs(a - b)
        for context_row, cold_row in zip(context_rows, cold_rows)
        for a, b in zip(context_row, cold_row)
    ]
    return max(diffs, default=0.0), sum(diffs) / len(diffs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-xau", default=str(DEFAULT_CONTEXT_XAU))
    parser.add_argument("--context-dxy", default=str(DEFAULT_CONTEXT_DXY))
    parser.add_argument("--us10y", default=str(DEFAULT_US10Y))
    parser.add_argument("--vix", default=str(DEFAULT_VIX))
    parser.add_argument("--research", default=str(DEFAULT_RESEARCH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    research = _load_research_daily(Path(args.research))
    all_context = load_context_daily_observations(
        args.context_xau, args.context_dxy, args.us10y, args.vix
    )
    context = tuple(obs for obs in all_context if obs.day < research[0].day)
    contract = Phase52FeatureContract()
    if len(context) < contract.warmup:
        raise ValueError(f"context has {len(context)} rows; {contract.warmup} required")

    results: dict[str, object] = {}
    for feature_set in FEATURE_SET_NAMES:
        context_dataset, context_audit = build_context_feature_dataset(
            context, research, feature_set, contract
        )
        cold_dataset = build_feature_dataset(research, feature_set, contract)

        context_by_day = dict(zip(context_dataset.source_days, context_dataset.rows))
        cold_days = cold_dataset.source_days
        aligned_context_rows = tuple(context_by_day[day] for day in cold_days)

        if cold_dataset.labels != tuple(
            dict(zip(context_dataset.source_days, context_dataset.labels))[day] for day in cold_days
        ):
            raise AssertionError(f"label mismatch for {feature_set}")

        if context_dataset.feature_names != cold_dataset.feature_names:
            raise AssertionError(f"feature-name mismatch for {feature_set}")

        max_abs, mean_abs = _max_mean_abs_diff(aligned_context_rows, cold_dataset.rows)
        differing_values = sum(
            1
            for context_row, cold_row in zip(aligned_context_rows, cold_dataset.rows)
            for a, b in zip(context_row, cold_row)
            if not math.isclose(a, b, rel_tol=0.0, abs_tol=1e-12)
        )
        total_values = len(cold_dataset.rows) * cold_dataset.feature_count
        results[feature_set] = {
            "context_seeded_rows": context_dataset.sample_count,
            "cold_start_rows": cold_dataset.sample_count,
            "comparison_rows": len(cold_days),
            "comparison_first_day": cold_days[0] if cold_days else None,
            "comparison_last_day": cold_days[-1] if cold_days else None,
            "feature_count": cold_dataset.feature_count,
            "max_absolute_feature_difference": max_abs,
            "mean_absolute_feature_difference": mean_abs,
            "differing_feature_values": differing_values,
            "total_feature_values": total_values,
            "label_identity": True,
            "context_audit_invariant_ok": context_audit.invariant_ok,
        }

    payload = {
        "status": "PASS",
        "research_rows": len(research),
        "context_rows_available": len(all_context),
        "context_rows_used_for_feature_state": len(context),
        "warmup_required": contract.warmup,
        "label_horizon": contract.horizon,
        "comparison_rule": "identical research source days where cold-start features are valid",
        "source_equivalence_proven": False,
        "interpretation": "quantify feature-state sensitivity to pre-research context; no equivalence claim",
        "feature_sets": results,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 70)
    print("PHASE 5.2 REBUILD — CONTEXT BOUNDARY SENSITIVITY")
    print("=" * 70)
    print(f"RESEARCH ROWS        : {len(research)}")
    print(f"CONTEXT STATE ROWS   : {len(context)}")
    print(f"WARMUP REQUIRED      : {contract.warmup}")
    for name, result in results.items():
        print(
            f"{name:20s}: compare {result['comparison_rows']} rows | "
            f"max_abs={result['max_absolute_feature_difference']:.12g} | "
            f"mean_abs={result['mean_absolute_feature_difference']:.12g} | "
            f"different={result['differing_feature_values']}/{result['total_feature_values']}"
        )
    print(f"STATUS               : {payload['status']}")
    print(f"OUTPUT               : {output}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
