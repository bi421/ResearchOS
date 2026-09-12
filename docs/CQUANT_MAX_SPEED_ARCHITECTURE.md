# CQuant Max-Speed Architecture

## Objective

CQuant is the numerical execution layer of ResearchOS. The target is not simply
"more C++"; it is to move the hot numerical loops out of Python while keeping
scientific contracts, provenance, and orchestration in Python.

## Current fast-path slice

The branch adds a dedicated `cpp_quant_fast_backend` nanobind module backed by
`quant::fast` kernels.

| Operation | Native implementation | Python callback in hot loop |
|---|---|---:|
| simple returns | `simple_returns` | No |
| running drawdown | `drawdown_pct` | No |
| batch next-open backtest | `backtest_next_open` | No |
| risk scan | `risk_scan` | No |

The batch backtest receives complete vectors once and performs the bar loop in
C++. Signal decisions are supplied as an already-materialized integer vector;
strategy fitting/feature construction remains outside this numerical kernel.

## Why this is materially different

The legacy `BacktestEngine` accepts a `SignalFn` callback. That is useful for
flexibility, but a Python callback per bar can dominate runtime at millions of
bars. The fast path removes that callback from the hot loop.

The existing bridge remains intact. The new module is additive and can be
benchmarked and adopted incrementally without changing the scientific Phase52
contracts.

## Performance contract

No speedup number is considered valid until measured on the same machine and
build configuration. CI now runs a 1,000,000-row Release benchmark and prints:

- Python median runtime
- C++ median runtime
- measured speedup
- maximum numerical error
- callback-free backtest runtime

The benchmark measures Python/C++ vector marshalling as part of the real call.
That prevents an artificial "kernel only" claim that ignores integration cost.

## Next optimization tiers

1. **Current:** one-shot vector batch kernels.
2. **Next:** zero-copy contiguous numeric buffers through nanobind ndarray/buffer
   interfaces to remove Python-list conversion and allocation.
3. **Next:** fused kernels that combine feature/return/risk passes to reduce
   memory bandwidth and intermediate allocations.
4. **Next:** parallel execution for independent parameter/feature-set sweeps;
   never parallelize a stateful chronological loop unless its semantics are
   explicitly partition-safe.
5. **Next:** SIMD-friendly data layout and cache-aware columnar arrays.
6. **Next:** benchmark matrix at 1M / 10M / 100M rows with throughput and peak
   RSS, then use evidence to choose optimization priorities.

## Scientific boundary

Speed must never change the research contract. CQuant must preserve:

- chronological ordering;
- exact timestamps supplied by the caller;
- no look-ahead;
- deterministic calculations for identical inputs;
- explicit commission/slippage assumptions;
- auditable input/result identity where the public bridge is used.

A faster wrong backtest is a regression, not an optimization.
