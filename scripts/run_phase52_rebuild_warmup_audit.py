from __future__ import annotations

import json
from pathlib import Path

from researchos.experiments.phase52_rebuild.warmup_audit import audit_warmup_coverage
from researchos.experiments.phase52_rebuild.daily_dataset import (
    load_daily_xau_from_m1,
    load_dxy_daily,
    load_macro_daily,
)


ROOT = Path(__file__).resolve().parents[1]
XAU = ROOT / "data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.csv"
DXY = ROOT / "data/macro/raw/DXY_Dukascopy_2021_2025.csv"
US10Y = ROOT / "data/macro/raw/DGS10_fred.csv"
VIX = ROOT / "data/macro/raw/VIXCLS_fred.csv"
OUT = ROOT / "reports/phase52_rebuild/warmup_audit.json"


def main() -> int:
    xau_days = {bar.day for bar in load_daily_xau_from_m1(XAU)}
    dxy_days = set(load_dxy_daily(DXY))
    macro = load_macro_daily(DXY, US10Y, VIX)
    from researchos.experiments.phase52_rebuild.daily_dataset import _load_fred_daily

    us10y_days = set(_load_fred_daily(US10Y, "dgs10", "US10Y"))
    vix_days = set(_load_fred_daily(VIX, "vixcls", "VIX"))

    audit = audit_warmup_coverage(
        xau_days=xau_days,
        dxy_days=dxy_days,
        us10y_days=us10y_days,
        vix_days=vix_days,
        research_start_day="2021-01-01",
        warmup_rows_required=60,
    )

    payload = {
        "research_start_day": audit.research_start_day,
        "warmup_rows_required": audit.warmup_rows_required,
        "earliest_xau_day": audit.earliest_xau_day,
        "earliest_dxy_day": audit.earliest_dxy_day,
        "earliest_us10y_day": audit.earliest_us10y_day,
        "earliest_vix_day": audit.earliest_vix_day,
        "common_days_before_research": audit.common_days_before_research,
        "required_context_start_day": audit.required_context_start_day,
        "context_available": audit.context_available,
        "status": audit.status,
        "source_rows": {
            "xau_daily": len(xau_days),
            "dxy_daily": len(dxy_days),
            "us10y_daily": len(us10y_days),
            "vix_daily": len(vix_days),
            "dxy_us10y_vix_common": len(macro),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("=" * 70)
    print("PHASE 5.2 REBUILD — REAL-DATA WARMUP COVERAGE AUDIT")
    print("=" * 70)
    print(f"RESEARCH START       : {audit.research_start_day}")
    print(f"WARMUP REQUIRED      : {audit.warmup_rows_required}")
    print(f"EARLIEST XAU DAY     : {audit.earliest_xau_day}")
    print(f"EARLIEST DXY DAY     : {audit.earliest_dxy_day}")
    print(f"EARLIEST US10Y DAY   : {audit.earliest_us10y_day}")
    print(f"EARLIEST VIX DAY     : {audit.earliest_vix_day}")
    print(f"4-WAY DAYS BEFORE    : {audit.common_days_before_research}")
    print(f"REQUIRED CONTEXT     : {audit.required_context_start_day}")
    print(f"CONTEXT AVAILABLE    : {audit.context_available}")
    print(f"STATUS               : {audit.status}")
    print(f"OUTPUT               : {OUT.relative_to(ROOT)}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
