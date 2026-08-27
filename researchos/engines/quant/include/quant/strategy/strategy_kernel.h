#ifndef QUANT_STRATEGY_STRATEGY_KERNEL_H
#define QUANT_STRATEGY_STRATEGY_KERNEL_H

#include "quant/strategy/strategy_config.h"
#include "quant/strategy/strategy_signal.h"
#include "quant/strategy/simulation_result.h"
#include "quant/market/types.h"
#include "quant/core/result.h"
#include <cstdint>
#include <vector>

namespace quant {
namespace strategy {

// Deterministic strategy simulation kernel.
//
// The kernel is a pure function of (bars, signals, config): identical inputs
// always produce identical trades, equity curve, statistics, and hashes. It
// holds no mutable global state and may run concurrently on independent
// instances (multithread-ready).
//
// Performance model:
//   * bars, signals, positions, and every output live in contiguous
//     std::vector storage (vector-friendly, SIMD-friendly);
//   * the per-bar hot loop performs no heap allocation: the signal queue and
//     open-position store are reserved once and reused, and ATR is
//     precomputed into a contiguous series;
//   * hash computation is opt-out via `compute_hash` for pure-throughput runs.
class StrategyKernel {
public:
  StrategyKernel() = default;
  explicit StrategyKernel(StrategyConfig config);

  void set_config(StrategyConfig config);
  const StrategyConfig& config() const;

  // Runs the full simulation over `bars` and the signal stream `signals`.
  Result<SimulationResult> run(const std::vector<OHLCV>& bars,
                               const std::vector<StrategySignal>& signals,
                               bool compute_hash = true);

private:
  StrategyConfig config_;
};

// Canonical input hash over bars + signals + config (independent of results).
std::string compute_input_hash(const std::vector<OHLCV>& bars,
                               const std::vector<StrategySignal>& signals,
                               const StrategyConfig& config);

} // namespace strategy
} // namespace quant
#endif
