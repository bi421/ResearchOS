"""Run the production XAUUSD Market Memory evidence pipeline on a local D1 CSV.

This is an operator-facing entry point for the real-data milestone. It does not
change the decision pipeline or trading logic. It runs the existing strict
Market Memory pipeline and requires the certified C++ numerical backend by
default, then writes a machine-readable evidence report and a small
human-readable summary.

Example:
    python scripts/run_xauusd_production_evidence.py \
        --input data/curated/xauusd/xauusd_d1_2021_2025_mt5_final.csv \
        --output reports/xauusd_production_evidence.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from researchos.market_memory.strict_pipeline import run_strict_market_memory_pipeline


def _report_to_dict(report: Any) -> dict[str, Any]:
    serializer = getattr(report, "to_dict", None)
    if callable(serializer):
        value = serializer()
        if isinstance(value, dict):
            return value
    raise TypeError("MarketMemoryReport must expose to_dict() for production evidence export")


def _summary(report: dict[str, Any], input_path: Path) -> str:
    outcomes = report.get("outcomes", {})
    backend = outcomes.get("production_quant_backend", {})
    returns_backend = backend.get("returns", {})
    statistics_backend = backend.get("statistics", {})
    lines = [
        "# XAUUSD Production Evidence",
        "",
        f"- Input: `{input_path}`",
        f"- Asset: `{report.get('asset', 'XAUUSD')}`",
        f"- Timeframe: `{report.get('timeframe', 'D1')}`",
        f"- Status: **{report.get('overall_status', 'UNKNOWN')}**",
        f"- Total events: **{outcomes.get('total_events', report.get('total_events', 0))}**",
        f"- Bullish events: **{outcomes.get('bullish_count', 0)}**",
        f"- Bearish events: **{outcomes.get('bearish_count', 0)}**",
        f"- Average 1D return: **{outcomes.get('avg_return_1d', 0.0):.8f}**",
        "",
        "## Production Quant Backend",
        "",
        f"- Returns backend: **{returns_backend.get('backend', 'UNKNOWN')} {returns_backend.get('version', '')}**",
        f"- Returns validation: **{returns_backend.get('validation_status', 'UNKNOWN')}**",
        f"- Returns fallback: **{returns_backend.get('fallback_used', 'UNKNOWN')}**",
        f"- Statistics backend: **{statistics_backend.get('backend', 'UNKNOWN')} {statistics_backend.get('version', '')}**",
        f"- Statistics validation: **{statistics_backend.get('validation_status', 'UNKNOWN')}**",
        f"- Statistics fallback: **{statistics_backend.get('fallback_used', 'UNKNOWN')}**",
        "",
        "## Evidence records",
    ]
    for record in report.get("evidence_records", []):
        result = record.get("result", {})
        lines.append(
            f"- {record.get('finding_name', 'unknown')}: "
            f"status={record.get('status', 'UNKNOWN')}, "
            f"n={record.get('sample_size', 0)}, "
            f"p={result.get('raw_probability', 0.0):.6f}"
        )
    lines.extend([
        "",
        "## Interpretation rule",
        "",
        "This report is evidence, not a trading instruction. A finding is not",
        "promoted to predictive intelligence unless the validated evidence and",
        "out-of-sample requirements are satisfied.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to the validated XAUUSD D1 CSV")
    parser.add_argument("--output", required=True, help="JSON evidence report path")
    parser.add_argument(
        "--summary",
        default=None,
        help="Optional Markdown summary path (default: alongside JSON as .md)",
    )
    parser.add_argument("--fast", type=int, default=20, help="Fast SMA period")
    parser.add_argument("--slow", type=int, default=100, help="Slow SMA period")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed")
    parser.add_argument("--minimum-events", type=int, default=100)
    parser.add_argument(
        "--allow-python-fallback",
        action="store_true",
        help="Allow Python fallback for the production numerical boundary (not recommended for C++ certification).",
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    summary_path = (
        Path(args.summary).expanduser().resolve()
        if args.summary
        else output_path.with_suffix(".md")
    )

    if not input_path.is_file():
        raise FileNotFoundError(f"XAUUSD D1 input not found: {input_path}")

    report = run_strict_market_memory_pipeline(
        str(input_path),
        fast_period=args.fast,
        slow_period=args.slow,
        seed=args.seed,
        minimum_events=args.minimum_events,
        require_cpp=not args.allow_python_fallback,
    )
    payload = _report_to_dict(report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    summary_path.write_text(_summary(payload, input_path), encoding="utf-8")

    backend = payload.get("outcomes", {}).get("production_quant_backend", {})
    returns_backend = backend.get("returns", {})
    print(f"Evidence status : {payload.get('overall_status', 'UNKNOWN')}")
    print(f"Events          : {payload.get('total_events', 0)}")
    print(
        "C++ backend     : "
        f"{returns_backend.get('backend', 'UNKNOWN')} "
        f"v{returns_backend.get('version', 'UNKNOWN')} "
        f"fallback={returns_backend.get('fallback_used', 'UNKNOWN')}"
    )
    print(f"JSON report     : {output_path}")
    print(f"Markdown report : {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
