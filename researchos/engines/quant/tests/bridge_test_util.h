#ifndef QUANT_TEST_BRIDGE_UTIL_H
#define QUANT_TEST_BRIDGE_UTIL_H

#include "candle_factory.h"
#include "bridge_models.h"
#include "quant/backtest/serialization.h"
#include <string>
#include <vector>

namespace quant::bridge::test {

inline CandleModel make_bridge_candle(size_t i,
                                      std::chrono::system_clock::time_point start,
                                      const std::string& tf = "M1") {
  CandleModel c;
  c.timestamp = serialization::to_iso8601(
      start + std::chrono::minutes(1) * static_cast<int64_t>(i));
  const double price =
      100.0 + 10.0 * std::sin(static_cast<double>(i) / 7.0) +
      0.1 * static_cast<double>(i % 13);
  c.open = price;
  c.close = price + 1.0;
  c.high = std::max(c.open, c.close) + 0.5;
  c.low = std::min(c.open, c.close) - 0.5;
  c.volume = 1000.0;
  c.timeframe = tf;
  return c;
}

inline std::vector<CandleModel> make_bridge_candles(
    size_t n, std::chrono::system_clock::time_point start,
    const std::string& tf = "M1") {
  std::vector<CandleModel> out;
  out.reserve(n);
  for (size_t i = 0; i < n; ++i) out.push_back(make_bridge_candle(i, start, tf));
  return out;
}

} // namespace quant::bridge::test
#endif
