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
  const double price = bar.close;
  const double slippage = price * config_.slippage_pct;

  if (signal.direction == TradeDirection::Buy) {
    if (position < 0.0) {
      const double close_qty = std::min(signal.quantity, -position);
      const double exit_price = price + slippage;
      const double commission = close_qty * exit_price * config_.commission_pct;
      cash -= close_qty * exit_price + commission;
      position += close_qty;

      for (const auto& trade : book.open_trades()) {
        if (trade.direction == TradeDirection::Sell) {
          book.close_trade(trade.id, exit_price, bar.timestamp, commission, close_qty);
          break;
        }
      }

      const double residual = signal.quantity - close_qty;
      if (residual <= 0.0) return Result<void>::ok();

      const double cost = residual * exit_price;
      const double entry_commission = cost * config_.commission_pct;
      if (cash < cost + entry_commission) return Result<void>::ok();
      cash -= cost + entry_commission;
      position += residual;

      Trade t;
      t.symbol = book.symbol();
      t.direction = TradeDirection::Buy;
      t.quantity = residual;
      t.entry_price = exit_price;
      t.entry_commission = entry_commission;
      t.entry_time = bar.timestamp;
      t.status = TradeStatus::Open;
      book.add_trade(t);
      return Result<void>::ok();
    }

    const double cost = signal.quantity * (price + slippage);
    const double comm = cost * config_.commission_pct;
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
      const double close_qty = std::min(signal.quantity, position);
      const double exit_price = price - slippage;
      const double commission = close_qty * exit_price * config_.commission_pct;
      cash += close_qty * exit_price - commission;
      position -= close_qty;

      for (const auto& trade : book.open_trades()) {
        if (trade.direction == TradeDirection::Buy) {
          book.close_trade(trade.id, exit_price, bar.timestamp, commission, close_qty);
          break;
        }
      }

      const double residual = signal.quantity - close_qty;
      if (residual <= 0.0) return Result<void>::ok();

      if (config_.allow_short) {
        const double proceeds = residual * exit_price;
        const double entry_commission = proceeds * config_.commission_pct;
        cash += proceeds - entry_commission;
        position -= residual;

        Trade t;
        t.symbol = book.symbol();
        t.direction = TradeDirection::Sell;
        t.quantity = residual;
        t.entry_price = exit_price;
        t.entry_commission = entry_commission;
        t.entry_time = bar.timestamp;
        t.status = TradeStatus::Open;
        book.add_trade(t);
      }
      return Result<void>::ok();
    }

    if (config_.allow_short) {
      const double proceeds = signal.quantity * (price - slippage);
      const double comm = proceeds * config_.commission_pct;
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
  std::optional<SignalResult> pending_signal;

  double running_peak = -std::numeric_limits<double>::infinity();

  for (size_t i = 0; i < data.size(); ++i) {
    const auto& bar = data[i];

    // Signals are generated from the completed/current bar and can only be
    // executed on the following bar's open. This prevents same-close
    // execution from leaking information from the signal bar into fills.
    if (pending_signal.has_value() && pending_signal->quantity > 0.0) {
      OHLCV execution_bar = bar;
      execution_bar.close = bar.open;
      auto exec = execute_signal(*pending_signal, execution_bar, cash, position, book);
      if (exec.is_err()) return exec.error();
    }

    history.push_back(bar);
    result.bars_used.push_back(bar);

    const double equity = cash + position * bar.close;
    result.equity_curve.push_back(equity);
    running_peak = std::max(running_peak, equity);
    result.drawdown_curve.push_back(
        running_peak > 0.0 ? (running_peak - equity) / running_peak * 100.0 : 0.0);

    pending_signal = signal_fn(i, history);
  }

  // A signal generated on the final bar has no subsequent bar and is therefore
  // deliberately not executed. Any existing position is closed at the final
  // close using the configured exit costs.
  if (position != 0.0) {
    const auto& last_bar = data[data.size() - 1];
    if (position > 0.0) {
      const double exit_price = last_bar.close - last_bar.close * config_.slippage_pct;
      const double commission = position * exit_price * config_.commission_pct;
      cash += position * exit_price - commission;
      for (const auto& t : book.open_trades()) {
        if (t.direction == TradeDirection::Buy) {
          book.close_trade(t.id, exit_price, last_bar.timestamp, commission, position);
          break;
        }
      }
    } else {
      const double qty = -position;
      const double exit_price = last_bar.close + last_bar.close * config_.slippage_pct;
      const double commission = qty * exit_price * config_.commission_pct;
      cash -= qty * exit_price + commission;
      for (const auto& t : book.open_trades()) {
        if (t.direction == TradeDirection::Sell) {
          book.close_trade(t.id, exit_price, last_bar.timestamp, commission, qty);
          break;
        }
      }
    }
    position = 0.0;
  }

  result.final_equity = cash;
  result.trade_book = std::move(book);
  result.num_trades = result.trade_book.closed_trades().size();
  result.win_rate = result.trade_book.win_rate();
  result.total_return_pct = ((result.final_equity - config_.initial_capital) /
                             config_.initial_capital) * 100.0;

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
  (void)data;
  (void)signal_fn;
  (void)train_window;
  (void)test_window;
  return Result<BacktestResult>::fail(
      Error{ErrorCode::NotImplemented,
            "walk-forward backtesting is not implemented; refusing to run a full-sample backtest"});
}

} // namespace quant
