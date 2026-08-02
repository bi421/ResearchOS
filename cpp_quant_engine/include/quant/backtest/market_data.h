#ifndef QUANT_BACKTEST_MARKET_DATA_H
#define QUANT_BACKTEST_MARKET_DATA_H

#include "quant/market/candle.h"
#include "quant/market/time_index.h"
#include "quant/backtest/ohlcv_source.h"
#include "quant/core/result.h"
#include <string>
#include <vector>
#include <optional>

namespace quant {

// Describes the shape of a dataset handed to the backtest engine.
struct MarketDataConfig {
  std::string symbol;
  Timeframe timeframe{Timeframe::M1};
  std::optional<TimePoint> start;
  std::optional<TimePoint> end;
};

// MarketData is the canonical data-flow entry point for the backtest
// pipeline: MarketData -> BacktestEngine -> PerformanceReport.
//
// It owns a chronologically ordered candle series, validates the series
// (valid OHLC, non-decreasing timestamps), and exposes slices/adapters for
// downstream consumers (backtest engine, replay engine, analytics).
class MarketData {
public:
  MarketData() = default;
  explicit MarketData(MarketDataConfig cfg);

  const MarketDataConfig& config() const { return config_; }
  void set_config(MarketDataConfig cfg) { config_ = std::move(cfg); }

  // Load a complete series. Replaces any existing candles.
  Result<void> load(const std::string& symbol, Timeframe tf,
                    const std::vector<Candle>& candles);
  Result<void> load(const std::string& symbol, Timeframe tf,
                    const std::vector<OHLCV>& candles);

  // Append a single candle at the end of the series.
  Result<void> append(const Candle& candle);

  size_t size() const { return candles_.size(); }
  bool empty() const { return candles_.empty(); }

  const Candle& at(size_t index) const;
  const Candle& operator[](size_t index) const;
  const std::vector<Candle>& candles() const { return candles_; }

  TimePoint first_time() const;
  TimePoint last_time() const;
  const std::string& symbol() const { return config_.symbol; }
  Timeframe timeframe() const { return config_.timeframe; }

  // Full structural validation. Returns an Error describing the first
  // problem found, or ok() when the series is clean.
  Result<void> validate() const;

  // Index-range slice of the underlying candles.
  std::vector<Candle> slice(size_t start, size_t end) const;

  // Conversion helpers for downstream engines that consume OHLCV.
  std::vector<OHLCV> to_ohlcv() const;
  OHLCV as_ohlcv(size_t index) const;

  std::optional<size_t> find_index(TimePoint tp) const;

private:
  MarketDataConfig config_;
  std::vector<Candle> candles_;
  mutable TimeIndex index_;
  mutable bool index_dirty_{true};

  void rebuild_index_if_needed() const;
};

// Adapter that exposes a MarketData series through the existing
// OHLCVSource contract used by BacktestEngine.
class MarketDataSource : public OHLCVSource {
public:
  explicit MarketDataSource(const MarketData& md);

  size_t size() const override;
  const OHLCV& operator[](size_t index) const override;
  std::vector<OHLCV> range(size_t start, size_t end) const override;

private:
  std::vector<OHLCV> ohlcv_;
};

} // namespace quant
#endif
