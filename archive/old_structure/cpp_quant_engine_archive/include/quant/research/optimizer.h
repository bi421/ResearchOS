#ifndef QUANT_RESEARCH_OPTIMIZER_H
#define QUANT_RESEARCH_OPTIMIZER_H

#include "quant/research/optimization_result.h"
#include "quant/research/parameter_space.h"
#include "quant/core/result.h"
#include "quant/market/types.h"
#include "quant/strategy/strategy_config.h"
#include "quant/strategy/strategy_signal.h"

#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace quant {
namespace research {

// Signal stream generator interface: turns the historical candles and a
// concrete parameter combo into the StrategySignal stream consumed by the
// StrategyKernel. Implementations must be deterministic and thread-safe
// (const, no shared mutable state).
class SignalStreamGenerator {
public:
  virtual ~SignalStreamGenerator() = default;
  virtual std::vector<strategy::StrategySignal> generate(
      const std::vector<OHLCV>& bars, const ParamSet& params) const = 0;
};

// Adapts a std::function into the SignalStreamGenerator interface.
class FunctionSignalGenerator final : public SignalStreamGenerator {
public:
  using Fn = std::function<std::vector<strategy::StrategySignal>(
      const std::vector<OHLCV>&, const ParamSet&)>;

  explicit FunctionSignalGenerator(Fn fn) : fn_(std::move(fn)) {}

  std::vector<strategy::StrategySignal> generate(
      const std::vector<OHLCV>& bars, const ParamSet& params) const override {
    return fn_(bars, params);
  }

private:
  Fn fn_;
};

// Strategy-config provider: derives the full StrategyConfig for a parameter
// combo (e.g. mapping `stop`/`tp` parameters onto TradeConfig). Must be
// deterministic and thread-safe. A null provider means "use the base config".
class ConfigProvider {
public:
  virtual ~ConfigProvider() = default;
  virtual strategy::StrategyConfig provide(const ParamSet& params) const = 0;
};

// Adapts a std::function into the ConfigProvider interface.
class FunctionConfigProvider final : public ConfigProvider {
public:
  using Fn = std::function<strategy::StrategyConfig(const ParamSet&)>;

  explicit FunctionConfigProvider(Fn fn) : fn_(std::move(fn)) {}

  strategy::StrategyConfig provide(const ParamSet& params) const override {
    return fn_(params);
  }

private:
  Fn fn_;
};

// Tuning knobs for an optimization sweep.
struct OptimizerConfig {
  SearchType search_type{SearchType::Grid};
  uint64_t seed{42};           // used by Seeded search (and recorded on Random)
  size_t random_samples{1000}; // number of combos sampled by Random/Seeded
  OptimizationMetric rank_metric{OptimizationMetric::NetProfit};
  size_t max_parallelism{0};   // 0 -> std::thread::hardware_concurrency()
  size_t top_n{0};             // 0 -> retain every evaluated strategy
};

// Returns +1 when larger metric values rank first, -1 when smaller rank first
// (only MaxDrawdown). Used to sort ranked results.
int rank_direction(OptimizationMetric metric);

// Deterministic parameter sweep engine.
//
// Thread safety: `optimize()` is const and holds no mutable state, so a single
// Optimizer instance may be used concurrently from multiple threads. Within one
// `optimize()` call evaluations are spread across `max_parallelism` threads; the
// results are stored by combo index and ranked deterministically, so a run is
// byte-for-byte reproducible regardless of thread scheduling.
class Optimizer {
public:
  Optimizer() = default;
  explicit Optimizer(strategy::StrategyConfig base_config);
  Optimizer(strategy::StrategyConfig base_config, OptimizerConfig config);

  void set_base_config(strategy::StrategyConfig config);
  const strategy::StrategyConfig& base_config() const;
  void set_config(OptimizerConfig config);
  const OptimizerConfig& config() const;

  // Runs the sweep. `config_provider` may be null (base config is used).
  Result<OptimizationResult> optimize(
      const std::vector<OHLCV>& bars, const ParameterSpace& space,
      const SignalStreamGenerator& signal_generator,
      const ConfigProvider* config_provider = nullptr) const;

  // Evaluates one parameter combo to full detail (single-strategy research).
  Result<StrategyEvaluation> evaluate_combo(
      const std::vector<OHLCV>& bars, const ParamSet& params,
      const SignalStreamGenerator& signal_generator,
      const ConfigProvider* config_provider = nullptr) const;

private:
  strategy::StrategyConfig base_config_;
  OptimizerConfig config_;
};

} // namespace research
} // namespace quant
#endif
