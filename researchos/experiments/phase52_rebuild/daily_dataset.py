"""Deterministic daily XAUUSD + macro observation assembly for Phase 5.2.

This module is the boundary between the raw M1 XAUUSD source and the
research dataset. It deliberately performs only transformations that are
well-defined from the source data:

* XAUUSD M1 bars are aggregated by UTC calendar day.
* Daily OHLC uses first-open, max-high, min-low, last-close.
* Tick and real volume are summed; spread is averaged when present.
* Macro sources contribute only observations that actually exist on the
  same UTC calendar day. No interpolation or forward-fill is performed.
* The returned observations are ordered by UTC day and carry source counts.

No labels or model features are created here. That separation prevents the
calendar/alignment boundary from being silently mixed with feature warm-up
or future-label eligibility.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class DailyXAUBar:
    day: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    tick_volume: float
    spread: float | None
    real_volume: float
    m1_rows: int


@dataclass(frozen=True)
class DailyMacroObservation:
    day: str
    dxy: float
    us10y: float
    vix: float


@dataclass(frozen=True)
class DailyObservation:
    day: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    tick_volume: float
    spread: float | None
    real_volume: float
    dxy: float
    us10y: float
    vix: float
    m1_rows: int


def _utc_iso(value: str) -> str:
    value = value.strip()
    if value.isdigit():
        n = int(value)
        if abs(n) >= 100_000_000_000:
            dt = datetime.fromtimestamp(n / 1000, tz=timezone.utc)
        elif abs(n) >= 1_000_000_000:
            dt = datetime.fromtimestamp(n, tz=timezone.utc)
        else:
            raise ValueError(f"unsupported numeric timestamp: {value}")
        return dt.isoformat().replace("+00:00", "Z")
    if value.endswith("Z"):
        dt = datetime.fromisoformat(value[:-1] + "+00:00")
    else:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _day(timestamp: str) -> str:
    return timestamp[:10]


def _float(row: dict[str, str | None], key: str) -> float:
    value = row.get(key)
    if value is None or value.strip() == "":
        raise ValueError(f"missing numeric field: {key}")
    return float(value)


def load_daily_xau_from_m1(path: str | Path) -> tuple[DailyXAUBar, ...]:
    """Aggregate canonical MT5 XAUUSD M1 CSV into UTC daily OHLCV bars."""
    path = Path(path)
    groups: dict[str, list[tuple[str, float, float, float, float, float, float | None, float]]] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = {str(x).strip().lower() for x in (reader.fieldnames or [])}
        required = {"time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"}
        if not required.issubset(fields):
            raise ValueError("XAUUSD source must use canonical MT5 OHLCV schema")
        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
            ts = _utc_iso(str(row["time"]))
            values = (
                ts,
                _float(row, "open"),
                _float(row, "high"),
                _float(row, "low"),
                _float(row, "close"),
                _float(row, "tick_volume"),
                _float(row, "spread"),
                _float(row, "real_volume"),
            )
            groups.setdefault(_day(ts), []).append(values)

    output: list[DailyXAUBar] = []
    for day in sorted(groups):
        rows = sorted(groups[day], key=lambda x: x[0])
        spreads = [r[6] for r in rows]
        output.append(
            DailyXAUBar(
                day=day,
                timestamp=f"{day}T00:00:00Z",
                open=rows[0][1],
                high=max(r[2] for r in rows),
                low=min(r[3] for r in rows),
                close=rows[-1][4],
                tick_volume=sum(r[5] for r in rows),
                spread=sum(spreads) / len(spreads) if spreads else None,
                real_volume=sum(r[7] for r in rows),
                m1_rows=len(rows),
            )
        )
    return tuple(output)


def load_dxy_daily(path: str | Path) -> dict[str, float]:
    """Load DXY daily close observations keyed by UTC calendar day."""
    path = Path(path)
    out: dict[str, float] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
            ts = _utc_iso(str(row["timestamp"]))
            day = _day(ts)
            if day in out:
                raise ValueError(f"DXY duplicate calendar day: {day}")
            out[day] = _float(row, "close")
    return out


def _load_fred_daily(path: str | Path, value_key: str, symbol: str) -> dict[str, float]:
    path = Path(path)
    out: dict[str, float] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {str(k).strip().lower(): v for k, v in raw.items() if k is not None}
            raw_value = row.get(value_key)
            if raw_value is None or raw_value.strip() in {"", "."}:
                continue
            ts = _utc_iso(str(row["observation_date"]))
            day = _day(ts)
            if day in out:
                raise ValueError(f"{symbol} duplicate calendar day: {day}")
            out[day] = float(raw_value)
    return out


def load_macro_daily(
    dxy_path: str | Path,
    us10y_path: str | Path,
    vix_path: str | Path,
) -> DailyMacroObservation | tuple[DailyMacroObservation, ...]:
    """Return the exact four-way daily intersection as immutable observations."""
    dxy = load_dxy_daily(dxy_path)
    us10y = _load_fred_daily(us10y_path, "dgs10", "US10Y")
    vix = _load_fred_daily(vix_path, "vixcls", "VIX")
    common = sorted(set(dxy) & set(us10y) & set(vix))
    return tuple(DailyMacroObservation(day, dxy[day], us10y[day], vix[day]) for day in common)


def build_daily_common_dataset(
    xau_path: str | Path,
    dxy_path: str | Path,
    us10y_path: str | Path,
    vix_path: str | Path,
) -> tuple[DailyObservation, ...]:
    """Build the exact common-day dataset from raw XAU M1 and macro sources."""
    xau = {bar.day: bar for bar in load_daily_xau_from_m1(xau_path)}
    macro = load_macro_daily(dxy_path, us10y_path, vix_path)
    observations: list[DailyObservation] = []
    for m in macro:
        bar = xau.get(m.day)
        if bar is None:
            continue
        observations.append(
            DailyObservation(
                day=bar.day,
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                tick_volume=bar.tick_volume,
                spread=bar.spread,
                real_volume=bar.real_volume,
                dxy=m.dxy,
                us10y=m.us10y,
                vix=m.vix,
                m1_rows=bar.m1_rows,
            )
        )
    return tuple(observations)


__all__ = [
    "DailyXAUBar",
    "DailyMacroObservation",
    "DailyObservation",
    "load_daily_xau_from_m1",
    "load_dxy_daily",
    "load_macro_daily",
    "build_daily_common_dataset",
]
