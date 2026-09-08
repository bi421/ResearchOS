# Walk-forward audit gate

The production-hardening branch contains a real chronological OOS evaluator in the C++ backtest engine. The evaluator refuses invalid window sizes and incomplete datasets, disables signals during training/context bars, and advances by disjoint test windows. The existing next-bar-open execution rule remains authoritative.

The evaluator is intentionally scoped to the current `SignalFn` contract: it does not claim to perform parameter fitting because that API has no training callback. Any fitted strategy must expose an explicit train-only fitting boundary before it can be certified as fitted walk-forward validation.
