#ifndef QUANT_BACKTEST_PERFORMANCE_ANALYZER_H
#define QUANT_BACKTEST_PERFORMANCE_ANALYZER_H

#include "quant/backtest/performance.h"
#include "quant/statistics/risk.h"
#include <cstddef>
#include <vector>

namespace quant {

// A single drawdown episode: peak -> trough -> recovery.
struct DrawdownPeriod {
  size_t start_index{0};   // index of the running peak
  size_t trough_index{0};  // index of the lowest equity point
  size_t end_index{0};     // recovery index (first index back at/above peak); == equity.size() if unrecovered
  double peak{0.0};
  double trough{0.0};
  double max_drawdown_pct{0.0};  // (peak - trough) / peak * 100
  size_t length_bars{0};         // peak -> recovery bars (or -> end when unrecovered)
  bool recovered{false};
};

// Return over a calendar bucket (yearly or monthly).
struct PeriodReturn {
  int year{0};
  int month{0};          // 0 for yearly buckets, 1..12 for monthly
  double return_pct{0.0};
  size_t bars{0};
  bool monthly{false};
};

struct DownsideMetrics {
  double downside_deviation{0.0};
  double downside_deviation_annualized{0.0};
  double max_drawdown_pct{0.0};
  double average_drawdown_pct{0.0};
  double mean_drawdown_duration_bars{0.0};
  double max_drawdown_duration_bars{0.0};
  double var_95{0.0};
  double var_99{0.0};
  double cvar_95{0.0};
  double cvar_99{0.0};
  double annualized_volatility{0.0};
};

struct DetailedPerformanceReport {
  PerformanceReport base;

  std::vector<double> returns;           // period (bar-to-bar) returns
  std::vector<DrawdownPeriod> drawdowns;
  std::vector<PeriodReturn> yearly_returns;
  std::vector<PeriodReturn> monthly_returns;
  DownsideMetrics downside;

  size_t max_drawdown_recovery_bars{0};
  double average_drawdown_recovery_bars{0.0};
  size_t total_underwater_bars{0};
  double time_in_drawdown_pct{0.0};
};

class PerformanceAnalyzer {
public:
  // Full analysis over a completed backtest result.
  static DetailedPerformanceReport analyze(const BacktestResult& result,
                                           double trading_days_per_year = 252.0);

  // All drawdown episodes of an equity curve.
  static std::vector<DrawdownPeriod> drawdown_periods(
      const std::vector<double>& equity_curve);

  // Downside metrics from a series of periodic returns.
  static DownsideMetrics downside_metrics(const std::vector<double>& returns,
                                          double trading_days_per_year = 252.0);

  // Calendar-bucketed returns. `bars_used` carries the bar timestamps; when it
  // is empty, period returns are empty as well.
  static std::vector<PeriodReturn> yearly_returns(
      const std::vector<double>& equity_curve,
      const std::vector<OHLCV>& bars_used,
      double initial_capital = 0.0);

  static std::vector<PeriodReturn> monthly_returns(
      const std::vector<double>& equity_curve,
      const std::vector<OHLCV>& bars_used,
      double initial_capital = 0.0);
};

} // namespace quant
#endif
