# Phase 5.1 — XAUUSD Predictive-Value Experiment (TODO)

## Goal
Build the smallest scientifically valid XAUUSD experiment to answer:
"Can ResearchOS estimate a defined future XAUUSD outcome better than a
defensible baseline, out-of-sample, after realistic spread/slippage?"

## Constraints (absolute)
- Reuse existing infra; do NOT build unnecessary architecture.
- No Debate/Memory/Explanation Engines, no expanding Reasoning, no AI/LLM,
  no vector DBs, no broker execution, no synthetic-data-as-evidence.
- Real XAUUSD data is the gating input. Missing data => BLOCKED, never
  interpreted as model success/failure.
- Do NOT optimize toward any target accuracy/profitability/51%.

## Steps
- [x] Reuse analysis of existing experiments framework + quant_engine builders.
- [x] Create `contracts.py` — deterministic result contract + reproducibility hash.
- [x] Create `baseline.py` — unconditional-frequency baseline per class.
- [x] Create `probability.py` — 10-feature empirical conditional-frequency estimator.
- [x] Create `calibration.py` — reliability table + Brier score.
- [x] Create `statistics.py` — significance + confidence intervals.
- [x] Create `cost.py` — spread/slippage/commission net adjustment.
- [x] Create `self_validation.py` — PASS/FAIL/UNCERTAIN/BLOCKED flags.
- [x] Create `experiment.py` — walk-forward orchestration + deterministic result.
- [x] Create `__init__.py` — exports.
- [x] Create `tests/test_phase51.py` — determinism, leakage, baseline, cost, calibration.
- [x] Create `scripts/run_phase51_experiment.py` — entrypoint.
- [x] Run `python -m ruff check .` in ResearchOS (All checks passed).
- [x] Run Phase 5.1 tests (13 passed).
- [x] Run full regression suite (2314 passed, 56 skipped).
- [x] Report results — BLOCKED pending real XAUUSD data (entrypoint verified).

## Phase 5.1 — FINAL CODE FREEZE

Phase 5.1 implementation is FROZEN as of this checkpoint:

* 13/13 Phase 5.1 tests passed.
* Ruff passed (`python -m ruff check researchos/experiments/phase51`).
* CLI data-gating works (no real CSV -> `OUTCOME: BLOCKED`, exit code 2).
* No real XAUUSD empirical result exists yet.

## Empirical status

```
EMPIRICAL STATUS = BLOCKED
REAL XAUUSD HISTORICAL DATA REQUIRED
```

No real XAUUSD D1 dataset is currently present in the repository.  The only
CSV found (`cpp_quant_engine/docs/_baseline_native_raw.csv`) is a C++ benchmark
artifact, NOT market data.

Per the freeze, no code will be modified, refactored, or extended, and no
synthetic data will be used as evidence.  When a real XAUUSD D1 dataset is
supplied, run the EXISTING entrypoint exactly as implemented:
`python -m researchos.experiments.phase51.scripts.run_phase51_experiment
--csv <path> --format mt5 --symbol XAUUSD --timeframe 1d`

Execution precondition check (verify all before running):
1. Dataset is real.
2. Symbol is XAUUSD.
3. Timeframe is D1.
4. At least 2000 bars exist.
5. OHLC fields are valid.
6. Timestamps are chronological.
7. No obvious synthetic/demo data.
