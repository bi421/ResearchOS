#include <gtest/gtest.h>
#include "candle_factory.h"
#include "quant/backtest/market_data.h"
#include "quant/backtest/backtest_engine.h"
#include "quant/backtest/event_replay.h"
#include "quant/backtest/performance_analyzer.h"
#include "quant/backtest/serialization.h"
#include <cmath>

using namespace quant;
using namespace quant::test;

namespace {

quant::SignalResult naive_signal(size_t /*bar_index*/,
                                 const std::vector<OHLCV>& history) {
  quant::SignalResult s;
  if (history.empty()) return s;
  const auto& last = history.back();
  if (last.close > last.open) {
    s.direction = quant::TradeDirection::Buy;
    s.quantity = 1.0;
  }
  return s;
}

} // namespace

TEST(IntegrationTest, MarketDataToBacktestToReport) {
  MarketData md = make_market_data(make_candles(1000));
  BacktestEngine engine;
  BacktestConfig cfg;
  cfg.initial_capital = 100'000.0;
  engine.set_config(cfg);

  auto result = engine.run(md, naive_signal);
  ASSERT_TRUE(result.is_ok());
  ASSERT_EQ(1000u, result.value().equity_curve.size());

  auto report = PerformanceAnalyzer::analyze(result.value());
  EXPECT_GT(report.yearly_returns.size(), 0u);
  EXPECT_GT(report.monthly_returns.size(), 0u);
  EXPECT_GT(report.returns.size(), 0u);
  EXPECT_EQ(report.base.total_trades,
            report.base.winning_trades + report.base.losing_trades);

  auto json = serialization::report_to_json(report);
  ASSERT_TRUE(json.is_ok());
  EXPECT_NE(std::string::npos, json.value().find("\"total_return\""));
}

TEST(IntegrationTest, FullPipelineEndToEnd) {
  auto candles = make_candles(500);
  MarketData md = make_market_data(candles);

  auto csv = serialization::candles_to_csv(candles);
  ASSERT_TRUE(csv.is_ok());
  auto parsed = serialization::candles_from_csv(csv.value());
  ASSERT_TRUE(parsed.is_ok());

  MarketData md2 = make_market_data(parsed.value(), "PIPELINE");
  ASSERT_EQ(md.size(), md2.size());
  EXPECT_EQ(md.first_time(), md2.first_time());

  auto events = build_event_sequence(md2, ReplayMode::CandleTimestamp);
  auto json = serialization::events_to_json(events);
  ASSERT_TRUE(json.is_ok());
  auto parsed_events = serialization::events_from_json(json.value());
  ASSERT_TRUE(parsed_events.is_ok());
  ASSERT_EQ(events.size(), parsed_events.value().size());

  BacktestEngine engine;
  auto result = engine.run(md2, naive_signal);
  ASSERT_TRUE(result.is_ok());
  EXPECT_EQ(500u, result.value().total_bars);
}

TEST(IntegrationTest, LargeDatasetBacktest) {
  const size_t n = 100'000;
  MarketData md = make_market_data(make_candles(n));
  BacktestEngine engine;
  auto result = engine.run(md, naive_signal);
  ASSERT_TRUE(result.is_ok());
  EXPECT_EQ(n, result.value().total_bars);
  EXPECT_EQ(n, result.value().equity_curve.size());
  EXPECT_EQ(n, result.value().bars_used.size());
}

TEST(IntegrationTest, LargeDatasetReplay) {
  const size_t n = 100'000;
  MarketData md = make_market_data(make_candles(n));
  EventReplayEngine replay(md, ReplayMode::CandlesOnly);
  size_t count = 0;
  while (replay.advance()) ++count;
  EXPECT_EQ(n, count);
}

TEST(IntegrationTest, LargeDatasetSnapshotDeterminism) {
  const size_t n = 50'000;
  MarketData md = make_market_data(make_candles(n));
  auto a = build_event_sequence(md, ReplayMode::CandleTimestamp);
  auto b = build_event_sequence(md, ReplayMode::CandleTimestamp);
  ASSERT_EQ(a.size(), b.size());
  ASSERT_EQ(n * 2, a.size());
  for (size_t i = 0; i < a.size(); ++i) EXPECT_EQ(a[i], b[i]);
}

TEST(IntegrationTest, DeterministicRunTwice) {
  MarketData md = make_market_data(make_candles(200));
  BacktestEngine engine;
  auto a = engine.run(md, naive_signal);
  auto b = engine.run(md, naive_signal);
  ASSERT_TRUE(a.is_ok());
  ASSERT_TRUE(b.is_ok());
  EXPECT_DOUBLE_EQ(a.value().final_equity, b.value().final_equity);
  EXPECT_EQ(a.value().equity_curve, b.value().equity_curve);
}

TEST(IntegrationTest, EmptyDataPipelineSafe) {
  MarketData md;
  BacktestEngine engine;
  auto result = engine.run(md, naive_signal);
  ASSERT_TRUE(result.is_ok());
  auto report = PerformanceAnalyzer::analyze(result.value());
  EXPECT_TRUE(report.returns.empty());

  auto csv = serialization::candles_to_csv({});
  ASSERT_TRUE(csv.is_ok());
  auto parsed = serialization::candles_from_csv(csv.value());
  ASSERT_TRUE(parsed.is_ok());
  EXPECT_TRUE(parsed.value().empty());

  EventReplayEngine replay(md, ReplayMode::FullWithSessions);
  EXPECT_TRUE(replay.done());
}

TEST(IntegrationTest, SummaryContainsDownsideFields) {
  MarketData md = make_market_data(make_candles(300));
  BacktestEngine engine;
  auto result = engine.run(md, naive_signal);
  ASSERT_TRUE(result.is_ok());
  auto report = PerformanceAnalyzer::analyze(result.value());
  auto summary = report.base.summary();
  EXPECT_NE(std::string::npos, summary.find("Downside Dev"));
  EXPECT_NE(std::string::npos, summary.find("VaR95"));
  EXPECT_NE(std::string::npos, summary.find("Time in DD"));
}

TEST(IntegrationTest, CorruptedDataNeverReachesEngine) {
  auto candles = make_candles(10);
  candles[4] = Candle{};  // all zeros → invalid
  MarketData md;
  auto load = md.load("BAD", Timeframe::M1, candles);
  ASSERT_TRUE(load.is_err());
}

TEST(IntegrationTest, BarsUsedMatchesSource) {
  auto candles = make_candles(50);
  MarketData md = make_market_data(candles);
  BacktestEngine engine;
  auto result = engine.run(md, naive_signal);
  ASSERT_TRUE(result.is_ok());
  ASSERT_EQ(50u, result.value().bars_used.size());
  EXPECT_EQ(candles[0].timestamp, result.value().bars_used[0].timestamp);
  EXPECT_EQ(candles[49].timestamp, result.value().bars_used[49].timestamp);
}
