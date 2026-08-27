#ifndef QUANT_BACKTEST_SERIALIZATION_H
#define QUANT_BACKTEST_SERIALIZATION_H

#include "quant/backtest/event_replay.h"
#include "quant/backtest/performance_analyzer.h"
#include "quant/market/candle.h"
#include "quant/core/result.h"
#include <string>
#include <string_view>
#include <vector>

namespace quant {
namespace serialization {

// ── Timestamps ─────────────────────────────────────────────────────────────
// ISO-8601 "YYYY-MM-DDTHH:MM:SS" (UTC-naive; matches the engine's TimePoint).
std::string to_iso8601(TimePoint tp);
TimePoint from_iso8601(std::string_view str);

// ── Candle CSV ─────────────────────────────────────────────────────────────
// Columns: timestamp,open,high,low,close,volume,trade_count,vwap,timeframe
Result<std::string> candles_to_csv(const std::vector<Candle>& candles);
Result<std::vector<Candle>> candles_from_csv(std::string_view csv);

// ── Event JSON ─────────────────────────────────────────────────────────────
Result<std::string> events_to_json(const std::vector<ReplayEvent>& events);
Result<std::vector<ReplayEvent>> events_from_json(std::string_view json);

// ── Report JSON ────────────────────────────────────────────────────────────
Result<std::string> report_to_json(const DetailedPerformanceReport& report);
Result<std::string> report_to_json(const PerformanceReport& report);

} // namespace serialization
} // namespace quant
#endif
