# SESSION_TIME_ARCHITECTURE.md

**Date:** 2026-08-17 — AUDIT ONLY. No implementation.

---

## CURRENT STATE

Three time stacks exist; the strongest is `macro_intelligence/time/` (1,644 lines, FROZEN, tested).

### 1. `researchos/data_engine/timezone.py` (174 lines) — load-time UTC normalization
- Fixed-offset table (20 abbreviations; EST and EDT separate entries — caller must know DST state).
- `normalize_timestamp()` (naive+source offset → UTC), `convert_timezone()`, ISO helpers.

### 2. `macro_intelligence/time/` — the real time model
- `enums.py`: `TimezoneType` (**fixed offsets only** — `US_EASTERN = -5h` always, wrong during EDT); `MarketSession` = **equity taxonomy** (`PRE_MARKET/REGULAR/AFTER_HOURS/OVERNIGHT/CLOSED`) — no FX sessions; `ReleaseStatus` state machine (PLANNED→ACTIVE→COMPLETED/DELAYED/CANCELLED→REVISED); `EventCategory`, `Frequency`, `WindowType`.
- `normalizer.py`: `TimeNormalizer` — UTC normalization, precision rounding, `is_dst_transition()` (works for tz-aware inputs), DST-safe arithmetic, `get_business_hours()` (**hardcoded 9–16h default — equity hours**), `is_trading_day` (weekend-only; holidays explicitly not handled here).
- `calendar.py`: `MarketHoliday` (**holidays are data**, incl. `markets_affected`), `EconomicCalendar` — auto-sorted, `is_holiday`, `is_trading_day` (weekend+holidays), range queries, integrity verification. Weekend = Sat/Sun hardcoded.
- `schedule.py`: **`PlannedRelease` with `planned_time` vs `actual_time` vs `estimated_time` + `delay_minutes` + `ReleaseStatus` — the only publication-time vs scheduled-time model in the codebase.**
- `timeline.py`: `TimeWindow`, `EventWindowSpec` (pre/post/full event windows), `EventTimeline` with overlap verification.

### 3. Sessions as data (not logic)
`objects/market_memory.py:350-420` `MarketSession` — free-string `session_name` ("London", "NewYork", "Asia"…), caller-supplied start/end per instance, OHLC summary. Recorded post-hoc via `memory/engine.py:39 record_session("London", "EURUSD", ...)`. **No session-boundary definitions exist anywhere** — nothing can answer "is 14:00 UTC inside the London session?".

## PROBLEM

1. **Latent correctness bug — documented-but-unimplemented IANA support:** `data_engine/timezone.py:56` docstring advertises `"America/New_York"`, but `_get_offset()` (`:144-172`) **silently returns UTC for unrecognized names**. `normalize_timestamp(dt, "America/New_York")` mislabels input as UTC with no error. Fixed-offset table handles 20 abbreviations only; no DST computation.
2. **Fixed-offset `TimezoneType`** (`macro_intelligence/time/enums.py`) — wrong by one hour half the year for US/EU zones.
3. **No FX session model:** `MarketSession` enum is equity-centric; Tokyo/London/NY boundaries exist nowhere as definitions; overlapping sessions (London+NY 13:00–17:00 UTC) unrepresentable except as recorded data.
4. **Duplicated UTC stacks:** `data_engine/timezone.py` vs `macro_intelligence/time/normalizer.py` (different naive-handling defaults); trading-day logic duplicated inside MIL (`TimeNormalizer.is_trading_day` weekend-only vs `EconomicCalendar.is_trading_day` weekend+holiday); two divergent `EventCategory` enums (`contracts/enums.py` FOMC-centric vs `time/enums.py` generic).
5. `get_business_hours()` and the Sat/Sun weekend rule are single-market assumptions (Middle-East markets break both).

## EVIDENCE

All items cite file:line (verified by direct read). `quant_engine/` contains **no** time logic (only observational `router.py:743` timestamp, hash-excluded) — the session model must NOT move into the engine (correct today).

## TARGET STATE

```
Instrument/calendar metadata (data):  sessions, boundaries, holidays, DST rules, calendars per market
                    ↓ consumed by
Data engine (load-time):             single UTC normalization (one implementation)
Macro intelligence (event-time):      planned/actual release times, event windows, calendars  [exists]
Quant engine:                         NO time logic (indices only)                             [exists — keep]
```

- **S1 — Fix the silent-UTC bug (SAFE-class change, REQUIRES REVIEW as it alters load-time behavior):** `data_engine/timezone.py` must raise on unrecognized zone names (or implement IANA via `zoneinfo` — stdlib since 3.9; the project requires ≥3.10). Silent UTC is the worst option. Any change is a **data-semantics change → scientific-integrity gate applies** (datasets loaded with wrong offsets would hash differently → must be verified against real curated XAUUSD data).
- **S2 — Unify the UTC stack (DEFER):** one canonical normalizer; MIL's frozen TimeNormalizer stays frozen — adapter at the MIL boundary if ever needed.
- **S3 — FX session calendar as data (cross-asset branch, with T3 instrument metadata):** session definitions (name, market, UTC window, DST rule) as data files feeding a boundary resolver; never hardcoded Tokyo/London/NY logic in the engine. `MarketSession` enum stays for equity; FX sessions get their own data-driven definitions.
- **S4 — Deduplicate `EventCategory` enums (DEFER to macro-consolidation branch).**

## MIGRATION RISK

| Step | Risk |
|------|------|
| S1 raise-on-unknown | Low code risk, **medium data risk** (latent mis-normalized historical loads become loud errors); gate with real-data verification |
| S1 zoneinfo | Same as above + new dependency surface (stdlib tzdata) |
| S2/S4 | Medium — MIL contracts frozen; needs adapter, not edit |
| S3 | Medium — new data layer; do with DXY onboarding |

## REQUIRED TESTS

- S1: unit tests for recognized abbreviations (unchanged), explicit-error test for unknown names; regression: curated XAUUSD loader outputs identical dataset hashes before/after (proves no currently-used path depended on the bug).

## DO NOT CHANGE

- `macro_intelligence/time/` frozen contracts (MIL invariants).
- `PlannedRelease` planned/actual semantics.
- Walk-forward/splitter index arithmetic (no timestamps by design — do not bolt timestamps onto `Fold`).
