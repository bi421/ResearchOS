# Real walk-forward validation

The C++ `BacktestEngine::run_walk_forward` now performs chronological out-of-sample evaluation instead of silently falling back to a full-sample backtest.

## Contract

- Each fold has a contiguous training/context interval followed by a disjoint test interval.
- Signals are disabled during the training/context interval.
- The signal callback sees only the fold prefix through the current bar.
- Execution remains next-bar-open through the existing `run()` execution model.
- Folds advance by the test-window size, so OOS test intervals do not overlap.
- Incomplete final folds are excluded; if no complete fold exists, the call fails.
- The current `SignalFn` API has no fit callback. Therefore the implementation is a strict OOS evaluator for a fixed deterministic signal function, with the training interval serving as causal indicator warm-up/context rather than parameter fitting.

A future model-fitting API must explicitly fit only on the training interval and bind the resulting parameters before evaluating the corresponding test interval.
