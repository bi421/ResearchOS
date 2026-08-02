#include "quant/research/optimizer.h"

#include "quant/strategy/strategy_kernel.h"

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdio>
#include <limits>
#include <random>
#include <thread>
#include <unordered_set>
#include <utility>

namespace quant {
namespace research {

namespace {

constexpr double kFitEps = 1e-9;

// Coefficient of determination (R^2) of a least-squares line through the
// per-bar equity curve, scaled to [0, 100]. 100 = perfectly consistent
// growth (or flat equity), 0 = no linear trend fit.
double stability_score(const std::vector<double>& equity) {
  const size_t n = equity.size();
  if (n < 2) return 0.0;
  double sum_x = 0.0, sum_y = 0.0, sum_xx = 0.0, sum_xy = 0.0;
  for (size_t i = 0; i < n; ++i) {
    const double x = static_cast<double>(i);
    sum_x += x;
    sum_y += equity[i];
    sum_xx += x * x;
    sum_xy += x * equity[i];
  }
  const double denom = n * sum_xx - sum_x * sum_x;
  double slope = 0.0, intercept = 0.0;
  if (std::abs(denom) > kFitEps) {
    slope = (n * sum_xy - sum_x * sum_y) / denom;
    intercept = (sum_y - slope * sum_x) / static_cast<double>(n);
  }
  double ss_res = 0.0, ss_tot = 0.0;
  const double mean_y = sum_y / static_cast<double>(n);
  for (size_t i = 0; i < n; ++i) {
    const double pred = intercept + slope * static_cast<double>(i);
    const double d = equity[i] - pred;
    ss_res += d * d;
    const double t = equity[i] - mean_y;
    ss_tot += t * t;
  }
  if (ss_tot <= kFitEps) return 100.0; // flat equity: perfectly stable
  double r2 = 1.0 - ss_res / ss_tot;
  r2 = std::max(0.0, std::min(1.0, r2));
  return r2 * 100.0;
}

std::string fnv1a64_hex(const std::string& input) {
  uint64_t h = 14695981039346656037ull;
  for (unsigned char c : input) {
    h ^= c;
    h *= 1099511628211ull;
  }
  char buf[24];
  std::snprintf(buf, sizeof(buf), "%016llx", static_cast<unsigned long long>(h));
  return std::string(buf);
}

std::string canonical_metric(double v) {
  if (std::isnan(v)) return "nan";
  if (std::isinf(v)) return v > 0.0 ? "inf" : "-inf";
  char buf[40];
  std::snprintf(buf, sizeof(buf), "%.6g", v);
  return std::string(buf);
}

// Validation shared by every evaluation path.
Result<void> validate_bars(const std::vector<OHLCV>& bars) {
  if (bars.empty())
    return Error(ErrorCode::InsufficientData,
                 "research requires at least one bar");
  for (size_t i = 0; i < bars.size(); ++i) {
    if (!bars[i].is_valid())
      return Error(ErrorCode::InvalidArgument,
                   "invalid OHLC bar at index " + std::to_string(i));
    if (i > 0 && bars[i].timestamp < bars[i - 1].timestamp)
      return Error(ErrorCode::InvalidArgument,
                   "bar timestamps must be non-decreasing");
  }
  return Result<void>::ok();
}

} // namespace

// ── metrics ─────────────────────────────────────────────────────────────────

OptimizationMetrics compute_optimization_metrics(const strategy::StrategyStats& s,
                                                 const std::vector<double>& eq) {
  OptimizationMetrics m;
  m.net_profit = s.net_profit;
  m.sharpe = s.sharpe;
  m.sortino = s.sortino;
  m.calmar = s.calmar;
  m.max_drawdown = s.max_drawdown;
  m.max_drawdown_pct = s.max_drawdown_pct;
  m.profit_factor = s.profit_factor;
  m.win_rate = s.win_rate;
  m.expectancy = s.expectancy;
  m.recovery_factor = s.recovery_factor;
  m.stability = stability_score(eq);
  m.total_return_pct = s.total_return_pct;
  m.annualized_return = s.annualized_return;
  m.trade_count = s.total_trades;
  return m;
}

int rank_direction(OptimizationMetric metric) {
  return metric == OptimizationMetric::MaxDrawdown ? -1 : 1;
}

namespace {

double rank_value(const OptimizationMetrics& m, OptimizationMetric metric) {
  switch (metric) {
    case OptimizationMetric::NetProfit: return m.net_profit;
    case OptimizationMetric::Sharpe: return m.sharpe;
    case OptimizationMetric::Sortino: return m.sortino;
    case OptimizationMetric::Calmar: return m.calmar;
    case OptimizationMetric::MaxDrawdown: return m.max_drawdown;
    case OptimizationMetric::ProfitFactor: return m.profit_factor;
    case OptimizationMetric::WinRate: return m.win_rate;
    case OptimizationMetric::Expectancy: return m.expectancy;
    case OptimizationMetric::RecoveryFactor: return m.recovery_factor;
    case OptimizationMetric::TradeCount:
      return static_cast<double>(m.trade_count);
    case OptimizationMetric::Stability: return m.stability;
  }
  return 0.0;
}

// Lightweight per-combo evaluation record (no full SimulationResult kept so a
// large sweep stays memory-bounded).
struct EvalRecord {
  size_t combo_index{0};
  ParamSet params;
  strategy::StrategyStats stats;
  OptimizationMetrics metrics;
  size_t signals_processed{0};
  double final_equity{0.0};
  bool ok{false};
  std::string error;
};

// Builds the list of combo indices for the search type.
std::vector<size_t> combo_indices(const ParameterSpace& space,
                                  const OptimizerConfig& cfg, size_t total,
                                  uint64_t& used_seed) {
  std::vector<size_t> idx;
  if (cfg.search_type == SearchType::Grid) {
    idx.reserve(total);
    for (size_t i = 0; i < total; ++i) idx.push_back(i);
    used_seed = 0;
    return idx;
  }

  uint64_t seed = cfg.seed;
  if (cfg.search_type == SearchType::Random) {
    std::random_device rd;
    seed = (static_cast<uint64_t>(rd()) << 32) ^ static_cast<uint64_t>(rd());
    seed ^= (seed == 0 ? 1 : 0);
  }
  used_seed = seed;

  const size_t want = std::min(cfg.random_samples, total);
  if (want >= total) {
    idx.reserve(total);
    for (size_t i = 0; i < total; ++i) idx.push_back(i);
    return idx;
  }

  idx.reserve(want);
  std::mt19937_64 rng(seed);
  std::uniform_int_distribution<size_t> dist(0, total - 1);
  std::unordered_set<size_t> seen;
  seen.reserve(want * 2);
  const size_t max_tries = want * 8 + 1024;
  size_t tries = 0;
  while (seen.size() < want && tries++ < max_tries) {
    const size_t v = dist(rng);
    if (seen.insert(v).second) idx.push_back(v);
  }
  // Guarantee the requested count even in pathological small spaces.
  for (size_t i = 0; i < total && idx.size() < want; ++i) {
    if (seen.insert(i).second) idx.push_back(i);
  }
  return idx;
}

} // namespace

// ── Optimizer ───────────────────────────────────────────────────────────────

Optimizer::Optimizer(strategy::StrategyConfig base_config)
    : base_config_(std::move(base_config)) {}

Optimizer::Optimizer(strategy::StrategyConfig base_config, OptimizerConfig config)
    : base_config_(std::move(base_config)), config_(std::move(config)) {}

void Optimizer::set_base_config(strategy::StrategyConfig config) {
  base_config_ = std::move(config);
}

const strategy::StrategyConfig& Optimizer::base_config() const { return base_config_; }

void Optimizer::set_config(OptimizerConfig config) { config_ = std::move(config); }

const OptimizerConfig& Optimizer::config() const { return config_; }

Result<StrategyEvaluation> Optimizer::evaluate_combo(
    const std::vector<OHLCV>& bars, const ParamSet& params,
    const SignalStreamGenerator& signal_generator,
    const ConfigProvider* config_provider) const {
  if (auto err = validate_bars(bars); err.is_err()) return err.error();

  strategy::StrategyConfig cfg =
      config_provider ? config_provider->provide(params) : base_config_;
  std::vector<strategy::StrategySignal> signals = signal_generator.generate(bars, params);
  strategy::StrategyKernel kernel(cfg);
  auto res = kernel.run(bars, signals, /*compute_hash=*/true);
  if (res.is_err()) return res.error();

  StrategyEvaluation ev;
  ev.params = params;
  ev.simulation = std::move(res).value();
  ev.stats = ev.simulation.stats;
  ev.metrics =
      compute_optimization_metrics(ev.stats, ev.simulation.equity_curve);
  ev.signals_processed = ev.simulation.signals_processed;
  ev.final_equity = ev.simulation.final_equity;
  return ev;
}

Result<OptimizationResult> Optimizer::optimize(
    const std::vector<OHLCV>& bars, const ParameterSpace& space,
    const SignalStreamGenerator& signal_generator,
    const ConfigProvider* config_provider) const {
  if (auto err = validate_bars(bars); err.is_err()) return err.error();
  if (space.empty())
    return Error(ErrorCode::InvalidArgument, "parameter space is empty");
  const size_t total = space.combo_count();
  if (total == 0)
    return Error(ErrorCode::InvalidArgument,
                 "parameter space has zero combinations (empty parameter grid)");
  if (total == std::numeric_limits<size_t>::max())
    return Error(ErrorCode::NumericOverflow,
                 "parameter space combination count overflows size_t");

  uint64_t used_seed = 0;
  std::vector<size_t> indices =
      combo_indices(space, config_, total, used_seed);
  if (indices.empty()) {
    // Zero requested samples: a valid empty run.
    OptimizationResult result;
    result.search_type = config_.search_type;
    result.seed = used_seed;
    result.rank_metric = config_.rank_metric;
    result.parameter_names = space.names();
    return result;
  }

  std::vector<EvalRecord> records(indices.size());
  std::atomic<size_t> next{0};

  auto evaluate_one = [&](size_t slot) {
    EvalRecord& rec = records[slot];
    const size_t combo = indices[slot];
    const ParamSet params = space.combo(combo);
    strategy::StrategyConfig cfg =
        config_provider ? config_provider->provide(params) : base_config_;
    std::vector<strategy::StrategySignal> signals =
        signal_generator.generate(bars, params);
    strategy::StrategyKernel kernel(cfg);
    auto res = kernel.run(bars, signals, /*compute_hash=*/false);
    if (res.is_err()) {
      rec.combo_index = combo;
      rec.params = params;
      rec.error = res.error().message();
      return;
    }
    auto&& sim = std::move(res).value();
    rec.combo_index = combo;
    rec.params = std::move(params);
    rec.stats = sim.stats;
    rec.metrics = compute_optimization_metrics(sim.stats, sim.equity_curve);
    rec.signals_processed = sim.signals_processed;
    rec.final_equity = sim.final_equity;
    rec.ok = true;
  };

  size_t threads = config_.max_parallelism;
  if (threads == 0) {
    threads = std::thread::hardware_concurrency();
    if (threads == 0) threads = 1;
  }
  threads = std::max<size_t>(1, std::min(threads, indices.size()));

  {
    std::vector<std::thread> pool;
    auto worker = [&]() {
      for (;;) {
        const size_t slot = next.fetch_add(1);
        if (slot >= indices.size()) break;
        evaluate_one(slot);
      }
    };
    if (threads > 1) {
      pool.reserve(threads - 1);
      for (size_t t = 1; t < threads; ++t) pool.emplace_back(worker);
    }
    worker(); // the calling thread participates
    for (auto& t : pool) t.join();
  }

  // Deterministic ranking: rank metric (direction-aware), tie-broken by
  // ascending combo index.
  std::vector<size_t> order;
  order.reserve(records.size());
  for (size_t i = 0; i < records.size(); ++i) {
    if (records[i].ok) order.push_back(i);
  }
  const int dir = rank_direction(config_.rank_metric);
  std::stable_sort(order.begin(), order.end(), [&](size_t a, size_t b) {
    const double va = rank_value(records[a].metrics, config_.rank_metric);
    const double vb = rank_value(records[b].metrics, config_.rank_metric);
    if (va != vb) return dir > 0 ? va > vb : va < vb;
    return records[a].combo_index < records[b].combo_index;
  });

  const size_t retain =
      config_.top_n == 0 ? order.size() : std::min(config_.top_n, order.size());

  OptimizationResult result;
  result.requested = indices.size();
  result.evaluated = order.size();
  result.failed = records.size() - order.size();
  result.search_type = config_.search_type;
  result.seed = used_seed;
  result.rank_metric = config_.rank_metric;
  result.parameter_names = space.names();
  result.ranked.reserve(retain);

  // Re-evaluate the retained subset to full detail (equity curve, trades,
  // hashes). The re-run is deterministic and cheap for a bounded `top_n`.
  for (size_t k = 0; k < retain; ++k) {
    const EvalRecord& rec = records[order[k]];
    RankedStrategy rs;
    auto full =
        evaluate_combo(bars, rec.params, signal_generator, config_provider);
    if (full.is_ok()) {
      rs.evaluation = std::move(full).value();
      rs.evaluation.combo_index = rec.combo_index;
    } else {
      StrategyEvaluation ev;
      ev.combo_index = rec.combo_index;
      ev.params = rec.params;
      ev.stats = rec.stats;
      ev.metrics = rec.metrics;
      ev.signals_processed = rec.signals_processed;
      ev.final_equity = rec.final_equity;
      rs.evaluation = std::move(ev);
    }
    rs.rank = k + 1;
    rs.rank_value = rank_value(rec.metrics, config_.rank_metric);
    result.ranked.push_back(std::move(rs));
  }

  return result;
}

// ── hash ────────────────────────────────────────────────────────────────────

std::string OptimizationResult::compute_result_hash() const {
  std::string canon;
  canon += std::to_string(seed);
  canon += ";";
  canon += optimization_metric_name(rank_metric);
  canon += ";";
  canon += std::to_string(requested);
  canon += ";";
  canon += std::to_string(evaluated);
  canon += ";";
  canon += std::to_string(failed);
  canon += ";";
  for (const RankedStrategy& rs : ranked) {
    canon += std::to_string(rs.evaluation.combo_index);
    canon += "=";
    canon += rs.evaluation.params.to_string();
    canon += "|";
    canon += canonical_metric(rs.rank_value);
    canon += ",";
    canon += canonical_metric(rs.evaluation.metrics.net_profit);
    canon += ",";
    canon += canonical_metric(rs.evaluation.metrics.sharpe);
    canon += ",";
    canon += canonical_metric(rs.evaluation.metrics.max_drawdown);
    canon += ",";
    canon += canonical_metric(rs.evaluation.metrics.stability);
    canon += ",";
    canon += canonical_metric(rs.evaluation.final_equity);
    canon += ";";
  }
  return fnv1a64_hex(canon);
}

} // namespace research
} // namespace quant
