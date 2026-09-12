"""Canonical ResearchOS Phase 5.2 production report.

The report follows one lifecycle: load -> exact-align -> prepare once ->
validate -> execute five feature sets -> render evidence. Scientific gates
remain fail-closed; insufficient real observations are reported as BLOCKED.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from researchos.experiments.phase52 import FEATURE_SET_NAMES, Phase52Config
from researchos.experiments.phase52.execution import run_prepared_phase52_comparison
from researchos.experiments.phase52.prepared import Phase52PreparedData
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
SYMBOL, TIMEFRAME = "XAUUSD", "1d"
HORIZON, THRESHOLD = 5, 0.0
TRAIN_SIZE, VALIDATION_SIZE, STEP_SIZE = 1000, 200, 200
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
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
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
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _raw_timestamp_set(path: Path, name: str) -> tuple[int, set[datetime]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {str(x).strip().lower(): x for x in (reader.fieldnames or [])}
        rows, timestamps = 0, set()
        for row in reader:
            rows += 1
            try:
                if name == "XAUUSD" and fields.get("date") and fields.get("time"):
                    ts = datetime.strptime(f"{row[fields['date']].strip()} {row[fields['time']].strip()}", "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)
                elif "timestamp" in fields:
                    ts = _parse_timestamp(row[fields["timestamp"]])
                elif "observation_date" in fields:
                    ts = datetime.strptime(row[fields["observation_date"]].strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                elif "date" in fields:
                    ts = datetime.strptime(row[fields["date"]].strip(), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                else:
                    raise KeyError("no supported timestamp column")
                timestamps.add(ts)
            except Exception:
                continue
    return rows, timestamps


def _source(name: str, path: Path, identity: str) -> SourceReport:
    if not path.exists():
        return SourceReport(name, str(path.relative_to(ROOT)), None, None, None, identity, False, "file missing")
    try:
        raw_rows, _ = _raw_timestamp_set(path, name)
        error = None
    except Exception as exc:
        raw_rows, error = None, str(exc)
    return SourceReport(name, str(path.relative_to(ROOT)), raw_rows, None, _sha256(path), identity, True, error)


def _production_loads():
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
    macro, macro_ts = {}, {}
    for name, path in (("DXY", DXY_PATH), ("US10Y", US10Y_PATH), ("VIX", VIX_PATH)):
        macro[name], macro_ts[name] = _load_macro_series(str(path), "auto", name, TIMEFRAME)
    sources["XAUUSD"].production_rows = len(xau_ts)
    for name in MACROS:
        sources[name].production_rows = len(macro_ts[name])
    return {"close": close, "high": high, "low": low, "volume": volume, "timestamps": xau_ts, "macro": macro, "macro_timestamps": macro_ts}, sources


def _result_dict(result: Any) -> dict[str, Any]:
    model = getattr(result, "model", None)
    baseline = getattr(result, "baseline", None)
    significance = getattr(result, "significance", None)
    calibration = getattr(result, "calibration", None)
    metadata = getattr(result, "metadata", {}) or {}
    accuracy = getattr(model, "accuracy", None) if model else None
    baseline_accuracy = getattr(baseline, "accuracy", None) if baseline else None
    return {
        "outcome": getattr(result, "outcome", None),
        "folds": getattr(result, "num_folds", None),
        "validation_samples": getattr(model, "sample_count", None) if model else None,
        "accuracy": accuracy,
        "baseline_accuracy": baseline_accuracy,
        "accuracy_delta_vs_baseline": (accuracy - baseline_accuracy) if accuracy is not None and baseline_accuracy is not None else None,
        "brier": getattr(model, "brier_score", None) if model else None,
        "baseline_brier": getattr(baseline, "brier_score", None) if baseline else None,
        "brier_delta_vs_baseline": (getattr(model, "brier_score", None) - getattr(baseline, "brier_score", None)) if model and baseline and getattr(model, "brier_score", None) is not None and getattr(baseline, "brier_score", None) is not None else None,
        "p_value": getattr(significance, "p_value", None) if significance else None,
        "significant": getattr(significance, "significant", None) if significance else None,
        "calibration_status": getattr(calibration, "status", None) if calibration else None,
        "data_valid": getattr(result, "data_valid", False),
        "leakage_check": getattr(result, "leakage_check", False),
        "out_of_sample": getattr(result, "out_of_sample", False),
        "cost_adjusted": getattr(result, "cost_adjusted", False),
        "reproducible": bool(getattr(result, "reproducibility_hash", None) or metadata.get("combined_input_hash")),
        "reproducibility_hash": getattr(result, "reproducibility_hash", None),
        "combined_input_hash": metadata.get("combined_input_hash"),
        "blocked_reason": metadata.get("blocked_reason") or metadata.get("reason") or getattr(result, "reason", None),
    }


def _build_report() -> Report:
    loaded, sources = _production_loads()
    raw_sets = {name: _raw_timestamp_set(path, name)[1] for name, path in (("XAUUSD", XAU_PATH), ("DXY", DXY_PATH), ("US10Y", US10Y_PATH), ("VIX", VIX_PATH))}
    production_sets = {"XAUUSD": set(loaded["timestamps"]), **{k: set(v) for k, v in loaded["macro_timestamps"].items()}}
    raw_common = set.intersection(*(raw_sets[n] for n in ("XAUUSD", *MACROS)))
    production_common = set.intersection(*(production_sets[n] for n in ("XAUUSD", *MACROS)))
    pairwise = {}
    for name in MACROS:
        missing = sorted(production_sets["XAUUSD"] - production_sets[name], key=lambda x: x.isoformat())
        pairwise[name] = {"common": len(production_sets["XAUUSD"] & production_sets[name]), "xau_missing": len(missing), "xau_missing_examples": [x.isoformat() for x in missing[:10]]}

    common_close, common_high, common_low, common_volume, common_ts, common_macro, common_macro_ts = _build_common_observation_sample(
        loaded["close"], loaded["high"], loaded["low"], loaded["volume"], loaded["timestamps"], loaded["macro"], loaded["macro_timestamps"], MACROS
    )
    prepared = Phase52PreparedData.build(
        common_close, common_high, common_low, common_volume, common_ts, common_macro_ts, common_macro,
        horizon=HORIZON, threshold=THRESHOLD, required_macro_symbols=MACROS,
    )
    prepared.validate(MACROS)
    drop_diagnostics = diagnose_dataset_drops(common_close, common_high, common_low, common_volume, common_macro, horizon=HORIZON, threshold=THRESHOLD)
    config = Phase52Config(symbol=SYMBOL, timeframe=TIMEFRAME, horizon=HORIZON, threshold=THRESHOLD, train_size=TRAIN_SIZE, validation_size=VALIDATION_SIZE, step_size=STEP_SIZE, n_neighbors=N_NEIGHBORS, spread_spec=COSTS["spread"], slippage_spec=COSTS["slippage"], commission_spec=COSTS["commission"])
    results = run_prepared_phase52_comparison(prepared, config)
    result_map = {name: _result_dict(results[name]) for name in FEATURE_SET_NAMES}
    dataset_blocked = prepared.sample_count < TRAIN_SIZE + VALIDATION_SIZE
    experiment_blocked = any(v["outcome"] == "BLOCKED" for v in result_map.values())
    source_indices = prepared.source_indices
    dataset_report = {
        "common_sample": len(common_ts), "usable_sample": prepared.sample_count, "required_samples": TRAIN_SIZE + VALIDATION_SIZE,
        "shortfall": max(0, TRAIN_SIZE + VALIDATION_SIZE - prepared.sample_count), "feature_count": prepared.dataset.feature_count,
        "label_count": len(prepared.dataset.labels), "source_indices": len(source_indices),
        "warmup_dropped": source_indices[0] if source_indices else None,
        "tail_dropped": max(0, len(common_ts) - 1 - source_indices[-1]) if source_indices else None,
        "drop_diagnostics": drop_diagnostics, "gate": "BLOCKED" if dataset_blocked else "PASS",
        "combined_input_hash": prepared.input_provenance.get("combined_input_hash"),
        "dataset_contract": "single_materialized_prepared_dataset",
    }
    evidence = {
        "source_data": "PASS", "alignment": "AVAILABLE", "dataset": "BLOCKED" if dataset_blocked else "PASS",
        "experiment": "BLOCKED" if experiment_blocked else "PASS", "overall": "READY" if not dataset_blocked and not experiment_blocked else "NOT READY",
        "scientific_claim": "NO_PREDICTIVE_CLAIM_WHILE_BLOCKED" if dataset_blocked or experiment_blocked else "EVALUATE_ONLY_AFTER_ALL_GATES_PASS",
        "blocking_reason": "REAL XAUUSD + MACRO DATA REQUIRED (insufficient aligned samples after merge)" if dataset_blocked else None,
    }
    if production_common:
        first, last = min(production_common).date().isoformat(), max(production_common).date().isoformat()
    else:
        first = last = None
    alignment = {
        "raw_exact_intersection": len(raw_common), "production_exact_intersection": len(production_common),
        "raw_vs_production_difference": len(raw_common) - len(production_common), "first": first, "last": last,
        "dropped_from_xauusd": len(production_sets["XAUUSD"] - production_common),
        "rule": "Exact timestamp equality; no date truncation, interpolation, forward-fill, resampling, or repair", "pairwise": pairwise,
    }
    return Report(
        schema="researchos/canonical-report/v2", project={"name": "ResearchOS", "commit": _git("rev-parse", "HEAD"), "working_tree": "CLEAN" if not _git("status", "--porcelain") else "DIRTY", "report_source": "LIVE_PRODUCTION_PIPELINE"},
        configuration={"symbol": SYMBOL, "timeframe": TIMEFRAME, "horizon": HORIZON, "threshold": THRESHOLD, "train_size": TRAIN_SIZE, "validation_size": VALIDATION_SIZE, "step_size": STEP_SIZE, "n_neighbors": N_NEIGHBORS, **COSTS},
        data={name: asdict(src) for name, src in sources.items()}, alignment=alignment, dataset=dataset_report, phase52=result_map, evidence_status=evidence,
        artifacts={"json": "reports/phase52/canonical_phase52_report.json", "markdown": "reports/phase52/canonical_phase52_report.md"},
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)): return [_json_safe(v) for v in value]
    if isinstance(value, Path): return str(value)
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)): return None
    return value


def _render(report: Report) -> str:
    r = _json_safe(asdict(report)); lines = [
        "# ResearchOS — Canonical Phase 5.2 Report", "", f"**Overall gate:** {r['evidence_status']['overall']}",
        f"**Scientific claim:** {r['evidence_status']['scientific_claim']}", "",
        "## Executive conclusion", "",
        f"Usable observations: **{r['dataset']['usable_sample']} / {r['dataset']['required_samples']}**; shortfall: **{r['dataset']['shortfall']}**.",
        f"Dataset gate: **{r['dataset']['gate']}**. Experiment gate: **{r['evidence_status']['experiment']}**.",
    ]
    if r['evidence_status']['blocking_reason']: lines += [f"Blocking reason: **{r['evidence_status']['blocking_reason']}**."]
    lines += ["", "## Data identity", "", "| Source | Production rows | SHA-256 |", "|---|---:|---|"]
    for name, src in r["data"].items(): lines.append(f"| {name} | {src['production_rows']} | `{src['sha256']}` |")
    lines += ["", "## Alignment", "", f"Exact raw intersection: **{r['alignment']['raw_exact_intersection']}**", f"Exact production intersection: **{r['alignment']['production_exact_intersection']}**", f"Raw → production difference: **{r['alignment']['raw_vs_production_difference']}**", f"Rule: {r['alignment']['rule']}", "", "## Dataset accounting", "", f"Common aligned rows: **{r['dataset']['common_sample']}**", f"Warmup dropped: **{r['dataset']['warmup_dropped']}**", f"Tail dropped: **{r['dataset']['tail_dropped']}**", f"Usable labels: **{r['dataset']['label_count']}**", f"Combined input hash: `{r['dataset']['combined_input_hash']}`", "", "## Feature-set comparison", "", "| Feature set | Outcome | Samples | Accuracy | Baseline | Δ accuracy | Brier | Δ Brier | p-value |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, v in r["phase52"].items():
        fmt = lambda x: "—" if x is None else (f"{x:.4f}" if isinstance(x, float) else str(x))
        lines.append(f"| {name} | {v['outcome']} | {v['validation_samples'] or 0} | {fmt(v['accuracy'])} | {fmt(v['baseline_accuracy'])} | {fmt(v['accuracy_delta_vs_baseline'])} | {fmt(v['brier'])} | {fmt(v['brier_delta_vs_baseline'])} | {fmt(v['p_value'])} |")
    lines += ["", "## Evidence interpretation", "", "### What this proves", "- The report used the live production loaders and exact timestamp identity checks.", "- All feature sets consumed the same single prepared dataset and source-index mapping.", "- When the sample gate is blocked, no predictive-performance claim is certified.", "", "### What this does not prove", "- It does not prove profitable trading or future predictive power.", "- It does not turn an insufficient sample into evidence by relaxing the gate.", "- It does not justify causal macro conclusions from this experiment alone.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Canonical ResearchOS Phase 5.2 report")
    parser.add_argument("command", choices=["phase52"])
    args = parser.parse_args()
    report = _build_report()
    payload = _json_safe(asdict(report))
    out_dir = ROOT / "reports/phase52"; out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "canonical_phase52_report.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "canonical_phase52_report.md").write_text(_render(report) + "\n", encoding="utf-8")
    print(_render(report))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
