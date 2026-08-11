# REAL XAUUSD DATA VALIDATION REPORT

**Phase:** 5.1 — Real Data Acquisition & Validation
**Role:** ResearchOS data-acquisition and validation engineer
**Date of report:** 2026-08-09
**Status:** Read-only. No Phase 5.1 code, architecture, loader, or thresholds were modified.

---

## Summary of Outcome

```
EMPIRICAL STATUS = BLOCKED
DATASET GATE = NOT SATISFIED
PREDICTIVE-VALUE CLAIM = NONE
```

No constraint-compliant real XAUUSD D1 dataset (>= 2000 bars) was obtainable
from the sources available on this machine. The dataset gate is therefore
**NOT SATISFIED**, and Phase 5.1 remains **BLOCKED**. No predictive-value
claim is made.

---

## 1. Source

The Phase 5.1 dataset identity is **frozen** and must remain:

* Symbol: **XAUUSD**
* Timeframe: **D1**
* Minimum bars: **>= 2000**
* Data: **Real historical market data**
* Synthetic / demo / benchmark data: **PROHIBITED**

Candidate sources investigated:

| Candidate | Reachability | Verdict |
| --------- | ------------ | ------- |
| MT5 broker export (local install) | Present but only `MetaQuotes-Demo` has abundant XAUUSD | REJECTED (demo feed) |
| Dukascopy (`datafeed.dukascopy.com`) | Network timeouts / 404 / connection reset | NOT OBTAINABLE here |
| Stooq (`stooq.com/q/d/l/`) | JS anti-bot challenge blocks CSV | NOT OBTAINABLE programmatically |
| OANDA | Requires API credentials (405 without auth) | NOT OBTAINABLE without credentials |
| Yahoo Finance `GC=F` | Reachable, real OHLCV | REJECTED as XAUUSD substitute (gold futures, not XAUUSD) |
| gold-api.com | Reachable, spot price only | NOT a historical OHLCV dataset |

---

## 2. Provenance

**FACT (verified on this machine):**

* A local MetaTrader 5 installation exists at
  `C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`
  (`origin.txt` points to `C:\Program Files\MetaTrader 5`).
* The profile `bases\MetaQuotes-Demo\history\XAUUSD\` contains yearly `.hcc`
  history files `2019.hcc` through `2026.hcc`, plus a `cache\Daily.hc`
  (~150,926 bytes) that would represent D1 bars.
* The profile name is literally **`MetaQuotes-Demo`**.

**OBSERVATION:**

* Abundant XAUUSD data exists only under the `MetaQuotes-Demo` server profile.
* The `bases\Default\History\XAUUSD\` profile contains only a single small
  file `2026.hcc` (~15,144 bytes) — insufficient for >= 2000 D1 bars.

**CONCLUSION:**

* The only locally abundant XAUUSD source is a **demo** broker feed.
* The task constraints explicitly state: **"Synthetic/demo/benchmark data is
  PROHIBITED."**
* Therefore the locally available XAUUSD data **cannot be used** for the gated
  empirical experiment.

---

## 3. Dataset Identity

No dataset was acquired. The required identity is:

```
Symbol:     XAUUSD
Timeframe:  D1
Format:     MT5 export preferred (Date, Time, Open, High, Low, Close, TickVolume, Spread)
Min bars:   2000
```

No such dataset was brought into the repository. The only candidate that
matched the symbol/timeframe was the `MetaQuotes-Demo` feed, which is rejected
on provenance.

---

## 4. Date Range

**UNKNOWN — no accepted dataset exists.**

The rejected `MetaQuotes-Demo` XAUUSD history nominally spans 2019–2026
(8 yearly files), but because it is a demo feed and was not parsed, no date
range is recorded for an accepted dataset.

---

## 5. Number of Bars

**UNKNOWN — no accepted dataset exists.**

The D1 cache (`Daily.hc`, ~150,926 bytes) from the demo feed would need parsing
to obtain a bar count, but that feed is rejected and was not used.

---

## 6. Timezone

**UNKNOWN — no accepted dataset exists.**

MT5 exports are typically in the broker server timezone (often
EST/UTC+2/UTC+3 depending on broker). Because no compliant MT5 export was
obtained, no timezone normalization result is recorded.

---

## 7. OHLC Validation

**NOT RUN — no accepted dataset loaded.**

The existing `DatasetValidator` (`researchos/data_engine/validator.py`) and
`Candle` schema (`researchos/data_engine/candle.py`) were not executed because
no compliant dataset was supplied.

---

## 8. Duplicate Validation

**NOT RUN — no accepted dataset loaded.**

---

## 9. Gap Validation

**NOT RUN — no accepted dataset loaded.**

---

## 10. Chronology Validation

**NOT RUN — no accepted dataset loaded.**

---

## 11. Weekend/Holiday Validation

**NOT RUN — no accepted dataset loaded.**

---

## 12. Synthetic-Data Sanity Check

**NOT RUN — no accepted dataset loaded.**

The only locally abundant XAUUSD data is a demo feed. Demo feeds are not
necessarily synthetic, but they are **not acceptable evidence** under the
constraints regardless, so no synthetic-signature analysis was performed on
them.

---

## 13. Volume

**UNKNOWN — no accepted dataset.**

The MT5 loader supports `tick_volume`, `real_volume`, and `volume`
(`researchos/data_engine/loader.py`, `_parse_mt5_rows`), but no compliant MT5
export was obtained.

---

## 14. Spread

**UNKNOWN — no accepted dataset.**

The MT5 loader supports a `spread` column (in points), and `Candle.spread`
exists, but no compliant MT5 export was obtained. Therefore:

```
SPREAD CONVERSION = UNKNOWN
```

No point-to-price-unit conversion was fabricated. The assumption
`1 point = 0.01` was **not** applied because no XAUUSD symbol specification
from a compliant source was available to confirm the point size.

---

## 15. Cost-Model Implications

The Phase 5.1 cost model (`cost.py`) applies `spread + slippage + 2*commission`
per round-trip in **price units**, using `parse_cost_spec` (`fixed:X` / `pct:Y`).

Because no dataset (and no validated spread) was obtained, **no cost-model
calibration from observed data is possible.**

Separation of what is known:

**OBSERVED DATA (none accepted):**
* OHLC — none
* timestamp — none
* volume — none
* spread — none

**ASSUMPTIONS / CONFIG-ONLY (NOT observed facts):**
* Default CLI cost specs are `spread=fixed:0.0`, `slippage=fixed:0.0`,
  `commission=fixed:0.0` (zero-cost baseline only).
* Any nonzero spread/slippage/commission values would be **assumptions**, not
  historical facts, unless documented from a compliant source.

No assumption is presented as a historical fact.

---

## 16. SHA-256

**NONE — no dataset file was accepted or hashed.**

No dataset file was imported, so no SHA-256 hash is recorded. (The repository
provides `researchos/data_engine/hashing.py` for dataset hashing once a
compliant file is supplied.)

---

## 17. Validation Table

| Check                | Result            | Evidence                                                         |
| -------------------- | ----------------- | ---------------------------------------------------------------- |
| Provenance           | UNKNOWN           | No compliant source; only `MetaQuotes-Demo` (demo) has XAUUSD    |
| Symbol               | UNKNOWN           | No accepted dataset; GC=F is not XAUUSD                         |
| Timeframe            | UNKNOWN           | No accepted dataset                                              |
| Row count            | UNKNOWN           | No accepted dataset (>=2000 not demonstrated)                   |
| OHLC                 | UNKNOWN           | No accepted dataset loaded                                      |
| Duplicates           | UNKNOWN           | No accepted dataset loaded                                      |
| Chronology           | UNKNOWN           | No accepted dataset loaded                                      |
| Gaps                 | UNKNOWN           | No accepted dataset loaded                                      |
| Timezone             | UNKNOWN           | No compliant MT5 export obtained                                |
| Synthetic-data check | UNKNOWN           | No accepted dataset loaded                                      |
| Spread               | UNKNOWN           | No compliant spread source; SPREAD CONVERSION = UNKNOWN          |

Per the task rule, **UNKNOWN is not converted into PASS.**

---

## 18. FINAL GATE

```
DATASET REJECTED
```

**Reason (evidence-based):**

1. **Provenance fails the hard constraint.** The only locally abundant XAUUSD
   D1 data resides in the **`MetaQuotes-Demo`** broker profile, and the
   constraints explicitly prohibit **demo** data. Using it would be a
   provenance violation.
2. **Yahoo `GC=F` is not XAUUSD.** It is a real COMEX gold-futures series, but
   the frozen Phase 5.1 identity is `XAUUSD`. Substituting `GC=F` would change
   the dataset identity and is not permitted.
3. **Dukascopy, Stooq, and OANDA were not obtainable** from this machine
   (network timeouts / anti-bot protection / missing credentials).
4. **No dataset was loaded, validated, or hashed**, so every validation check
   is `UNKNOWN` and the gate requirements (>= 2000 valid bars, chronological
   ordering, OHLC validity, duplicate check, timezone understanding, no serious
   synthetic indicators) are **not demonstrated**.

---

## Appendix A — Repository Readiness (frozen, no changes)

The Phase 5.1 pipeline is **code-complete and frozen**, and will accept a
compliant file with no changes:

| Component | Path | Status |
| --------- | ---- | ------ |
| `CsvLoader.load_mt5_candles` | `researchos/data_engine/loader.py` | Ready |
| `Candle` schema (spread/tick_volume/real_volume) | `researchos/data_engine/candle.py` | Ready |
| `LoaderConfig` / `CandleField` / `Timeframe(D1)` | `researchos/data_engine/contracts.py` | Ready |
| `DatasetValidator` / `GapDetector` / `DuplicateDetector` / `MissingCandleDetector` | `researchos/data_engine/validator.py` | Ready |
| Provenance (`DatasetMetadata`, SHA-256 `compute_dataset_hash`) | `researchos/data_engine/metadata.py`, `hashing.py` | Ready |
| Phase 5.1 entrypoint (CLI) | `researchos/experiments/phase51/scripts/run_phase51_experiment.py` | Ready / BLOCKED |
| Cost model (`parse_cost_spec`) | `researchos/quant_engine/execution.py` | Ready |

The CLI that will consume the future dataset (unchanged):
```
python -m researchos.experiments.phase51.scripts.run_phase51_experiment \
    --csv <path> --format mt5 --symbol XAUUSD --timeframe 1d
```

---

## Appendix B — Exact Missing Requirement

```
A legitimate, non-demo XAUUSD D1 historical dataset with:
  - symbol == XAUUSD
  - timeframe == D1
  - >= 2000 valid bars (>= ~8 years)
  - chronologically ordered OHLC (timestamp, open, high, low, close)
  - optionally tick_volume and spread (MT5 export, in points)
  - verifiable provenance (broker / Dukascopy / OANDA / Stooq preferred)
```

---

## Appendix C — Recommended Next Acquisition Path

1. **Preferred:** Obtain an MT5 export from a **live (non-demo) broker account**
   for `XAUUSD` D1, exporting `Date, Time, Open, High, Low, Close, TickVolume,
   Spread` (>= 2000 bars). This is the preferred source and matches the frozen
   identity exactly.
2. **Alternative:** Download XAUUSD D1 from **Dukascopy** (bank-feed data,
   bid/ask per tick, real market data) via a reachable network or a download
   tool, then convert to an MT5/CsvLoader-compatible CSV.
3. **Alternative:** Use **OANDA** (requires API credentials) to pull XAUUSD/USD
   daily candles.
4. **Alternative:** Use **Stooq** XAUUSD daily data via a browser/manual export
   (its automated endpoint is bot-protected).
5. Do **not** use `MetaQuotes-Demo`, `GC=F`, Kaggle, or unverifiable scrapes as
   a substitute for `XAUUSD`.

Once such a file is supplied, it must pass the full validation gate before
Phase 5.1 is allowed to run.

---

## Appendix D — Strict Separation of Claims

**FACT**
* Local MT5 install exists; only `MetaQuotes-Demo` has abundant XAUUSD.
* `GC=F` (Yahoo) is reachable and is COMEX gold futures, not XAUUSD.
* Dukascopy, Stooq, OANDA were not obtainable from this machine.
* No dataset was imported, loaded, validated, or hashed.

**OBSERVATION**
* The demo feed nominally spans 2019–2026 but was not parsed/used.

**ASSUMPTION**
* (None applied to the dataset; no data was acquired.)

**UNKNOWN**
* Every validation metric (OHLC, duplicates, chronology, gaps, timezone,
  synthetic check, spread) is UNKNOWN — no dataset was loaded.

**CONCLUSION**
* DATASET REJECTED. EMPIRICAL STATUS = BLOCKED. No predictive-value claim.
* Next action is external acquisition of a legitimate non-demo XAUUSD D1
  dataset with >= 2000 bars.
