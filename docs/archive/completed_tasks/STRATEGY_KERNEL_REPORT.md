# Document Status

Status:
ARCHIVED

Reason:
Historical record only

Superseded by:
See docs/ARCHITECTURE_FREEZE_V2.md (current constitution)

Original purpose:
See docs/DOCUMENTATION_INVENTORY_REPORT.md

---

# C++ Strategy Simulation Kernel Report

**Project:** ResearchOS — `cpp_quant_engine`
**Date:** 2026-07-31
**Scope:** `C:\Users\User\Desktop\ResearchOS\cpp_quant_engine` (C++ engine only; no changes to the ResearchOS Python architecture).

---

## 1. Executive Summary

A deterministic strategy simulation kernel was added to the C++ engine. The kernel
is a **pure function of (bars, signals, config)**: identical inputs always produce
identical trades, equity curve, statistics, and hashes, and independent instances
may run concurrently with no shared mutable state. It fills signals at the next
bar open (no look-ahead), manages long/short positions with stop loss, take
profit, trailing stop, break-even, partial close, ATR stops, time stops, daily
loss limits, session filters and per-signal overrides, and produces a full
statistics/reporting object plus canonical input/result hashes.

Per the task constraints, no trading-strategy research, broker connections, or AI
components were added — only deterministic simulation, risk/exit logic,
statistics, hashing, and performance measurement. The phase adds **90 unit tests**
(4 suites) and 5 native benchmark rows; the full suite is now **365 tests / 39
suites, all green in Debug and Release**.

## 2. Deliverables & Status

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Deterministic `StrategyKernel` (`run(bars, signals, config)` → `SimulationResult`) | Done |
| 2 | Position management (SL / TP / trailing / break-even / partial close / time stop / ATR) | Done |
| 3 | Long & short, fixed-lot & risk-% sizing, costs (commission, spread, slippage), per-signal overrides | Done |
| 4 | Portfolio risk (daily loss limit, max open positions, max trades/day, session filter, close-on-session-end) | Done |
| 5 | Statistics (P&L, R, profit factor, drawdown, Sharpe/Sortino/Calmar/Ulcer, equity & drawdown curves, period returns) | Done |
| 6 | Canonical input/result hashing + determinism guarantees | Done |
| 7 | Benchmark rows (10M-candle sweep, 1M signals, 1M trades) | Done |
| 8 | 90 new unit tests (365 total, Debug + Release green) | Done |

## 3. Scope Boundaries (Explicitly NOT Changed)

- ❌ No trading signals / strategy research logic added.
- ❌ No broker/execution connections.
- ❌ No AI/ML components.
- ✅ Only: deterministic simulation, risk & exit logic, statistics, hashing, benchmarking.

## 4. Architecture Overview

```
                  bars (OHLCV[]) + signals[] + StrategyConfig
                                      │
                                      ▼
                         ┌───────────────────────┐
                         │    StrategyKernel     │   pure function, no global state
                         │  include/quant/strategy/strategy_kernel.h
                         │  src/strategy/strategy_kernel.cpp
                         └───────────┬───────────┘
                                     │
              ┌──────────────────────┼───────────────────────┐
              ▼                      ▼                       ▼
┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────────────┐
│  PositionManager    │  │  Stats + reports     │  │  Hashing               │
│  src/strategy/      │  │  SimulationResult /  │  │  src/strategy/         │
│  position.cpp       │  │  TradeStats          │  │  strategy_hash.cpp     │
│  (SL/TP/trailing)   │  │  simulation_result.h │  │  compute_input_hash /   │
│                     │  │  trade_result.h      │  │  result hash           │
└─────────────────────┘  └──────────────────────┘  └─────────────────────────┘
```

## 5. Component Details

### 5.1 `StrategyKernel` — execution model

New module `include/quant/strategy/strategy_kernel.h` / `src/strategy/strategy_kernel.cpp`.

- **No look-ahead**: a signal with `bar_index == i` is queued while bar *i* is
  processed and filled at the **open of bar *i+1***; a signal on the final bar is
  never filled. Signals are `stable_sort`ed by `bar_index` before processing, so
  execution is identical regardless of the caller's signal ordering.
- **Reference-anchored exits**: stop / take-profit / partial / trailing / ATR
  levels are anchored to the **reference price = close of the signal bar**, not
  the fill price. A gap that opens through a level fills at the open price;
  otherwise the level is exercised at the level price. This gives deterministic
  behavior for gaps, same-candle SL/TP races, and ATR-derived levels.
- **Same-candle resolution order**: stop loss is checked before take profit
  (conservative) on a bar where both are touched; time stop is evaluated after
  price-based exits.
- **Costs**: entry commission is charged at open (reflected in `realized_pnl`
  and `cash`); exit commission / slippage / spread applied per fill.
- **Validation**: empty bars, invalid OHLC, non-monotonic timestamps, and
  out-of-range/negative signal bar indices are rejected with typed errors.
- **Performance model**: bars, signals, positions and outputs live in contiguous
  `std::vector` storage; the per-bar hot loop performs **no heap allocation** (the
  signal queue and open-position store are reserved once); ATR is precomputed
  once into a contiguous series; hashing is opt-out (`compute_hash = false`) for
  pure-throughput runs.

### 5.2 Position management — `PositionManager` / `position.h`

`include/quant/strategy/position.h` / `src/strategy/position.cpp`.

- Long & short P&L helpers, MFE/MAE tracking.
- Stop loss / take profit / trailing stop with ratchet (longs ratchet up, shorts
  ratchet down), trailing activation gate (profit ≥ activation × stop distance),
  break-even activation, partial close (fraction closed at the partial target,
  remainder managed), time stop (`max_bars_in_trade`).
- Fixed (`StopType::Fixed`) and ATR (`StopType::ATR`) stop distance modes with
  `atr_period`, SL/TP/trailing multipliers.
- Per-signal overrides: `stop_loss`, `take_profit`, `trailing_stop`,
  `quantity`, `risk_amount`.

### 5.3 Sizing & costs

- `PositionSizing::FixedLot` (fixed quantity) or `PositionSizing::RiskPercent`
  (quantity = risk / stop distance, where risk = `risk_percent` × equity or the
  `risk_amount` override); `default_quantity` fallback when a risk-based trade has
  no stop distance.
- `commission_pct` (notional fraction), `commission_per_lot` (flat per unit),
  `spread_pct` (round-trip half-spread), `slippage_pct`.

### 5.4 Portfolio risk

- **Daily loss limit**: at the close, when equity ≤ start-of-day ×
  (1 − `daily_loss_limit_pct`/100), all positions are closed with
  `ExitReason::DailyLossLimit` and new **Open** signals generated during the halt
  are rejected at the signal bar (counted in `signals_ignored`); the limit resets
  at the next UTC day.
- **Max open positions** cap and **max trades per day** gate.
- **Session filter** (UTC hour window, weekday gating, wrap past midnight) and
  **close-on-session-end** force close.

### 5.5 Statistics & reporting

`include/quant/strategy/simulation_result.h`, `trade_result.h`.

- Per-trade records (entry/exit bar & price, quantity, commission, slippage, net
  P&L, R multiple, MFE/MAE, exit reasons) and classification helpers.
- `TradeStats`: total/winning/losing trades, win rate, average win/loss, average
  R, gross profit/loss, profit factor (∞ when no losses), expectancy (currency &
  R), net profit, max consecutive win/loss streaks, Sharpe, Sortino, Calmar,
  Ulcer index, `max_drawdown` (largest **peak-at-time** to trough distance),
  `recovery_factor`, annualized return/volatility, total return %.
- Per-bar equity curve and drawdown curve, `final_equity`, yearly/monthly returns.

### 5.6 Hashing & determinism

`src/strategy/strategy_hash.cpp`.

- `compute_input_hash(bars, signals, config)` — canonical, **independent of
  caller signal order** (signals sorted by `bar_index` before serialization).
- Result hash — stable across independently constructed instances running the
  same input.
- Hashing is deterministic, canonical-float based, and opt-out per run.

## 6. Build & Test Results

Environment: Visual Studio 17 2022 (x64), CMake 4.4.0, C++20, GoogleTest v1.15.2 (static).

```
cmake -S . -B build
cmake --build build --config Debug
cmake --build build --config Release
```

| Config | Test executable | Result |
|--------|-----------------|--------|
| Debug | `build/tests/Debug/quant_engine_tests.exe` | **365/365 passed** (39 suites, ~34 s) |
| Release | `build/tests/Release/quant_engine_tests.exe` | **365/365 passed** (39 suites, ~0.8 s) |

**New tests (90) by suite:**

| Suite | Coverage | Tests |
|-------|----------|-------|
| `StrategyKernel` | execution model, gaps & same-candle races, costs, sizing, trailing/break-even/partial/time/ATR stops, daily loss limit, max positions, sessions, close/modify actions, statistics, drawdown, period returns, determinism, hashing, throughput | 78 |
| `Position` | P&L helpers, MFE/MAE, break-even, trailing ratchet (long/short) | 8 |
| `TradeResult` | classification helpers, readable summary, exit-reason names | 3 |
| `StrategySignal` | side/action name helpers | 1 |

Notable verified semantics (Debug + Release):
- Gap through stop/TP fills at the open; same-candle stop beats take profit.
- Commission charged on entry and exit; per-lot commission; huge spread flips a
  profit into a loss.
- Trailing stop ratchets only in the favorable direction; ATR levels derive from
  true range.
- Daily-loss circuit breaker closes positions and rejects subsequent opens until
  the next day.
- Identical inputs → identical trades/equity/stats/hashes; input hash is
  insensitive to signal ordering; result hash stable across instances.
- `max_drawdown` / `recovery_factor` match hand-computed peak-to-trough values.

## 7. Benchmark Results (Release build)

New rows added to `benchmarks/benchmark_main.cpp` (same CSV harness as the
backtest report; measured on this machine):

| Row | count | seconds | notes |
|-----|-------|---------|-------|
| `strategy.kernel.run` 100k  | 100k bars | 0.043 | full sweep, 10k signals, no hash |
| `strategy.kernel.run` 1M    | 1M bars   | 1.450 | ~1.5M bars/s |
| `strategy.kernel.run` 10M   | 10M bars  | 6.721 | ~1.5M bars/s; peak mem 4184 MiB |
| `strategy.kernel.signals_1m` | 1M signals | 0.802 | one signal per bar; ~1.25M signals/s |
| `strategy.kernel.trades_1m` | 1M signals | 0.876 | 999,999 completed trades; ~1.14M trades/s |

Notes:
- The 10M-candle sweep covers ~19 years of M1 bars with a 10k-signal stream,
  full per-bar equity/drawdown curves, statistics, and no result hashing.
- The 1M-signals and 1M-trades rows stream one signal per bar over 1M bars; the
  trades row uses a 1-bar time stop for deterministic round trips (999,999
  trades, 0 open at end).
- Memory is dominated by the bar/equity storage for the 10M dataset (consistent
  with the backtest harness); the kernel itself keeps open-position storage
  bounded and allocation-free in the hot loop.

## 8. Notable Build-System Changes

- Sources are picked up by the existing `file(GLOB_RECURSE src/*.cpp ...)` rule;
  the benchmark harness (`quant_engine_bench`) gained the StrategyKernel rows via
  `#include "quant/strategy/strategy_kernel.h"`.
- No CMake target or test-registration changes were required; the new test
  sources are discovered by `gtest_discover_tests`.

## 9. Known Limitations & Future Work

- Single-threaded by design per instance; throughput rows were measured without
  result hashing. Parallel backtests over independent instances are a natural
  follow-up (the kernel is multithread-ready by construction).
- Intra-bar fill detail is bar-close/bar-open granularity (no intra-bar tick
  simulation); same-candle SL/TP races resolve conservatively (stop first).
- ATR is computed with the configured `atr_period` over the full series up front;
  warm-up bars prior to the period produce a defined (rolling) ATR series.
- `RiskMetrics::max_drawdown` (`src/statistics/risk.cpp`) computes the drawdown
  amount with the global peak rather than the peak at the time of the drawdown;
  the kernel's own `TradeStats::max_drawdown` was fixed to peak-at-time semantics
  this phase, and aligning the legacy risk metric is a candidate follow-up.
