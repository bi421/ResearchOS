#ifndef QUANT_STRATEGY_STRATEGY_SIGNAL_H
#define QUANT_STRATEGY_STRATEGY_SIGNAL_H

#include <cstdint>

namespace quant {
namespace strategy {

enum class TradeSide : uint8_t {
  Long = 0,
  Short = 1,
};

inline const char* side_name(TradeSide s) {
  return s == TradeSide::Long ? "Long" : "Short";
}

enum class SignalAction : uint8_t {
  None = 0,
  Open,       // open a new position (sizing from TradeConfig)
  Close,      // close the most recent open position of `side`
  CloseAll,   // close every open position
  Modify,     // update stop / take-profit / trailing of the most recent `side` position
};

inline const char* action_name(SignalAction a) {
  switch (a) {
    case SignalAction::None: return "None";
    case SignalAction::Open: return "Open";
    case SignalAction::Close: return "Close";
    case SignalAction::CloseAll: return "CloseAll";
    case SignalAction::Modify: return "Modify";
  }
  return "Unknown";
}

// A single strategy instruction attached to a bar.
//
// Execution model: a signal with `bar_index == i` is queued while bar i is
// processed and filled at the OPEN of bar i+1 (no look-ahead). A signal on
// the final bar is never filled. Signals with the same `bar_index` execute
// in their given order.
struct StrategySignal {
  int64_t bar_index{-1};     // bar the signal refers to (fill at next bar open)
  SignalAction action{SignalAction::None};
  TradeSide side{TradeSide::Long};

  double quantity{0.0};      // 0.0 -> position sizing from TradeConfig
  double stop_loss{0.0};     // absolute price override (only if has_stop_loss)
  double take_profit{0.0};   // absolute price override (only if has_take_profit)
  double trailing_stop{0.0}; // absolute distance override (only if has_trailing_stop)

  bool has_stop_loss{false};
  bool has_take_profit{false};
  bool has_trailing_stop{false};

  double risk_amount{0.0};   // optional currency risk override for sizing; 0 -> config
};

} // namespace strategy
} // namespace quant
#endif
