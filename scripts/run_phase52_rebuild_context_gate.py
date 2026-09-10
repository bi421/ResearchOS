from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from researchos.experiments.phase52_rebuild.daily_dataset import _load_fred_daily

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_XAU = ROOT / "data/macro/context/dukascopy_2020/XAUUSD_Dukascopy_M1_2020_context.csv"
CONTEXT_DXY = ROOT / "data/macro/context/dukascopy_2020/DXY_Dukascopy_D1_2020_context.csv"
US10Y = ROOT / "data/macro/raw/DGS10_fred.csv"
VIX = ROOT / "data/macro/raw/VIXCLS_fred.csv"
CONTINUITY = ROOT / "reports/phase52_rebuild/context_continuity_audit.json"
OUT = ROOT / "reports/phase52_rebuild/context_gate.json"

RESEARCH_START = "2021-01-01"
WARMUP_REQUIRED = 60
MIN_SOURCE_OVERLAP_DAYS = 30


def _day(value: str) -> str:
    value = value.strip()
    if value.isdigit():
        n = int(value)
        if abs(n) >= 100_000_000_000:
            dt = datetime.fromtimestamp(n / 1000, tz=timezone.utc)
        else:
            dt = datetime.fromtimestamp(n, tz=timezone.utc)
        return dt.date().isoformat()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date().isoformat()


def _xau_days(path: Path) -> set[str]:
    groups: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            groups.add(_day(str(row["timestamp"])))
    return groups


def _dxy_days(path: Path) -> set[str]:
    days: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            days.add(_day(str(row["timestamp"])))
    return days


def main() -> int:
    if not CONTINUITY.exists():
        raise SystemExit(f"missing continuity audit: {CONTINUITY}")
    if not CONTEXT_XAU.exists() or not CONTEXT_DXY.exists():
        raise SystemExit("missing Dukascopy context files; run the context download first")

    continuity = json.loads(CONTINUITY.read_text(encoding="utf-8"))
    xau = _xau_days(CONTEXT_XAU)
    dxy = _dxy_days(CONTEXT_DXY)
    us10y = set(_load_fred_daily(US10Y, "dgs10", "US10Y"))
    vix = set(_load_fred_daily(VIX, "vixcls", "VIX"))

    pre_research = sorted(
        d for d in (xau & dxy & us10y & vix) if d < RESEARCH_START
    )
    xau_overlap = int(continuity.get("xau", {}).get("days", 0))
    dxy_overlap = int(continuity.get("dxy", {}).get("days", 0))
    max_xau_diff = continuity.get("xau", {}).get("max_close_relative_difference")
    mean_xau_diff = continuity.get("xau", {}).get("mean_close_relative_difference")

    payload = {
        "research_start_day": RESEARCH_START,
        "warmup_required": WARMUP_REQUIRED,
        "minimum_source_overlap_days": MIN_SOURCE_OVERLAP_DAYS,
        "source_validation": {
            "status": "REVIEW_REQUIRED",
            "xau_overlap_days": xau_overlap,
            "dxy_overlap_days": dxy_overlap,
            "xau_max_close_relative_difference": max_xau_diff,
            "xau_mean_close_relative_difference": mean_xau_diff,
            "dxy_max_close_relative_difference": continuity.get("dxy", {}).get("max_close_relative_difference"),
            "acceptance_rule": "No automatic source equivalence claim; scientific review is required after adequate overlap.",
        },
        "warmup_context": {
            "four_way_pre_research_days": len(pre_research),
            "first_day": pre_research[0] if pre_research else None,
            "last_day": pre_research[-1] if pre_research else None,
            "status": "PASS" if len(pre_research) >= WARMUP_REQUIRED else "BLOCKED",
        },
        "overall_status": "BLOCKED",
        "reason": "Source equivalence is not automatically accepted; warm-up context may only be used after scientific source review.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 70)
    print("PHASE 5.2 REBUILD — CONTEXT ACCEPTANCE GATE")
    print("=" * 70)
    print(f"XAU SOURCE OVERLAP   : {xau_overlap} days")
    print(f"DXY SOURCE OVERLAP   : {dxy_overlap} days")
    print(f"XAU MAX REL DIFF     : {max_xau_diff}")
    print(f"XAU MEAN REL DIFF    : {mean_xau_diff}")
    print(f"4-WAY PRE-RESEARCH   : {len(pre_research)} days")
    print(f"WARMUP REQUIRED      : {WARMUP_REQUIRED}")
    print("SOURCE STATUS        : REVIEW_REQUIRED")
    print(f"WARMUP STATUS        : {payload['warmup_context']['status']}")
    print("OVERALL STATUS       : BLOCKED")
    print(f"OUTPUT               : {OUT.relative_to(ROOT)}")
    print("=" * 70)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
