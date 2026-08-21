#include "quant/backtest/performance_analyzer.h"
#include "quant/statistics/descriptive.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>

namespace quant {

namespace {

// Bar-to-bar returns of an equity curve (in fractional form).
std::vector<double> compute_returns(const std::vector<double>& equity) {
  std::vector<double> returns;
  if (equity.size() < 2) return returns;
  returns.reserve(equity.size() - 1);
  for (size_t i = 1; i < equity.size(); ++i) {
    double prev = equity[i - 1];
    if (prev != 0.0) returns.push_back((equity[i] - prev) / prev);
  }
  return returns;
}

struct YearMonth {
  int year{0};
  int month{0};
};

YearMonth year_month_of(const OHLCV& bar) {
  const auto days = std::chrono::floor<std::chrono::days>(bar.timestamp);
  const std::chrono::year_month_day ymd{days};
  return YearMonth{static_cast<int>(ymd.year()),
                   static_cast<int>(static_cast<unsigned>(ymd.month()))};
}

std::vector<PeriodReturn> period_returns_impl(
    const std::vector<double>& equity, const std::vector<OHLCV>& bars,
    bool monthly, double initial_capital) {
  std::vector<PeriodReturn> out;
  const size_t n = std::min(equity.size(), bars.size());
  if (n == 0) return out;

  auto key_matches = [&](YearMonth a, YearMonth b) {
    return a.year == b.year && (!monthly || a.month == b.month);
  };

  YearMonth current = year_month_of(bars[0]);
  size_t group_start = 0;
  double baseline = initial_capital > 0.0 ? initial_capital : equity[0];

  auto flush = [&](size_t last_index, YearMonth key) {
    PeriodReturn pr;
    pr.year = key.year;
    pr.month = monthly ? key.month : 0;
    pr.monthly = monthly;
    pr.bars = last_index - group_start + 1;
    pr.return_pct = baseline != 0.0 ? (equity[last_index] - baseline) / baseline * 100.0 : 0.0;
    out.push_back(pr);
  };

  for (size_t i = 1; i < n; ++i) {
    YearMonth ym = year_month_of(bars[i]);
    if (!key_matches(ym, current)) {
      flush(i - 1, current);
      baseline = equity[i - 1];
      group_start = i;
      current = ym;
    }
  }
  flush(n - 1, current);
  return out;
}

} // namespace

std::vector<DrawdownPeriod> PerformanceAnalyzer::drawdown_periods(
    const std::vector<double>& equity) {
  std::vector<DrawdownPeriod> out;
  if (equity.size() < 2) return out;

  double peak = equity[0];
  size_t peak_index = 0;
  bool in_drawdown = false;
  DrawdownPeriod current;

  for (size_t i = 0; i < equity.size(); ++i) {
    if (equity[i] >= peak) {
      if (in_drawdown) {
        current.end_index = i;
        current.length_bars = i - current.start_index;
        current.recovered = true;
        out.push_back(current);
        in_drawdown = false;
      }
      peak = equity[i];
      peak_index = i;
    } else {
      if (!in_drawdown) {
        current = DrawdownPeriod{};
        current.start_index = peak_index;
        current.peak = peak;
        current.trough = equity[i];
        current.trough_index = i;
        in_drawdown = true;
      } else if (equity[i] < current.trough) {
        current.trough = equity[i];
        current.trough_index = i;
      }
    }
  }

  if (in_drawdown) {
    current.end_index = equity.size();
    current.length_bars = equity.size() - current.start_index;
    current.recovered = false;
    out.push_back(current);
  }

  for (auto& d : out) {
    d.max_drawdown_pct = d.peak != 0.0 ? (d.peak - d.trough) / d.peak * 100.0 : 0.0;
  }
  return out;
}

DownsideMetrics PerformanceAnalyzer::downside_metrics(
    const std::vector<double>& returns, double trading_days_per_year) {
  DownsideMetrics m;
  if (returns.empty()) return m;

  double target = 0.0;
  double sum_sq = 0.0;
  for (double r : returns) {
    if (r < target) {
      const double d = r - target;
      sum_sq += d * d;
    }
  }
  m.downside_deviation =
      std::sqrt(sum_sq / static_cast<double>(returns.size()));
  m.downside_deviation_annualized =
      m.downside_deviation * std::sqrt(trading_days_per_year);

  auto var = RiskMetrics::value_at_risk(returns);
  if (var.is_ok()) {
    m.var_95 = var.value().var_95;
    m.var_99 = var.value().var_99;
    m.cvar_95 = var.value().cvar_95;
    m.cvar_99 = var.value().cvar_99;
  }

  const double mean = DescriptiveStats::mean_of(returns);
  const double variance = DescriptiveStats::variance_of(returns, mean);
  m.annualized_volatility = std::sqrt(variance) * std::sqrt(trading_days_per_year);
  return m;
}

std::vector<PeriodReturn> PerformanceAnalyzer::yearly_returns(
    const std::vector<double>& equity, const std::vector<OHLCV>& bars_used,
    double initial_capital) {
  return period_returns_impl(equity, bars_used, /*monthly=*/false, initial_capital);
}

std::vector<PeriodReturn> PerformanceAnalyzer::monthly_returns(
    const std::vector<double>& equity, const std::vector<OHLCV>& bars_used,
    double initial_capital) {
  return period_returns_impl(equity, bars_used, /*monthly=*/true, initial_capital);
}

DetailedPerformanceReport PerformanceAnalyzer::analyze(
    const BacktestResult& result, double trading_days_per_year) {
  DetailedPerformanceReport rep;
  rep.base = PerformanceReport::compute(result, trading_days_per_year);

  const auto& equity = result.equity_curve;
  rep.returns = compute_returns(equity);
  rep.drawdowns = drawdown_periods(equity);
  rep.downside = downside_metrics(rep.returns, trading_days_per_year);
  rep.yearly_returns = yearly_returns(equity, result.bars_used,
                                      result.config.initial_capital);
  rep.monthly_returns = monthly_returns(equity, result.bars_used,
                                        result.config.initial_capital);

  // Underwater / recovery statistics.
  size_t underwater = 0;
  double running_max = 0.0;
  for (double eq : equity) {
    running_max = std::max(running_max, eq);
    if (eq < running_max) ++underwater;
  }
  size_t max_recovery = 0;
  double sum_recovery = 0.0;
  size_t count_recovered = 0;
  for (const auto& d : rep.drawdowns) {
    const size_t recovery = d.end_index - d.trough_index;
    max_recovery = std::max(max_recovery, recovery);
    if (d.recovered) {
      sum_recovery += recovery;
      ++count_recovered;
    }
  }
  rep.max_drawdown_recovery_bars = max_recovery;
  rep.average_drawdown_recovery_bars =
      count_recovered > 0 ? sum_recovery / static_cast<double>(count_recovered) : 0.0;
  rep.total_underwater_bars = underwater;
  rep.time_in_drawdown_pct =
      !equity.empty() ? static_cast<double>(underwater) / static_cast<double>(equity.size()) * 100.0 : 0.0;

  // Mirror into the flat report.
  rep.base.max_drawdown_recovery_bars = max_recovery;
  rep.base.time_in_drawdown_pct = rep.time_in_drawdown_pct;
  rep.base.downside_deviation = rep.downside.downside_deviation;
  rep.base.downside_deviation_annualized = rep.downside.downside_deviation_annualized;
  rep.base.var_95 = rep.downside.var_95;
  rep.base.var_99 = rep.downside.var_99;
  rep.base.cvar_95 = rep.downside.cvar_95;
  rep.base.cvar_99 = rep.downside.cvar_99;

  return rep;
}

} // namespace quant
