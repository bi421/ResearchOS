#ifndef QUANT_STRATEGY_POSITION_H
#define QUANT_STRATEGY_POSITION_H

#include "quant/strategy/strategy_signal.h"
#include "quant/market/types.h"
#include <algorithm>
#include <cstdint>

namespace quant {
namespace strategy {

// An open position. All state lives in plain values so positions can be stored
// in a contiguous std::vector (cache-friendly, no per-position allocation).
struct OpenPosition {
  int64_t id{0};
  int64_t entry_bar{0};
  TimePoint entry_time;
  TradeSide side{TradeSide::Long};

  double entry_price{0.0};   // actual fill price (incl. spread + slippage)
  double open_raw{0.0};      // raw execution price before costs
  double quantity{0.0};      // remaining quantity (after partial closes)
  double entry_quantity{0.0};

  double stop_loss{0.0};     // current absolute level (moved by BE / trailing)
  double take_profit{0.0};   // current absolute level
  double initial_stop{0.0};
  double trailing_distance{0.0};
  double activation_distance{0.0};
  double break_even_activation{0.0};
  double partial_target{0.0}; // absolute level; 0 -> off

  double entry_commission{0.0};
  double total_commission{0.0};
  double entry_value{0.0};   // notional at raw entry price
  double risked_amount{0.0}; // planned risk for R-multiples

  double mfe{0.0};           // best favorable move per unit (price units)
  double mae{0.0};           // worst adverse move per unit (price units, negative)
  double realized_pnl{0.0};  // realized net pnl (incl. commissions)
  double avg_exit_price{0.0};
  double closed_quantity{0.0};
  double slippage{0.0};      // accumulated spread + slippage cost

  int64_t bars_open{0};
  bool trailing_active{false};
  bool break_even_moved{false};
  bool partial_closed{false};
  int64_t partial_fill_count{0};

  bool is_long() const { return side == TradeSide::Long; }
  double sign() const { return is_long() ? 1.0 : -1.0; }

  // PnL per unit at `price` (positive = favorable for the position side).
  double value_per_unit(double price) const {
    return (price - open_raw) * sign();
  }

  double unrealized_pnl(double price) const {
    return (price - entry_price) * quantity * sign();
  }

  double profit_per_unit(double price) const { return value_per_unit(price); }

  bool stop_hit(double high, double low) const {
    return is_long() ? low <= stop_loss : high >= stop_loss;
  }

  bool tp_hit(double high, double low) const {
    if (take_profit <= 0.0) return false;
    return is_long() ? high >= take_profit : low <= take_profit;
  }

  // Gap-aware fill price: fills at `open` when the bar gaps through the level.
  double stop_fill(double open) const {
    return is_long() ? std::min(open, stop_loss) : std::max(open, stop_loss);
  }

  double tp_fill(double open) const {
    return is_long() ? std::max(open, take_profit) : std::min(open, take_profit);
  }

  // Management helpers (defined in position.cpp).
  void update_mfe_mae(double high, double low);
  void move_stop_to_break_even();
  void ratchet_trailing(double best_price);
};

} // namespace strategy
} // namespace quant
#endif
