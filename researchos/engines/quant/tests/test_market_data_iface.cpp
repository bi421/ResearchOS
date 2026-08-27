#include <gtest/gtest.h>
#include "candle_factory.h"
#include "quant/backtest/market_data.h"
#include "quant/backtest/backtest_engine.h"
#include <chrono>

using namespace quant;
using namespace quant::test;

namespace {

OHLCV make_ohlcv(TimePoint tp, double price) {
  OHLCV o;
  o.timestamp = tp;
  o.open = price;
  o.high = price + 1.0;
  o.low = price - 1.0;
  o.close = price + 0.5;
  o.volume = 500.0;
  return o;
}

} // namespace

TEST(MarketDataTest, LoadValidSeries) {
  const auto candles = make_candles(10);
  MarketData md = make_market_data(candles);
  ASSERT_EQ(10u, md.size());
  EXPECT_FALSE(md.empty());
  EXPECT_EQ("TEST", md.symbol());
  EXPECT_EQ(Timeframe::M1, md.timeframe());
  EXPECT_EQ(candles.front().timestamp, md.first_time());
  EXPECT_EQ(candles.back().timestamp, md.last_time());
  EXPECT_EQ(candles[3].timestamp, md[3].timestamp);
}

TEST(MarketDataTest, LoadFromOHLCV) {
  const auto candles = make_candles(8);
  MarketData md;
  auto res = md.load("O", Timeframe::M5, candles);
  ASSERT_TRUE(res.is_ok());
  const auto ohlcv = md.to_ohlcv();
  ASSERT_EQ(8u, ohlcv.size());
  EXPECT_EQ(candles[0].close, ohlcv[0].close);
  EXPECT_EQ(md.timeframe(), Timeframe::M5);
}

TEST(MarketDataTest, LoadRejectsInvalidCandle) {
  auto candles = make_candles(3);
  candles[1].low = candles[1].high + 5.0;  // low > high → invalid
  MarketData md;
  auto res = md.load("X", Timeframe::M1, candles);
  ASSERT_TRUE(res.is_err());
}

TEST(MarketDataTest, LoadRejectsNonIncreasingTimestamps) {
  auto candles = make_candles(4);
  candles[2].timestamp = candles[1].timestamp;  // equal timestamps
  MarketData md;
  auto res = md.load("X", Timeframe::M1, candles);
  ASSERT_TRUE(res.is_err());

  candles[2].timestamp = candles[1].timestamp - std::chrono::seconds(1);
  res = md.load("X", Timeframe::M1, candles);
  ASSERT_TRUE(res.is_err());
}

TEST(MarketDataTest, AppendValidSucceeds) {
  MarketData md;
  ASSERT_TRUE(md.load("T", Timeframe::M1, make_candles(2)).is_ok());
  auto ok = md.append(make_candles(1, md.last_time() + std::chrono::minutes(1))[0]);
  ASSERT_TRUE(ok.is_ok());
  EXPECT_EQ(3u, md.size());
}

TEST(MarketDataTest, AppendRejectsOutOfOrder) {
  MarketData md;
  ASSERT_TRUE(md.load("T", Timeframe::M1, make_candles(2)).is_ok());
  auto bad = md.append(make_candles(1, md.first_time())[0]);
  ASSERT_TRUE(bad.is_err());
}

TEST(MarketDataTest, AppendRejectsInvalidCandle) {
  MarketData md;
  ASSERT_TRUE(md.load("T", Timeframe::M1, std::vector<Candle>{}).is_ok());
  auto c = make_candles(1)[0];
  c.high = 0.0;
  c.low = 100.0;
  ASSERT_TRUE(md.append(c).is_err());
}

TEST(MarketDataTest, EmptyDatasetValidates) {
  MarketData md;
  auto res = md.validate();
  ASSERT_TRUE(res.is_ok());
  EXPECT_EQ(0u, md.size());
  EXPECT_TRUE(md.empty());
}

TEST(MarketDataTest, ValidateCleanSeriesOk) {
  MarketData md = make_market_data(make_candles(100));
  ASSERT_TRUE(md.validate().is_ok());
}

TEST(MarketDataTest, ValidateRejectsStartBeforeConfig) {
  MarketData md = make_market_data(make_candles(5));
  MarketDataConfig cfg;
  cfg.symbol = "T";
  cfg.start = md.first_time() + std::chrono::hours(1);
  md.set_config(cfg);
  ASSERT_TRUE(md.validate().is_err());
}

TEST(MarketDataTest, SliceSubset) {
  const auto candles = make_candles(20);
  MarketData md = make_market_data(candles);
  auto slice = md.slice(5, 10);
  ASSERT_EQ(5u, slice.size());
  EXPECT_EQ(candles[5].timestamp, slice[0].timestamp);
  EXPECT_EQ(candles[9].timestamp, slice[4].timestamp);
}

TEST(MarketDataTest, SliceOutOfRangeReturnsEmpty) {
  MarketData md = make_market_data(make_candles(3));
  EXPECT_TRUE(md.slice(10, 20).empty());
}

TEST(MarketDataTest, ToOhlcvRoundTrip) {
  const auto candles = make_candles(5);
  MarketData md = make_market_data(candles);
  auto ohlcv = md.to_ohlcv();
  ASSERT_EQ(5u, ohlcv.size());
  for (size_t i = 0; i < ohlcv.size(); ++i) {
    EXPECT_EQ(candles[i].open, ohlcv[i].open);
    EXPECT_EQ(candles[i].close, ohlcv[i].close);
    EXPECT_EQ(candles[i].timestamp, ohlcv[i].timestamp);
  }
}

TEST(MarketDataTest, FindIndexWorks) {
  const auto candles = make_candles(10);
  MarketData md = make_market_data(candles);
  auto idx = md.find_index(candles[6].timestamp);
  ASSERT_TRUE(idx.has_value());
  EXPECT_EQ(6u, *idx);
  EXPECT_FALSE(md.find_index(candles[6].timestamp - std::chrono::seconds(30)).has_value());
}

TEST(MarketDataTest, AtThrowsOnOutOfRange) {
  MarketData md = make_market_data(make_candles(2));
  EXPECT_THROW(md.at(5), std::out_of_range);
}

TEST(MarketDataTest, MarketDataSourceAdapter) {
  const auto candles = make_candles(12);
  MarketData md = make_market_data(candles);
  MarketDataSource source(md);
  ASSERT_EQ(12u, source.size());
  EXPECT_EQ(candles[2].close, source[2].close);
  auto r = source.range(1, 4);
  ASSERT_EQ(3u, r.size());
  EXPECT_EQ(candles[3].close, r[2].close);
  EXPECT_TRUE(source.range(100, 200).empty());
}

TEST(MarketDataTest, BacktestEngineRunsOnMarketData) {
  MarketData md = make_market_data(make_candles(100));
  BacktestEngine engine;
  BacktestConfig cfg;
  cfg.initial_capital = 100'000.0;
  engine.set_config(cfg);

  auto result = engine.run(md, [](size_t, const std::vector<OHLCV>&) -> SignalResult {
    return {TradeDirection::Buy, 1.0};
  });
  ASSERT_TRUE(result.is_ok());
  EXPECT_EQ(100u, result.value().total_bars);
  EXPECT_EQ(100u, result.value().equity_curve.size());
  EXPECT_EQ(100u, result.value().bars_used.size());
}

TEST(MarketDataTest, BacktestEngineRejectsCorruptSeries) {
  auto candles = make_candles(10);
  candles[5].high = 1.0;
  candles[5].low = 99.0;
  MarketData md;
  ASSERT_TRUE(md.load("X", Timeframe::M1, candles).is_err());
}

TEST(MarketDataTest, EmptyMarketDataToBacktest) {
  MarketData md;
  BacktestEngine engine;
  auto result = engine.run(md, [](size_t, const std::vector<OHLCV>&) -> SignalResult {
    return {TradeDirection::Buy, 1.0};
  });
  ASSERT_TRUE(result.is_ok());
  EXPECT_EQ(0u, result.value().total_bars);
  EXPECT_TRUE(result.value().equity_curve.empty());
}
