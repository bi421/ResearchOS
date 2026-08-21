#include "quant/backtest/market_data.h"
#include <algorithm>
#include <stdexcept>

namespace quant {

MarketData::MarketData(MarketDataConfig cfg) : config_(std::move(cfg)) {}

Result<void> MarketData::load(const std::string& symbol, Timeframe tf,
                              const std::vector<Candle>& candles) {
  MarketDataConfig cfg;
  cfg.symbol = symbol;
  cfg.timeframe = tf;
  config_ = std::move(cfg);

  candles_.clear();
  candles_.reserve(candles.size());

  TimePoint prev{};
  for (size_t i = 0; i < candles.size(); ++i) {
    const auto& c = candles[i];
    if (!c.is_valid()) {
      return Error(ErrorCode::InvalidArgument,
                   "MarketData::load: invalid candle at index " +
                       std::to_string(i));
    }
    if (i > 0 && c.timestamp <= prev) {
      return Error(ErrorCode::InvalidArgument,
                   "MarketData::load: timestamps must be strictly increasing; "
                   "violation at index " + std::to_string(i));
    }
    prev = c.timestamp;
    candles_.push_back(c);
  }

  index_dirty_ = true;
  return Result<void>::ok();
}

Result<void> MarketData::load(const std::string& symbol, Timeframe tf,
                              const std::vector<OHLCV>& ohlcv) {
  std::vector<Candle> candles;
  candles.reserve(ohlcv.size());
  for (const auto& o : ohlcv) candles.emplace_back(o, tf);
  return load(symbol, tf, candles);
}

Result<void> MarketData::append(const Candle& candle) {
  if (!candle.is_valid()) {
    return Error(ErrorCode::InvalidArgument,
                 "MarketData::append: invalid candle");
  }
  if (!candles_.empty() && candle.timestamp <= candles_.back().timestamp) {
    return Error(ErrorCode::InvalidArgument,
                 "MarketData::append: timestamp must be strictly increasing");
  }
  candles_.push_back(candle);
  index_dirty_ = true;
  return Result<void>::ok();
}

const Candle& MarketData::at(size_t index) const {
  if (index >= candles_.size())
    throw std::out_of_range("MarketData::at: index out of range");
  return candles_[index];
}

const Candle& MarketData::operator[](size_t index) const {
  return candles_[index];
}

TimePoint MarketData::first_time() const {
  return candles_.empty() ? TimePoint{} : candles_.front().timestamp;
}

TimePoint MarketData::last_time() const {
  return candles_.empty() ? TimePoint{} : candles_.back().timestamp;
}

Result<void> MarketData::validate() const {
  for (size_t i = 0; i < candles_.size(); ++i) {
    const auto& c = candles_[i];
    if (!c.is_valid()) {
      return Error(ErrorCode::InvalidArgument,
                   "MarketData::validate: invalid candle at index " +
                       std::to_string(i));
    }
    if (i > 0 && c.timestamp <= candles_[i - 1].timestamp) {
      return Error(ErrorCode::InvalidArgument,
                   "MarketData::validate: timestamps not strictly increasing "
                   "at index " + std::to_string(i));
    }
  }
  if (config_.start.has_value() && !candles_.empty() &&
      candles_.front().timestamp < *config_.start) {
    return Error(ErrorCode::InvalidArgument,
                 "MarketData::validate: data starts before config.start");
  }
  if (config_.end.has_value() && !candles_.empty() &&
      candles_.back().timestamp > *config_.end) {
    return Error(ErrorCode::InvalidArgument,
                 "MarketData::validate: data ends after config.end");
  }
  return Result<void>::ok();
}

std::vector<Candle> MarketData::slice(size_t start, size_t end) const {
  if (start >= candles_.size()) return {};
  end = std::min(end, candles_.size());
  return std::vector<Candle>(candles_.begin() + static_cast<ptrdiff_t>(start),
                             candles_.begin() + static_cast<ptrdiff_t>(end));
}

std::vector<OHLCV> MarketData::to_ohlcv() const {
  std::vector<OHLCV> out;
  out.reserve(candles_.size());
  for (const auto& c : candles_) out.push_back(static_cast<OHLCV>(c));
  return out;
}

OHLCV MarketData::as_ohlcv(size_t index) const {
  return static_cast<OHLCV>(candles_[index]);
}

std::optional<size_t> MarketData::find_index(TimePoint tp) const {
  rebuild_index_if_needed();
  return index_.find(tp);
}

void MarketData::rebuild_index_if_needed() const {
  if (!index_dirty_) return;
  std::vector<TimePoint> times;
  times.reserve(candles_.size());
  for (const auto& c : candles_) times.push_back(c.timestamp);
  index_.build(times);
  index_dirty_ = false;
}

MarketDataSource::MarketDataSource(const MarketData& md) : ohlcv_(md.to_ohlcv()) {}

size_t MarketDataSource::size() const { return ohlcv_.size(); }

const OHLCV& MarketDataSource::operator[](size_t index) const {
  return ohlcv_[index];
}

std::vector<OHLCV> MarketDataSource::range(size_t start, size_t end) const {
  if (start >= ohlcv_.size()) return {};
  end = std::min(end, ohlcv_.size());
  return std::vector<OHLCV>(ohlcv_.begin() + static_cast<ptrdiff_t>(start),
                            ohlcv_.begin() + static_cast<ptrdiff_t>(end));
}

} // namespace quant
