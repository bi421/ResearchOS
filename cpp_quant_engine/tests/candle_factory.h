#ifndef QUANT_TEST_CANDLE_FACTORY_H
#define QUANT_TEST_CANDLE_FACTORY_H

#include "quant/market/candle.h"
#include "quant/backtest/market_data.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <vector>

namespace quant::test {

// Deterministic pseudo-random-looking candle series (valid OHLC, strictly
// increasing timestamps at the requested timeframe cadence).
inline std::vector<Candle> make_candles(
    size_t n, TimePoint start = std::chrono::system_clock::time_point{},
    Timeframe tf = Timeframe::M1, double base = 100.0) {
  std::vector<Candle> out;
  out.reserve(n);
  const auto step = std::chrono::minutes(timeframe_minutes(tf));
  for (size_t i = 0; i < n; ++i) {
    Candle c;
    c.timestamp = start + step * static_cast<int64_t>(i);
    const double price =
        base + 10.0 * std::sin(static_cast<double>(i) / 7.0) +
        0.1 * static_cast<double>(i % 13);
    c.open = price;
    c.close = price + 1.0;
    c.high = std::max(c.open, c.close) + 0.5;
    c.low = std::min(c.open, c.close) - 0.5;
    c.volume = 1000.0;
    c.trade_count = 100;
    c.timeframe = tf;
    out.push_back(c);
  }
  return out;
}

// Build a MarketData from a vector of candles.
inline MarketData make_market_data(const std::vector<Candle>& candles,
                                   const std::string& symbol = "TEST",
                                   Timeframe tf = Timeframe::M1) {
  MarketData md;
  auto res = md.load(symbol, tf, candles);
  (void)res;
  return md;
}

// OHLCV bars from make_candles (for BacktestResult::bars_used fixtures).
inline std::vector<OHLCV> make_ohlcv_bars(size_t n) {
  const auto candles = make_candles(n);
  std::vector<OHLCV> out;
  out.reserve(n);
  for (const auto& c : candles) out.push_back(static_cast<OHLCV>(c));
  return out;
}

} // namespace quant::test
#endif
