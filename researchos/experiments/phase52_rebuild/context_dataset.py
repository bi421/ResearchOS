"""Load pre-research context observations without accepting source equivalence.

This module only parses and aligns downloaded context sources. Scientific source
acceptance remains a separate gate and is never implied by successful parsing.
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

from .daily_dataset import DailyObservation, _float, _load_fred_daily, _utc_iso


def _dukascopy_xau_daily(path: str | Path) -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict[str, float | str]]] = {}
    seen_timestamps: set[str] = set()
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {str(x).strip().lower() for x in (reader.fieldnames or [])}
        required = {"timestamp", "open", "high", "low", "close", "volume"}
        if not required.issubset(fields):
            raise ValueError("Dukascopy XAU context must contain timestamp, OHLC, and volume columns")
        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
            ts = _utc_iso(str(row["timestamp"]))
            if ts in seen_timestamps:
                raise ValueError(f"context XAU duplicate timestamp: {ts}")
            seen_timestamps.add(ts)
            open_ = _float(row, "open")
            high = _float(row, "high")
            low = _float(row, "low")
            close = _float(row, "close")
            if high < max(open_, close) or low > min(open_, close) or high < low:
                raise ValueError(f"invalid context XAU OHLC relationship at timestamp: {ts}")
            groups.setdefault(ts[:10], []).append(
                {
                    "timestamp": ts,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": _float(row, "volume"),
                }
            )

    out: dict[str, dict[str, float]] = {}
    for day, rows in sorted(groups.items()):
        rows.sort(key=lambda r: str(r["timestamp"]))
        out[day] = {
            "open": float(rows[0]["open"]),
            "high": max(float(r["high"]) for r in rows),
            "low": min(float(r["low"]) for r in rows),
            "close": float(rows[-1]["close"]),
            "tick_volume": sum(float(r["volume"]) for r in rows),
            "real_volume": 0.0,
            "m1_rows": float(len(rows)),
        }
    return out


def _dukascopy_daily_close(path: str | Path) -> dict[str, float]:
    out: dict[str, float] = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {str(x).strip().lower() for x in (reader.fieldnames or [])}
        required = {"timestamp", "close"}
        if not required.issubset(fields):
            raise ValueError("Dukascopy DXY context must contain timestamp and close columns")
        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
            day = _utc_iso(str(row["timestamp"]))[:10]
            if day in out:
                raise ValueError(f"context DXY duplicate calendar day: {day}")
            out[day] = _float(row, "close")
    return out


def load_context_daily_observations(
    xau_context_path: str | Path,
    dxy_context_path: str | Path,
    us10y_path: str | Path,
    vix_path: str | Path,
) -> tuple[DailyObservation, ...]:
    """Build exact four-way context observations from parsed source files."""
    xau = _dukascopy_xau_daily(xau_context_path)
    dxy = _dukascopy_daily_close(dxy_context_path)
    us10y = _load_fred_daily(us10y_path, "dgs10", "US10Y")
    vix = _load_fred_daily(vix_path, "vixcls", "VIX")
    days = sorted(set(xau) & set(dxy) & set(us10y) & set(vix))
    observations: list[DailyObservation] = []
    for day in days:
        bar = xau[day]
        observations.append(
            DailyObservation(
                day=day,
                timestamp=f"{day}T00:00:00Z",
                open=bar["open"],
                high=bar["high"],
                low=bar["low"],
                close=bar["close"],
                tick_volume=bar["tick_volume"],
                spread=None,
                real_volume=bar["real_volume"],
                dxy=dxy[day],
                us10y=us10y[day],
                vix=vix[day],
                m1_rows=int(bar["m1_rows"]),
            )
        )
    return tuple(observations)


__all__ = ["load_context_daily_observations"]
