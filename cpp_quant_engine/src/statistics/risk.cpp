#include "quant/statistics/risk.h"
#include "quant/statistics/descriptive.h"

namespace quant {

double VaRResult::historical_var(size_t percentile) const {
  if (percentile == 95) return var_95;
  if (percentile == 99) return var_99;
  return 0.0;
}

Result<VaRResult> RiskMetrics::value_at_risk(const std::vector<double>& returns,
                                              double confidence_95, double confidence_99) {
  if (returns.empty()) return Error(ErrorCode::InsufficientData, "empty returns");
  auto sorted = returns;
  std::sort(sorted.begin(), sorted.end());
  VaRResult result;

  auto compute_var = [&](double conf) -> double {
    size_t idx = static_cast<size_t>((1.0 - conf) * static_cast<double>(sorted.size()));
    idx = std::min(idx, sorted.size() - 1);
    return -sorted[idx];
  };
  auto compute_cvar = [&](double conf) -> double {
    size_t idx = static_cast<size_t>((1.0 - conf) * static_cast<double>(sorted.size()));
    idx = std::min(idx, sorted.size() - 1);
    double sum = 0.0;
    for (size_t i = 0; i <= idx; ++i) sum += sorted[i];
    return -sum / static_cast<double>(idx + 1);
  };

  result.var_95 = compute_var(confidence_95);
  result.var_99 = compute_var(confidence_99);
  result.cvar_95 = compute_cvar(confidence_95);
  result.cvar_99 = compute_cvar(confidence_99);
  return result;
}

Result<DrawdownInfo> RiskMetrics::max_drawdown(const std::vector<double>& equity_curve) {
  if (equity_curve.empty()) return Error(ErrorCode::InsufficientData, "empty equity curve");
  DrawdownInfo dd;
  double peak = equity_curve[0];
  size_t peak_idx = 0;
  double max_dd = 0.0;
  size_t trough_idx = 0;

  for (size_t i = 1; i < equity_curve.size(); ++i) {
    if (equity_curve[i] > peak) {
      peak = equity_curve[i];
      peak_idx = i;
    }
    double drawdown = (peak - equity_curve[i]) / peak;
    if (drawdown > max_dd) {
      max_dd = drawdown;
      trough_idx = i;
      dd.peak_index = peak_idx;
      dd.trough_index = i;
    }
    if (equity_curve[i] >= peak && max_dd > 0.0 && dd.recovery_index == 0) {
      dd.recovery_index = i;
    }
  }
  dd.max_drawdown = peak - equity_curve[trough_idx];
  dd.max_drawdown_pct = max_dd * 100.0;
  return dd;
}

Result<double> RiskMetrics::sharpe_ratio(const std::vector<double>& returns,
                                          double risk_free_rate) {
  if (returns.size() < 2) return Error(ErrorCode::InsufficientData, "need at least 2 returns");
  double mean_ret = DescriptiveStats::mean_of(returns);
  double excess = mean_ret - risk_free_rate;
  double var = DescriptiveStats::variance_of(returns, mean_ret);
  if (var == 0.0) return Error(ErrorCode::DivisionByZero, "zero variance");
  return excess / std::sqrt(var);
}

Result<double> RiskMetrics::sortino_ratio(const std::vector<double>& returns,
                                           double risk_free_rate, double target_return) {
  if (returns.size() < 2) return Error(ErrorCode::InsufficientData, "need at least 2 returns");
  double mean_ret = DescriptiveStats::mean_of(returns);
  double excess = mean_ret - risk_free_rate;
  double downside = 0.0;
  size_t count = 0;
  for (auto r : returns) {
    double diff = r - target_return;
    if (diff < 0.0) { downside += diff * diff; ++count; }
  }
  if (count == 0) return excess / std::sqrt(static_cast<double>(DescriptiveStats::variance_of(returns, mean_ret)));
  double downside_dev = std::sqrt(downside / static_cast<double>(returns.size()));
  if (downside_dev == 0.0) return Error(ErrorCode::DivisionByZero, "zero downside deviation");
  return excess / downside_dev;
}

Result<double> RiskMetrics::beta(const std::vector<double>& asset_returns,
                                  const std::vector<double>& benchmark_returns) {
  if (asset_returns.size() != benchmark_returns.size())
    return Error(ErrorCode::InvalidArgument, "size mismatch");
  if (asset_returns.size() < 2) return Error(ErrorCode::InsufficientData, "need at least 2 points");

  double ma = DescriptiveStats::mean_of(asset_returns);
  double mb = DescriptiveStats::mean_of(benchmark_returns);
  double cov = 0.0, var_b = 0.0;
  for (size_t i = 0; i < asset_returns.size(); ++i) {
    double da = asset_returns[i] - ma;
    double db = benchmark_returns[i] - mb;
    cov += da * db;
    var_b += db * db;
  }
  if (var_b == 0.0) return Error(ErrorCode::DivisionByZero, "zero benchmark variance");
  return cov / var_b;
}

Result<double> RiskMetrics::alpha(const std::vector<double>& asset_returns,
                                   const std::vector<double>& benchmark_returns,
                                   double risk_free_rate) {
  auto b = beta(asset_returns, benchmark_returns);
  if (b.is_err()) return b.error();
  double ma = DescriptiveStats::mean_of(asset_returns);
  double mb = DescriptiveStats::mean_of(benchmark_returns);
  return ma - risk_free_rate - b.value() * (mb - risk_free_rate);
}

Result<double> RiskMetrics::information_ratio(const std::vector<double>& returns,
                                               const std::vector<double>& benchmark_returns) {
  if (returns.size() != benchmark_returns.size())
    return Error(ErrorCode::InvalidArgument, "size mismatch");
  if (returns.empty()) return Error(ErrorCode::InsufficientData, "empty data");

  std::vector<double> diff(returns.size());
  for (size_t i = 0; i < returns.size(); ++i) diff[i] = returns[i] - benchmark_returns[i];
  double excess_mean = DescriptiveStats::mean_of(diff);
  double tracking_error = std::sqrt(static_cast<double>(DescriptiveStats::variance_of(diff, excess_mean)));
  if (tracking_error == 0.0) return Error(ErrorCode::DivisionByZero, "zero tracking error");
  return excess_mean / tracking_error;
}

} // namespace quant
