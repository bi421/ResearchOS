#ifndef QUANT_RESEARCH_OPTIMIZATION_RESULT_H
#define QUANT_RESEARCH_OPTIMIZATION_RESULT_H

#include "quant/research/parameter_space.h"
#include "quant/strategy/simulation_result.h"
#include "quant/strategy/strategy_config.h"

#include <cstdint>
#include <string>
#include <vector>

namespace quant {
namespace research {

enum class SearchType : uint8_t {
  Grid = 0,   // full cartesian product
  Random,     // uniform random sample (seed drawn non-deterministically)
  Seeded,     // uniform random sample from a caller-provided seed
};

inline const char* search_type_name(SearchType t) {
  switch (t) {
    case SearchType::Grid: return "grid";
    case SearchType::Random: return "random";
    case SearchType::Seeded: return "seeded";
  }
  return "unknown";
}

// The research ranking metric. Ranking is descending for every metric except
// MaxDrawdown (lower drawdown ranks first).
enum class OptimizationMetric : uint8_t {
  NetProfit = 0,
  Sharpe,
  Sortino,
  Calmar,
  MaxDrawdown,
  ProfitFactor,
  WinRate,
  Expectancy,
  RecoveryFactor,
  TradeCount,
  Stability,
};

inline const char* optimization_metric_name(OptimizationMetric m) {
  switch (m) {
    case OptimizationMetric::NetProfit: return "net_profit";
    case OptimizationMetric::Sharpe: return "sharpe";
    case OptimizationMetric::Sortino: return "sortino";
    case OptimizationMetric::Calmar: return "calmar";
    case OptimizationMetric::MaxDrawdown: return "max_drawdown";
    case OptimizationMetric::ProfitFactor: return "profit_factor";
    case OptimizationMetric::WinRate: return "win_rate";
    case OptimizationMetric::Expectancy: return "expectancy";
    case OptimizationMetric::RecoveryFactor: return "recovery_factor";
    case OptimizationMetric::TradeCount: return "trade_count";
    case OptimizationMetric::Stability: return "stability";
  }
  return "unknown";
}

// The research metric set evaluated for every strategy.
struct OptimizationMetrics {
  double net_profit{0.0};
  double sharpe{0.0};
  double sortino{0.0};
  double calmar{0.0};
  double max_drawdown{0.0};
  double max_drawdown_pct{0.0};
  double profit_factor{0.0};
  double win_rate{0.0};
  double expectancy{0.0};
  double recovery_factor{0.0};
  double stability{0.0};   // R^2 of a linear fit over the equity curve, x100
  double total_return_pct{0.0};
  double annualized_return{0.0};
  size_t trade_count{0};
};

// Computes the research metrics from kernel statistics and the equity curve.
// `stability` is the coefficient of determination of a least-squares line fit
// through the per-bar equity curve, scaled to [0, 100] (100 = perfectly
// consistent growth, 0 = no linear trend fit). Defined in src/research/optimizer.cpp.
OptimizationMetrics compute_optimization_metrics(
    const strategy::StrategyStats& stats,
    const std::vector<double>& equity_curve);

// Full evaluation of a single parameter combo (lightweight sweep record plus,
// for ranked strategies, the complete SimulationResult).
struct StrategyEvaluation {
  size_t combo_index{0};        // index within the parameter space (0 for
                                // standalone evaluate_combo calls)
  ParamSet params;              // the parameter values used
  strategy::StrategyStats stats;          // kernel statistics
  OptimizationMetrics metrics;  // research metrics
  strategy::SimulationResult simulation;  // full kernel result (equity curve, trades, hashes)
  size_t signals_processed{0};
  double final_equity{0.0};
};

// A strategy placed in the final ranking.
struct RankedStrategy {
  StrategyEvaluation evaluation;
  size_t rank{0};         // 1-based rank within the returned list
  double rank_value{0.0}; // the metric value used for ranking
};

// Result of an optimization sweep: strategies ranked by `rank_metric`.
struct OptimizationResult {
  std::vector<RankedStrategy> ranked;       // best-first
  size_t requested{0};                      // combos the search asked to evaluate
  size_t evaluated{0};                      // combos that produced a result
  size_t failed{0};                         // combos that errored and were skipped
  SearchType search_type{SearchType::Grid};
  uint64_t seed{0};                         // seed actually used (Random records its draw)
  OptimizationMetric rank_metric{OptimizationMetric::NetProfit};
  std::vector<std::string> parameter_names; // parameter order of the space

  bool empty() const { return ranked.empty(); }

  // Highest-ranked strategy, or nullptr when nothing was evaluated.
  const RankedStrategy* best() const {
    return ranked.empty() ? nullptr : &ranked.front();
  }

  // Deterministic canonical hash over the ranked result (search params,
  // combo indices, parameter values and key metrics). Two identical inputs
  // always produce the identical hash.
  std::string compute_result_hash() const;
};

} // namespace research
} // namespace quant
#endif
