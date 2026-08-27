#include <gtest/gtest.h>
#include "candle_factory.h"
#include "quant/backtest/serialization.h"
#include "quant/backtest/event_replay.h"
#include "quant/backtest/performance_analyzer.h"
#include <chrono>

using namespace quant;
using namespace quant::test;

TEST(SerializationTest, CandleCsvRoundTrip) {
  const auto candles = make_candles(50);
  auto csv = serialization::candles_to_csv(candles);
  ASSERT_TRUE(csv.is_ok());
  auto parsed = serialization::candles_from_csv(csv.value());
  ASSERT_TRUE(parsed.is_ok());
  ASSERT_EQ(candles.size(), parsed.value().size());
  for (size_t i = 0; i < candles.size(); ++i) {
    EXPECT_EQ(candles[i].timestamp, parsed.value()[i].timestamp);
    EXPECT_DOUBLE_EQ(candles[i].open, parsed.value()[i].open);
    EXPECT_DOUBLE_EQ(candles[i].high, parsed.value()[i].high);
    EXPECT_DOUBLE_EQ(candles[i].low, parsed.value()[i].low);
    EXPECT_DOUBLE_EQ(candles[i].close, parsed.value()[i].close);
    EXPECT_DOUBLE_EQ(candles[i].volume, parsed.value()[i].volume);
    EXPECT_EQ(candles[i].trade_count, parsed.value()[i].trade_count);
    EXPECT_DOUBLE_EQ(candles[i].vwap, parsed.value()[i].vwap);
    EXPECT_EQ(candles[i].timeframe, parsed.value()[i].timeframe);
  }
}

TEST(SerializationTest, CandleCsvHeaderAndEmptyLines) {
  const auto candles = make_candles(3);
  auto csv = serialization::candles_to_csv(candles);
  ASSERT_TRUE(csv.is_ok());
  auto csv_with_blanks = csv.value() + "\n\n";
  auto parsed = serialization::candles_from_csv(csv_with_blanks);
  ASSERT_TRUE(parsed.is_ok());
  EXPECT_EQ(3u, parsed.value().size());
}

TEST(SerializationTest, CandleCsvRejectsMalformedRow) {
  std::string csv = "timestamp,open,high,low,close,volume,trade_count,vwap,timeframe\n";
  csv += "2020-01-01T00:00:00,100,101,99,100,1000,10,100,M1\n";
  csv += "2020-01-02T00:00:00,abc,101,99,100,1000,10,100,M1\n";
  auto parsed = serialization::candles_from_csv(csv);
  ASSERT_TRUE(parsed.is_err());
}

TEST(SerializationTest, CandleCsvRejectsMalformedTimestamp) {
  std::string csv = "not-a-date,100,101,99,100,1000,10,100,M1\n";
  auto parsed = serialization::candles_from_csv(csv);
  ASSERT_TRUE(parsed.is_err());
}

TEST(SerializationTest, CandleCsvRejectsInvalidOhlc) {
  std::string csv = "2020-01-01T00:00:00,100,50,99,100,1000,10,100,M1\n";
  auto parsed = serialization::candles_from_csv(csv);
  ASSERT_TRUE(parsed.is_err());  // high(50) < low(99) → invalid candle
}

TEST(SerializationTest, CandleCsvEmptyProducesEmpty) {
  auto parsed = serialization::candles_from_csv("");
  ASSERT_TRUE(parsed.is_ok());
  EXPECT_TRUE(parsed.value().empty());
}

TEST(SerializationTest, Iso8601RoundTrip) {
  const auto tp = std::chrono::sys_days{std::chrono::year{2021} /
                                        std::chrono::month{6} / std::chrono::day{15}} +
                  std::chrono::hours{10} + std::chrono::minutes{30} +
                  std::chrono::seconds{45};
  const auto s = serialization::to_iso8601(tp);
  EXPECT_EQ("2021-06-15T10:30:45", s);
  EXPECT_EQ(tp, serialization::from_iso8601(s));
}

TEST(SerializationTest, Iso8601Epoch) {
  const auto epoch = std::chrono::system_clock::time_point{};
  EXPECT_EQ("1970-01-01T00:00:00", serialization::to_iso8601(epoch));
}

TEST(SerializationTest, Iso8601RejectsGarbage) {
  EXPECT_EQ(TimePoint{}, serialization::from_iso8601("garbage"));
  EXPECT_EQ(TimePoint{}, serialization::from_iso8601("2020"));
}

TEST(SerializationTest, EventsJsonRoundTrip) {
  auto candles = make_candles(20);
  MarketData md = make_market_data(candles);
  auto events = build_event_sequence(md, ReplayMode::FullWithSessions);

  auto json = serialization::events_to_json(events);
  ASSERT_TRUE(json.is_ok());
  auto parsed = serialization::events_from_json(json.value());
  ASSERT_TRUE(parsed.is_ok());
  ASSERT_EQ(events.size(), parsed.value().size());
  for (size_t i = 0; i < events.size(); ++i) {
    const auto& a = events[i];
    const auto& b = parsed.value()[i];
    EXPECT_EQ(a.type, b.type);
    EXPECT_EQ(a.timestamp, b.timestamp);
    EXPECT_EQ(a.bar_index, b.bar_index);
    EXPECT_EQ(a.sequence, b.sequence);
    EXPECT_EQ(a.session_status, b.session_status);
    if (a.type == EventType::Candle) {
      EXPECT_DOUBLE_EQ(a.candle.open, b.candle.open);
      EXPECT_DOUBLE_EQ(a.candle.close, b.candle.close);
    }
  }
}

TEST(SerializationTest, EventsJsonEmptyArray) {
  auto json = serialization::events_to_json({});
  ASSERT_TRUE(json.is_ok());
  auto parsed = serialization::events_from_json(json.value());
  ASSERT_TRUE(parsed.is_ok());
  EXPECT_TRUE(parsed.value().empty());
}

TEST(SerializationTest, EventsJsonRejectsMalformedJson) {
  auto parsed = serialization::events_from_json("{not json");
  ASSERT_TRUE(parsed.is_err());
  parsed = serialization::events_from_json("{\"a\":1}");
  ASSERT_TRUE(parsed.is_err());  // object, not array
}

TEST(SerializationTest, EventsJsonRejectsUnknownType) {
  const std::string json = R"([{"seq":1,"type":"warp","time":"2020-01-01T00:00:00","bar":0}])";
  auto parsed = serialization::events_from_json(json);
  ASSERT_TRUE(parsed.is_err());
}

TEST(SerializationTest, ReportJsonContainsKeyFields) {
  BacktestResult r;
  r.config.initial_capital = 100'000.0;
  r.equity_curve = {100'000.0, 102'000.0, 101'000.0, 105'000.0};
  r.bars_used = make_ohlcv_bars(4);
  r.final_equity = 105'000.0;
  r.total_return_pct = 5.0;
  r.total_bars = 4;

  auto rep = PerformanceAnalyzer::analyze(r);
  auto json = serialization::report_to_json(rep);
  ASSERT_TRUE(json.is_ok());
  const auto& s = json.value();
  EXPECT_NE(std::string::npos, s.find("\"total_return_pct\""));
  EXPECT_NE(std::string::npos, s.find("\"sharpe_ratio\""));
  EXPECT_NE(std::string::npos, s.find("\"max_drawdown_pct\""));
  EXPECT_NE(std::string::npos, s.find("\"num_drawdown_periods\""));
  EXPECT_NE(std::string::npos, s.find("\"time_in_drawdown_pct\""));
  EXPECT_EQ('}', s.back());
}

TEST(SerializationTest, ReportJsonFlatRoundTripNumericFields) {
  PerformanceReport r;
  r.total_return_pct = 12.5;
  r.sharpe_ratio = 1.25;
  r.max_drawdown_pct = 4.2;
  r.total_trades = 42;
  r.var_95 = 0.015;
  auto json = serialization::report_to_json(r);
  ASSERT_TRUE(json.is_ok());
  EXPECT_NE(std::string::npos, json.value().find("\"total_return_pct\":12.5"));
  EXPECT_NE(std::string::npos, json.value().find("\"total_trades\":42"));
}
