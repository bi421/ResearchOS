#ifndef QUANT_STATISTICS_RISK_H
#define QUANT_STATISTICS_RISK_H

#include "quant/core/result.h"
#include <vector>
#include <algorithm>
#include <cmath>
#include <numeric>

namespace quant {

struct VaRResult {
  double var_95{0.0};
  double var_99{0.0};
  double cvar_95{0.0};
  double cvar_99{0.0};
  double historical_var(size_t percentile) const;
};

struct DrawdownInfo {
  double max_drawdown{0.0};
  double max_drawdown_pct{0.0};
  size_t peak_index{0};
  size_t trough_index{0};
  size_t recovery_index{0};
};

struct RiskMetrics {
  static Result<VaRResult> value_at_risk(const std::vector<double>& returns,
                                          double confidence_95 = 0.95,
                                          double confidence_99 = 0.99);

  static Result<DrawdownInfo> max_drawdown(const std::vector<double>& equity_curve);

  static Result<double> sharpe_ratio(const std::vector<double>& returns,
                                      double risk_free_rate = 0.0);

  static Result<double> sortino_ratio(const std::vector<double>& returns,
                                       double risk_free_rate = 0.0,
                                       double target_return = 0.0);

  static Result<double> beta(const std::vector<double>& asset_returns,
                              const std::vector<double>& benchmark_returns);

  static Result<double> alpha(const std::vector<double>& asset_returns,
                               const std::vector<double>& benchmark_returns,
                               double risk_free_rate = 0.0);

  static Result<double> information_ratio(const std::vector<double>& returns,
                                           const std::vector<double>& benchmark_returns);
};

} // namespace quant
#endif
