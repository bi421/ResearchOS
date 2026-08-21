#include "quant/research/research_runner.h"

#include <algorithm>
#include <cstdio>
#include <string>
#include <utility>

namespace quant {
namespace research {

namespace {

OptimizerConfig plan_to_config(const ResearchPlan& plan) {
  OptimizerConfig cfg;
  cfg.search_type = plan.search_type;
  cfg.seed = plan.seed;
  cfg.random_samples = plan.random_samples;
  cfg.rank_metric = plan.rank_metric;
  cfg.max_parallelism = plan.max_parallelism;
  cfg.top_n = plan.top_n;
  return cfg;
}

} // namespace

ResearchRunner::ResearchRunner(strategy::StrategyConfig base_config)
    : base_config_(std::move(base_config)) {}

void ResearchRunner::set_base_config(strategy::StrategyConfig config) {
  base_config_ = std::move(config);
}

const strategy::StrategyConfig& ResearchRunner::base_config() const {
  return base_config_;
}

Result<OptimizationResult> ResearchRunner::run(
    const ResearchPlan& plan, const std::vector<OHLCV>& bars,
    const SignalStreamGenerator& signal_generator,
    const ConfigProvider* config_provider) const {
  Optimizer optimizer(base_config_, plan_to_config(plan));
  return optimizer.optimize(bars, plan.space, signal_generator, config_provider);
}

Result<StrategyEvaluation> ResearchRunner::evaluate_combo(
    const std::vector<OHLCV>& bars, const ParamSet& params,
    const SignalStreamGenerator& signal_generator,
    const ConfigProvider* config_provider) const {
  Optimizer optimizer(base_config_);
  return optimizer.evaluate_combo(bars, params, signal_generator, config_provider);
}

Result<OptimizationResult> ResearchRunner::run_grid(
    const ParameterSpace& space, const std::vector<OHLCV>& bars,
    const SignalStreamGenerator& signal_generator,
    const ConfigProvider* config_provider, OptimizationMetric rank_metric) const {
  ResearchPlan plan;
  plan.space = space;
  plan.search_type = SearchType::Grid;
  plan.rank_metric = rank_metric;
  return run(plan, bars, signal_generator, config_provider);
}

Result<OptimizationResult> ResearchRunner::run_seeded(
    const ParameterSpace& space, const std::vector<OHLCV>& bars, size_t samples,
    uint64_t seed, const SignalStreamGenerator& signal_generator,
    const ConfigProvider* config_provider, OptimizationMetric rank_metric) const {
  ResearchPlan plan;
  plan.space = space;
  plan.search_type = SearchType::Seeded;
  plan.random_samples = samples;
  plan.seed = seed;
  plan.rank_metric = rank_metric;
  return run(plan, bars, signal_generator, config_provider);
}

Result<OptimizationResult> ResearchRunner::run_random(
    const ParameterSpace& space, const std::vector<OHLCV>& bars, size_t samples,
    const SignalStreamGenerator& signal_generator,
    const ConfigProvider* config_provider, OptimizationMetric rank_metric) const {
  ResearchPlan plan;
  plan.space = space;
  plan.search_type = SearchType::Random;
  plan.random_samples = samples;
  plan.rank_metric = rank_metric;
  return run(plan, bars, signal_generator, config_provider);
}

std::string optimization_summary(const OptimizationResult& result, size_t top) {
  std::string out;
  out += "optimization summary: search=";
  out += search_type_name(result.search_type);
  out += " seed=";
  out += std::to_string(result.seed);
  out += " metric=";
  out += optimization_metric_name(result.rank_metric);
  out += " requested=";
  out += std::to_string(result.requested);
  out += " evaluated=";
  out += std::to_string(result.evaluated);
  out += " failed=";
  out += std::to_string(result.failed);
  out += "\n";
  const size_t n = std::min(top, result.ranked.size());
  for (size_t i = 0; i < n; ++i) {
    const RankedStrategy& rs = result.ranked[i];
    char buf[512];
    std::snprintf(buf, sizeof(buf),
                  "rank=%zu params={%s} net_profit=%.4f sharpe=%.4f "
                  "max_dd=%.4f pf=%.4f win_rate=%.4f stability=%.4f "
                  "trades=%zu\n",
                  rs.rank, rs.evaluation.params.to_string().c_str(),
                  rs.evaluation.metrics.net_profit, rs.evaluation.metrics.sharpe,
                  rs.evaluation.metrics.max_drawdown,
                  rs.evaluation.metrics.profit_factor,
                  rs.evaluation.metrics.win_rate,
                  rs.evaluation.metrics.stability,
                  rs.evaluation.metrics.trade_count);
    out += buf;
  }
  return out;
}

} // namespace research
} // namespace quant
