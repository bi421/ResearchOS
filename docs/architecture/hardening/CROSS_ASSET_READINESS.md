# CROSS_ASSET_READINESS.md

**Date:** 2026-08-17 — AUDIT ONLY. No implementation.

---

## CURRENT STATE

**Verdict: the computation layer is genuinely asset-agnostic.** Every symbol/asset/reference-market hit in `quant_engine/` was located, read, and classified. Asset-specific *code* is correctly quarantined in `data_engine/` loaders and `experiments/`.

### Functional violations in generic quant_engine code (complete list, 3 + 1 assumption)

| # | Location | Issue | Severity |
|---|----------|-------|----------|
| V1 | `quant_engine/compatibility.py:369` | `dataset_reference="XAU/USD:PARITY"` hardcoded in `_make_default_request()` — label only (backend parity certification), not computation | Low |
| V2 | `quant_engine/fundamental/contracts.py:94,97` | `country="US"`, `currency="USD"` defaults on `EconomicCalendarEvent` | Low |
| V3 | `quant_engine/fundamental/contracts.py:113-127` + `fundamental/analytics.py:133-172` | `CommodityBasket` hardcodes oil/silver/copper/gold members; analytics hardcode `gold_oil`, `gold_silver`, `gold_copper` correlations and gold ratios; `DOLLAR_INDEX` indicator | **By design** — this subpackage IS the precious-metals fundamental layer; question is its location (asset-specific analytics inside generic engine) |
| V4 | `quant_engine/models.py:49` + `models/legacy_models.py:49` | `"tick": 252 * 6.5 * 3600` in `periods_per_year` — US-equity session assumption baked into generic models; wrong for FX/metals (~24h, ~260d) and crypto (365/24) | **Medium — affects annualization correctness for future assets** |

### Cosmetic (no logic): docstring examples `"XAU/USD:2020-2024"` (`models.py:72`), `"xauusd_direction_v1"` (`models/contracts.py:51`, `training/contracts.py:109`).

### Misleading names (flag only): `historical/analytics.py:215` `session_statistics()` computes whole-series stats (no session boundaries); `technical/indicators.py:393` `vwap()` says "Session VWAP" but is cumulative whole-series VWAP.

### Correctly quarantined (verified, not violations)

- `data_engine/xauusd_csv_loader.py`, `xauusd_dataset.py` — **never imported by quant_engine** (grep: zero external references).
- `data_engine/loader.py:39-59` — generic registry-based loader; `"xauusd"` entry is configuration data (marked FROZEN) alongside `btcusdt`/`ethusdt`, not logic.
- `experiments/phase51` — `symbol="XAUUSD"` default is experiment configuration; `run_phase51` takes arbitrary OHLCV; `experiments/crypto/run_btc_research.py` demonstrates the reuse pattern.
- The only quant_engine→data_engine import is `replay.py:22-23` (`HistoricalDataset`, `HistoricalIterator` — generic contracts).

## PROBLEM

1. **V4 annualization assumption** — silent wrong annualized metrics for non-equity assets if `periods_per_year` defaults are used uncritically.
2. **V3 placement** — gold/commodity fundamental analytics live inside the generic engine; when EURUSD/DXY arrive, the pattern invites EUR-specific analytics into `quant_engine/` too.
3. No canonical **instrument/symbol metadata registry** exists (tick size, session calendar, currency, pip/point conventions) — see SESSION_TIME_ARCHITECTURE.md; without it, every asset brings ad-hoc constants (as V4 shows).

## EVIDENCE

All items above cite file:line and were classified by reading the code, not filenames. Session/timezone grep across `quant_engine/`: zero Tokyo/London/NY hits; only `router.py:743` `datetime.now(timezone.utc)` (observational, excluded from hashes by contract).

## TARGET STATE

- **T1 — Parameterize annualization (REQUIRES REVIEW — touches metrics semantics).** `periods_per_year` per request/instrument (supplied by instrument metadata), not a global table with equity assumptions. Until then: document that the tick constant is US-equity.
- **T2 — Freeze the boundary rule:** generic `quant_engine/` accepts NO new asset-specific analytics; asset fundamentals belong to asset-context packages (macro interpretation layer, per MACRO_OWNERSHIP_PROPOSAL.md). `fundamental/` stays where it is (moving it now breaks public API for zero functional gain) but is documented as the XAUUSD/metals fundamental module.
- **T3 — Introduce an instrument metadata contract when cross-asset work starts** (symbol → tick size, calendar id, currency, annualization periods, session ids). NOT NOW — build it on the cross-asset branch when DXY/EURUSD data actually arrives.

## MIGRATION RISK

| Step | Risk |
|------|------|
| T2 docs | None |
| T1 | Medium — changes default metrics semantics if done carelessly; must be additive (explicit per-request override first, default change never) |
| T3 | Medium — new contract; do with first second-asset onboarding |

## REQUIRED TESTS

- T1: new parameterized-annualization unit tests (252d equity, 260d FX, 365d crypto) asserting annualized metrics scale exactly with periods; existing tests must remain green (default path unchanged).

## DO NOT CHANGE

- Any formula in `metrics.py`, `performance.py`, `statistics.py` — scientific reference implementation.
- Router/backend certification flow.
- `fundamental/` analytics values (gold correlations are research content).
