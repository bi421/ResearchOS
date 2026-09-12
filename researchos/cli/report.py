"""Canonical ResearchOS Phase 5.2 report.

Single command:
    python -m researchos.cli.report phase52

This command is read-only with respect to scientific inputs. It loads the
same production data loaders used by Phase 5.2, computes raw/source and
production alignment diagnostics, builds the actual production dataset,
runs the Phase 5.2 comparison, and emits one canonical report.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from researchos.experiments.phase52 import FEATURE_SET_NAMES, Phase52Config, run_phase52_comparison
from researchos.experiments.phase52.dataset import build_macro_augmented_dataset
from researchos.experiments.phase52.drop_diagnostics import diagnose_dataset_drops
from researchos.experiments.phase52.scripts.run_phase52_experiment import (
    _build_common_observation_sample,
    _load_candles,
    _load_macro_series,
)

ROOT = Path(__file__).resolve().parents[2]

XAU_PATH = ROOT / "data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv"
DXY_PATH = ROOT / "data/macro/raw/DXY_Dukascopy_2021_2025.csv"
US10Y_PATH = ROOT / "data/macro/raw/DGS10_fred.csv"
VIX_PATH = ROOT / "data/macro/raw/VIXCLS_fred.csv"

SYMBOL = "XAUUSD"
TIMEFRAME = "1d"
HORIZON = 5
THRESHOLD = 0.0
TRAIN_SIZE = 1000
VALIDATION_SIZE = 200
STEP_SIZE = 200
N_NEIGHBORS = 25
COSTS = {"spread": "fixed:0", "slippage": "fixed:0", "commission": "fixed:0"}
MACROS = ("DXY", "US10Y", "VIX")


@dataclass
class SourceReport:
    name: str
    path: str
    raw_rows: int | None
    production_rows: int | None
    sha256: str | None
    identity: str
    exists: bool
    error: str | None = None


@dataclass
class Report:
    schema: str
    project: dict[str, Any]
    configuration: dict[str, Any]
    data: dict[str, Any]
    alignment: dict[str, Any]
    dataset: dict[str, Any]
    phase52: dict[str, Any]
    evidence_status: dict[str, Any]
    artifacts: dict[str, Any]


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNKNOWN"


def _parse_timestamp(value: str) -> datetime:
    s = value.strip()
    if not s:
        raise ValueError("empty timestamp")
    try:
        n = float(s)
        if abs(n) > 1e11:
            return datetime.fromtimestamp(n / 1000.0, tz=timezone.utc)
        if abs(n) > 1e9:
            return datetime.fromtimestamp(n, tz=timezone.utc)
    except ValueError:
        pass
    s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _raw_timestamp_set(path: Path, name: str) -> tuple[int, set[datetime]]:
    """Read source rows without invoking production filtering/repair."""
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {str(x).strip().lower(): x for x in (reader.fieldnames or [])}
        rows = 0
        timestamps: set[datetime] = set()
        for row in reader:
            rows += 1
            try:
                if name == "XAUUSD":
                    date_key = fields.get("date")
                    time_key = fields.get("time")
                    if date_key and time_key:
                        ts = datetime.strptime(
                            f"{row[date_key].strip()} {row[time_key].strip()}",
                            "%Y.%m.%d %H:%M:%S",
                        ).replace(tzinfo=timezone.utc)
                    else:
                        ts = _parse_timestamp(row[fields["timestamp"]])
                elif "timestamp" in fields:
                    ts = _parse_timestamp(row[fields["timestamp"]])
                elif "observation_date" in fields:
                    ts = datetime.strptime(
                        row[fields["observation_date"]].strip(), "%Y-%m-%d"
                    ).replace(tzinfo=timezone.utc)
                elif "date" in fields:
                    ts = datetime.strptime(
                        row[fields["date"]].strip(), "%Y-%m-%d"
                    ).replace(tzinfo=timezone.utc)
                else:
                    raise KeyError("no supported timestamp column")
                timestamps.add(ts)
            except Exception:
                timestamps.add(ts) if "ts" in locals() else None
                continue
    return rows, timestamps


def _source(name: str, path: Path, identity: str) -> SourceReport:
    if not path.exists():
        return SourceReport(name, str(path.relative_to(ROOT)), None, None, None, identity, False, "file missing")
    try:
        raw_rows, _ = _raw_timestamp_set(path, name)
    except Exception as exc:
        raw_rows = None
        raw_error = str(exc)
    else:
        raw_error = None
    return SourceReport(
        name=name,
        path=str(path.relative_to(ROOT)),
        raw_rows=raw_rows,
        production_rows=None,
        sha256=_sha256(path),
        identity=identity,
        exists=True,
        error=raw_error,
    )


def _production_loads() -> tuple[dict[str, Any], dict[str, set[datetime]], dict[str, SourceReport]]:
    sources = {
        "XAUUSD": _source("XAUUSD", XAU_PATH, "MT5 curated canonical D1"),
        "DXY": _source("DXY", DXY_PATH, "Dukascopy dollaridxusd; secondary DXY series"),
        "US10Y": _source("US10Y", US10Y_PATH, "FRED DGS10"),
        "VIX": _source("VIX", VIX_PATH, "FRED VIXCLS"),
    }
    required = [("XAUUSD", XAU_PATH), ("DXY", DXY_PATH), ("US10Y", US10Y_PATH), ("VIX", VIX_PATH)]
    missing = [name for name, path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing source files: " + ", ".join(missing))

    close, high, low, volume, xau_ts = _load_candles(str(XAU_PATH), "auto", SYMBOL, TIMEFRAME)
    macro: dict[str, list[float]] = {}
    macro_ts: dict[str, list[datetime]] = {}
    for name, path in (("DXY", DXY_PATH), ("US10Y", US10Y_PATH), ("VIX", VIX_PATH)):
        values, timestamps = _load_macro_series(str(path), "auto", name, TIMEFRAME)
        macro[name] = values
        macro_ts[name] = timestamps

    sources["XAUUSD"].production_rows = len(xau_ts)
    for name in MACROS:
        sources[name].production_rows = len(macro_ts[name])

    return (
        {
            "close": close,
            "high": high,
            "low": low,
            "volume": volume,
            "timestamps": xau_ts,
            "macro": macro,
            "macro_timestamps": macro_ts,
        },
        {"XAUUSD": set(xau_ts), **{k: set(v) for k, v in macro_ts.items()}},
        sources,
    )


def _result_dict(result: Any) -> dict[str, Any]:
    metadata = getattr(result, "metadata", {}) or {}
    model = getattr(result, "model", None)
    return {
        "outcome": getattr(result, "outcome", None),
        "folds": getattr(result, "num_folds", None),
        "model_sample_count": getattr(model, "sample_count", None) if model else None,
        "accuracy": getattr(model, "accuracy", None) if model else None,
        "brier": getattr(model, "brier_score", None) if model else None,
        "p_value": getattr(getattr(result, "significance", None), "p_value", None),
        "data_valid": getattr(result, "data_valid", False),
        "leakage_check": getattr(result, "leakage_check", False),
        "out_of_sample": getattr(result, "out_of_sample", False),
        "cost_adjusted": getattr(result, "cost_adjusted", False),
        "reproducible": bool(getattr(result, "reproducibility_hash", None)),
        "reproducibility_hash": getattr(result, "reproducibility_hash", None),
        "blocked_reason": metadata.get("blocked_reason") or metadata.get("reason") or getattr(result, "reason", None),
    }


def _build_report() -> Report:
    loaded, timestamp_sets, sources = _production_loads()

    raw_sets = {}
    for name, path in (("XAUUSD", XAU_PATH), ("DXY", DXY_PATH), ("US10Y", US10Y_PATH), ("VIX", VIX_PATH)):
        _, raw_sets[name] = _raw_timestamp_set(path, name)

    raw_common = set.intersection(*(raw_sets[name] for name in ("XAUUSD", *MACROS)))
    production_common = set.intersection(*(timestamp_sets[name] for name in ("XAUUSD", *MACROS)))

    pairwise = {}
    for name in MACROS:
        common = timestamp_sets["XAUUSD"] & timestamp_sets[name]
        pairwise[name] = {
            "common": len(common),
            "xau_missing": len(timestamp_sets["XAUUSD"] - timestamp_sets[name]),
            "macro_missing_from_xau": sorted(
                (timestamp_sets["XAUUSD"] - timestamp_sets[name]),
                key=lambda x: x.isoformat(),
            )[:10],
        }

    close, high, low, volume, xau_ts = (
        loaded["close"], loaded["high"], loaded["low"], loaded["volume"], loaded["timestamps"]
    )
    common_close, common_high, common_low, common_volume, common_ts, common_macro, common_macro_ts = _build_common_observation_sample(
        close,
        high,
        low,
        volume,
        xau_ts,
        loaded["macro"],
        loaded["macro_timestamps"],
        MACROS,
    )

    drop_diagnostics = diagnose_dataset_drops(
        common_close,
        common_high,
        common_low,
        common_volume,
        common_macro,
        horizon=HORIZON,
        threshold=THRESHOLD,
    )

    dataset, _ = build_macro_augmented_dataset(
        common_close,
        common_high,
        common_low,
        common_volume,
        common_macro,
        horizon=HORIZON,
        threshold=THRESHOLD,
    )

    config = Phase52Config(
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        horizon=HORIZON,
        threshold=THRESHOLD,
        train_size=TRAIN_SIZE,
        validation_size=VALIDATION_SIZE,
        step_size=STEP_SIZE,
        n_neighbors=N_NEIGHBORS,
        spread_spec=COSTS["spread"],
        slippage_spec=COSTS["slippage"],
        commission_spec=COSTS["commission"],
    )
    results = run_phase52_comparison(
        common_close,
        common_high,
        common_low,
        common_volume,
        common_macro,
        config=config,
        timestamps=common_ts,
        macro_timestamps=common_macro_ts,
    )

    result_map = {name: _result_dict(results[name]) for name in FEATURE_SET_NAMES}
    experiment_blocked = any(v["outcome"] == "BLOCKED" for v in result_map.values())
    dataset_blocked = dataset.sample_count < TRAIN_SIZE + VALIDATION_SIZE

    project = {
        "name": "ResearchOS",
        "commit": _git("rev-parse", "HEAD"),
        "working_tree": "CLEAN" if not _git("status", "--porcelain") else "DIRTY",
        "report_source": "LIVE_PRODUCTION_PIPELINE",
    }
    configuration = {
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "horizon": HORIZON,
        "threshold": THRESHOLD,
        "train_size": TRAIN_SIZE,
        "validation_size": VALIDATION_SIZE,
        "step_size": STEP_SIZE,
        "n_neighbors": N_NEIGHBORS,
        **COSTS,
    }
    data = {name: asdict(src) for name, src in sources.items()}
    alignment = {
        "raw_exact_intersection": len(raw_common),
        "production_exact_intersection": len(production_common),
        "raw_vs_production_difference": len(raw_common) - len(production_common),
        "first": min(production_common).date().isoformat(),
        "last": max(production_common).date().isoformat(),
        "dropped_from_xauusd": len(timestamp_sets["XAUUSD"] - production_common),
        "rule": "Exact timestamp equality; no date truncation, interpolation, forward-fill, resampling, or repair",
        "pairwise": pairwise,
    }
    source_indices = dataset.metadata.get("source_indices", [])
    dataset_report = {
        "common_sample": len(common_ts),
        "usable_sample": dataset.sample_count,
        "required_samples": TRAIN_SIZE + VALIDATION_SIZE,
        "shortfall": max(0, TRAIN_SIZE + VALIDATION_SIZE - dataset.sample_count),
        "feature_count": dataset.feature_count,
        "label_count": len(dataset.labels),
        "source_indices": len(source_indices),
        "warmup_dropped": source_indices[0] if source_indices else None,
        "tail_dropped": max(0, len(common_ts) - 1 - source_indices[-1]) if source_indices else None,
        "drop_diagnostics": drop_diagnostics,
        "gate": "BLOCKED" if dataset_blocked else "PASS",
    }
    evidence = {
        "source_data": "PASS",
        "alignment": "AVAILABLE",
        "dataset": "BLOCKED" if dataset_blocked else "PASS",
        "experiment": "BLOCKED" if experiment_blocked else "PASS",
        "overall": "READY" if not dataset_blocked and not experiment_blocked else "NOT READY",
    }

    return Report(
        schema="researchos/canonical-report/v1",
        project=project,
        configuration=configuration,
        data=data,
        alignment=alignment,
        dataset=dataset_report,
        phase52=result_map,
        evidence_status=evidence,
        artifacts={
            "json": "reports/phase52/canonical_phase52_report.json",
            "markdown": "reports/phase52/canonical_phase52_report.md",
        },
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _render(report: Report) -> str:
    r = _json_safe(asdict(report))
    lines: list[str] = []
    lines += ["RESEARCHOS CANONICAL REPORT", "=" * 80]
    lines += ["", "PROJECT", "=" * 80]
    for k, v in r["project"].items():
        lines.append(f"{k:34}: {v}")
    lines += ["", "CONFIGURATION", "=" * 80]
    for k, v in r["configuration"].items():
        lines.append(f"{k:34}: {v}")
    lines += ["", "DATA", "=" * 80]
    for name, item in r["data"].items():
        lines.append(f"{name:34}: raw={item['raw_rows']} production={item['production_rows']} sha256={item['sha256']}")
        lines.append(f"{'':34}  identity={item['identity']}")
    a = r["alignment"]
    lines += ["", "ALIGNMENT", "=" * 80]
    lines.append(f"{'Raw exact intersection':34}: {a['raw_exact_intersection']}")
    lines.append(f"{'Production exact intersection':34}: {a['production_exact_intersection']}")
    lines.append(f"{'Raw -> production loss':34}: {a['raw_vs_production_difference']}")
    lines.append(f"{'XAUUSD dropped':34}: {a['dropped_from_xauusd']}")
    lines.append(f"{'First / Last':34}: {a['first']} / {a['last']}")
    for name, item in a["pairwise"].items():
        lines.append(f"{name + ' pairwise':34}: common={item['common']} xau_missing={item['xau_missing']}")
    lines.append(f"{'Rule':34}: {a['rule']}")
    d = r["dataset"]
    diag = d["drop_diagnostics"]
    lines += ["", "DATASET", "=" * 80]
    for k in ("common_sample", "usable_sample", "required_samples", "shortfall", "feature_count", "label_count", "warmup_dropped", "tail_dropped", "gate"):
        lines.append(f"{k:34}: {d[k]}")
    lines.append(f"{'Dropped rows':34}: {diag['dropped_rows']}")
    lines.append(f"{'Label-missing rows':34}: {diag['label_missing_rows']}")
    lines.append(f"{'Feature-missing rows':34}: {diag['feature_missing_rows']}")
    lines.append(f"{'First retained index':34}: {diag['first_retained_index']}")
    lines.append(f"{'Last retained index':34}: {diag['last_retained_index']}")
    lines.append(f"{'Price / macro features':34}: {diag['price_feature_count']} / {diag['macro_feature_count']}")
    lines.append(f"{'Macro symbols present':34}: {', '.join(diag['macro_symbols_present']) or 'NONE'}")
    if diag["feature_missing_counts"]:
        lines.append(f"{'Feature missing counts':34}: {diag['feature_missing_counts']}")
    lines += ["", "PHASE 5.2", "=" * 80]
    for name, item in r["phase52"].items():
        lines.append(f"{name:34}: {item['outcome']} folds={item['folds']} accuracy={item['accuracy']} brier={item['brier']} p={item['p_value']}")
        if item["blocked_reason"]:
            lines.append(f"{'':34}  reason={item['blocked_reason']}")
    lines += ["", "EVIDENCE STATUS", "=" * 80]
    for k, v in r["evidence_status"].items():
        lines.append(f"{k:34}: {v}")
    lines += ["", "ARTIFACTS", "=" * 80]
    lines.append(f"JSON{'':30}: {r['artifacts']['json']}")
    lines.append(f"Markdown{'':26}: {r['artifacts']['markdown']}")
    lines += ["", "=" * 80]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-command canonical ResearchOS report")
    parser.add_argument("target", choices=["phase52"])
    args = parser.parse_args(argv)
    if args.target != "phase52":
        return 2

    try:
        report = _build_report()
    except Exception as exc:  # noqa: BLE001
        print("RESEARCHOS CANONICAL REPORT")
        print("=" * 80)
        print("OVERALL: BLOCKED")
        print(f"REASON : {type(exc).__name__}: {exc}")
        return 2

    payload = _json_safe(asdict(report))
    json_path = ROOT / report.artifacts["json"]
    md_path = ROOT / report.artifacts["markdown"]
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    rendered = _render(report)
    md_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report.evidence_status["overall"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
