# XAUUSD M1 data acceptance policy

## Purpose

This document defines when the real MT5 XAUUSD M1 dataset may be used as empirical evidence by ResearchOS.

## Current dataset

- Source boundary: MetaTrader 5 export
- Instrument: XAUUSD
- Timeframe: M1
- Covered period: 2021-2025 dataset supplied to the repository
- Raw archive: `data/mt5/xauusd/XAUUSD_M1_2021_2025_MT5.zip`
- Expected member: `XAUUSD_M1_2021_2025_MT5.csv`

The archive is tracked as research input; it is not synthetic evidence.

## Acceptance gates

### Gate 1 — file integrity

The ZIP must open successfully and contain the expected CSV member. A corrupt archive or missing member is a hard failure.

### Gate 2 — schema integrity

The raw XAUUSD M1 CSV must contain exactly the expected market fields:

`time, open, high, low, close, tick_volume, spread, real_volume`

No null timestamps, non-finite OHLC values, non-positive prices, invalid OHLC relationships, or negative volume/spread values are accepted.

### Gate 3 — timestamp integrity

Timestamps must parse as UTC, be strictly increasing, and contain no duplicates. A gap greater than one minute is an observation requiring temporal classification; it is not automatically treated as missing data.

### Gate 4 — temporal gap classification

The gap audit is deliberately conservative:

- `weekend_overlap_candidate`: the interval contains Saturday or Sunday.
- `non_weekend_suspicious`: the interval contains no weekend day and therefore cannot be justified by a generic weekly-closure assumption.

A weekend candidate is **not** proof that the broker was open/closed at those exact times. Broker-specific session calendars, maintenance windows, and holidays must be supplied before a gap can be declared an expected closure.

### Gate 5 — no repair of evidence

ResearchOS must not interpolate, forward-fill, fabricate, or silently delete market bars to make the series continuous. Any transformation used by an experiment must be explicit and reproducible.

### Gate 6 — provenance

Every empirical experiment should retain enough provenance to reproduce the input identity, including source boundary, symbol, timeframe, row count, time range, and content hash where available.

### Gate 7 — macro alignment for Phase 5.2

Phase 5.2 additionally requires real XAUUSD, DXY, US10Y, and VIX inputs. Exact-date alignment is required. Missing or misaligned macro observations block the experiment; they are not interpreted as model failure or success. No interpolation or forward-fill is permitted.

## Decision semantics

- **ACCEPT** — all core integrity gates pass and no unresolved suspicious temporal gaps remain.
- **ACCEPT_WITH_CONDITIONS** — core integrity passes but unresolved temporal gaps remain and are explicitly documented.
- **REQUIRES_REVIEW** — one or more suspicious non-weekend gaps require broker/session evidence.
- **REJECT** — a core integrity contract fails.
- **BLOCKED** — required empirical inputs are absent or insufficient.

## Scientific rule

A green CI run proves software correctness for the covered tests. It does **not** prove that XAUUSD contains no missing market data, nor does it prove predictive value. Empirical acceptance requires the dataset gates above plus an auditable research result.
