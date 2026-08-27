#ifndef QUANT_BACKTEST_EVENT_REPLAY_H
#define QUANT_BACKTEST_EVENT_REPLAY_H

#include "quant/backtest/market_data.h"
#include "quant/market/candle.h"
#include <cstdint>
#include <vector>

namespace quant {

enum class EventType : uint8_t {
  Candle,
  Timestamp,
  Session,
};

enum class SessionStatus : uint8_t {
  Open,
  Close,
};

enum class ReplayMode : uint8_t {
  // Emit only candle events (cheapest replay).
  CandlesOnly,
  // Emit a timestamp event at each bar close in addition to candles.
  CandleTimestamp,
  // Full replay: session open/close events around candle/timestamp events.
  FullWithSessions,
};

inline const char* event_type_name(EventType t) {
  switch (t) {
    case EventType::Candle:    return "candle";
    case EventType::Timestamp: return "timestamp";
    case EventType::Session:   return "session";
  }
  return "unknown";
}

// A single replayed event in the deterministic event stream.
struct ReplayEvent {
  EventType type{EventType::Candle};
  TimePoint timestamp{};
  size_t bar_index{0};    // candle index for Candle/Timestamp events; session ordinal for Session events
  Candle candle;          // valid when type == Candle
  SessionStatus session_status{SessionStatus::Open};
  uint64_t sequence{0};   // global 1-based sequence number; identical across replays of the same data

  bool operator==(const ReplayEvent&) const = default;
};

// Deterministic forward-only event replay over a MarketData series.
//
// Event ordering per candle (FullWithSessions):
//   [SessionOpen] -> CandleEvent(bar open) -> TimestampEvent(bar close) -> [SessionClose]
//
// Replaying the same MarketData twice always yields the exact same event
// stream (same types, timestamps, and sequence numbers), which makes the
// engine suitable for reproducible simulation and regression testing.
class EventReplayEngine {
public:
  explicit EventReplayEngine(const MarketData& data,
                             ReplayMode mode = ReplayMode::FullWithSessions);

  // Move the replay cursor to the next event. Returns false when exhausted.
  bool advance();
  // Rewind to the beginning of the stream.
  void reset();

  const ReplayEvent& current_event() const { return current_; }
  ReplayEvent& current_event() { return current_; }

  bool done() const { return done_; }
  size_t position() const { return candle_index_; }
  uint64_t sequence() const { return seq_; }
  size_t event_count() const { return seq_; }
  bool has_next() const { return !done_; }

  ReplayMode mode() const { return mode_; }
  void set_mode(ReplayMode mode);

  // Materialize the complete event stream. Deterministic by construction.
  std::vector<ReplayEvent> snapshot() const;

private:
  const MarketData& data_;
  ReplayMode mode_{ReplayMode::FullWithSessions};

  size_t candle_index_{0};
  // Phase within the current candle:
  //   0 = (optional) session open
  //   1 = candle event
  //   2 = (optional) timestamp event
  //   3 = (optional) session close
  int phase_{0};
  uint64_t seq_{0};
  bool done_{false};
  ReplayEvent current_;

  bool is_session_open(size_t i) const;
  bool is_session_close(size_t i) const;
  void set_next_candle();
  bool emit_next();
};

// Convenience: build the full deterministic event sequence for a dataset.
std::vector<ReplayEvent> build_event_sequence(
    const MarketData& data, ReplayMode mode = ReplayMode::FullWithSessions);

} // namespace quant
#endif
