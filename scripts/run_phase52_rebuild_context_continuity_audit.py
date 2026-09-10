from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from researchos.experiments.phase52_rebuild.daily_dataset import load_daily_xau_from_m1, load_dxy_daily

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_XAU = ROOT / "data/macro/context/dukascopy_2020/XAUUSD_Dukascopy_M1_2020_context.csv"
CONTEXT_DXY = ROOT / "data/macro/context/dukascopy_2020/DXY_Dukascopy_D1_2020_context.csv"
RESEARCH_XAU = ROOT / "data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.csv"
RESEARCH_DXY = ROOT / "data/macro/raw/DXY_Dukascopy_2021_2025.csv"
OUT = ROOT / "reports/phase52_rebuild/context_continuity_audit.json"


def _utc_day(value: str) -> str:
    n = int(value.strip())
    dt = datetime.fromtimestamp(n / 1000, tz=timezone.utc)
    return dt.date().isoformat()


def _load_dukascopy_xau_daily(path: Path) -> dict[str, dict[str, float]]:
    """Aggregate Dukascopy XAUUSD M1 using the same OHLC daily rule as research data."""
    groups: dict[str, list[dict[str, float | str]]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        fields = {str(x).strip().lower() for x in (reader.fieldnames or [])}
        if not required.issubset(fields):
            raise ValueError(f"unexpected Dukascopy XAU schema: {sorted(fields)}")
        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
            ts = str(row["timestamp"]).strip()
            day = _utc_day(ts)
            groups.setdefault(day, []).append(
                {
                    "timestamp": ts,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                }
            )

    output: dict[str, dict[str, float]] = {}
    for day in sorted(groups):
        rows = sorted(groups[day], key=lambda x: str(x["timestamp"]))
        output[day] = {
            "open": float(rows[0]["open"]),
            "high": max(float(r["high"]) for r in rows),
            "low": min(float(r["low"]) for r in rows),
            "close": float(rows[-1]["close"]),
            "volume": sum(float(r["volume"]) for r in rows),
        }
    return output


def _load_dukascopy_daily(path: Path) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        fields = {str(x).strip().lower() for x in (reader.fieldnames or [])}
        if not required.issubset(fields):
            raise ValueError(f"unexpected Dukascopy schema: {sorted(fields)}")
        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
            day = _utc_day(str(row["timestamp"]))
            if day in out:
                raise ValueError(f"duplicate Dukascopy calendar day: {day}")
            out[day] = {k: float(row[k]) for k in ("open", "high", "low", "close", "volume")}
    return out


def _rel_diff(a: float, b: float) -> float:
    scale = max(abs(a), abs(b), 1e-12)
    return abs(a - b) / scale


def main() -> int:
    missing = [str(p) for p in (CONTEXT_XAU, CONTEXT_DXY, RESEARCH_XAU, RESEARCH_DXY) if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required files:\n" + "\n".join(missing))

    # Context XAU uses Dukascopy's schema, so parse and aggregate it independently.
    # The aggregation rule is intentionally identical to the research-period daily rule.
    context_xau = _load_dukascopy_xau_daily(CONTEXT_XAU)
    research_xau = {bar.day: bar for bar in load_daily_xau_from_m1(RESEARCH_XAU)}
    context_dxy = _load_dukascopy_daily(CONTEXT_DXY)
    research_dxy = load_dxy_daily(RESEARCH_DXY)

    xau_overlap = sorted(set(context_xau) & set(research_xau))
    dxy_overlap = sorted(set(context_dxy) & set(research_dxy))

    xau_close_diffs = [_rel_diff(context_xau[d]["close"], research_xau[d].close) for d in xau_overlap]
    dxy_close_diffs = [_rel_diff(context_dxy[d]["close"], research_dxy[d]) for d in dxy_overlap]

    payload = {
        "context_xau_rows": len(context_xau),
        "context_dxy_rows": len(context_dxy),
        "research_xau_rows": len(research_xau),
        "research_dxy_rows": len(research_dxy),
        "xau_overlap_days": len(xau_overlap),
        "xau_overlap_first": xau_overlap[0] if xau_overlap else None,
        "xau_overlap_last": xau_overlap[-1] if xau_overlap else None,
        "xau_max_close_relative_difference": max(xau_close_diffs) if xau_close_diffs else None,
        "dxy_overlap_days": len(dxy_overlap),
        "dxy_overlap_first": dxy_overlap[0] if dxy_overlap else None,
        "dxy_overlap_last": dxy_overlap[-1] if dxy_overlap else None,
        "dxy_max_close_relative_difference": max(dxy_close_diffs) if dxy_close_diffs else None,
        "status": "REVIEW_REQUIRED",
        "acceptance_policy": "No automatic source equivalence claim; overlap statistics require scientific review before context is accepted.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 70)
    print("PHASE 5.2 REBUILD — CONTEXT CONTINUITY AUDIT")
    print("=" * 70)
    print(f"CONTEXT XAU DAYS             : {len(context_xau)}")
    print(f"CONTEXT DXY DAYS             : {len(context_dxy)}")
    print(f"XAU OVERLAP DAYS             : {len(xau_overlap)}")
    print(f"XAU OVERLAP FIRST/LAST       : {xau_overlap[0] if xau_overlap else None} / {xau_overlap[-1] if xau_overlap else None}")
    print(f"XAU MAX CLOSE REL DIFF       : {max(xau_close_diffs) if xau_close_diffs else None}")
    print(f"DXY OVERLAP DAYS              : {len(dxy_overlap)}")
    print(f"DXY OVERLAP FIRST/LAST        : {dxy_overlap[0] if dxy_overlap else None} / {dxy_overlap[-1] if dxy_overlap else None}")
    print(f"DXY MAX CLOSE REL DIFF        : {max(dxy_close_diffs) if dxy_close_diffs else None}")
    print("STATUS                        : REVIEW_REQUIRED")
    print(f"OUTPUT                        : {OUT.relative_to(ROOT)}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
