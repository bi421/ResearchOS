#ifndef QUANT_RESEARCH_RESEARCH_RUNNER_H
#define QUANT_RESEARCH_RESEARCH_RUNNER_H

#include "quant/research/optimization_result.h"
#include "quant/research/optimizer.h"
#include "quant/research/parameter_space.h"
#include "quant/core/result.h"
#include "quant/market/types.h"
#include "quant/strategy/strategy_config.h"

#include <cstdint>
#include <string>
#include <vector>

namespace quant {
namespace research {

// A complete research plan: what to sweep, how, and how to rank.
struct ResearchPlan {
  ParameterSpace space;
  SearchType search_type{SearchType::Grid};
  uint64_t seed{42};
  size_t random_samples{1000};
  OptimizationMetric rank_metric{OptimizationMetric::NetProfit};
  size_t max_parallelism{0};   // 0 -> hardware concurrency
  size_t top_n{0};             // 0 -> retain every evaluated strategy
};

// High-level orchestrator for historical parameter research. Wraps an
// Optimizer (which performs the actual grid/random/seeded sweeps) and adds
// convenience helpers for running a full plan, evaluating a single strategy,
// and producing a human-readable summary. Historical research only: no
// execution, no broker, no live signal generation.
class ResearchRunner {
public:
  explicit ResearchRunner(strategy::StrategyConfig base_config = {});

  void set_base_config(strategy::StrategyConfig config);
  const strategy::StrategyConfig& base_config() const;

  // Runs a research plan and returns the ranked optimization result.
  Result<OptimizationResult> run(
      const ResearchPlan& plan, const std::vector<OHLCV>& bars,
      const SignalStreamGenerator& signal_generator,
      const ConfigProvider* config_provider = nullptr) const;

  // Evaluates a single parameter combo to full detail.
  Result<StrategyEvaluation> evaluate_combo(
      const std::vector<OHLCV>& bars, const ParamSet& params,
      const SignalStreamGenerator& signal_generator,
      const ConfigProvider* config_provider = nullptr) const;

  // Convenience wrappers that build a plan and call `run`.
  Result<OptimizationResult> run_grid(
      const ParameterSpace& space, const std::vector<OHLCV>& bars,
      const SignalStreamGenerator& signal_generator,
      const ConfigProvider* config_provider = nullptr,
      OptimizationMetric rank_metric = OptimizationMetric::NetProfit) const;

  Result<OptimizationResult> run_seeded(
      const ParameterSpace& space, const std::vector<OHLCV>& bars,
      size_t samples, uint64_t seed,
      const SignalStreamGenerator& signal_generator,
      const ConfigProvider* config_provider = nullptr,
      OptimizationMetric rank_metric = OptimizationMetric::NetProfit) const;

  Result<OptimizationResult> run_random(
      const ParameterSpace& space, const std::vector<OHLCV>& bars,
      size_t samples, const SignalStreamGenerator& signal_generator,
      const ConfigProvider* config_provider = nullptr,
      OptimizationMetric rank_metric = OptimizationMetric::NetProfit) const;

private:
  strategy::StrategyConfig base_config_;
};

// Human-readable summary of an optimization result (top strategies + config).
std::string optimization_summary(const OptimizationResult& result,
                                 size_t top = 5);

} // namespace research
} // namespace quant
#endif
