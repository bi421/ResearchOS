"""Acquire broker-native XAUUSD M1 bars from MetaTrader 5.

This script is intentionally an external acquisition boundary.  It requires
Python 3.12 with the MetaTrader5 package and does not become a ResearchOS core
dependency.  Dates are UTC, and data is fetched in monthly chunks so terminal
history synchronization can complete incrementally.

Example:
    python scripts/acquisition/mt5_xauusd_m1.py \
        --start 2021-01-01 --end 2025-12-31 \
        --output-dir data/raw/mt5/xauusd

``--end`` is inclusive through 23:59:59 UTC.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from researchos.data_engine.mt5_xauusd_validation import validate_m1_rows

UTC = timezone.utc
FIELDS = [
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
]


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=UTC)


def month_end(start: datetime) -> datetime:
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(seconds=1)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rows_from_rates(rates: Any) -> list[dict[str, Any]]:
    return [
        {
            "time": int(row["time"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "tick_volume": int(row["tick_volume"]),
            "spread": int(row["spread"]),
            "real_volume": int(row["real_volume"]),
        }
        for row in rates
    ]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def fetch_chunk(
    mt5: Any, start: datetime, end: datetime, retries: int, delay: float
) -> list[dict[str, Any]]:
    last_error: object = None
    for attempt in range(1, retries + 1):
        rates = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_M1, start, end)
        if rates is not None and len(rates):
            rows = rows_from_rates(rates)
            if rows:
                return rows
        last_error = mt5.last_error()
        if attempt < retries:
            time.sleep(delay * attempt)
    raise RuntimeError(f"MT5 returned no bars for {start}..{end}; last_error={last_error!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, type=parse_date)
    parser.add_argument("--end", required=True, type=parse_date)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/mt5/xauusd"))
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--retry-delay", type=float, default=2.0)
    args = parser.parse_args()
    args.end = args.end + timedelta(days=1) - timedelta(seconds=1)

    if args.end < args.start:
        raise SystemExit("--end must be on or after --start")

    try:
        import MetaTrader5 as mt5  # type: ignore[import-not-found]
    except ImportError as exc:
        raise SystemExit("MetaTrader5 is required in the Python 3.12 acquisition environment") from exc

    if not mt5.initialize():
        raise SystemExit(f"MT5 initialize failed: {mt5.last_error()}")

    try:
        if not mt5.symbol_select("XAUUSD", True):
            raise SystemExit(f"Cannot select XAUUSD: {mt5.last_error()}")
        info = mt5.symbol_info("XAUUSD")
        terminal = mt5.terminal_info()
        if info is None:
            raise SystemExit(f"Cannot read XAUUSD metadata: {mt5.last_error()}")

        args.output_dir.mkdir(parents=True, exist_ok=True)
        manifests: list[dict[str, Any]] = []
        cursor = args.start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        while cursor <= args.end:
            chunk_start = max(cursor, args.start)
            chunk_end = min(month_end(cursor), args.end)
            rows = fetch_chunk(mt5, chunk_start, chunk_end, args.retries, args.retry_delay)
            report = validate_m1_rows(
                rows,
                start_epoch=int(chunk_start.timestamp()),
                end_epoch=int(chunk_end.timestamp()),
            )
            if not report.passed_integrity:
                raise SystemExit(f"Integrity validation failed for {chunk_start.date()}: {report}")

            path = args.output_dir / f"XAUUSD_M1_{cursor:%Y_%m}.csv"
            write_csv(path, rows)
            manifests.append(
                {
                    "file": path.as_posix(),
                    "sha256": sha256_file(path),
                    "rows": report.rows,
                    "first_epoch": min(int(row["time"]) for row in rows),
                    "last_epoch": max(int(row["time"]) for row in rows),
                    "validation": report.__dict__,
                }
            )
            print(f"{cursor:%Y-%m}: {report.rows} rows; max_gap={report.max_gap_seconds}s")
            cursor = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1)

        manifest = {
            "schema_version": 1,
            "source": "MetaTrader5",
            "symbol": "XAUUSD",
            "timeframe": "M1",
            "requested_start": args.start.isoformat(),
            "requested_end": args.end.isoformat(),
            "terminal": {
                "version": getattr(terminal, "build", None),
                "maxbars": getattr(terminal, "maxbars", None),
            },
            "symbol_metadata": {
                "digits": getattr(info, "digits", None),
                "point": getattr(info, "point", None),
                "trade_tick_size": getattr(info, "trade_tick_size", None),
                "trade_contract_size": getattr(info, "trade_contract_size", None),
                "currency_base": getattr(info, "currency_base", None),
                "currency_profit": getattr(info, "currency_profit", None),
            },
            "chunks": manifests,
        }
        manifest_path = args.output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
        print(f"Manifest: {manifest_path}")
    finally:
        mt5.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
