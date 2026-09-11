from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from researchos.experiments.phase52_rebuild.daily_dataset import (
    load_daily_xau_from_m1,
    load_dxy_daily,
)

ROOT = Path(__file__).resolve().parents[1]
CONTEXT_XAU = ROOT / "data/mt5/xauusd/XAUUSD_M1_2020_context_MT5.csv"
CONTEXT_DXY = ROOT / "data/macro/context/dukascopy_2020/DXY_Dukascopy_D1_2020_context.csv"
RESEARCH_XAU = ROOT / "data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.csv"
RESEARCH_DXY = ROOT / "data/macro/raw/DXY_Dukascopy_2021_2025.csv"
OUT = ROOT / "reports/phase52_rebuild/context_continuity_audit.json"


def _utc_day(value: str) -> str:
    n = int(value.strip())
    return datetime.fromtimestamp(n / 1000, tz=timezone.utc).date().isoformat()


def _load_dukascopy_daily(path: Path) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"timestamp", "open", "high", "low", "close"}
        fields = {str(x).strip().lower() for x in (reader.fieldnames or [])}
        if not required.issubset(fields):
            raise ValueError(f"unexpected Dukascopy schema: {sorted(fields)}")
        has_volume = "volume" in fields
        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
            day = _utc_day(str(row["timestamp"]))
            if day in out:
                raise ValueError(f"duplicate Dukascopy calendar day: {day}")
            out[day] = {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"])
                if has_volume and row.get("volume") not in (None, "")
                else 0.0,
            }
    return out


def _rel_diff(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def _diff_summary(
    days: list[str], left: dict[str, float], right: dict[str, float]
) -> dict[str, object]:
    diffs = [_rel_diff(left[d], right[d]) for d in days]
    return {
        "days": len(days),
        "first": days[0] if days else None,
        "last": days[-1] if days else None,
        "max_close_relative_difference": max(diffs) if diffs else None,
        "mean_close_relative_difference": (sum(diffs) / len(diffs)) if diffs else None,
        "close_relative_differences": [
            {"day": d, "relative_difference": diff} for d, diff in zip(days, diffs)
        ],
    }


def main() -> int:
    REQUIRED_XAU_CONTEXT_DAYS = 240
    REQUIRED_DXY_OVERLAP_DAYS = 60
    MAX_DXY_CLOSE_RELATIVE_DIFFERENCE = 1e-12

    missing = [
        str(p) for p in (CONTEXT_XAU, CONTEXT_DXY, RESEARCH_XAU, RESEARCH_DXY) if not p.exists()
    ]
    if missing:
        raise FileNotFoundError("Missing required files:\n" + "\n".join(missing))

    context_xau = {bar.day: bar for bar in load_daily_xau_from_m1(CONTEXT_XAU)}
    research_xau = {bar.day: bar for bar in load_daily_xau_from_m1(RESEARCH_XAU)}
    context_dxy = _load_dukascopy_daily(CONTEXT_DXY)
    research_dxy = load_dxy_daily(RESEARCH_DXY)

    # XAU is a strictly pre-research same-feed context.
    # Research/context overlap is therefore NOT required.
    research_first_xau_day = min(research_xau)
    research_last_xau_day = max(research_xau)
    context_first_xau_day = min(context_xau)
    context_last_xau_day = max(context_xau)

    xau_pre_context_days = sorted(day for day in context_xau if day < research_first_xau_day)

    xau_context_boundary_ok = context_last_xau_day < research_first_xau_day
    xau_context_depth_ok = len(xau_pre_context_days) >= REQUIRED_XAU_CONTEXT_DAYS

    # XAU overlap is retained as an informational diagnostic only.
    xau_overlap_days = sorted(set(context_xau) & set(research_xau))

    # DXY retains its overlap/equality continuity check because the
    # existing DXY context and research sources share the same observation
    # calendar and can be directly compared.
    dxy_days = sorted(set(context_dxy) & set(research_dxy))
    dxy_left = {d: context_dxy[d]["close"] for d in dxy_days}
    dxy_right = {d: research_dxy[d] for d in dxy_days}
    dxy_summary = _diff_summary(dxy_days, dxy_left, dxy_right)

    dxy_overlap_ok = len(dxy_days) >= REQUIRED_DXY_OVERLAP_DAYS
    dxy_equivalence_ok = (
        dxy_summary["max_close_relative_difference"] is not None
        and dxy_summary["max_close_relative_difference"] <= MAX_DXY_CLOSE_RELATIVE_DIFFERENCE
    )

    acceptance_ok = (
        xau_context_boundary_ok and xau_context_depth_ok and dxy_overlap_ok and dxy_equivalence_ok
    )

    payload = {
        "context_xau_rows": len(context_xau),
        "context_dxy_rows": len(context_dxy),
        "research_xau_rows": len(research_xau),
        "research_dxy_rows": len(research_dxy),
        "xau": {
            "context_first": context_first_xau_day,
            "context_last": context_last_xau_day,
            "research_first": research_first_xau_day,
            "research_last": research_last_xau_day,
            "pre_context_days": len(xau_pre_context_days),
            "required_context_days": REQUIRED_XAU_CONTEXT_DAYS,
            "boundary_ok": xau_context_boundary_ok,
            "depth_ok": xau_context_depth_ok,
            "overlap_days": len(xau_overlap_days),
        },
        "dxy": dxy_summary,
        "acceptance": {
            "xau_pre_context_boundary_ok": xau_context_boundary_ok,
            "xau_pre_context_depth_ok": xau_context_depth_ok,
            "xau_required_context_days": REQUIRED_XAU_CONTEXT_DAYS,
            "xau_available_pre_context_days": len(xau_pre_context_days),
            "dxy_overlap_ok": dxy_overlap_ok,
            "dxy_required_overlap_days": REQUIRED_DXY_OVERLAP_DAYS,
            "dxy_actual_overlap_days": len(dxy_days),
            "dxy_equivalence_ok": dxy_equivalence_ok,
        },
        "status": "PASS" if acceptance_ok else "REVIEW_REQUIRED",
        "acceptance_policy": (
            "XAU acceptance requires strictly pre-research same-feed "
            "context with adequate warm-up depth. XAU overlap with "
            "research is not required. DXY retains an explicit multi-day "
            "overlap and equality check. No automatic cross-source "
            "equivalence claim is made."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=" * 70)
    print("PHASE 5.2 REBUILD - CONTEXT CONTINUITY AUDIT")
    print("=" * 70)
    print(f"CONTEXT XAU DAYS             : {len(context_xau)}")
    print(f"CONTEXT XAU FIRST/LAST       : " f"{context_first_xau_day} / {context_last_xau_day}")
    print(f"RESEARCH XAU FIRST/LAST      : " f"{research_first_xau_day} / {research_last_xau_day}")
    print(f"XAU PRE-CONTEXT DAYS         : {len(xau_pre_context_days)}")
    print(f"XAU REQUIRED CONTEXT DAYS   : " f"{REQUIRED_XAU_CONTEXT_DAYS}")
    print(f"XAU BOUNDARY OK              : {xau_context_boundary_ok}")
    print(f"XAU DEPTH OK                 : {xau_context_depth_ok}")
    print(f"XAU OVERLAP DAYS             : {len(xau_overlap_days)}")
    print(f"DXY OVERLAP DAYS             : {len(dxy_days)}")
    print(f"DXY REQUIRED OVERLAP         : {REQUIRED_DXY_OVERLAP_DAYS}")
    print(f"DXY MAX CLOSE REL DIFF       : " f"{dxy_summary['max_close_relative_difference']}")
    print(f"DXY MEAN CLOSE REL DIFF      : " f"{dxy_summary['mean_close_relative_difference']}")
    print(f"STATUS                        : {payload['status']}")
    print(f"OUTPUT                        : {OUT.relative_to(ROOT)}")
    print("=" * 70)

    return 0 if acceptance_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
