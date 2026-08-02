#ifndef QUANT_MARKET_CANDLE_H
#define QUANT_MARKET_CANDLE_H

#include "types.h"
#include <string>
#include <string_view>
#include <compare>
#include <cstdint>
#include <cmath>

namespace quant {

enum class Timeframe : uint32_t {
  M1 = 1,
  M5 = 5,
  M15 = 15,
  M30 = 30,
  H1 = 60,
  H4 = 240,
  D1 = 1440,
  W1 = 10080,
  MN1 = 43200,
};

inline std::string_view timeframe_name(Timeframe tf) {
  switch (tf) {
    case Timeframe::M1:  return "M1";
    case Timeframe::M5:  return "M5";
    case Timeframe::M15: return "M15";
    case Timeframe::M30: return "M30";
    case Timeframe::H1:  return "H1";
    case Timeframe::H4:  return "H4";
    case Timeframe::D1:  return "D1";
    case Timeframe::W1:  return "W1";
    case Timeframe::MN1: return "MN1";
    default:             return "UNK";
  }
}

inline int64_t timeframe_minutes(Timeframe tf) {
  return static_cast<int64_t>(tf);
}

struct Candle {
  TimePoint timestamp;
  double open{0.0};
  double high{0.0};
  double low{0.0};
  double close{0.0};
  double volume{0.0};
  uint64_t trade_count{0};
  double vwap{0.0};
  Timeframe timeframe{Timeframe::M1};

  Candle() = default;

  explicit Candle(const OHLCV& ohlcv, Timeframe tf = Timeframe::M1)
    : timestamp(ohlcv.timestamp), open(ohlcv.open), high(ohlcv.high),
      low(ohlcv.low), close(ohlcv.close), volume(ohlcv.volume),
      timeframe(tf) {}

  operator OHLCV() const {
    return OHLCV{timestamp, open, high, low, close, volume};
  }

  double spread() const { return high - low; }
  double change() const { return close - open; }
  double change_pct() const { return open != 0.0 ? (close - open) / open * 100.0 : 0.0; }
  double body() const { return std::abs(close - open); }
  double upper_wick() const { return high - std::max(open, close); }
  double lower_wick() const { return std::min(open, close) - low; }
  bool is_bullish() const { return close >= open; }
  bool is_bearish() const { return close < open; }
  bool is_valid() const {
    return high >= low && high >= open && high >= close &&
           low <= open && low <= close && volume >= 0.0 &&
           (high > 0.0 || low > 0.0 || open > 0.0 || close > 0.0);
  }

  auto operator<=>(const Candle&) const = default;
};

} // namespace quant
#endif
