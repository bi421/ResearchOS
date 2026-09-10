"""Phase 5.2 rebuild data ledger.

This module deliberately does not call the legacy Phase 5.2 experiment path.
It establishes an auditable data boundary before any model is allowed to run.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

EXPECTED_MACRO = ("DXY", "US10Y", "VIX")


@dataclass(frozen=True)
class LedgerConfig:
    feature_warmup: int = 60
    label_horizon: int = 5


@dataclass(frozen=True)
class SourceAudit:
    name: str
    path: str
    sha256: str
    rows_read: int
    rows_valid: int
    unique_timestamps: int
    duplicate_timestamps: int
    first_timestamp: str | None
    last_timestamp: str | None
    invalid_rows: int
    unsorted_timestamps: bool


@dataclass(frozen=True)
class Phase52DataLedger:
    sources: tuple[SourceAudit, ...]
    xau_rows: int
    dxy_rows: int
    us10y_rows: int
    vix_rows: int
    xau_calendar_days: int
    dxy_calendar_days: int
    us10y_calendar_days: int
    vix_calendar_days: int
    xau_dxy_common_days: int
    xau_us10y_common_days: int
    xau_vix_common_days: int
    common_rows: int
    common_first: str | None
    common_last: str | None
    xau_minus_common: int
    feature_warmup_rows: int
    after_feature_warmup: int
    label_horizon_rows: int
    final_usable_rows: int
    final_usable_first: str | None
    final_usable_last: str | None
    timestamp_hash: str
    invariant_ok: bool
    invariant_errors: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _utc_iso(value: str) -> str:
    value = value.strip()
    if value.isdigit():
        n = int(value)
        if abs(n) >= 100_000_000_000:
            return datetime.fromtimestamp(n / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        if abs(n) >= 1_000_000_000:
            return datetime.fromtimestamp(n, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    if value.endswith("Z"):
        return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _calendar_key(timestamp: str) -> str:
    return timestamp[:10]


def _calendar_iso(day: str) -> str:
    return f"{day}T00:00:00Z"


def _audit(name: str, path: Path, rows_read: int, rows_valid: int, ts: list[str], invalid: int) -> SourceAudit:
    unique = set(ts)
    return SourceAudit(
        name=name, path=str(path), sha256=_sha256(path), rows_read=rows_read,
        rows_valid=rows_valid, unique_timestamps=len(unique),
        duplicate_timestamps=rows_valid - len(unique),
        first_timestamp=min(ts) if ts else None, last_timestamp=max(ts) if ts else None,
        invalid_rows=invalid, unsorted_timestamps=ts != sorted(ts),
    )


def _read_xau(path: Path) -> tuple[list[str], SourceAudit]:
    timestamps: list[str] = []
    rows_read = rows_valid = invalid = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = {name.strip().lower() for name in (reader.fieldnames or [])}
        canonical = {"time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume"}
        legacy = {"date", "time", "open", "high", "low", "close", "volume"}
        if canonical.issubset(fieldnames):
            schema = "canonical"
        elif legacy.issubset(fieldnames):
            schema = "legacy"
        else:
            schema = "unknown"

        for row in reader:
            rows_read += 1
            try:
                normalized = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
                if schema == "canonical":
                    ts = _utc_iso(normalized["time"])
                    for key in ("open", "high", "low", "close", "tick_volume", "spread", "real_volume"):
                        float(normalized[key])
                elif schema == "legacy":
                    date = (normalized.get("date") or "").strip().replace(".", "-")
                    time = (normalized.get("time") or "00:00:00").strip()
                    ts = _utc_iso(f"{date}T{time}:00" if len(time) == 5 else f"{date}T{time}")
                    for key in ("open", "high", "low", "close", "volume"):
                        float(normalized[key])
                else:
                    raise ValueError("unsupported XAUUSD CSV schema")
                timestamps.append(ts)
                rows_valid += 1
            except (KeyError, TypeError, ValueError, OverflowError):
                invalid += 1
    return timestamps, _audit("XAUUSD", path, rows_read, rows_valid, timestamps, invalid)


def _read_macro(path: Path, name: str) -> tuple[list[str], SourceAudit]:
    timestamps: list[str] = []
    rows_read = rows_valid = invalid = 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_read += 1
            try:
                normalized = {str(k).strip().lower(): v for k, v in row.items() if k is not None}
                if name == "DXY":
                    raw_ts = normalized["timestamp"]
                    float(normalized["close"])
                else:
                    raw_ts = normalized["observation_date"]
                    value = normalized.get("dgs10" if name == "US10Y" else "vixcls")
                    if value in (None, ".", ""):
                        continue
                    float(value)
                timestamps.append(_utc_iso(raw_ts))
                rows_valid += 1
            except (KeyError, TypeError, ValueError, OverflowError):
                invalid += 1
    return timestamps, _audit(name, path, rows_read, rows_valid, timestamps, invalid)


def _calendar_set(ts_list: list[str]) -> set[str]:
    return {_calendar_key(ts) for ts in ts_list}


def _intersection(named: Iterable[tuple[str, list[str]]]) -> list[str]:
    calendar_sets = [_calendar_set(ts_list) for _, ts_list in named]
    if not calendar_sets:
        return []
    return sorted(set.intersection(*calendar_sets))


def _hash_timestamps(days: list[str]) -> str:
    return hashlib.sha256(json.dumps(days, separators=(",", ":")).encode()).hexdigest()


def build_data_ledger(xau_path: str | Path, dxy_path: str | Path, us10y_path: str | Path, vix_path: str | Path, config: LedgerConfig | None = None) -> Phase52DataLedger:
    cfg = config or LedgerConfig()
    if cfg.feature_warmup < 0 or cfg.label_horizon < 0:
        raise ValueError("feature_warmup and label_horizon must be >= 0")
    paths = [Path(xau_path), Path(dxy_path), Path(us10y_path), Path(vix_path)]
    if not all(p.is_file() for p in paths):
        missing = [str(p) for p in paths if not p.is_file()]
        raise FileNotFoundError("Missing required source files: " + ", ".join(missing))

    xau, ax = _read_xau(paths[0])
    dxy, ad = _read_macro(paths[1], "DXY")
    us10y, au = _read_macro(paths[2], "US10Y")
    vix, av = _read_macro(paths[3], "VIX")

    xau_days = _calendar_set(xau)
    dxy_days = _calendar_set(dxy)
    us10y_days = _calendar_set(us10y)
    vix_days = _calendar_set(vix)
    common_days = sorted(xau_days & dxy_days & us10y_days & vix_days)

    after_feature = max(0, len(common_days) - cfg.feature_warmup)
    final = max(0, after_feature - cfg.label_horizon)
    usable_days = common_days[cfg.feature_warmup : len(common_days) - cfg.label_horizon] if final else []

    errors: list[str] = []
    for audit in (ax, ad, au, av):
        if audit.duplicate_timestamps:
            errors.append(f"{audit.name}: duplicate timestamps={audit.duplicate_timestamps}")
        if audit.invalid_rows:
            errors.append(f"{audit.name}: invalid rows={audit.invalid_rows}")
        if audit.unsorted_timestamps:
            errors.append(f"{audit.name}: timestamps are not sorted")
    if not set(common_days).issubset(xau_days):
        errors.append("common calendar day exists outside XAU source")
    if final != len(usable_days):
        errors.append("final usable row accounting failed")
    if common_days != sorted(common_days):
        errors.append("common calendar days are not sorted")

    return Phase52DataLedger(
        sources=(ax, ad, au, av),
        xau_rows=len(xau), dxy_rows=len(dxy), us10y_rows=len(us10y), vix_rows=len(vix),
        xau_calendar_days=len(xau_days), dxy_calendar_days=len(dxy_days),
        us10y_calendar_days=len(us10y_days), vix_calendar_days=len(vix_days),
        xau_dxy_common_days=len(xau_days & dxy_days),
        xau_us10y_common_days=len(xau_days & us10y_days),
        xau_vix_common_days=len(xau_days & vix_days),
        common_rows=len(common_days),
        common_first=_calendar_iso(common_days[0]) if common_days else None,
        common_last=_calendar_iso(common_days[-1]) if common_days else None,
        xau_minus_common=len(xau_days) - len(common_days),
        feature_warmup_rows=min(cfg.feature_warmup, len(common_days)),
        after_feature_warmup=after_feature,
        label_horizon_rows=min(cfg.label_horizon, after_feature),
        final_usable_rows=final,
        final_usable_first=_calendar_iso(usable_days[0]) if usable_days else None,
        final_usable_last=_calendar_iso(usable_days[-1]) if usable_days else None,
        timestamp_hash=_hash_timestamps(common_days),
        invariant_ok=not errors,
        invariant_errors=tuple(errors),
    )


def write_ledger_report(ledger: Phase52DataLedger, json_path: str | Path, md_path: str | Path) -> None:
    jp, mp = Path(json_path), Path(md_path)
    jp.parent.mkdir(parents=True, exist_ok=True)
    mp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(ledger.to_dict(), indent=2), encoding="utf-8")
    lines = [
        "# Phase 5.2 Rebuild — Data Ledger", "",
        f"- Ledger invariant: **{'PASS' if ledger.invariant_ok else 'FAIL'}**",
        f"- XAUUSD raw rows: **{ledger.xau_rows}**", f"- DXY valid rows: **{ledger.dxy_rows}**",
        f"- US10Y valid rows: **{ledger.us10y_rows}**", f"- VIX valid rows: **{ledger.vix_rows}**",
        f"- XAUUSD unique calendar days: **{ledger.xau_calendar_days}**",
        f"- DXY unique calendar days: **{ledger.dxy_calendar_days}**",
        f"- US10Y unique calendar days: **{ledger.us10y_calendar_days}**",
        f"- VIX unique calendar days: **{ledger.vix_calendar_days}**",
        f"- XAU ∩ DXY calendar days: **{ledger.xau_dxy_common_days}**",
        f"- XAU ∩ US10Y calendar days: **{ledger.xau_us10y_common_days}**",
        f"- XAU ∩ VIX calendar days: **{ledger.xau_vix_common_days}**",
        f"- Exact four-way calendar intersection: **{ledger.common_rows}**",
        f"- Calendar-day drop from XAUUSD: **{ledger.xau_minus_common}**",
        f"- Feature warm-up rows: **{ledger.feature_warmup_rows}**",
        f"- After feature warm-up: **{ledger.after_feature_warmup}**",
        f"- Label horizon rows: **{ledger.label_horizon_rows}**",
        f"- Final usable rows: **{ledger.final_usable_rows}**",
        f"- Common first/last: `{ledger.common_first}` / `{ledger.common_last}`",
        f"- Final usable first/last: `{ledger.final_usable_first}` / `{ledger.final_usable_last}`",
        f"- Common calendar SHA-256: `{ledger.timestamp_hash}`", "",
        "## Row-loss ledger", "",
        "`XAU raw rows → unique XAU calendar days → exact 4-way calendar days → feature warm-up → label horizon → final usable`", "",
    ]
    if ledger.invariant_errors:
        lines += ["## Invariant errors", ""] + [f"- {e}" for e in ledger.invariant_errors]
    mp.write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = ["LedgerConfig", "SourceAudit", "Phase52DataLedger", "build_data_ledger", "write_ledger_report"]
