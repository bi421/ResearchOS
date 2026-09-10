"""Audit feature initialization sensitivity against a fixed long-context reference.

This is a scientific initialization audit, not a model-performance test. It compares
identical research-period source days under multiple strictly pre-research context
depths. The longest requested depth is treated as the reference so convergence can
be assessed against a fixed target rather than by potentially misleading adjacent
pair comparisons. It does not judge Dukascopy/MT5 source equivalence and does not
make predictive claims.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from researchos.experiments.phase52_rebuild.context_dataset import load_context_daily_observations
from researchos.experiments.phase52_rebuild.context_features import build_context_feature_dataset
from researchos.experiments.phase52_rebuild.daily_dataset import DailyObservation
from researchos.experiments.phase52_rebuild.feature_contract import FEATURE_SET_NAMES, Phase52FeatureContract

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT_XAU = ROOT / "data/macro/context/dukascopy_2020/XAUUSD_Dukascopy_M1_2020_context.csv"
DEFAULT_CONTEXT_DXY = ROOT / "data/macro/context/dukascopy_2020/DXY_Dukascopy_D1_2020_context.csv"
DEFAULT_US10Y = ROOT / "data/macro/raw/DGS10_fred.csv"
DEFAULT_VIX = ROOT / "data/macro/raw/VIXCLS_fred.csv"
DEFAULT_RESEARCH = ROOT / "reports/phase52_rebuild/daily_common_dataset.csv"
DEFAULT_OUTPUT = ROOT / "reports/phase52_rebuild/context_initialization_convergence.json"


def _load_research(path: Path) -> tuple[DailyObservation, ...]:
    rows: list[DailyObservation] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            rows.append(
                DailyObservation(
                    day=str(raw["day"]), timestamp=str(raw["timestamp"]),
                    open=float(raw["open"]), high=float(raw["high"]),
                    low=float(raw["low"]), close=float(raw["close"]),
                    tick_volume=float(raw["tick_volume"]),
                    spread=None if raw.get("spread") in (None, "", "None") else float(raw["spread"]),
                    real_volume=float(raw["real_volume"]), dxy=float(raw["dxy"]),
                    us10y=float(raw["us10y"]), vix=float(raw["vix"]),
                    m1_rows=int(float(raw["m1_rows"])),
                )
            )
    return tuple(rows)


def _relative_difference(a: float, b: float) -> float:
    scale = max(abs(a), abs(b), 1e-12)
    return abs(a - b) / scale


def _compare(
    left: tuple[tuple[float, ...], ...],
    right: tuple[tuple[float, ...], ...],
    names: tuple[str, ...],
    days: tuple[str, ...],
) -> dict[str, object]:
    by_feature: dict[str, dict[str, float | int]] = {}
    top: list[dict[str, object]] = []
    for day, left_row, right_row in zip(days, left, right):
        for name, a, b in zip(names, left_row, right_row):
            abs_diff = abs(a - b)
            rel_diff = _relative_difference(a, b)
            item = by_feature.setdefault(name, {
                "count": 0,
                "max_absolute_difference": 0.0,
                "max_relative_difference": 0.0,
                "sum_absolute_difference": 0.0,
                "sum_relative_difference": 0.0,
            })
            item["count"] += 1
            item["max_absolute_difference"] = max(float(item["max_absolute_difference"]), abs_diff)
            item["max_relative_difference"] = max(float(item["max_relative_difference"]), rel_diff)
            item["sum_absolute_difference"] += abs_diff
            item["sum_relative_difference"] += rel_diff
            if abs_diff > 1e-12:
                top.append({
                    "day": day,
                    "feature": name,
                    "left": a,
                    "right": b,
                    "absolute_difference": abs_diff,
                    "relative_difference": rel_diff,
                })
    for item in by_feature.values():
        count = int(item["count"])
        item["mean_absolute_difference"] = float(item["sum_absolute_difference"]) / count
        item["mean_relative_difference"] = float(item["sum_relative_difference"]) / count
        del item["sum_absolute_difference"]
        del item["sum_relative_difference"]
    top.sort(key=lambda r: (-float(r["absolute_difference"]), str(r["day"]), str(r["feature"])))
    affected = sorted({str(r["day"]) for r in top})
    return {
        "differing_feature_values": len(top),
        "total_feature_values": len(days) * len(names),
        "affected_days": len(affected),
        "affected_day_first": affected[0] if affected else None,
        "affected_day_last": affected[-1] if affected else None,
        "by_feature": dict(sorted(by_feature.items(), key=lambda kv: (-int(kv[1]["count"]), kv[0]))),
        "top_differences": top[:20],
    }


def _supports_monotone_improvement(
    diagnostics: list[tuple[int, float, float]],
) -> bool:
    """Return True when reference-relative max and mean errors do not increase with depth."""
    if len(diagnostics) < 2:
        return False
    previous_max = float("inf")
    previous_mean = float("inf")
    for _, max_diff, mean_diff in diagnostics:
        if max_diff > previous_max + 1e-12 or mean_diff > previous_mean + 1e-12:
            return False
        previous_max = max_diff
        previous_mean = mean_diff
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--context-xau", default=str(DEFAULT_CONTEXT_XAU))
    p.add_argument("--context-dxy", default=str(DEFAULT_CONTEXT_DXY))
    p.add_argument("--us10y", default=str(DEFAULT_US10Y))
    p.add_argument("--vix", default=str(DEFAULT_VIX))
    p.add_argument("--research", default=str(DEFAULT_RESEARCH))
    p.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p.add_argument("--depths", default="60,70,83,120,180,240")
    args = p.parse_args(argv)

    research = _load_research(Path(args.research))
    all_context = load_context_daily_observations(args.context_xau, args.context_dxy, args.us10y, args.vix)
    pre = tuple(obs for obs in all_context if obs.day < research[0].day)
    contract = Phase52FeatureContract()
    depths = tuple(sorted({int(x.strip()) for x in args.depths.split(",") if x.strip()}))
    if len(depths) < 2:
        raise ValueError("at least two context depths are required")
    if any(d < contract.warmup for d in depths):
        raise ValueError(f"all context depths must be >= {contract.warmup}: {depths}")
    if max(depths) > len(pre):
        raise ValueError(
            f"requested context depth {max(depths)} exceeds available pre-research rows {len(pre)}"
        )

    reference_depth = max(depths)
    payload: dict[str, object] = {
        "status": "PASS",
        "scientific_convergence_status": "NOT_PROVEN",
        "research_rows": len(research),
        "research_start": research[0].day,
        "available_pre_research_context_rows": len(pre),
        "depths": list(depths),
        "reference_depth": reference_depth,
        "source_equivalence_proven": False,
        "feature_sets": {},
        "interpretation": (
            "Each shorter context depth is compared against the fixed longest-context reference. "
            "A structural PASS means the audit executed and dataset invariants held. "
            "Scientific convergence is supported only when reference-relative maximum and mean errors "
            "do not increase as context depth grows; this does not prove source equivalence, leakage safety, "
            "or predictive value."
        ),
    }

    all_scientifically_monotone = True

    for feature_set in FEATURE_SET_NAMES:
        datasets: dict[int, object] = {}
        for depth in depths:
            context = pre[-depth:]
            dataset, audit = build_context_feature_dataset(context, research, feature_set, contract)
            if not audit.invariant_ok:
                payload["status"] = "FAIL"
            datasets[depth] = dataset

        reference = datasets[reference_depth]
        ref_map = dict(zip(reference.source_days, reference.rows))
        fs: dict[str, object] = {
            "reference_depth": reference_depth,
            "depths": {},
            "reference_relative_convergence": {},
        }
        for depth in depths:
            ds = datasets[depth]
            fs["depths"][str(depth)] = {
                "rows": len(ds.source_days),
                "first_source_day": ds.source_days[0] if ds.source_days else None,
                "last_source_day": ds.source_days[-1] if ds.source_days else None,
            }

        diagnostics: list[tuple[int, float, float]] = []
        for depth in depths:
            ds = datasets[depth]
            left_map = dict(zip(ds.source_days, ds.rows))
            common_days = tuple(d for d in ds.source_days if d in ref_map)
            compared = _compare(
                tuple(left_map[d] for d in common_days),
                tuple(ref_map[d] for d in common_days),
                ds.feature_names,
                common_days,
            )
            fs["reference_relative_convergence"][str(depth)] = {
                "comparison_rows": len(common_days),
                **compared,
            }
            by_feature = compared["by_feature"]
            max_abs = max(
                (float(v["max_absolute_difference"]) for v in by_feature.values()),
                default=0.0,
            )
            mean_abs = (
                sum(float(v["mean_absolute_difference"]) for v in by_feature.values())
                / len(by_feature)
                if by_feature else 0.0
            )
            diagnostics.append((depth, max_abs, mean_abs))

        monotone = _supports_monotone_improvement(diagnostics)
        fs["reference_convergence_monotone"] = monotone
        if not monotone:
            all_scientifically_monotone = False
        payload["feature_sets"][feature_set] = fs

    if payload["status"] == "PASS" and all_scientifically_monotone:
        payload["scientific_convergence_status"] = "SUPPORTED"

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 70)
    print("PHASE 5.2 REBUILD — CONTEXT INITIALIZATION CONVERGENCE")
    print("=" * 70)
    print(f"RESEARCH ROWS        : {len(research)}")
    print(f"PRE-RESEARCH CONTEXT : {len(pre)}")
    print(f"DEPTHS               : {','.join(map(str, depths))}")
    print(f"REFERENCE DEPTH      : {reference_depth}")
    for feature_set, result in payload["feature_sets"].items():
        print(f"{feature_set:20s}")
        for depth in depths:
            audit = result["reference_relative_convergence"][str(depth)]
            print(
                f"  depth={depth:3d} vs ref : affected_days={audit['affected_days']} | "
                f"differing={audit['differing_feature_values']}/{audit['total_feature_values']}"
            )
            if audit["top_differences"]:
                top = audit["top_differences"][0]
                print(
                    f"    TOP              : {top['day']} / {top['feature']} / "
                    f"abs_diff={top['absolute_difference']:.12g} / "
                    f"rel_diff={top['relative_difference']:.12g}"
                )
        print(f"  MONOTONE           : {result['reference_convergence_monotone']}")
    print(f"STRUCTURAL STATUS    : {payload['status']}")
    print(f"SCIENTIFIC STATUS    : {payload['scientific_convergence_status']}")
    print(f"OUTPUT               : {output}")
    print("=" * 70)
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
