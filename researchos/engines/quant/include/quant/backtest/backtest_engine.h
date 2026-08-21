#ifndef QUANT_BACKTEST_BACKTEST_ENGINE_H
#define QUANT_BACKTEST_BACKTEST_ENGINE_H

#include "ohlcv_source.h"
#include "trade_book.h"
#include "quant/market/types.h"
#include "quant/core/result.h"
#include "quant/core/config.h"
#include <vector>
#include <functional>
#include <memory>

namespace quant {

struct BacktestConfig {
  double initial_capital{100'000.0};
  double commission_pct{0.001};
  double slippage_pct{0.0005};
  bool allow_short{true};
};

struct SignalResult {
  TradeDirection direction;
  double quantity;
  double stop_loss{0.0};
  double take_profit{0.0};
};

using SignalFn = std::function<SignalResult(size_t bar_index, const std::vector<OHLCV>& history)>;

struct BacktestResult {
  std::vector<double> equity_curve;
  std::vector<double> drawdown_curve;
  std::vector<OHLCV> bars_used;
  TradeBook trade_book;
  BacktestConfig config;
  size_t total_bars{0};
  double final_equity{0.0};
  double total_return_pct{0.0};
  double max_drawdown_pct{0.0};
  double sharpe{0.0};
  size_t num_trades{0};
  double win_rate{0.0};
  double profit_factor{0.0};
};

class MarketData;

class BacktestEngine {
public:
  BacktestEngine() = default;

  void set_config(const BacktestConfig& cfg) { config_ = cfg; }
  const BacktestConfig& config() const { return config_; }

  Result<BacktestResult> run(OHLCVSource& data, SignalFn signal_fn);
  Result<BacktestResult> run(MarketData& data, SignalFn signal_fn);
  Result<BacktestResult> run_walk_forward(OHLCVSource& data, SignalFn signal_fn,
                                           size_t train_window, size_t test_window);

private:
  BacktestConfig config_;

  Result<void> execute_signal(const SignalResult& signal, const OHLCV& bar,
                               double& cash, double& position,
                               TradeBook& book) const;
};

} // namespace quant
#endif
