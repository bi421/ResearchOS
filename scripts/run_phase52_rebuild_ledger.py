"""Build and emit the Phase 5.2 rebuild data ledger from real source files."""
from __future__ import annotations

import argparse
from pathlib import Path

from researchos.experiments.phase52_rebuild import LedgerConfig, build_data_ledger, write_ledger_report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Phase 5.2 rebuild: source/alignment/eligibility ledger")
    p.add_argument("--csv", required=True, help="XAUUSD daily/raw CSV")
    p.add_argument("--dxy", required=True, help="Dukascopy DXY CSV")
    p.add_argument("--us10y", required=True, help="FRED DGS10 CSV")
    p.add_argument("--vix", required=True, help="FRED VIXCLS CSV")
    p.add_argument("--feature-warmup", type=int, default=60)
    p.add_argument("--label-horizon", type=int, default=5)
    p.add_argument("--out-dir", default="reports/phase52_rebuild")
    args = p.parse_args(argv)
    if args.feature_warmup < 0 or args.label_horizon < 0:
        p.error("feature warm-up and label horizon must be >= 0")

    ledger = build_data_ledger(
        args.csv, args.dxy, args.us10y, args.vix,
        LedgerConfig(feature_warmup=args.feature_warmup, label_horizon=args.label_horizon),
    )
    out = Path(args.out_dir)
    write_ledger_report(ledger, out / "data_ledger.json", out / "data_ledger.md")

    print("=" * 88)
    print("PHASE 5.2 REBUILD — DATA LEDGER")
    print("=" * 88)
    print(f"XAUUSD SOURCE          : {ledger.xau_rows}")
    print(f"DXY SOURCE             : {ledger.dxy_rows}")
    print(f"US10Y SOURCE           : {ledger.us10y_rows}")
    print(f"VIX SOURCE             : {ledger.vix_rows}")
    print(f"4-WAY CALENDAR COMMON  : {ledger.common_rows}")
    print(f"CALENDAR DROP          : {ledger.xau_minus_common}")
    print(f"FEATURE WARM-UP DROP   : {ledger.feature_warmup_rows}")
    print(f"AFTER FEATURE WARM-UP  : {ledger.after_feature_warmup}")
    print(f"LABEL HORIZON DROP     : {ledger.label_horizon_rows}")
    print(f"FINAL USABLE           : {ledger.final_usable_rows}")
    print(f"COMMON FIRST / LAST     : {ledger.common_first} / {ledger.common_last}")
    print(f"LEDGER INVARIANTS      : {'PASS' if ledger.invariant_ok else 'FAIL'}")
    if ledger.invariant_errors:
        for error in ledger.invariant_errors:
            print(f"  ERROR: {error}")
    print(f"JSON                   : {out / 'data_ledger.json'}")
    print(f"REPORT                 : {out / 'data_ledger.md'}")
    print("=" * 88)
    return 0 if ledger.invariant_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
