from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

START = date(2021, 1, 1)
END = date(2025, 12, 31)
FRED_DATE_KEYS = ("DATE", "observation_date", "date")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def in_window(value: date) -> bool:
    return START <= value <= END


def load_xau_dates(path: Path) -> tuple[set[date], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    dates: set[date] = set()
    for row in rows:
        value = (row.get("Date") or "").strip()
        if not value:
            continue
        parsed = datetime.strptime(value, "%Y.%m.%d").date()
        if in_window(parsed):
            dates.add(parsed)
    return dates, len(rows)


def load_dxy_dates(path: Path) -> tuple[set[date], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    dates: set[date] = set()
    for row in rows:
        raw = (row.get("timestamp") or "").strip()
        if not raw:
            continue
        parsed = datetime.fromtimestamp(int(raw) / 1000, tz=timezone.utc).date()
        if in_window(parsed):
            dates.add(parsed)
    return dates, len(rows)


def load_fred_dates(path: Path, value_key: str) -> tuple[set[date], int, int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        date_key = next((key for key in FRED_DATE_KEYS if key in fieldnames), None)
        if date_key is None:
            raise ValueError(f"{path}: no FRED date column; columns={fieldnames}")
        rows = list(reader)
    dates: set[date] = set()
    missing_value_rows = 0
    for row in rows:
        raw_date = (row.get(date_key) or "").strip()
        if not raw_date:
            continue
        parsed = date.fromisoformat(raw_date)
        if not in_window(parsed):
            continue
        value = (row.get(value_key) or "").strip()
        if value in {"", ".", "NA", "N/A", "null", "None"}:
            missing_value_rows += 1
            continue
        dates.add(parsed)
    return dates, len(rows), missing_value_rows


def audit(xau_path: Path, dxy_path: Path, dgs10_path: Path, vix_path: Path) -> dict:
    xau, xau_raw = load_xau_dates(xau_path)
    dxy, dxy_raw = load_dxy_dates(dxy_path)
    dgs10, dgs10_raw, dgs10_missing = load_fred_dates(dgs10_path, "DGS10")
    vix, vix_raw, vix_missing = load_fred_dates(vix_path, "VIXCLS")

    common = xau & dxy & dgs10 & vix
    result = {
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "sources": {
            "XAUUSD": {"raw_rows": xau_raw, "window_rows": len(xau), "sha256": sha256_file(xau_path)},
            "DXY": {
                "source": "Dukascopy",
                "instrument": "dollaridxusd",
                "source_type": "secondary",
                "ice_equivalence": "NOT_PROVEN",
                "raw_rows": dxy_raw,
                "window_rows": len(dxy),
                "sha256": sha256_file(dxy_path),
            },
            "DGS10": {"raw_rows": dgs10_raw, "window_rows": len(dgs10), "missing_value_rows": dgs10_missing, "sha256": sha256_file(dgs10_path)},
            "VIX": {"raw_rows": vix_raw, "window_rows": len(vix), "missing_value_rows": vix_missing, "sha256": sha256_file(vix_path)},
        },
        "intersection": {
            "xauusd": len(xau),
            "xauusd_dxy": len(xau & dxy),
            "xauusd_dgs10": len(xau & dgs10),
            "xauusd_vix": len(xau & vix),
            "four_way": len(common),
            "xauusd_dropped": len(xau - common),
            "dxy_extra": len(dxy - xau),
            "dgs10_missing_from_xau": len(xau - dgs10),
            "vix_missing_from_xau": len(xau - vix),
            "first_common": min(common).isoformat() if common else None,
            "last_common": max(common).isoformat() if common else None,
            "xauusd_only": sorted(d.isoformat() for d in xau - common),
            "dxy_only": sorted(d.isoformat() for d in dxy - xau),
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the Phase 5.2 four-way macro observation calendar")
    parser.add_argument("--xau", default="data/phase52/xauusd.csv")
    parser.add_argument("--dxy", default="data/macro/raw/DXY_Dukascopy_2021_2025.csv")
    parser.add_argument("--dgs10", default="data/macro/raw/DGS10_fred.csv")
    parser.add_argument("--vix", default="data/macro/raw/VIXCLS_fred.csv")
    parser.add_argument("--json", default="", help="Optional JSON output path")
    args = parser.parse_args()

    result = audit(Path(args.xau), Path(args.dxy), Path(args.dgs10), Path(args.vix))
    i = result["intersection"]
    print("=" * 70)
    print("PHASE 5.2 FOUR-WAY COMMON OBSERVATION AUDIT")
    print("=" * 70)
    print(f"XAUUSD       : {i['xauusd']}")
    print(f"DXY          : {result['sources']['DXY']['window_rows']}")
    print(f"DGS10        : {result['sources']['DGS10']['window_rows']}")
    print(f"VIX          : {result['sources']['VIX']['window_rows']}")
    print(f"XAU ∩ DXY    : {i['xauusd_dxy']}")
    print(f"XAU ∩ DGS10  : {i['xauusd_dgs10']}")
    print(f"XAU ∩ VIX    : {i['xauusd_vix']}")
    print(f"4-WAY COMMON : {i['four_way']}")
    print(f"Dropped      : {i['xauusd_dropped']}")
    print(f"First common : {i['first_common']}")
    print(f"Last common  : {i['last_common']}")
    print(f"XAU-only     : {', '.join(i['xauusd_only']) or '(none)'}")
    print(f"DXY-only     : {', '.join(i['dxy_only']) or '(none)'}")
    print("=" * 70)
    if args.json:
        import json
        Path(args.json).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Audit JSON saved: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
