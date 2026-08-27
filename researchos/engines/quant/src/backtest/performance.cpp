#include "quant/backtest/performance.h"
#include <algorithm>
#include <numeric>
#include <cmath>
#include <limits>

namespace quant {

PerformanceReport PerformanceReport::compute(const BacktestResult& result,
                                               double trading_days_per_year) {
  PerformanceReport r;
  r.total_return = result.final_equity - result.config.initial_capital;
  r.total_return_pct = result.total_return_pct;
  r.total_trades = result.trade_book.total_trades();
  r.winning_trades = result.trade_book.winning_trades();
  r.losing_trades = result.trade_book.losing_trades_count();
  r.win_rate = result.win_rate;
  r.profit_factor = result.profit_factor;
  r.max_drawdown_pct = result.max_drawdown_pct;

  if (!result.equity_curve.empty()) {
    std::vector<double> returns;
    returns.reserve(result.equity_curve.size() - 1);
    for (size_t i = 1; i < result.equity_curve.size(); ++i) {
      double prev = result.equity_curve[i - 1];
      if (prev != 0.0)
        returns.push_back((result.equity_curve[i] - prev) / prev);
    }

    // Downside deviation (target = 0), standard: divide by number of returns.
    {
      double sum_sq = 0.0;
      for (double ret : returns) {
        if (ret < 0.0) sum_sq += ret * ret;
      }
      r.downside_deviation =
          std::sqrt(sum_sq / static_cast<double>(returns.size()));
      r.downside_deviation_annualized =
          r.downside_deviation * std::sqrt(trading_days_per_year);
    }

    // Historical VaR / CVaR.
    auto var = RiskMetrics::value_at_risk(returns);
    if (var.is_ok()) {
      r.var_95 = var.value().var_95;
      r.var_99 = var.value().var_99;
      r.cvar_95 = var.value().cvar_95;
      r.cvar_99 = var.value().cvar_99;
    }

    // Time in drawdown + worst-case recovery length.
    {
      size_t underwater = 0;
      size_t worst_recovery = 0;
      size_t peak_idx = 0;
      double peak = result.equity_curve[0];
      for (size_t i = 0; i < result.equity_curve.size(); ++i) {
        const double eq = result.equity_curve[i];
        if (eq >= peak) {
          peak = eq;
          peak_idx = i;
        } else {
          ++underwater;
          worst_recovery = std::max(worst_recovery, i - peak_idx);
        }
      }
      r.time_in_drawdown_pct =
          static_cast<double>(underwater) / static_cast<double>(result.equity_curve.size()) * 100.0;
      r.max_drawdown_recovery_bars = worst_recovery;
    }

    if (!returns.empty()) {
      double mean_ret = DescriptiveStats::mean_of(returns);
      double var = DescriptiveStats::variance_of(returns, mean_ret);
      double stddev = std::sqrt(var);

      double n = static_cast<double>(returns.size());
      r.annualized_return = mean_ret * trading_days_per_year;
      r.annualized_volatility = stddev * std::sqrt(trading_days_per_year);

      auto sr = RiskMetrics::sharpe_ratio(returns);
      if (sr.is_ok()) {
        r.sharpe_ratio = sr.value() * std::sqrt(trading_days_per_year);
      }

      auto sortino = RiskMetrics::sortino_ratio(returns);
      if (sortino.is_ok()) {
        r.sortino_ratio = sortino.value() * std::sqrt(trading_days_per_year);
      }

      if (r.max_drawdown_pct != 0.0)
        r.calmar_ratio = r.annualized_return / (r.max_drawdown_pct / 100.0);
    }
  }

  auto closed = result.trade_book.closed_trades();
  if (!closed.empty()) {
    std::vector<double> pnls;
    pnls.reserve(closed.size());
    for (auto& t : closed) pnls.push_back(t.pnl());
    auto minmax = std::minmax_element(pnls.begin(), pnls.end());
    r.largest_loss = *minmax.first;
    r.largest_win = *minmax.second;

    double win_sum = 0.0, loss_sum = 0.0;
    size_t wins = 0, losses = 0;
    for (auto& t : closed) {
      if (t.is_profitable()) { win_sum += t.pnl(); ++wins; }
      else { loss_sum += std::abs(t.pnl()); ++losses; }
    }
    r.avg_win = wins > 0 ? win_sum / static_cast<double>(wins) : 0.0;
    r.avg_loss = losses > 0 ? loss_sum / static_cast<double>(losses) : 0.0;
    r.profit_factor = loss_sum > 0.0 ? win_sum / loss_sum : (win_sum > 0.0 ? std::numeric_limits<double>::infinity() : 0.0);
    r.win_rate = static_cast<double>(wins) / static_cast<double>(closed.size()) * 100.0;
  }

  return r;
}

std::string PerformanceReport::summary() const {
  return std::format(
      "PerformanceReport:\n"
      "  Total Return: {:.2f} ({:.2f}%)\n"
      "  Annualized Return: {:.2f}%\n"
      "  Annualized Vol: {:.2f}%\n"
      "  Sharpe: {:.4f}\n"
      "  Sortino: {:.4f}\n"
      "  Calmar: {:.4f}\n"
      "  Max DD: {:.2f}%\n"
      "  Win Rate: {:.1f}%\n"
      "  Profit Factor: {:.2f}\n"
      "  Trades: {} ({}W/{}L)\n"
      "  Avg Win: {:.2f}, Avg Loss: {:.2f}\n"
      "  Largest Win: {:.2f}, Largest Loss: {:.2f}\n"
      "  Downside Dev (ann): {:.2f}%\n"
      "  VaR95: {:.4f}, VaR99: {:.4f}\n"
      "  Time in DD: {:.1f}%, Max Recovery: {} bars",
      total_return, total_return_pct,
      annualized_return * 100.0,
      annualized_volatility * 100.0,
      sharpe_ratio, sortino_ratio, calmar_ratio,
      max_drawdown_pct, win_rate, profit_factor,
      total_trades, winning_trades, losing_trades,
      avg_win, avg_loss, largest_win, largest_loss,
      downside_deviation_annualized * 100.0,
      var_95, var_99,
      time_in_drawdown_pct, max_drawdown_recovery_bars);
}

} // namespace quant
