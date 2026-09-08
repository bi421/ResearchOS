# Phase 5.2 — Macro-Augmented (DXY / US10Y / VIX) XAUUSD Experiment (TODO)

## Goal
Extend Phase 5.1's question with macro conditioning:
"Can ResearchOS estimate a defined future XAUUSD outcome better than a
defensible baseline, out-of-sample, after realistic spread/slippage, when
conditioned on a DXY / US10Y / VIX macro factor?"

## Relationship to Phase 5.1
Phase 5.1 (`researchos/experiments/phase51/`) is under a FINAL CODE FREEZE
and is **not modified** by this phase. Phase 5.2 imports its frozen
primitives (`EmpiricalProbabilityEstimator`, `baseline_always_predict`,
`evaluate_calibration`, `apply_costs`, `evaluate_significance`,
`aggregate_outcome`) unmodified and composes them with a new macro-aware
feature/dataset layer. This keeps the PASS/FAIL/UNCERTAIN/BLOCKED semantics
and reproducibility-hash scheme identical across phases, so a Phase 5.1
result and a Phase 5.2 result are directly comparable.

## Constraints (absolute, carried over from Phase 5.1)
- Reuse existing infra; do NOT build unnecessary architecture.
- No Debate/Memory/Explanation Engines, no expanding Reasoning, no AI/LLM,
  no vector DBs, no broker execution, no synthetic-data-as-evidence.
- Real XAUUSD data AND real, aligned DXY/US10Y/VIX data are gating inputs.
  Missing/misaligned data => BLOCKED, never interpreted as model success or
  failure.
- No interpolation/forward-fill of macro data across a gap — a bar with no
  matching macro row is `None` at that index, not an estimated value.
- Do NOT optimize toward any target accuracy/profitability/51%.

## Steps
- [x] Create `macro_features.py` — deterministic, lookahead-safe DXY/US10Y/VIX
      feature builder (3 features per factor: 1-bar return, 5-bar rolling
      mean return, 20-bar rolling z-score).
- [x] Create `dataset.py` — merges price/technical features (Phase 5.1's
      `FeatureBuilder`, untouched) with macro features into one aligned
      `ResearchDataset`, without modifying `DatasetBuilder`.
- [x] Create `contracts.py` — `Phase52Result`, reusing `BaselineResult` /
      `ModelResult` / `CostResult` / `CalibrationResult` / `SignificanceResult`
      / `ValidationFlags` / `Outcome` / `reproducibility_hash` from the frozen
      Phase 5.1 contracts unmodified.
- [x] Create `experiment.py` — walk-forward orchestration identical in
      structure to Phase 5.1's, with macro-availability gating and a feature
      resolver that defaults to a macro feature (falls back to price) so the
      experiment actually tests macro conditioning unless overridden.
- [x] Create `__init__.py` — exports.
- [x] Create `tests/test_phase52.py` — determinism, macro-missing gating,
      macro-misaligned-length gating, insufficient-bars gating, walk-forward
      fold count, explicit feature override, macro feature builder
      missing-symbol handling and no-lookahead behavior (10 tests).
- [x] Create `scripts/run_phase52_experiment.py` — entrypoint requiring
      XAUUSD + DXY + US10Y + VIX CSVs, aligned by exact date match (no
      interpolation); BLOCKED with a clear reason if any is absent/misaligned.
- [x] Register `researchos/experiments/phase52/tests` in `pyproject.toml`
      `[tool.pytest.ini_options].testpaths` and in the CI pytest invocations
      (`test-python.yml`, `coverage.yml`) alongside phase51/tests.
- [x] Run `ruff check .` across the full repo (All checks passed).
- [x] Run the full regression suite (3042 passed, 71 skipped, 0 failed —
      up from 3032/71 pre-Phase-5.2, confirming nothing existing broke).

## Empirical status

```
EMPIRICAL STATUS = BLOCKED
REAL XAUUSD + DXY + US10Y + VIX HISTORICAL DATA REQUIRED
```

No real XAUUSD, DXY, US10Y, or VIX dataset is currently present in the
repository. When real, date-aligned CSVs for all four are supplied, run:

```
python -m researchos.experiments.phase52.scripts.run_phase52_experiment \
    --csv <xauusd.csv> --dxy <dxy.csv> --us10y <us10y.csv> --vix <vix.csv> \
    --format mt5 --symbol XAUUSD --timeframe 1d
```

Execution precondition checklist (verify all before treating a result as
empirical evidence):
1. All four datasets are real (not synthetic/demo).
2. XAUUSD symbol/timeframe match the configured experiment.
3. DXY/US10Y/VIX cover the same date range as the XAUUSD series.
4. At least `train_size + validation_size` aligned bars remain after the
   exact-date-match merge (2000+ recommended, matching Phase 5.1).
5. Timestamps are chronological in every input file.
6. `result.macro_symbols_missing` is empty — if it is not, the result is
   BLOCKED and carries no empirical weight regardless of any accuracy figure
   printed alongside it.
