"""Audit context-seeded Phase 5.2 feature construction on real daily data.

The script intentionally requires an explicit --source-validated acknowledgement.
That flag is not a scientific proof; it records that a human has reviewed the
source-continuity audit before cross-source context is allowed into feature state.
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
DEFAULT_OUTPUT = ROOT / "reports/phase52_rebuild/context_feature_audit.json"


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-xau", default=str(DEFAULT_CONTEXT_XAU))
    parser.add_argument("--context-dxy", default=str(DEFAULT_CONTEXT_DXY))
    parser.add_argument("--us10y", default=str(DEFAULT_US10Y))
    parser.add_argument("--vix", default=str(DEFAULT_VIX))
    parser.add_argument("--research", default=str(DEFAULT_RESEARCH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--source-validated",
        action="store_true",
        help="Explicitly acknowledge that source-continuity review has been completed.",
    )
    args = parser.parse_args(argv)

    if not args.source_validated:
        print("BLOCKED: pass --source-validated only after reviewing context_continuity_audit.json")
        return 2

    context = load_context_daily_observations(
        args.context_xau, args.context_dxy, args.us10y, args.vix
    )
    research = _load_research_daily(Path(args.research))
    contract = Phase52FeatureContract()

    results: dict[str, object] = {}
    for feature_set in FEATURE_SET_NAMES:
        dataset, audit = build_context_feature_dataset(
            context, research, feature_set, contract
        )
        results[feature_set] = {
            "feature_count": dataset.feature_count,
            "sample_count": dataset.sample_count,
            "expected_sample_count": len(research) - contract.horizon,
            "first_source_day": dataset.source_days[0] if dataset.source_days else None,
            "last_source_day": dataset.source_days[-1] if dataset.source_days else None,
            "first_prediction_timestamp": dataset.prediction_timestamps[0] if dataset.prediction_timestamps else None,
            "last_prediction_timestamp": dataset.prediction_timestamps[-1] if dataset.prediction_timestamps else None,
            "audit": audit.__dict__,
            "gate": "PASS" if dataset.sample_count >= contract.minimum_samples else "BLOCKED",
        }

    payload = {
        "status": "PASS" if all(r["gate"] == "PASS" for r in results.values()) else "BLOCKED",
        "source_validated_acknowledged": True,
        "context_rows": len(context),
        "research_rows": len(research),
        "label_horizon": contract.horizon,
        "warmup_required": contract.warmup,
        "minimum_required": contract.minimum_samples,
        "expected_research_samples": len(research) - contract.horizon,
        "feature_sets": results,
        "context_is_feature_state_only": True,
        "context_rows_emitted": False,
        "no_interpolation_or_forward_fill": True,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 70)
    print("PHASE 5.2 REBUILD — CONTEXT FEATURE AUDIT")
    print("=" * 70)
    print(f"CONTEXT ROWS         : {len(context)}")
    print(f"RESEARCH ROWS        : {len(research)}")
    print(f"EXPECTED RESEARCH    : {len(research) - contract.horizon}")
    print(f"MINIMUM REQUIRED     : {contract.minimum_samples}")
    for name, result in results.items():
        print(f"{name:20s}: {result['sample_count']} rows / {result['feature_count']} features / {result['gate']}")
    print(f"STATUS               : {payload['status']}")
    print(f"OUTPUT               : {output}")
    print("=" * 70)
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
