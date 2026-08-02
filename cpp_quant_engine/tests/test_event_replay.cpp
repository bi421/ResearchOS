#include <gtest/gtest.h>
#include "candle_factory.h"
#include "quant/backtest/event_replay.h"
#include <chrono>

using namespace quant;
using namespace quant::test;

namespace {

std::vector<Candle> same_day_candles(size_t n) {
  return make_candles(n);
}

MarketData multi_day_market_data(int days, size_t candles_per_day) {
  MarketData md;
  const auto start = std::chrono::system_clock::time_point{};
  std::vector<Candle> candles;
  for (int d = 0; d < days; ++d) {
    auto day_candles = make_candles(
        candles_per_day, start + std::chrono::hours(24) * d);
    candles.insert(candles.end(), day_candles.begin(), day_candles.end());
  }
  auto res = md.load("MD", Timeframe::M1, candles);
  (void)res;
  return md;
}

} // namespace

TEST(EventReplayTest, CandlesOnlyCount) {
  MarketData md = make_market_data(same_day_candles(10));
  EventReplayEngine replay(md, ReplayMode::CandlesOnly);
  size_t count = 0;
  bool all_candles = true;
  while (replay.advance()) {
    ++count;
    all_candles = all_candles && replay.current_event().type == EventType::Candle;
  }
  EXPECT_EQ(10u, count);
  EXPECT_TRUE(all_candles);
}

TEST(EventReplayTest, CandleTimestampModeCount) {
  MarketData md = make_market_data(same_day_candles(7));
  EventReplayEngine replay(md, ReplayMode::CandleTimestamp);
  size_t candles = 0, timestamps = 0;
  while (replay.advance()) {
    const auto& e = replay.current_event();
    if (e.type == EventType::Candle) ++candles;
    if (e.type == EventType::Timestamp) ++timestamps;
  }
  EXPECT_EQ(7u, candles);
  EXPECT_EQ(7u, timestamps);
}

TEST(EventReplayTest, FullWithSessionsCount) {
  MarketData md = make_market_data(same_day_candles(5));
  EventReplayEngine replay(md, ReplayMode::FullWithSessions);
  size_t candles = 0, timestamps = 0, sessions = 0;
  while (replay.advance()) {
    switch (replay.current_event().type) {
      case EventType::Candle: ++candles; break;
      case EventType::Timestamp: ++timestamps; break;
      case EventType::Session: ++sessions; break;
    }
  }
  EXPECT_EQ(5u, candles);
  EXPECT_EQ(5u, timestamps);
  EXPECT_EQ(2u, sessions);  // one open, one close (single session day)
}

TEST(EventReplayTest, DeterministicReplay) {
  MarketData md = make_market_data(same_day_candles(50));
  EventReplayEngine a(md, ReplayMode::FullWithSessions);
  EventReplayEngine b(md, ReplayMode::FullWithSessions);
  while (a.advance()) {
    ASSERT_TRUE(b.advance());
    EXPECT_EQ(a.current_event(), b.current_event());
  }
  EXPECT_FALSE(b.advance());
}

TEST(EventReplayTest, SnapshotMatchesBuildEventSequence) {
  MarketData md = make_market_data(same_day_candles(25));
  EventReplayEngine replay(md, ReplayMode::FullWithSessions);
  auto snap = replay.snapshot();
  auto built = build_event_sequence(md, ReplayMode::FullWithSessions);
  ASSERT_EQ(built.size(), snap.size());
  for (size_t i = 0; i < snap.size(); ++i) EXPECT_EQ(snap[i], built[i]);
}

TEST(EventReplayTest, SequenceNumbersMonotonic) {
  MarketData md = make_market_data(same_day_candles(20));
  EventReplayEngine replay(md, ReplayMode::CandleTimestamp);
  uint64_t expected = 1;
  while (replay.advance()) {
    EXPECT_EQ(expected, replay.current_event().sequence);
    EXPECT_EQ(expected, replay.sequence());
    ++expected;
  }
  EXPECT_EQ(40u, replay.event_count());
}

TEST(EventReplayTest, EmptyDatasetNoEvents) {
  MarketData md;
  EventReplayEngine replay(md, ReplayMode::FullWithSessions);
  EXPECT_TRUE(replay.done());
  EXPECT_FALSE(replay.advance());
  EXPECT_EQ(0u, replay.event_count());
}

TEST(EventReplayTest, SingleCandleFullSequence) {
  MarketData md = make_market_data(same_day_candles(1));
  EventReplayEngine replay(md, ReplayMode::FullWithSessions);
  ASSERT_TRUE(replay.advance());
  EXPECT_EQ(EventType::Session, replay.current_event().type);
  EXPECT_EQ(SessionStatus::Open, replay.current_event().session_status);
  ASSERT_TRUE(replay.advance());
  EXPECT_EQ(EventType::Candle, replay.current_event().type);
  ASSERT_TRUE(replay.advance());
  EXPECT_EQ(EventType::Timestamp, replay.current_event().type);
  ASSERT_TRUE(replay.advance());
  EXPECT_EQ(EventType::Session, replay.current_event().type);
  EXPECT_EQ(SessionStatus::Close, replay.current_event().session_status);
  EXPECT_FALSE(replay.advance());
}

TEST(EventReplayTest, FirstEventIsCandleInCandlesOnly) {
  MarketData md = make_market_data(same_day_candles(3));
  EventReplayEngine replay(md, ReplayMode::CandlesOnly);
  ASSERT_TRUE(replay.advance());
  EXPECT_EQ(EventType::Candle, replay.current_event().type);
  EXPECT_EQ(0u, replay.current_event().bar_index);
}

TEST(EventReplayTest, TimestampsMonotonicAndAligned) {
  const auto candles = same_day_candles(10);
  MarketData md = make_market_data(candles);
  EventReplayEngine replay(md, ReplayMode::CandleTimestamp);
  TimePoint prev{};
  bool first = true;
  while (replay.advance()) {
    const auto& e = replay.current_event();
    if (!first) EXPECT_GE(e.timestamp, prev);
    first = false;
    prev = e.timestamp;
    if (e.type == EventType::Candle) {
      EXPECT_EQ(candles[e.bar_index].timestamp, e.timestamp);
    }
    if (e.type == EventType::Timestamp) {
      EXPECT_EQ(candles[e.bar_index].timestamp + std::chrono::minutes(1),
                e.timestamp);
    }
  }
}

TEST(EventReplayTest, ResetReplaysSameStream) {
  MarketData md = make_market_data(same_day_candles(30));
  EventReplayEngine replay(md, ReplayMode::FullWithSessions);
  auto full = replay.snapshot();

  for (int i = 0; i < 7; ++i) ASSERT_TRUE(replay.advance());
  replay.reset();
  size_t i = 0;
  while (replay.advance()) {
    ASSERT_LT(i, full.size());
    EXPECT_EQ(full[i], replay.current_event());
    ++i;
  }
  EXPECT_EQ(full.size(), i);
}

TEST(EventReplayTest, SessionBoundariesAcrossDays) {
  MarketData md = multi_day_market_data(/*days=*/3, /*candles_per_day=*/5);
  EventReplayEngine replay(md, ReplayMode::FullWithSessions);
  int opens = 0, closes = 0, candles = 0;
  while (replay.advance()) {
    const auto& e = replay.current_event();
    if (e.type == EventType::Session) {
      if (e.session_status == SessionStatus::Open) ++opens;
      else ++closes;
    } else if (e.type == EventType::Candle) {
      ++candles;
    }
  }
  EXPECT_EQ(3, opens);
  EXPECT_EQ(3, closes);
  EXPECT_EQ(15, candles);
}

TEST(EventReplayTest, SessionOpenStartsEachDay) {
  MarketData md = multi_day_market_data(/*days=*/2, /*candles_per_day=*/3);
  EventReplayEngine replay(md, ReplayMode::FullWithSessions);
  size_t open_bars[2] = {0, 0};
  size_t expected_opens = 0;
  bool after_first = false;
  while (replay.advance()) {
    const auto& e = replay.current_event();
    if (e.type == EventType::Session && e.session_status == SessionStatus::Open) {
      if (after_first) open_bars[1] = e.bar_index;
      ++expected_opens;
      after_first = true;
    }
  }
  EXPECT_EQ(2u, expected_opens);
  EXPECT_EQ(3u, open_bars[1]);  // second session starts at candle 3
}

TEST(EventReplayTest, CandleEventsMatchSourceData) {
  const auto candles = same_day_candles(12);
  MarketData md = make_market_data(candles);
  EventReplayEngine replay(md, ReplayMode::CandlesOnly);
  size_t i = 0;
  while (replay.advance()) {
    ASSERT_EQ(EventType::Candle, replay.current_event().type);
    EXPECT_EQ(candles[i].timestamp, replay.current_event().candle.timestamp);
    EXPECT_EQ(candles[i].close, replay.current_event().candle.close);
    EXPECT_EQ(i, replay.current_event().bar_index);
    ++i;
  }
  EXPECT_EQ(12u, i);
}

TEST(EventReplayTest, PositionAdvances) {
  MarketData md = make_market_data(same_day_candles(6));
  EventReplayEngine replay(md, ReplayMode::CandlesOnly);
  size_t last = 0;
  while (replay.advance()) last = replay.position();
  EXPECT_EQ(6u, last);
}

TEST(EventReplayTest, SetModeResetsCursor) {
  MarketData md = make_market_data(same_day_candles(10));
  EventReplayEngine replay(md, ReplayMode::CandlesOnly);
  for (int i = 0; i < 4; ++i) ASSERT_TRUE(replay.advance());
  replay.set_mode(ReplayMode::CandleTimestamp);
  EXPECT_EQ(0u, replay.position());
  size_t count = 0;
  while (replay.advance()) ++count;
  EXPECT_EQ(20u, count);
}
