#ifndef QUANT_STRATEGY_TRADE_RESULT_H
#define QUANT_STRATEGY_TRADE_RESULT_H

#include "quant/strategy/strategy_signal.h"
#include "quant/market/types.h"
#include <cstdint>
#include <string>

namespace quant {
namespace strategy {

enum class ExitReason : uint8_t {
  Signal = 0,
  StopLoss,
  TakeProfit,
  TrailingStop,
  BreakEven,
  TimeStop,
  DailyLossLimit,
  SessionClose,
  EndOfData,
};

inline const char* exit_reason_name(ExitReason r) {
  switch (r) {
    case ExitReason::Signal: return "Signal";
    case ExitReason::StopLoss: return "StopLoss";
    case ExitReason::TakeProfit: return "TakeProfit";
    case ExitReason::TrailingStop: return "TrailingStop";
    case ExitReason::BreakEven: return "BreakEven";
    case ExitReason::TimeStop: return "TimeStop";
    case ExitReason::DailyLossLimit: return "DailyLossLimit";
    case ExitReason::SessionClose: return "SessionClose";
    case ExitReason::EndOfData: return "EndOfData";
  }
  return "Unknown";
}

// A fully closed position. Partial closes are aggregated: `quantity` is the
// total closed size, `avg_exit_price` the quantity-weighted exit price, and
// `partial_fill_count` records how many fills produced the exit.
struct TradeResult {
  int64_t trade_id{0};
  TradeSide side{TradeSide::Long};

  int64_t entry_bar{0};
  int64_t exit_bar{0};
  TimePoint entry_time;
  TimePoint exit_time;

  double entry_price{0.0};     // actual fill incl. costs
  double exit_price{0.0};      // final fill incl. costs
  double avg_exit_price{0.0};  // quantity-weighted across partial fills
  double quantity{0.0};        // total closed quantity
  double gross_pnl{0.0};
  double net_pnl{0.0};
  double net_pnl_pct{0.0};     // net_pnl / entry_value * 100
  double r_multiple{0.0};
  double commission{0.0};
  double slippage{0.0};        // cost attributable to spread + slippage
  double mfe{0.0};
  double mae{0.0};
  int64_t bars_held{0};
  ExitReason exit_reason{ExitReason::Signal};
  bool partial_close{false};
  int64_t partial_fill_count{0};

  bool is_profitable() const { return net_pnl > 0.0; }
  bool is_loss() const { return net_pnl < 0.0; }
  bool is_breakeven() const { return net_pnl == 0.0; }

  double profit_loss_percent() const;
  std::string summary() const;
};

} // namespace strategy
} // namespace quant
#endif
