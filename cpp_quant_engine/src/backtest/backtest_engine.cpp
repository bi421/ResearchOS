#include "quant/backtest/backtest_engine.h"
#include "quant/backtest/market_data.h"
#include "quant/statistics/risk.h"
#include <algorithm>
#include <limits>
#include <optional>
#include <utility>

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
  if (train_window == 0 || test_window == 0) {
    return Result<BacktestResult>::fail(
        Error{ErrorCode::InvalidArgument, "walk-forward windows must be greater than zero"});
  }
  if (data.size() < train_window + test_window) {
    return Result<BacktestResult>::fail(
        Error{ErrorCode::InvalidArgument, "insufficient bars for a train/test walk-forward fold"});
  }

  // SignalFn has no fit/train callback. Therefore this API implements a strict
  // chronological OOS evaluator for a fixed deterministic signal function:
  // each fold exposes the training history to the signal, but trades are
  // disabled until the test interval. No observations after test_end are ever
  // visible to the fold. The train window is context/warm-up, not parameter
  // optimization; callers requiring fitting must perform that fit explicitly
  // and bind the resulting parameters before supplying signal_fn.
  BacktestResult aggregate;
  aggregate.config = config_;
  aggregate.total_bars = 0;
  aggregate.final_equity = config_.initial_capital;
  aggregate.trade_book = TradeBook();

  double compounded_equity = config_.initial_capital;
  size_t fold_start = 0;
  size_t fold_id = 0;

  while (fold_start + train_window + test_window <= data.size()) {
    const size_t test_start = fold_start + train_window;
    const size_t test_end = test_start + test_window;

    std::vector<OHLCV> fold_data;
    fold_data.reserve(train_window + test_window);
    for (size_t i = fold_start; i < test_end; ++i) {
      fold_data.push_back(data[i]);
    }

    InMemoryOHLCVSource fold_source;
    fold_source.data = std::move(fold_data);

    auto fold_result = run(fold_source, [&, test_start_local = train_window](
                                      size_t local_index,
                                      const std::vector<OHLCV>& history) -> SignalResult {
      if (local_index < test_start_local) {
        return {TradeDirection::Buy, 0.0};
      }
      // The callback sees only fold-local history, whose prefix is the training
      // interval and whose suffix is the current test interval. This preserves
      // causal indicator warm-up without allowing future test bars into a signal.
      return signal_fn(fold_start + local_index, history);
    });
    if (fold_result.is_err()) return fold_result.error();

    const auto& fold = fold_result.value();
    const double fold_return = fold.total_return_pct / 100.0;
    compounded_equity *= (1.0 + fold_return);
    aggregate.total_bars += test_window;
    ++fold_id;

    for (const auto& trade : fold.trade_book.closed_trades()) {
      aggregate.trade_book.add_trade(trade);
    }

    // Advance by the non-overlapping test interval. The next fold's training
    // window expands forward, while each OOS test interval remains disjoint.
    fold_start = test_start;
  }

  if (fold_id == 0) {
    return Result<BacktestResult>::fail(
        Error{ErrorCode::InvalidArgument, "walk-forward produced no complete OOS folds"});
  }

  aggregate.final_equity = compounded_equity;
  aggregate.num_trades = aggregate.trade_book.closed_trades().size();
  aggregate.win_rate = aggregate.trade_book.win_rate();
  aggregate.total_return_pct =
      ((aggregate.final_equity - config_.initial_capital) / config_.initial_capital) * 100.0;
  aggregate.max_drawdown_pct = 0.0;
  return aggregate;
}

} // namespace quant
