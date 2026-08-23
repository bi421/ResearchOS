#include "quant/backtest/backtest_engine.h"
#include "quant/backtest/market_data.h"
#include "quant/statistics/risk.h"
#include <limits>

namespace quant {

std::vector<OHLCV> InMemoryOHLCVSource::range(size_t start, size_t end) const {
  if (start >= data.size()) return {};
  end = std::min(end, data.size());
  return std::vector<OHLCV>(data.begin() + static_cast<ptrdiff_t>(start),
                             data.begin() + static_cast<ptrdiff_t>(end));
}

Result<void> BacktestEngine::execute_signal(const SignalResult& signal, const OHLCV& bar,
                                             double& cash, double& position,
                                             TradeBook& book) const {
  double price = bar.close;
  double slippage = price * config_.slippage_pct;

  if (signal.direction == TradeDirection::Buy) {
    if (position < 0.0) {
      // Close the short: record an immediate, closed buy-back trade.
      double buy_qty = std::min(signal.quantity, -position);
      Trade t;
      t.symbol = book.symbol();
      t.direction = TradeDirection::Buy;
      t.quantity = buy_qty;
      t.entry_price = price + slippage;
      t.entry_commission = t.entry_price * buy_qty * config_.commission_pct;
      t.entry_time = bar.timestamp;
      t.status = TradeStatus::Closed;
      t.exit_price = t.entry_price;
      t.exit_commission = 0.0;
      t.exit_time = bar.timestamp;
      book.add_trade(t);
    }
    double cost = signal.quantity * (price + slippage);
    double comm = cost * config_.commission_pct;
    if (cash >= cost + comm) {
      cash -= cost + comm;
      position += signal.quantity;
      Trade t;
      t.symbol = book.symbol();
      t.direction = TradeDirection::Buy;
      t.quantity = signal.quantity;
      t.entry_price = price + slippage;
      t.entry_commission = comm;
      t.entry_time = bar.timestamp;
      t.status = TradeStatus::Open;
      book.add_trade(t);
    }
  } else {
    if (position > 0.0) {
      double sell_qty = std::min(signal.quantity, position);
      double proceeds = sell_qty * (price - slippage);
      double comm = (sell_qty * price) * config_.commission_pct;
      cash += proceeds - comm;
      position -= sell_qty;
      Trade t;
      t.symbol = book.symbol();
      t.direction = TradeDirection::Sell;
      t.quantity = sell_qty;
      t.entry_price = price;
      t.entry_commission = 0.0;
      t.entry_time = bar.timestamp;
      t.exit_price = price - slippage;
      t.exit_commission = comm;
      t.exit_time = bar.timestamp;
      t.status = TradeStatus::Closed;
      book.add_trade(t);
    } else if (config_.allow_short) {
      double proceeds = signal.quantity * (price - slippage);
      double comm = (signal.quantity * price) * config_.commission_pct;
      cash += proceeds - comm;
      position -= signal.quantity;
      Trade t;
      t.symbol = book.symbol();
      t.direction = TradeDirection::Sell;
      t.quantity = signal.quantity;
      t.entry_price = price - slippage;
      t.entry_commission = comm;
      t.entry_time = bar.timestamp;
      t.status = TradeStatus::Open;
      book.add_trade(t);
    }
  }
  return Result<void>::ok();
}

Result<BacktestResult> BacktestEngine::run(OHLCVSource& data, SignalFn signal_fn) {
  BacktestResult result;
  result.config = config_;
  result.total_bars = data.size();

  double cash = config_.initial_capital;
  double position = 0.0;
  TradeBook book;

  result.equity_curve.reserve(data.size());
  result.drawdown_curve.reserve(data.size());
  result.bars_used.reserve(data.size());

  std::vector<OHLCV> history;
  history.reserve(data.size());

  double running_peak = -std::numeric_limits<double>::infinity();

  for (size_t i = 0; i < data.size(); ++i) {
    const auto& bar = data[i];
    history.push_back(bar);
    result.bars_used.push_back(bar);

    double equity = cash + position * bar.close;
    result.equity_curve.push_back(equity);

    // Running drawdown curve (positive percentage magnitude, 0 at peaks).
    running_peak = std::max(running_peak, equity);
    result.drawdown_curve.push_back(
        running_peak > 0.0 ? (running_peak - equity) / running_peak * 100.0 : 0.0);

    auto signal = signal_fn(i, history);

    if (signal.quantity > 0.0) {
      auto exec = execute_signal(signal, bar, cash, position, book);
      if (exec.is_err()) return exec.error();
    }
  }

  if (position != 0.0) {
    const auto& last_bar = data[data.size() - 1];
    cash += position * last_bar.close;
    position = 0.0;
    // Close any open trades at the final bar for a consistent trade log.
    for (const auto& t : book.open_trades()) {
      book.close_trade(t.id, last_bar.close, last_bar.timestamp);
    }
  }

  result.final_equity = cash;
  result.trade_book = std::move(book);
  result.total_return_pct = ((result.final_equity - config_.initial_capital) / config_.initial_capital) * 100.0;

  auto dd = RiskMetrics::max_drawdown(result.equity_curve);
  if (dd.is_ok()) result.max_drawdown_pct = dd.value().max_drawdown_pct;

  return result;
}

Result<BacktestResult> BacktestEngine::run(MarketData& data, SignalFn signal_fn) {
  MarketDataSource source(data);
  return run(source, std::move(signal_fn));
}

Result<BacktestResult> BacktestEngine::run_walk_forward(
    OHLCVSource& data, SignalFn signal_fn,
    size_t train_window, size_t test_window) {
  // Stub: runs full backtest for now
  return run(data, std::move(signal_fn));
}

} // namespace quant
