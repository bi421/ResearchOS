#ifndef QUANT_MARKET_OHLCV_CONTAINER_H
#define QUANT_MARKET_OHLCV_CONTAINER_H

#include "candle.h"
#include "time_index.h"
#include "quant/core/result.h"
#include <vector>
#include <string>
#include <span>
#include <optional>

namespace quant {

class OHLCVContainer {
public:
  OHLCVContainer() = default;
  explicit OHLCVContainer(std::string symbol, Timeframe tf = Timeframe::M1);

  void set_symbol(std::string s) { symbol_ = std::move(s); }
  const std::string& symbol() const { return symbol_; }
  Timeframe timeframe() const { return timeframe_; }

  Result<void> append(const Candle& candle);
  Result<void> append_batch(const std::vector<Candle>& candles);

  size_t size() const { return candles_.size(); }
  bool empty() const { return candles_.empty(); }

  const Candle& operator[](size_t i) const;
  const Candle& at(size_t i) const;
  std::span<const Candle> view(size_t start, size_t count) const;

  const std::vector<Candle>& candles() const { return candles_; }

  std::optional<size_t> find_index(TimePoint tp) const;
  std::optional<Candle> find_candle(TimePoint tp) const;

  OHLCVContainer range(size_t start, size_t end) const;
  OHLCVContainer range_by_time(TimePoint from, TimePoint to) const;

  const TimeIndex& time_index() const { return index_; }

  TimePoint first_time() const;
  TimePoint last_time() const;
  double duration_seconds() const;

  void clear();
  void shrink_to_fit();

  double total_volume() const;
  double avg_volume() const;

  Result<Candle> merge_candles(const std::vector<Candle>& target_candles) const;

private:
  std::string symbol_;
  Timeframe timeframe_{Timeframe::M1};
  std::vector<Candle> candles_;
  TimeIndex index_;
  bool index_dirty_{false};

  void rebuild_index_if_needed() const;
};

} // namespace quant
#endif
