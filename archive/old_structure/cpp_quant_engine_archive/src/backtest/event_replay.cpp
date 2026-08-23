#include "quant/backtest/event_replay.h"
#include <chrono>

namespace quant {

namespace {

// Day ordinal (since the clock epoch) of a timestamp. Used to detect session
// (calendar day) boundaries.
int64_t day_of(TimePoint tp) {
  return std::chrono::duration_cast<std::chrono::days>(tp.time_since_epoch()).count();
}

} // namespace

EventReplayEngine::EventReplayEngine(const MarketData& data, ReplayMode mode)
    : data_(data), mode_(mode) {
  reset();
}

bool EventReplayEngine::advance() {
  if (done_) return false;
  if (!emit_next()) {
    done_ = true;
    return false;
  }
  return true;
}

void EventReplayEngine::reset() {
  candle_index_ = 0;
  seq_ = 0;
  if (data_.empty()) {
    done_ = true;
    phase_ = 1;
    return;
  }
  done_ = false;
  phase_ = (mode_ == ReplayMode::FullWithSessions && is_session_open(0)) ? 0 : 1;
}

void EventReplayEngine::set_mode(ReplayMode mode) {
  mode_ = mode;
  reset();
}

bool EventReplayEngine::is_session_open(size_t i) const {
  if (i == 0) return true;
  return day_of(data_[i].timestamp) != day_of(data_[i - 1].timestamp);
}

bool EventReplayEngine::is_session_close(size_t i) const {
  if (i + 1 >= data_.size()) return true;
  return day_of(data_[i].timestamp) != day_of(data_[i + 1].timestamp);
}

void EventReplayEngine::set_next_candle() {
  ++candle_index_;
  if (candle_index_ >= data_.size()) {
    done_ = true;
    return;
  }
  phase_ = (mode_ == ReplayMode::FullWithSessions && is_session_open(candle_index_)) ? 0 : 1;
}

bool EventReplayEngine::emit_next() {
  const size_t i = candle_index_;
  const auto bar_close = data_[i].timestamp +
                         std::chrono::minutes(timeframe_minutes(data_.timeframe()));

  ++seq_;
  current_.sequence = seq_;
  current_.bar_index = i;
  current_.candle = Candle{};  // only populated for Candle events

  switch (phase_) {
    case 0: {
      current_.type = EventType::Session;
      current_.timestamp = data_[i].timestamp;
      current_.session_status = SessionStatus::Open;
      phase_ = 1;
      return true;
    }
    case 1: {
      current_.type = EventType::Candle;
      current_.timestamp = data_[i].timestamp;
      current_.candle = data_[i];
      if (mode_ != ReplayMode::CandlesOnly) {
        phase_ = 2;
      } else if (mode_ == ReplayMode::FullWithSessions && is_session_close(i)) {
        phase_ = 3;
      } else {
        set_next_candle();
      }
      return true;
    }
    case 2: {
      current_.type = EventType::Timestamp;
      current_.timestamp = bar_close;
      if (mode_ == ReplayMode::FullWithSessions && is_session_close(i)) {
        phase_ = 3;
      } else {
        set_next_candle();
      }
      return true;
    }
    case 3: {
      current_.type = EventType::Session;
      current_.timestamp = bar_close;
      current_.session_status = SessionStatus::Close;
      set_next_candle();
      return true;
    }
    default:
      return false;
  }
}

std::vector<ReplayEvent> EventReplayEngine::snapshot() const {
  std::vector<ReplayEvent> out;
  EventReplayEngine copy(data_, mode_);
  while (copy.advance()) out.push_back(copy.current_event());
  return out;
}

std::vector<ReplayEvent> build_event_sequence(
    const MarketData& data, ReplayMode mode) {
  EventReplayEngine replay(data, mode);
  std::vector<ReplayEvent> out;
  while (replay.advance()) out.push_back(replay.current_event());
  return out;
}

} // namespace quant
