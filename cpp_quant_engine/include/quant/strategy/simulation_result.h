#ifndef QUANT_STRATEGY_SIMULATION_RESULT_H
#define QUANT_STRATEGY_SIMULATION_RESULT_H

#include "quant/strategy/trade_result.h"
#include "quant/strategy/strategy_config.h"
#include "quant/market/types.h"
#include <cstdint>
#include <string>
#include <vector>

namespace quant {
namespace strategy {

// A calendar-period return bucket (label is "YYYY" or "YYYY-MM").
struct PeriodReturn {
  std::string label;
  double return_pct{0.0};
  double start_equity{0.0};
  double end_equity{0.0};
};

struct StrategyStats {
  size_t total_trades{0};
  size_t winning_trades{0};
  size_t losing_trades{0};
  size_t breakeven_trades{0};
  double win_rate{0.0};           // winning / total, percent
  double average_win{0.0};
  double average_loss{0.0};
  double average_rr{0.0};         // |average_win / average_loss|
  double profit_factor{0.0};
  double expectancy{0.0};         // avg net pnl per trade (currency)
  double expectancy_r{0.0};       // avg R-multiple per trade
  double gross_profit{0.0};
  double gross_loss{0.0};
  double net_profit{0.0};
  double max_drawdown{0.0};
  double max_drawdown_pct{0.0};
  size_t max_consecutive_losses{0};
  size_t max_consecutive_wins{0};
  double recovery_factor{0.0};    // net_profit / |max_drawdown|
  double sharpe{0.0};
  double sortino{0.0};
  double calmar{0.0};
  double ulcer_index{0.0};
  double total_commission{0.0};
  double total_slippage{0.0};
  double total_return_pct{0.0};
  double annualized_return{0.0};
  double annualized_volatility{0.0};
};

struct SimulationResult {
  StrategyStats stats;
  std::vector<double> equity_curve;   // per bar close (length == bars_processed)
  std::vector<double> drawdown_curve; // percentage drawdown per bar
  std::vector<TradeResult> trades;
  std::vector<PeriodReturn> monthly_returns;
  std::vector<PeriodReturn> yearly_returns;

  size_t bars_processed{0};
  size_t signals_processed{0};
  size_t signals_opened{0};
  size_t signals_ignored{0};
  double initial_equity{0.0};
  double final_equity{0.0};

  std::string input_hash;
  std::string result_hash;

  // Deterministic canonical hash over the full result (defined in
  // src/strategy/strategy_kernel.cpp).
  std::string compute_result_hash() const;
};

} // namespace strategy
} // namespace quant
#endif
