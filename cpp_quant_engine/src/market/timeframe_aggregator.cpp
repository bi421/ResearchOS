#include "quant/market/timeframe_aggregator.h"
#include <cmath>
#include <algorithm>

namespace quant {

TimePoint TimeframeAggregator::align_timestamp(TimePoint tp, int64_t minutes) {
  auto dur = tp.time_since_epoch();
  auto secs = std::chrono::duration_cast<std::chrono::seconds>(dur).count();
  int64_t period_secs = minutes * 60;
  if (period_secs <= 0) return tp;
  int64_t aligned = (secs / period_secs) * period_secs;
  return TimePoint(std::chrono::seconds(aligned));
}

int64_t TimeframeAggregator::minutes_between(Timeframe from, Timeframe to) {
  int64_t from_min = timeframe_minutes(from);
  int64_t to_min = timeframe_minutes(to);
  if (from_min == 0 || to_min < from_min) return 0;
  if (to_min % from_min != 0) return 0;
  return to_min / from_min;
}

bool TimeframeAggregator::can_aggregate(Timeframe from, Timeframe to) {
  return minutes_between(from, to) > 0;
}

std::vector<Candle> TimeframeAggregator::aggregate_impl(
    const std::vector<Candle>& candles, size_t chunk_size) {
  std::vector<Candle> result;
  result.reserve(candles.size() / chunk_size + 1);

  for (size_t i = 0; i < candles.size(); i += chunk_size) {
    size_t end = std::min(i + chunk_size, candles.size());
    Candle agg;
    agg.timestamp = candles[i].timestamp;
    agg.open = candles[i].open;
    agg.high = candles[i].high;
    agg.low = candles[i].low;
    agg.close = candles[end - 1].close;
    agg.volume = 0.0;
    agg.trade_count = 0;
    agg.timeframe = candles[i].timeframe;

    double vwap_numer = 0.0;
    for (size_t j = i; j < end; ++j) {
      const auto& c = candles[j];
      agg.high = std::max(agg.high, c.high);
      agg.low = std::min(agg.low, c.low);
      agg.volume += c.volume;
      agg.trade_count += c.trade_count;
      vwap_numer += (c.high + c.low + c.close) / 3.0 * c.volume;
    }
    agg.vwap = agg.volume > 0.0 ? vwap_numer / agg.volume : 0.0;
    result.push_back(agg);
  }

  return result;
}

Result<OHLCVContainer> TimeframeAggregator::aggregate(const OHLCVContainer& source,
                                                       Timeframe target_tf) {
  if (source.empty()) {
    return Error(ErrorCode::InsufficientData, "source container is empty");
  }

  size_t factor = static_cast<size_t>(minutes_between(source.timeframe(), target_tf));
  if (factor == 0) {
    return Error(ErrorCode::InvalidArgument,
                 std::format("cannot aggregate {} -> {}",
                              timeframe_name(source.timeframe()),
                              timeframe_name(target_tf)));
  }

  auto aggregated = aggregate_impl(source.candles(), factor);

  OHLCVContainer result(source.symbol(), target_tf);
  for (auto& c : aggregated) {
    c.timestamp = align_timestamp(c.timestamp, timeframe_minutes(target_tf));
    c.timeframe = target_tf;
    auto r = result.append(c);
    if (r.is_err()) return r.error();
  }

  return result;
}

Result<OHLCVContainer> TimeframeAggregator::aggregate_to_multiple(
    const OHLCVContainer& source, const std::vector<Timeframe>& timeframes) {
  // Return the first successfully aggregated timeframe
  for (auto tf : timeframes) {
    if (tf == source.timeframe()) {
      OHLCVContainer copy = source;
      return copy;
    }
    if (can_aggregate(source.timeframe(), tf)) {
      return aggregate(source, tf);
    }
  }
  return Error(ErrorCode::InvalidArgument, "no compatible target timeframe");
}

std::vector<Candle> TimeframeAggregator::aggregate_candles(
    const std::vector<Candle>& source, Timeframe source_tf, Timeframe target_tf) {
  size_t factor = static_cast<size_t>(minutes_between(source_tf, target_tf));
  if (factor == 0) return {};
  return aggregate_impl(source, factor);
}

} // namespace quant
