#ifndef QUANT_MARKET_TYPES_H
#define QUANT_MARKET_TYPES_H

#include <cstdint>
#include <chrono>
#include <string>
#include <compare>

namespace quant {

using TimePoint = std::chrono::system_clock::time_point;

struct OHLCV {
  TimePoint timestamp;
  double open{0.0};
  double high{0.0};
  double low{0.0};
  double close{0.0};
  double volume{0.0};

  double spread() const { return high - low; }
  double change() const { return close - open; }
  double change_pct() const { return open != 0.0 ? (close - open) / open * 100.0 : 0.0; }
  bool is_valid() const { return high >= low && high >= open && high >= close && low <= open && low <= close; }
};

struct Tick {
  TimePoint timestamp;
  double price{0.0};
  double volume{0.0};
  std::string symbol;
  uint64_t trade_id{0};

  auto operator<=>(const Tick&) const = default;
};

struct Position {
  std::string symbol;
  double quantity{0.0};
  double entry_price{0.0};
  double current_price{0.0};
  double commission_paid{0.0};

  double pnl() const { return (current_price - entry_price) * quantity - commission_paid; }
  double pnl_pct() const { return entry_price != 0.0 ? ((current_price - entry_price) / entry_price) * 100.0 : 0.0; }
  double market_value() const { return quantity * current_price; }
  double cost_basis() const { return quantity * entry_price; }
  bool is_long() const { return quantity > 0.0; }
  bool is_short() const { return quantity < 0.0; }
};

} // namespace quant
#endif
