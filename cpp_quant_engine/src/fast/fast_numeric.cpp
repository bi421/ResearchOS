#include "quant/fast/fast_numeric.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <stdexcept>
#include <string>

namespace quant::fast {
namespace {

double percentile_sorted(const std::vector<double>& sorted, double q) {
  if (sorted.empty()) return 0.0;
  const double pos = q * static_cast<double>(sorted.size() - 1);
  const auto lo = static_cast<std::size_t>(std::floor(pos));
  const auto hi = static_cast<std::size_t>(std::ceil(pos));
  if (lo == hi) return sorted[lo];
  const double w = pos - static_cast<double>(lo);
  return sorted[lo] * (1.0 - w) + sorted[hi] * w;
}

}  // namespace

std::vector<double> simple_returns(const std::vector<double>& close) {
  if (close.size() < 2) return {};
  std::vector<double> out(close.size() - 1);
  for (std::size_t i = 1; i < close.size(); ++i) {
    const double prev = close[i - 1];
    out[i - 1] = prev == 0.0 ? 0.0 : (close[i] / prev) - 1.0;
  }
  return out;
}

std::vector<double> drawdown_pct(const std::vector<double>& equity) {
  std::vector<double> out(equity.size(), 0.0);
  double peak = -std::numeric_limits<double>::infinity();
  for (std::size_t i = 0; i < equity.size(); ++i) {
    peak = std::max(peak, equity[i]);
    out[i] = peak > 0.0 ? (peak - equity[i]) / peak * 100.0 : 0.0;
  }
  return out;
}

BacktestOutput backtest_next_open(const std::vector<double>& open,
                                  const std::vector<double>& close,
                                  const std::vector<int>& signal,
                                  const std::vector<double>& quantity,
                                  double initial_capital,
                                  double commission_pct,
                                  double slippage_pct,
                                  bool allow_short) {
  if (open.size() != close.size() || open.size() != signal.size() ||
      open.size() != quantity.size()) {
    throw std::invalid_argument("open, close, signal and quantity must have equal length");
  }
  if (!(initial_capital > 0.0) || commission_pct < 0.0 || slippage_pct < 0.0) {
    throw std::invalid_argument("invalid backtest configuration");
  }

  double cash = initial_capital;
  double position = 0.0;
  double entry_price = 0.0;
  std::size_t trades = 0;
  std::size_t wins = 0;
  double peak = initial_capital;
  double max_dd = 0.0;

  // Signal at i-1 is executed at i's open. No Python callback occurs in this loop.
  for (std::size_t i = 1; i < open.size(); ++i) {
    const int s = signal[i - 1];
    const double requested_qty = std::max(0.0, quantity[i - 1]);
    if (s == 0 || requested_qty == 0.0) continue;

    const double px = open[i];
    if (!(px > 0.0)) continue;

    if (s > 0) {
      if (position < 0.0) {
        const double close_qty = std::min(requested_qty, -position);
        const double exit_px = px + px * slippage_pct;
        const double pnl = (entry_price - exit_px) * close_qty;
        const double commission = close_qty * exit_px * commission_pct;
        cash -= pnl + commission;
        ++trades;
        if (pnl - commission > 0.0) ++wins;
        position += close_qty;
        if (position == 0.0) entry_price = 0.0;
        const double residual = requested_qty - close_qty;
        if (residual > 0.0) {
          const double entry_px = px + px * slippage_pct;
          const double cost = residual * entry_px;
          const double commission_in = cost * commission_pct;
          if (cash >= cost + commission_in) {
            cash -= cost + commission_in;
            position = residual;
            entry_price = entry_px;
          }
        }
      } else {
        const double entry_px = px + px * slippage_pct;
        const double cost = requested_qty * entry_px;
        const double commission = cost * commission_pct;
        if (cash >= cost + commission) {
          cash -= cost + commission;
          position += requested_qty;
          entry_price = entry_px;
        }
      }
    } else {
      if (position > 0.0) {
        const double close_qty = std::min(requested_qty, position);
        const double exit_px = px - px * slippage_pct;
        const double pnl = (exit_px - entry_price) * close_qty;
        const double commission = close_qty * exit_px * commission_pct;
        cash += pnl + close_qty * entry_price - close_qty * entry_price - commission;
        // Equivalent to adding realized PnL; explicit terms keep the cash-flow model auditable.
        ++trades;
        if (pnl - commission > 0.0) ++wins;
        position -= close_qty;
        if (position == 0.0) entry_price = 0.0;
        const double residual = requested_qty - close_qty;
        if (residual > 0.0 && position == 0.0 && allow_short) {
          const double entry_px = px - px * slippage_pct;
          const double proceeds = residual * entry_px;
          const double commission_in = proceeds * commission_pct;
          cash += proceeds - commission_in;
          position = -residual;
          entry_price = entry_px;
        }
      } else if (allow_short) {
        const double entry_px = px - px * slippage_pct;
        const double proceeds = requested_qty * entry_px;
        const double commission = proceeds * commission_pct;
        cash += proceeds - commission;
        position -= requested_qty;
        entry_price = entry_px;
      }
    }

    const double mark = cash + position * close[i];
    peak = std::max(peak, mark);
    if (peak > 0.0) max_dd = std::max(max_dd, (peak - mark) / peak * 100.0);
  }

  if (position != 0.0 && !close.empty()) {
    const double px = close.back();
    if (position > 0.0) {
      const double exit_px = px - px * slippage_pct;
      const double pnl = (exit_px - entry_price) * position;
      const double commission = position * exit_px * commission_pct;
      cash += position * exit_px - commission;
      ++trades;
      if (pnl - commission > 0.0) ++wins;
    } else {
      const double qty = -position;
      const double exit_px = px + px * slippage_pct;
      const double pnl = (entry_price - exit_px) * qty;
      const double commission = qty * exit_px * commission_pct;
      cash -= qty * exit_px + commission;
      ++trades;
      if (pnl - commission > 0.0) ++wins;
    }
  }

  BacktestOutput out;
  out.final_equity = cash;
  out.total_return_pct = (cash / initial_capital - 1.0) * 100.0;
  out.max_drawdown_pct = max_dd;
  out.trades = trades;
  out.wins = wins;
  return out;
}

RiskScanOutput risk_scan(const std::vector<double>& returns,
                         const std::vector<double>& equity) {
  RiskScanOutput out;
  if (!returns.empty()) {
    const double sum = std::accumulate(returns.begin(), returns.end(), 0.0);
    out.mean = sum / static_cast<double>(returns.size());
    if (returns.size() > 1) {
      double ss = 0.0;
      for (double x : returns) {
        const double d = x - out.mean;
        ss += d * d;
      }
      out.stddev = std::sqrt(ss / static_cast<double>(returns.size() - 1));
    }
    out.sharpe = out.stddev > 0.0 ? out.mean / out.stddev * std::sqrt(252.0) : 0.0;

    std::vector<double> sorted = returns;
    std::sort(sorted.begin(), sorted.end());
    out.var95 = -percentile_sorted(sorted, 0.05);
    const double threshold = percentile_sorted(sorted, 0.05);
    double tail_sum = 0.0;
    std::size_t tail_n = 0;
    for (double x : returns) {
      if (x <= threshold) {
        tail_sum += x;
        ++tail_n;
      }
    }
    out.cvar95 = tail_n == 0 ? 0.0 : -tail_sum / static_cast<double>(tail_n);
  }

  if (!equity.empty()) {
    double peak = -std::numeric_limits<double>::infinity();
    for (double x : equity) {
      peak = std::max(peak, x);
      if (peak > 0.0) {
        out.max_drawdown_pct = std::max(out.max_drawdown_pct,
                                        (peak - x) / peak * 100.0);
      }
    }
  }
  return out;
}

}  // namespace quant::fast
