"""Run the Phase 5.2 rebuild feature/leakage audit on real source data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from researchos.experiments.phase52_rebuild.daily_dataset import build_daily_common_dataset
from researchos.experiments.phase52_rebuild.feature_contract import Phase52FeatureContract
from researchos.experiments.phase52_rebuild.feature_dataset import build_feature_dataset


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--dxy", required=True)
    parser.add_argument("--us10y", required=True)
    parser.add_argument("--vix", required=True)
    parser.add_argument("--output", default="reports/phase52_rebuild/feature_audit.json")
    args = parser.parse_args()

    observations = build_daily_common_dataset(args.csv, args.dxy, args.us10y, args.vix)
    contract = Phase52FeatureContract()

    results: dict[str, object] = {}
    for name in ("PRICE_ONLY", "PRICE_DXY", "PRICE_US10Y", "PRICE_VIX", "PRICE_ALL"):
        dataset = build_feature_dataset(observations, name, contract)
        results[name] = {
            "feature_count": dataset.feature_count,
            "sample_count": dataset.sample_count,
            "first_source_day": dataset.source_days[0] if dataset.source_days else None,
            "last_source_day": dataset.source_days[-1] if dataset.source_days else None,
            "first_prediction_timestamp": dataset.prediction_timestamps[0] if dataset.prediction_timestamps else None,
            "last_prediction_timestamp": dataset.prediction_timestamps[-1] if dataset.prediction_timestamps else None,
            "minimum_required": contract.minimum_samples,
            "gate": "PASS" if dataset.sample_count >= contract.minimum_samples else "BLOCKED",
        }

    payload = {
        "status": "BLOCKED" if len(observations) - contract.warmup - contract.horizon < contract.minimum_samples else "PASS",
        "common_rows": len(observations),
        "warmup_rows": contract.warmup,
        "label_horizon": contract.horizon,
        "final_usable_expected": len(observations) - contract.warmup - contract.horizon,
        "minimum_required": contract.minimum_samples,
        "train_size": contract.train_size,
        "validation_size": contract.validation_size,
        "prediction_timing": contract.prediction_timing,
        "label_definition": contract.label_definition,
        "feature_sets": results,
    }
    payload["summary_sha256"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 70)
    print("PHASE 5.2 REBUILD — FEATURE / LEAKAGE AUDIT")
    print("=" * 70)
    print(f"COMMON ROWS           : {len(observations)}")
    print(f"WARMUP                : {contract.warmup}")
    print(f"LABEL HORIZON         : {contract.horizon}")
    print(f"FINAL USABLE EXPECTED : {payload['final_usable_expected']}")
    print(f"MINIMUM REQUIRED      : {contract.minimum_samples}")
    for name, result in results.items():
        print(f"{name:20s}: {result['sample_count']} rows / {result['feature_count']} features / {result['gate']}")
    print(f"SUMMARY SHA-256       : {payload['summary_sha256']}")
    print(f"OUTPUT                : {output}")
    print(f"STATUS                : {payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
