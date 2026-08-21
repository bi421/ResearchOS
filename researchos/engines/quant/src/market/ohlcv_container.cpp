#include "quant/market/ohlcv_container.h"
#include <algorithm>
#include <numeric>
#include <cmath>

namespace quant {

OHLCVContainer::OHLCVContainer(std::string symbol, Timeframe tf)
  : symbol_(std::move(symbol)), timeframe_(tf) {}

Result<void> OHLCVContainer::append(const Candle& candle) {
  if (!candle.is_valid()) {
    return Error(ErrorCode::InvalidArgument, "invalid candle data");
  }
  if (!candles_.empty() && candle.timestamp <= candles_.back().timestamp) {
    return Error(ErrorCode::InvalidArgument, "timestamp must be increasing");
  }
  candles_.push_back(candle);
  index_.add(candle.timestamp, candles_.size() - 1);
  return Result<void>::ok();
}

Result<void> OHLCVContainer::append_batch(const std::vector<Candle>& candles) {
  for (auto& c : candles) {
    auto r = append(c);
    if (r.is_err()) return r;
  }
  return Result<void>::ok();
}

const Candle& OHLCVContainer::operator[](size_t i) const {
  return candles_[i];
}

const Candle& OHLCVContainer::at(size_t i) const {
  if (i >= candles_.size()) {
    throw std::out_of_range("OHLCVContainer index out of range");
  }
  return candles_[i];
}

std::span<const Candle> OHLCVContainer::view(size_t start, size_t count) const {
  if (start >= candles_.size()) return {};
  count = std::min(count, candles_.size() - start);
  return std::span<const Candle>(candles_.data() + start, count);
}

std::optional<size_t> OHLCVContainer::find_index(TimePoint tp) const {
  return index_.find(tp);
}

std::optional<Candle> OHLCVContainer::find_candle(TimePoint tp) const {
  auto idx = find_index(tp);
  if (idx) return candles_[*idx];
  return std::nullopt;
}

OHLCVContainer OHLCVContainer::range(size_t start, size_t end) const {
  OHLCVContainer result(symbol_, timeframe_);
  if (start >= candles_.size()) return result;
  end = std::min(end, candles_.size());
  for (size_t i = start; i < end; ++i) {
    result.candles_.push_back(candles_[i]);
    result.index_.add(candles_[i].timestamp, i - start);
  }
  return result;
}

OHLCVContainer OHLCVContainer::range_by_time(TimePoint from, TimePoint to) const {
  auto [lo, hi] = index_.range(from, to);
  return range(lo, hi);
}

TimePoint OHLCVContainer::first_time() const {
  if (candles_.empty()) return TimePoint{};
  return candles_.front().timestamp;
}

TimePoint OHLCVContainer::last_time() const {
  if (candles_.empty()) return TimePoint{};
  return candles_.back().timestamp;
}

double OHLCVContainer::duration_seconds() const {
  if (candles_.size() < 2) return 0.0;
  auto dur = candles_.back().timestamp - candles_.front().timestamp;
  return std::chrono::duration<double>(dur).count();
}

void OHLCVContainer::clear() {
  candles_.clear();
  index_.clear();
  index_dirty_ = false;
}

void OHLCVContainer::shrink_to_fit() {
  candles_.shrink_to_fit();
}

double OHLCVContainer::total_volume() const {
  return std::accumulate(candles_.begin(), candles_.end(), 0.0,
                          [](double sum, const Candle& c) { return sum + c.volume; });
}

double OHLCVContainer::avg_volume() const {
  if (candles_.empty()) return 0.0;
  return total_volume() / static_cast<double>(candles_.size());
}

Result<Candle> OHLCVContainer::merge_candles(const std::vector<Candle>& target_candles) const {
  if (target_candles.empty()) return Error(ErrorCode::InsufficientData, "no candles to merge");
  Candle merged = target_candles[0];
  for (size_t i = 1; i < target_candles.size(); ++i) {
    const auto& c = target_candles[i];
    merged.high = std::max(merged.high, c.high);
    merged.low = std::min(merged.low, c.low);
    merged.close = c.close;
    merged.volume += c.volume;
    merged.trade_count += c.trade_count;
    merged.vwap = (merged.vwap * (merged.volume - c.volume) + c.vwap * c.volume) / merged.volume;
  }
  return merged;
}

void OHLCVContainer::rebuild_index_if_needed() const {
  if (index_dirty_) {
    const_cast<OHLCVContainer*>(this)->index_.rebuild();
    const_cast<OHLCVContainer*>(this)->index_dirty_ = false;
  }
}

} // namespace quant
