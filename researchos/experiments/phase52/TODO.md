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
- Real XAUUSD data AND real DXY/US10Y/VIX data are gating inputs.
- Market calendars may differ. The Phase 5.2 CLI constructs an explicit
  common-observation sample using only timestamps present in XAUUSD AND all
  required macro sources. Missing observations are excluded from the sample;
  they are never fabricated, interpolated, or forward-filled.
- The core `run_phase52` contract remains exact, one-to-one, order-preserving
  UTC timestamp alignment. The CLI satisfies that contract only after the
  common-observation sample has been constructed.
- No interpolation/forward-fill of macro data across a gap. A source without
  an observation on a date contributes no row to the common sample.
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
      XAUUSD + DXY + US10Y + VIX CSVs. It constructs an explicit common
      observation sample by timestamp; no interpolation or forward-fill.
- [x] Add alignment tests covering calendar gaps and duplicate macro rows.
- [x] Register `researchos/experiments/phase52/tests` in `pyproject.toml`
      `[tool.pytest.ini_options].testpaths` and in the CI pytest invocations
      (`test-python.yml`, `coverage.yml`) alongside phase51/tests.
- [ ] Verify the common-observation sample on real XAUUSD + DGS10 + VIX + DXY
      inputs and record exact retained-row counts/provenance.
- [ ] Resolve and document a defensible DXY source identity before empirical
      execution; do not silently substitute a different dollar index.
- [ ] Run full CI on the common-observation-sample branch and review all tests.

## Current empirical status

```
EMPIRICAL STATUS = BLOCKED
REAL XAUUSD + DXY + US10Y + VIX HISTORICAL DATA REQUIRED
```

Real XAUUSD, DGS10 and VIX data are now available locally, but DXY has not
yet been acquired from a defensible source. The current local calendar audit
shows 1,290 XAUUSD 2021–2025 dates, with 1,247 DGS10 matches and 1,282 VIX
matches. The missing observations are primarily US market holidays. These
are calendar differences, not evidence that the macro series should be
forward-filled.

Once all four real datasets are supplied, run:

```
python -m researchos.experiments.phase52.scripts.run_phase52_experiment \
    --csv <xauusd.csv> --dxy <dxy.csv> --us10y <dgs10.csv> --vix <vix.csv> \
    --format mt5 --symbol XAUUSD --timeframe 1d
```

Execution precondition checklist (verify all before treating a result as
empirical evidence):
1. All four datasets are real (not synthetic/demo).
2. XAUUSD symbol/timeframe match the configured experiment.
3. DXY identity is explicitly documented; do not confuse ICE DXY with a
   different broad-dollar or broker-specific index without labeling it.
4. All timestamps are chronological and duplicate-free.
5. The common-observation sample is the exact intersection of XAUUSD and all
   required macro timestamps; no value is invented for a missing date.
6. At least `train_size + validation_size` aligned bars remain after the
   common-date merge (2000+ recommended, matching Phase 5.1 where applicable).
7. `result.macro_symbols_missing` is empty — if it is not, the result is
   BLOCKED and carries no empirical weight regardless of any accuracy figure
   printed alongside it.
