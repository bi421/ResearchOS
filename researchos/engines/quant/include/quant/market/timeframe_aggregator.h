#ifndef QUANT_MARKET_TIMEFRAME_AGGREGATOR_H
#define QUANT_MARKET_TIMEFRAME_AGGREGATOR_H

#include "candle.h"
#include "ohlcv_container.h"
#include "quant/core/result.h"
#include <vector>
#include <cstdint>

namespace quant {

class TimeframeAggregator {
public:
  TimeframeAggregator() = default;

  static Result<OHLCVContainer> aggregate(const OHLCVContainer& source,
                                           Timeframe target_tf);

  static Result<OHLCVContainer> aggregate_to_multiple(const OHLCVContainer& source,
                                                       const std::vector<Timeframe>& timeframes);

  static std::vector<Candle> aggregate_candles(const std::vector<Candle>& source,
                                                Timeframe source_tf,
                                                Timeframe target_tf);

  static TimePoint align_timestamp(TimePoint tp, int64_t minutes);
  static int64_t minutes_between(Timeframe from, Timeframe to);

  static bool can_aggregate(Timeframe from, Timeframe to);

private:
  static std::vector<Candle> aggregate_impl(const std::vector<Candle>& candles,
                                              size_t chunk_size);
};

} // namespace quant
#endif
