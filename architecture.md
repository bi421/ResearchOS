# ResearchOS Architecture

## Data Flow (Canonical)

DATA
  ↓
VALIDATION
  ↓
STRUCTURED DATA
  ↓
MARKET MEMORY
  ↓
QUANTITATIVE ANALYSIS
  ↓
MARKET CONTEXT
  ↓
RESEARCH
  ↓
EXPERIMENT
  ↓
EVALUATION
  ↓
EVIDENCE
  ↓
INTELLIGENCE
  ↓
FUTURE LEARNING
  ↓
PROBABILITY

## Implementation Status (2026-08-18)

| Component | Status | Evidence |
|-----------|--------|----------|
| Data Engine | ✅ CURRENT | esearchos/data_engine/ — Candle, Dataset, SQLite |
| Market Memory | ⚠️ TRANSITIONAL | esearchos/market_memory/ — partial integration |
| Quant Engine | ✅ CURRENT | PythonQuantBackend, C++ backend available |
| Decision Engine | ✅ CURRENT | compute_evidence_score, EvidenceItem |
| Macro Intelligence | ✅ CURRENT | macro_intelligence/ — econometrics, regime |
| Intelligence | ✅ CURRENT | esearchos/intelligence/ — EvidenceGraph |
| Future Learning | ❌ FUTURE | Not implemented (intentional) |

## Verified Capabilities

| Capability | Status | Evidence |
|------------|--------|----------|
| 7 assets + 3 macro factors analysis | ✅ | un_full_analysis_fixed4.py |
| Trend detection (SMA) | ✅ | un_trend_analysis_fixed.py |
| Evidence Score | ✅ | compute_evidence_score() |
| Backtesting (XAUUSD) | ✅ | un_first_backtest.py |
| Live vs historical candle validation | ✅ | live_candle_validator.py |
| Markdown reports | ✅ | 	rend_report_verified.md |

## Backtest Result (XAUUSD 2021-2025 D1)

| Metric | Value |
|--------|-------|
| Total bars | 1554 |
| Num trades | 55 |
| Final equity | 238,800.45 |
| Total return | 138.80% |
| Max drawdown | 20.72% |
| Result hash | d5b9125af75b069eca4e1b31223cbe3acc5f9aa2777c16636ec819a0368b9b6f |

## Critical Invariants

- ✅ NO PREDICTIVE INTELLIGENCE WITHOUT VALIDATED HISTORICAL EVIDENCE
- ✅ DETERMINISTIC: Same inputs → same outputs
- ✅ IMMUTABLE: Completed experiments cannot be mutated
- ⚠️ PROBABILITY: Current Score is heuristic, NOT calibrated probability

## Architecture Guards

- ✅ quant_engine must not depend on decision_engine
- ✅ core must not depend on high-level intelligence
- ✅ experiments must not mutate configurations
- ✅ evidence must preserve lineage
- ✅ learning.py remains future/unimplemented
- ✅ broker execution does not exist
- ⚠️ synthetic data gates need strengthening

## Next Steps

1. Fix change: 0.00% bug in trend analysis
2. Integrate macro_intelligence into full analysis pipeline
3. Add MACD, RSI, Bollinger Bands indicators
4. Implement probability calibration
5. Create HTML/PDF report format
