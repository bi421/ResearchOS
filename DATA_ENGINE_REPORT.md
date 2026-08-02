# ResearchOS — Data Engine Report

Phase: Data Engine Implementation (historical market-data infrastructure)

Scope: `researchos/data_engine/` only. No trading logic, signals, prediction,
probability, execution, or decision-making artifacts were introduced. The Data
Engine is the single source of truth that every future module consumes.

---

## 1. Architecture

The Data Engine is a deterministic, auditable, immutable, and versioned
historical-data layer.

### 1.1 Object model (Article XVII — Data Layer)

| Object | Purpose |
|---|---|
| `Candle` | OHLCV bar with optional MT5 fields: `spread`, `tick_volume`, `real_volume` |
| `Tick` | Finest-granularity price update (bid/ask/last/volume) |
| `Quote` | Best bid/ask snapshot with spread and spread-bps |
| `Trade` | Executed transaction record |
| `OrderBook` | Bid/ask level snapshot |
| `HistoricalDataset` | Immutable collection of records + lifecycle + content hash |
| `DatasetMetadata` | Lightweight metadata (symbol, timeframe, source, timezone, date range, quality, hash) |
| `DatasetVersion` | Semantic version history |

### 1.2 Contracts and enums

`Timeframe`, `DataSource`, `DatasetType`, `DatasetStatus`, `DataQuality`,
`QuoteSide`, `TradeSide`, `CandleField`, `LoaderConfig`, `ValidationReport`.

`DatasetType` is new and validates `candle | tick | quote | trade | orderbook`.

### 1.3 Pipeline stages

1. **Load** — `CsvLoader` reads MT5, TradingView, and Generic OHLC CSV. Format,
   columns, timeframe, and timezone are auto-detected; all timestamps are
   normalized to UTC.
2. **Validate** — `DatasetValidator` checks OHLC integrity, duplicates,
   timestamp ordering, negative values, missing candles, gaps, and timezone
   consistency, producing a `ValidationReport` with a quality score.
3. **Statistic** — `compute_dataset_statistics` derives record count, missing
   percentage, duplicate count, gap count, average spread, average volume,
   first/last timestamp, daily coverage, trading days, and completeness.
4. **Store** — `DatasetRepository` (in-memory) and `SqliteDatasetRepository`
   persist datasets and metadata with indexes on symbol, timeframe, and date
   range.
5. **Query** — `HistoricalIterator` (chronological, no-lookahead via `as_of`),
   `RangeQuery`, `MultiSymbolQuery`, and repository date-range lookup.
6. **Integrity** — deterministic SHA-256 hashing per record and per dataset,
   with `verify_dataset_integrity`.

### 1.4 Integration diagram

```
                      ┌────────────────────────────────────────────┐
                      │                   ResearchOS                 │
                      └────────────────────────────────────────────┘
                                             │
                                             ▼
                      ┌────────────────────────────────────────────┐
                      │                 DATA ENGINE                 │
                      │       (single source of truth for data)     │
                      ├────────────────────────────────────────────┤
                      │ Models    : Candle·Tick·Quote·Trade·OrderBook│
                      │ Loaders   : MT5 · TradingView · Generic OHLC │
                      │             (auto-detect, UTC normalized)    │
                      │ Validation: OHLC · gaps · duplicates ·       │
                      │             missing · negatives · timezone   │
                      │ Statistics: completeness · coverage ·        │
                      │             spreads · volume                 │
                      │ Storage   : in-memory · SQLite (indexed)     │
                      │ Access    : Iterator (no-lookahead) ·        │
                      │             RangeQuery · MultiSymbolQuery    │
                      │ Integrity : hashing · versioning · immutable │
                      └────────────────────────────────────────────┘
                           │          │          │           │
              ┌────────────┘          │          │           └────────────┐
              ▼                       ▼          ▼                        ▼
     ┌─────────────────┐    ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
     │   QUANT ENGINE   │    │ EXPERIMENT      │ │   MARKET     │ │  MT5 /           │
     │ (Python + C++    │    │ FRAMEWORK       │ │   MEMORY     │ │  TRADINGVIEW     │
     │  parity backend) │    │                 │ │              │ │  CONNECTORS      │
     └─────────────────┘    └─────────────────┘ └──────────────┘ └──────────────────┘
```

Flow: `ResearchOS → Data Engine → Quant Engine → Experiment Framework → Market Memory`

Every later component consumes data only through this Data Engine.

---

## 2. Determinism guarantees

- Same CSV → same objects → same IDs (content-addressed `generate_id`) →
  same hashes → same repository records.
- Legacy candles (no `spread`/`tick_volume`/`real_volume`) keep
  byte-identical hashes: the new fields only participate in the hash when set.
- Verified in `TestEndToEndDeterminism` and `TestHashingExtended`.

---

## 3. Performance

### 3.1 100k candles (1-minute bars)

| Stage | Time |
|---|---|
| CSV write | 0.32 s |
| Load | 2.45 s |
| Validate | 1.37 s |
| Hash | 5.73 s |
| Repository insert | 4.66 s |
| Repository lookup | 0.007 s |
| Iterator scan | 0.078 s |
| **Total** | **~17 s** |

### 3.2 1M candles (1-minute bars)

| Stage | Time (run 1) | Time (run 2) |
|---|---|---|
| CSV write | 5.37 s | 9.55 s |
| Load | 112.6 s | 156.7 s |
| Validate | 14.7 s | 17.2 s |
| Hash | 77.2 s | 61.8 s |
| Repository insert | 137.7 s | **44.8 s** |
| Repository lookup | 0.009 s | 0.003 s |
| Iterator scan | 1.13 s | 0.20 s |
| **Total** | **~5:55** | **~4:51** |

Notes:

- `repo_insert` was optimized from 1M individual `cursor.execute` calls to a
  single `executemany` batch — 137.7 s → 44.8 s (~3× faster).
- `dataset_hash` for the 1M dataset was identical across both runs
  (`252341776fb47eb78896e72cb8a8737517c5f2b6de7bb8ca4ea1b926c017d939`),
  confirming hash determinism at scale.
- Load is dominated by object construction (1M `BaseObject` instances with
  lifecycle tracking). Run-to-run variance on this machine is large (thermal /
  memory noise affects both Python and C++ backends equally).

### 3.3 Memory

- `load` materializes full `Candle` objects (the auditable in-memory form).
- SQLite storage is indexed on `(symbol, timeframe)`, `start_time`,
  `end_time` for metadata and per-dataset record tables for fast time-range
  queries.
- Lookups are effectively constant-time regardless of dataset size
  (0.003–0.009 s at 1M records).

---

## 4. Files

### Created

| File | Purpose |
|---|---|
| `researchos/data_engine/statistics.py` | `DatasetStatistics` + `compute_dataset_statistics` |
| `researchos/data_engine/queries.py` | Public `queries` namespace re-exporting `RangeQuery`/`MultiSymbolQuery` |
| `researchos/data_engine/tests/test_statistics.py` | 31 statistics tests |
| `researchos/data_engine/tests/test_data_engine_extended.py` | 56 extended tests (DatasetType, metadata, loaders, iterator, repository, determinism) |
| `researchos/data_engine/tests/test_benchmarks.py` | 100k / 1M benchmarks (gated by `RESEARCHOS_PERF=1`) |

### Modified

| File | Change |
|---|---|
| `contracts.py` | Added `DatasetType` enum with `from_string`/`matches` |
| `candle.py` | Added optional `spread`, `tick_volume`, `real_volume` (default `None`); hash-stable conditional inclusion |
| `metadata.py` | Added `timezone` and `date_range` |
| `loader.py` | Added MT5 / TradingView / Generic profiles, format/column/timeframe/timezone auto-detection, Unix-epoch time support, duplicate removal |
| `repository.py` | `executemany` insert optimization; date-range indexes; `find_by_date_range` (in-memory + SQLite); fixed restored-dataset truthiness bug |
| `iterator.py` | Added `as_of` no-lookahead cutoff |
| `__init__.py` | Exported new symbols (`DatasetType`, `DatasetStatistics`, `compute_dataset_statistics`) |
| `tests/test_data_engine.py` | Added `TestCandleExtendedFields` (12 tests) |

---

## 5. Tests

| Suite | Result |
|---|---|
| `researchos/data_engine/tests` | **190 passed, 2 skipped** (benchmarks gated) |
| `researchos/tests` | 875 passed |
| `cpp_quant_engine/python/tests` | 169 passed, 1 skipped |

Total Data Engine test functions: **192** (exceeds the 150 minimum).

Coverage includes serialization, repository (in-memory + SQLite), UTC
normalization, deterministic IDs, hash stability, statistics, CSV loading
(MT5/TradingView/generic), gap detection, iterator (including no-lookahead),
timezone, duplicate detection, and large datasets.

---

## 6. Future integration readiness

- **MT5 Connector** — `load_mt5_candles` already parses MT5 exports
  (`Date,Time,Open,High,Low,Close,Volume` plus `tick_volume`, `real_volume`,
  `spread`), normalizes to UTC, and auto-detects timeframe. A live connector
  needs only a data pump writing the same format.
- **TradingView Connector** — `load_tradingview_candles` handles ISO and Unix
  epoch timestamps, optional symbol columns, timezone conversion, and
  duplicate removal.
- **Quant Engine** — the `HistoricalDataset` produces deterministic hashes and
  chronological records; the Quant Engine can consume `RangeQuery`/
  `HistoricalIterator` outputs directly.
- **Experiment Framework** — versioned, immutable datasets (`DatasetVersion`)
  give experiments reproducible, pinned data snapshots.
- **Market Memory** — the repository's `(symbol, timeframe, date range)`
  indexes and canonical `dataset_hash` provide content-addressed, fast lookups
  for a memory layer.

---

## 7. Quality requirements

- No placeholders, TODO stubs, mock logic, or random outputs.
- Full backward compatibility: legacy candles hash identically; all existing
  tests continue passing (875 researchos + 169 cpp-python).
- New files pass `ruff check`; `mypy` reports no new errors in changed files
  (repo-wide baseline issues and a numpy stub syntax error pre-date this phase).
- Only `researchos/data_engine/` was touched. No changes to
  `decision_engine/`, `evidence/`, `probability/`, `reasoner/`, `report/`,
  `execution/`, or `signals/`.
