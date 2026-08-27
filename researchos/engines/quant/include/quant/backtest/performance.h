#ifndef QUANT_BACKTEST_PERFORMANCE_H
#define QUANT_BACKTEST_PERFORMANCE_H

#include "backtest_engine.h"
#include "quant/statistics/risk.h"
#include "quant/statistics/descriptive.h"
#include <vector>
#include <string>
#include <cmath>

namespace quant {

struct PerformanceReport {
  double total_return{0.0};
  double total_return_pct{0.0};
  double annualized_return{0.0};
  double annualized_volatility{0.0};
  double sharpe_ratio{0.0};
  double sortino_ratio{0.0};
  double calmar_ratio{0.0};
  double max_drawdown_pct{0.0};
  double max_drawdown_duration{0.0};
  double win_rate{0.0};
  double profit_factor{0.0};
  double avg_win{0.0};
  double avg_loss{0.0};
  double largest_win{0.0};
  double largest_loss{0.0};
  size_t total_trades{0};
  size_t winning_trades{0};
  size_t losing_trades{0};

  // Downside risk metrics (period basis).
  double downside_deviation{0.0};
  double downside_deviation_annualized{0.0};
  double var_95{0.0};
  double var_99{0.0};
  double cvar_95{0.0};
  double cvar_99{0.0};

  // Drawdown recovery / time-in-drawdown stats.
  size_t max_drawdown_recovery_bars{0};
  double time_in_drawdown_pct{0.0};

  static PerformanceReport compute(const BacktestResult& result,
                                     double trading_days_per_year = 252.0);
  std::string summary() const;
};

} // namespace quant
#endif
