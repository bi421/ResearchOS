#include <gtest/gtest.h>
#include "quant/market/candle.h"
#include "quant/market/ohlcv_container.h"
#include "quant/market/time_index.h"
#include "quant/market/data_loader.h"
#include "quant/market/timeframe_aggregator.h"
#include "quant/market/historical_iterator.h"
#include "quant/market/market_data_engine.h"
#include "quant/core/engine.h"
#include <filesystem>
#include <fstream>
#include <cmath>

using namespace quant;

auto make_time(int year, int month, int day, int hour = 0, int min = 0, int sec = 0) {
  std::tm tm = {};
  tm.tm_year = year - 1900;
  tm.tm_mon = month - 1;
  tm.tm_mday = day;
  tm.tm_hour = hour;
  tm.tm_min = min;
  tm.tm_sec = sec;
  return std::chrono::system_clock::from_time_t(std::mktime(&tm));
}

// ===== Candle Tests =====

TEST(CandleTest, DefaultConstruction) {
  Candle c;
  EXPECT_DOUBLE_EQ(0.0, c.open);
  EXPECT_DOUBLE_EQ(0.0, c.close);
  EXPECT_FALSE(c.is_valid());
}

TEST(CandleTest, BullishCandle) {
  Candle c;
  c.open = 100.0; c.high = 110.0; c.low = 95.0; c.close = 108.0;
  EXPECT_TRUE(c.is_bullish());
  EXPECT_FALSE(c.is_bearish());
  EXPECT_DOUBLE_EQ(8.0, c.body());
  EXPECT_DOUBLE_EQ(2.0, c.upper_wick());
  EXPECT_DOUBLE_EQ(5.0, c.lower_wick());
}

TEST(CandleTest, BearishCandle) {
  Candle c;
  c.open = 108.0; c.high = 110.0; c.low = 95.0; c.close = 100.0;
  EXPECT_TRUE(c.is_bearish());
  EXPECT_FALSE(c.is_bullish());
  EXPECT_DOUBLE_EQ(8.0, c.body());
  EXPECT_DOUBLE_EQ(2.0, c.upper_wick());
  EXPECT_DOUBLE_EQ(5.0, c.lower_wick());
}

TEST(CandleTest, FromOHLCV) {
  OHLCV ohlcv{make_time(2024, 1, 1), 100.0, 110.0, 95.0, 105.0, 1000.0};
  Candle c(ohlcv, Timeframe::H1);
  EXPECT_EQ(c.timestamp, ohlcv.timestamp);
  EXPECT_DOUBLE_EQ(105.0, c.close);
  EXPECT_EQ(Timeframe::H1, c.timeframe);
}

TEST(CandleTest, ToOHLCV) {
  Candle c;
  c.timestamp = make_time(2024, 1, 1);
  c.open = 100; c.high = 110; c.low = 95; c.close = 105; c.volume = 1000;
  OHLCV o = static_cast<OHLCV>(c);
  EXPECT_DOUBLE_EQ(105.0, o.close);
}

TEST(CandleTest, Validity) {
  Candle c;
  c.open = 100; c.high = 110; c.low = 95; c.close = 105; c.volume = 1000;
  EXPECT_TRUE(c.is_valid());
  c.high = 90; // invalid: high < low
  EXPECT_FALSE(c.is_valid());
}

TEST(CandleTest, TimeframeNames) {
  EXPECT_EQ("M1", timeframe_name(Timeframe::M1));
  EXPECT_EQ("H1", timeframe_name(Timeframe::H1));
  EXPECT_EQ("D1", timeframe_name(Timeframe::D1));
  EXPECT_EQ("W1", timeframe_name(Timeframe::W1));
  EXPECT_EQ("MN1", timeframe_name(Timeframe::MN1));
  EXPECT_EQ("UNK", timeframe_name(static_cast<Timeframe>(999)));
}

TEST(CandleTest, TimeframeMinutes) {
  EXPECT_EQ(1, timeframe_minutes(Timeframe::M1));
  EXPECT_EQ(5, timeframe_minutes(Timeframe::M5));
  EXPECT_EQ(60, timeframe_minutes(Timeframe::H1));
  EXPECT_EQ(1440, timeframe_minutes(Timeframe::D1));
  EXPECT_EQ(43200, timeframe_minutes(Timeframe::MN1));
}

// ===== TimeIndex Tests =====

TEST(TimeIndexTest, EmptyIndex) {
  TimeIndex idx;
  EXPECT_TRUE(idx.empty());
  EXPECT_EQ(0, idx.size());
}

TEST(TimeIndexTest, BuildAndFind) {
  TimeIndex idx;
  idx.add(make_time(2024, 1, 1, 9, 0), 0);
  idx.add(make_time(2024, 1, 1, 9, 5), 1);
  idx.add(make_time(2024, 1, 1, 9, 10), 2);
  idx.rebuild();

  auto f = idx.find(make_time(2024, 1, 1, 9, 5));
  ASSERT_TRUE(f.has_value());
  EXPECT_EQ(1, *f);

  auto missing = idx.find(make_time(2024, 1, 1, 10, 0));
  EXPECT_FALSE(missing.has_value());
}

TEST(TimeIndexTest, LowerUpperBound) {
  TimeIndex idx;
  idx.add(make_time(2024, 1, 1, 10, 0), 0);
  idx.add(make_time(2024, 1, 1, 10, 5), 1);
  idx.add(make_time(2024, 1, 1, 10, 10), 2);
  idx.add(make_time(2024, 1, 1, 10, 15), 3);

  EXPECT_EQ(0, idx.lower_bound(make_time(2024, 1, 1, 9, 0)));
  EXPECT_EQ(2, idx.lower_bound(make_time(2024, 1, 1, 10, 10)));
  EXPECT_EQ(4, idx.upper_bound(make_time(2024, 1, 1, 10, 15)));
  EXPECT_EQ(2, idx.upper_bound(make_time(2024, 1, 1, 10, 5))); // first > 10:05 is index 2
}

TEST(TimeIndexTest, Range) {
  TimeIndex idx;
  idx.add(make_time(2024, 1, 1, 10, 0), 0);
  idx.add(make_time(2024, 1, 1, 10, 5), 1);
  idx.add(make_time(2024, 1, 1, 10, 10), 2);
  idx.add(make_time(2024, 1, 1, 10, 15), 3);
  idx.rebuild();

  auto [lo, hi] = idx.range(make_time(2024, 1, 1, 10, 2), make_time(2024, 1, 1, 10, 12));
  EXPECT_EQ(1, lo);
  EXPECT_EQ(3, hi);
}

TEST(TimeIndexTest, FindClosest) {
  TimeIndex idx;
  idx.add(make_time(2024, 1, 1, 10, 0), 0);
  idx.add(make_time(2024, 1, 1, 10, 10), 1);
  idx.rebuild();

  auto c = idx.find_closest(make_time(2024, 1, 1, 10, 4));
  ASSERT_TRUE(c.has_value());
  EXPECT_EQ(0, *c);

  auto c2 = idx.find_closest(make_time(2024, 1, 1, 10, 7));
  ASSERT_TRUE(c2.has_value());
  EXPECT_EQ(1, *c2);
}

TEST(TimeIndexTest, BuildFromTimestamps) {
  std::vector<TimePoint> tps = {
    make_time(2024, 1, 1, 10, 0),
    make_time(2024, 1, 1, 10, 5),
    make_time(2024, 1, 1, 10, 10),
  };
  TimeIndex idx;
  idx.build(tps);
  EXPECT_EQ(3, idx.size());
  EXPECT_TRUE(idx.is_sorted());
}

// ===== OHLCVContainer Tests =====

TEST(OHLCVContainerTest, EmptyContainer) {
  OHLCVContainer c;
  EXPECT_TRUE(c.empty());
  EXPECT_EQ(0, c.size());
}

TEST(OHLCVContainerTest, AppendCandles) {
  OHLCVContainer c("XAUUSD", Timeframe::M1);

  Candle c1; c1.timestamp = make_time(2024, 1, 1, 9, 0);
  c1.open = 100; c1.high = 105; c1.low = 99; c1.close = 103; c1.volume = 100;

  Candle c2; c2.timestamp = make_time(2024, 1, 1, 9, 1);
  c2.open = 103; c2.high = 107; c2.low = 102; c2.close = 106; c2.volume = 150;

  EXPECT_TRUE(c.append(c1).is_ok());
  EXPECT_TRUE(c.append(c2).is_ok());
  EXPECT_EQ(2, c.size());
  EXPECT_EQ("XAUUSD", c.symbol());
  EXPECT_EQ(Timeframe::M1, c.timeframe());
}

TEST(OHLCVContainerTest, AppendRejectsOutOfOrder) {
  OHLCVContainer c;
  Candle c1; c1.timestamp = make_time(2024, 1, 1, 10, 0); c1.open = c1.high = c1.low = c1.close = 100; c1.volume = 1;
  Candle c2; c2.timestamp = make_time(2024, 1, 1, 9, 0); c2.open = c2.high = c2.low = c2.close = 100; c2.volume = 1;

  EXPECT_TRUE(c.append(c1).is_ok());
  EXPECT_TRUE(c.append(c2).is_err()); // timestamp must be increasing
}

TEST(OHLCVContainerTest, AppendRejectsInvalidCandle) {
  OHLCVContainer c;
  Candle bad; bad.timestamp = make_time(2024, 1, 1, 9, 0);
  bad.open = 100; bad.high = 90; bad.low = 95; bad.close = 105; bad.volume = 100;
  EXPECT_TRUE(c.append(bad).is_err());
}

TEST(OHLCVContainerTest, BatchAppend) {
  OHLCVContainer c;
  std::vector<Candle> batch;
  for (int i = 0; i < 100; ++i) {
    Candle candle;
    candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = candle.high = candle.low = candle.close = 100.0 + i;
    candle.volume = 100;
    batch.push_back(candle);
  }
  EXPECT_TRUE(c.append_batch(batch).is_ok());
  EXPECT_EQ(100, c.size());
}

TEST(OHLCVContainerTest, AccessByIndex) {
  OHLCVContainer c;
  Candle c1; c1.timestamp = make_time(2024, 1, 1, 9, 0); c1.open = 100; c1.high = 105; c1.low = 99; c1.close = 103; c1.volume = 100;
  c.append(c1);
  EXPECT_DOUBLE_EQ(100.0, c[0].open);
  EXPECT_THROW(c.at(100), std::out_of_range);
}

TEST(OHLCVContainerTest, SpanView) {
  OHLCVContainer c;
  for (int i = 0; i < 10; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = 100.0 + i; candle.high = 105 + i; candle.low = 99 + i;
    candle.close = 103 + i; candle.volume = 100;
    c.append(candle);
  }
  auto s = c.view(2, 4);
  EXPECT_EQ(4, s.size());
  EXPECT_DOUBLE_EQ(102.0, s[0].open);
}

TEST(OHLCVContainerTest, RangeQuery) {
  OHLCVContainer c;
  for (int i = 0; i < 10; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = 100.0 + i; candle.high = 105 + i; candle.low = 99 + i;
    candle.close = 103 + i; candle.volume = 100;
    c.append(candle);
  }
  auto sub = c.range(2, 7);
  EXPECT_EQ(5, sub.size());
  EXPECT_DOUBLE_EQ(102.0, sub[0].open);
}

TEST(OHLCVContainerTest, RangeByTime) {
  OHLCVContainer c;
  for (int i = 0; i < 10; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = 100.0 + i; candle.high = 105 + i; candle.low = 99 + i;
    candle.close = 103 + i; candle.volume = 100;
    c.append(candle);
  }
  auto sub = c.range_by_time(make_time(2024, 1, 1, 9, 2), make_time(2024, 1, 1, 9, 5));
  EXPECT_EQ(4, sub.size()); // indexes 2,3,4,5
}

TEST(OHLCVContainerTest, FindCandle) {
  OHLCVContainer c;
  Candle c1; c1.timestamp = make_time(2024, 1, 1, 9, 0); c1.open = 100; c1.high = 105; c1.low = 99; c1.close = 103; c1.volume = 100;
  c.append(c1);
  Candle c2; c2.timestamp = make_time(2024, 1, 1, 9, 5); c2.open = 103; c2.high = 107; c2.low = 102; c2.close = 106; c2.volume = 150;
  c.append(c2);

  auto found = c.find_candle(make_time(2024, 1, 1, 9, 5));
  ASSERT_TRUE(found.has_value());
  EXPECT_DOUBLE_EQ(106.0, found->close);

  auto missing = c.find_candle(make_time(2024, 1, 1, 10, 0));
  EXPECT_FALSE(missing.has_value());
}

TEST(OHLCVContainerTest, TimeBounds) {
  OHLCVContainer c;
  EXPECT_EQ(TimePoint{}, c.first_time());
  EXPECT_EQ(TimePoint{}, c.last_time());

  Candle c1; c1.timestamp = make_time(2024, 1, 1, 9, 0); c1.open = c1.high = c1.low = c1.close = 100; c1.volume = 1;
  Candle c2; c2.timestamp = make_time(2024, 1, 1, 9, 5); c2.open = c2.high = c2.low = c2.close = 101; c2.volume = 1;
  c.append(c1); c.append(c2);

  EXPECT_EQ(c1.timestamp, c.first_time());
  EXPECT_EQ(c2.timestamp, c.last_time());
}

TEST(OHLCVContainerTest, VolumeStats) {
  OHLCVContainer c;
  Candle c1; c1.timestamp = make_time(2024, 1, 1, 9, 0); c1.open = c1.high = c1.low = c1.close = 100; c1.volume = 200;
  Candle c2; c2.timestamp = make_time(2024, 1, 1, 9, 5); c2.open = c2.high = c2.low = c2.close = 101; c2.volume = 300;
  c.append(c1); c.append(c2);
  EXPECT_DOUBLE_EQ(500.0, c.total_volume());
  EXPECT_DOUBLE_EQ(250.0, c.avg_volume());
}

TEST(OHLCVContainerTest, Clear) {
  OHLCVContainer c;
  Candle c1; c1.timestamp = make_time(2024, 1, 1, 9, 0); c1.open = c1.high = c1.low = c1.close = 100; c1.volume = 1;
  c.append(c1);
  c.clear();
  EXPECT_TRUE(c.empty());
}

TEST(OHLCVContainerTest, AppendBatchLarge) {
  OHLCVContainer c;
  std::vector<Candle> batch;
  for (int i = 0; i < 10000; ++i) {
    Candle candle;
    candle.timestamp = make_time(2024, 1, 1, i / 60, i % 60);
    candle.open = candle.high = candle.low = candle.close = 100.0;
    candle.volume = 100;
    batch.push_back(candle);
  }
  auto r = c.append_batch(batch);
  EXPECT_TRUE(r.is_ok());
  EXPECT_EQ(10000, c.size());
}

// ===== DataLoader Tests (in-memory CSV) =====

TEST(DataLoaderTest, ParseCSVString) {
  auto csv = std::string_view(
    "timestamp,open,high,low,close,volume\n"
    "2024-01-01 09:00:00,100.0,105.0,99.0,103.0,1000\n"
    "2024-01-01 09:05:00,103.0,107.0,102.0,106.0,1500\n"
    "2024-01-01 09:10:00,106.0,110.0,105.0,108.0,2000\n"
  );
  LoadConfig cfg;
  auto candles = DataLoader::parse_csv_string(csv, cfg);
  ASSERT_TRUE(candles.is_ok());
  EXPECT_EQ(3, candles.value().size());
  EXPECT_DOUBLE_EQ(100.0, candles.value()[0].open);
  EXPECT_DOUBLE_EQ(106.0, candles.value()[1].close);
  EXPECT_DOUBLE_EQ(2000.0, candles.value()[2].volume);
}

TEST(DataLoaderTest, ParseCSVWithoutHeader) {
  auto csv = std::string_view(
    "2024-01-01 09:00:00,100.0,105.0,99.0,103.0,1000\n"
    "2024-01-01 09:05:00,103.0,107.0,102.0,106.0,1500\n"
  );
  LoadConfig cfg;
  cfg.has_header = false;
  auto candles = DataLoader::parse_csv_string(csv, cfg);
  ASSERT_TRUE(candles.is_ok());
  EXPECT_EQ(2, candles.value().size());
}

TEST(DataLoaderTest, ParseCSVInvalidCandle) {
  auto csv = std::string_view(
    "timestamp,open,high,low,close,volume\n"
    "2024-01-01 09:00:00,100.0,90.0,99.0,103.0,1000\n"
  );
  LoadConfig cfg;
  auto candles = DataLoader::parse_csv_string(csv, cfg);
  EXPECT_TRUE(candles.is_err()); // high < low
}

TEST(DataLoaderTest, ParseCSVDifferentDelimiter) {
  auto csv = std::string_view(
    "timestamp;open;high;low;close;volume\n"
    "2024-01-01 09:00:00;100.0;105.0;99.0;103.0;1000\n"
  );
  LoadConfig cfg;
  cfg.delimiter = ';';
  auto candles = DataLoader::parse_csv_string(csv, cfg);
  ASSERT_TRUE(candles.is_ok());
  EXPECT_EQ(1, candles.value().size());
}

TEST(DataLoaderTest, DateTimeParsing) {
  auto tp = DataLoader::parse_datetime("2024-01-15 14:30:00");
  // Verify it parsed to a valid non-zero timestamp (avoids timezone sensitivity)
  EXPECT_NE(TimePoint{}, tp);
  auto expected = make_time(2024, 1, 15, 14, 30, 0);
  auto diff = std::chrono::duration_cast<std::chrono::seconds>(tp - expected).count();
  EXPECT_NEAR(0, diff, 86400); // within a day (timezone offset safe)
}

TEST(DataLoaderTest, DateTimeFormatting) {
  auto tp = make_time(2024, 6, 15, 10, 30, 0);
  auto s = DataLoader::format_datetime(tp, "%Y-%m-%d");
  EXPECT_EQ("2024-06-15", s);
}

// ===== TimeframeAggregator Tests =====

TEST(TimeframeAggregatorTest, CanAggregate) {
  EXPECT_TRUE(TimeframeAggregator::can_aggregate(Timeframe::M1, Timeframe::M5));
  EXPECT_TRUE(TimeframeAggregator::can_aggregate(Timeframe::M5, Timeframe::H1));
  EXPECT_TRUE(TimeframeAggregator::can_aggregate(Timeframe::M1, Timeframe::D1));
  EXPECT_FALSE(TimeframeAggregator::can_aggregate(Timeframe::H1, Timeframe::M5));
}

TEST(TimeframeAggregatorTest, MinutesBetween) {
  EXPECT_EQ(5, TimeframeAggregator::minutes_between(Timeframe::M1, Timeframe::M5));
  EXPECT_EQ(12, TimeframeAggregator::minutes_between(Timeframe::M5, Timeframe::H1));
  EXPECT_EQ(0, TimeframeAggregator::minutes_between(Timeframe::H1, Timeframe::M5));
}

TEST(TimeframeAggregatorTest, AggregateM1toM5) {
  OHLCVContainer source;
  for (int i = 0; i < 10; ++i) {
    Candle c; c.timestamp = make_time(2024, 1, 1, 9, i);
    c.open = 100.0 + i * 0.5;
    c.high = 105.0 + i;
    c.low = 98.0;
    c.close = 100.0 + (i + 1) * 0.5;
    c.volume = 100.0;
    source.append(c);
  }

  auto agg = TimeframeAggregator::aggregate(source, Timeframe::M5);
  ASSERT_TRUE(agg.is_ok());
  EXPECT_EQ(2, agg.value().size());
  EXPECT_DOUBLE_EQ(100.0, agg.value()[0].open);
  // chunk 0-4 closes: 100.5,101.0,101.5,102.0,102.5 -> last close = 102.5
  // chunk 5-9 closes: 103.0,103.5,104.0,104.5,105.0 -> last close = 105.0
  EXPECT_DOUBLE_EQ(102.5, agg.value()[0].close);
  EXPECT_DOUBLE_EQ(105.0, agg.value()[1].close);
}

TEST(TimeframeAggregatorTest, AggregateEmptySource) {
  OHLCVContainer empty;
  auto r = TimeframeAggregator::aggregate(empty, Timeframe::H1);
  EXPECT_TRUE(r.is_err());
}

TEST(TimeframeAggregatorTest, AggregateDivisible) {
  OHLCVContainer source;
  for (int i = 0; i < 12; ++i) {
    Candle c; c.timestamp = make_time(2024, 1, 1, 9, i * 5);
    c.open = c.high = c.low = c.close = 100.0; c.volume = 100;
    source.append(c);
  }
  source = TimeframeAggregator::aggregate(source, Timeframe::H1).value();
  EXPECT_EQ(1, source.size());
}

TEST(TimeframeAggregatorTest, AggregateTimestampAlignment) {
  OHLCVContainer source;
  for (int i = 0; i < 5; ++i) {
    Candle c; c.timestamp = make_time(2024, 1, 1, 9, i);
    c.open = c.high = c.low = c.close = 100.0; c.volume = 100;
    source.append(c);
  }
  auto agg = TimeframeAggregator::aggregate(source, Timeframe::M5);
  ASSERT_TRUE(agg.is_ok());
  EXPECT_EQ(1, agg.value().size());
  auto expected_ts = TimeframeAggregator::align_timestamp(
    make_time(2024, 1, 1, 9, 0), 5);
  EXPECT_EQ(expected_ts, agg.value()[0].timestamp);
}

TEST(TimeframeAggregatorTest, AggregateToMultiple) {
  OHLCVContainer source;
  for (int i = 0; i < 30; ++i) {
    Candle c; c.timestamp = make_time(2024, 1, 1, 9, i);
    c.open = c.high = c.low = c.close = 100.0; c.volume = 100;
    source.append(c);
  }
  auto r = TimeframeAggregator::aggregate_to_multiple(source,
    {Timeframe::M15, Timeframe::M30});
  ASSERT_TRUE(r.is_ok());
  EXPECT_EQ(2, r.value().size());
}

// ===== HistoricalIterator Tests =====

TEST(HistoricalIteratorTest, IterateForward) {
  OHLCVContainer c;
  std::vector<Candle> batch;
  for (int i = 0; i < 5; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = 100.0 + i; candle.high = 105 + i; candle.low = 99 + i;
    candle.close = 103 + i; candle.volume = 100;
    batch.push_back(candle);
  }
  c.append_batch(batch);

  HistoricalIterator it(&c, 0);
  EXPECT_EQ(100.0, it->open);
  ++it;
  EXPECT_EQ(101.0, (*it).open);
}

TEST(HistoricalIteratorTest, IterateBackward) {
  OHLCVContainer c;
  for (int i = 0; i < 5; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = 100.0 + i; candle.high = 105 + i; candle.low = 99 + i;
    candle.close = 103 + i; candle.volume = 100;
    c.append(candle);
  }
  HistoricalIterator it(&c, 4);
  EXPECT_DOUBLE_EQ(104.0, it->open);
  --it;
  EXPECT_DOUBLE_EQ(103.0, it->open);
}

TEST(HistoricalIteratorTest, RandomAccess) {
  OHLCVContainer c;
  for (int i = 0; i < 10; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = 100.0 + i; candle.close = 103 + i; candle.volume = 100;
    candle.high = 105 + i; candle.low = 99 + i;
    c.append(candle);
  }
  HistoricalIterator it(&c, 0);
  EXPECT_DOUBLE_EQ(105.0, (it + 5)->open);
  EXPECT_DOUBLE_EQ(103.0, it[3].open);
}

TEST(HistoricalIteratorTest, IteratorDifference) {
  OHLCVContainer c;
  for (int i = 0; i < 10; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = 100.0 + i; candle.close = 103 + i; candle.volume = 100;
    candle.high = 105 + i; candle.low = 99 + i;
    c.append(candle);
  }
  HistoricalIterator it1(&c, 2);
  HistoricalIterator it2(&c, 7);
  EXPECT_EQ(5, it2 - it1);
}

TEST(HistoricalIteratorTest, HistoricalRange) {
  OHLCVContainer c;
  for (int i = 0; i < 10; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, i);
    candle.open = 100.0 + i; candle.close = 103 + i; candle.volume = 100;
    candle.high = 105 + i; candle.low = 99 + i;
    c.append(candle);
  }
  HistoricalRange range(c, 3, 7);
  EXPECT_EQ(4, range.size());
  auto vec = range.to_vector();
  EXPECT_EQ(4, vec.size());
  EXPECT_DOUBLE_EQ(103.0, vec[0].open);
}

// ===== MarketDataEngine Tests =====

TEST(MarketDataEngineTest, RegisterAndRetrieve) {
  MarketDataEngine mde;
  OHLCVContainer c("XAUUSD", Timeframe::M1);
  Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, 0);
  candle.open = candle.high = candle.low = candle.close = 100; candle.volume = 100;
  c.append(candle);

  mde.register_series("XAUUSD", Timeframe::M1, std::move(c));
  EXPECT_TRUE(mde.has_series("XAUUSD", Timeframe::M1));
  EXPECT_FALSE(mde.has_series("XAUUSD", Timeframe::H1));

  auto retrieved = mde.get_series("XAUUSD", Timeframe::M1);
  ASSERT_TRUE(retrieved.is_ok());
  EXPECT_EQ(1, retrieved.value().size());
}

TEST(MarketDataEngineTest, GetMissingSeries) {
  MarketDataEngine mde;
  auto r = mde.get_series("BTCUSD", Timeframe::H1);
  EXPECT_TRUE(r.is_err());
}

TEST(MarketDataEngineTest, Symbols) {
  MarketDataEngine mde;
  mde.register_series("XAUUSD", Timeframe::M1, OHLCVContainer("XAUUSD", Timeframe::M1));
  mde.register_series("XAGUSD", Timeframe::M1, OHLCVContainer("XAGUSD", Timeframe::M1));
  auto syms = mde.symbols();
  EXPECT_EQ(2, syms.size());
}

TEST(MarketDataEngineTest, AvailableTimeframes) {
  MarketDataEngine mde;
  mde.register_series("XAUUSD", Timeframe::M1, OHLCVContainer("XAUUSD", Timeframe::M1));
  mde.register_series("XAUUSD", Timeframe::H1, OHLCVContainer("XAUUSD", Timeframe::H1));
  auto tfs = mde.available_timeframes("XAUUSD");
  EXPECT_EQ(2, tfs.size());
  EXPECT_EQ(0, mde.available_timeframes("BTCUSD").size());
}

TEST(MarketDataEngineTest, LoadFromFileDoesNotCrashOnMissingFile) {
  MarketDataEngine mde;
  auto r = mde.load_from_file("nonexistent_file.csv");
  EXPECT_TRUE(r.is_err());
}

TEST(MarketDataEngineTest, Clear) {
  MarketDataEngine mde;
  mde.register_series("XAUUSD", Timeframe::M1, OHLCVContainer("XAUUSD", Timeframe::M1));
  EXPECT_EQ(1, mde.total_series());
  mde.clear();
  EXPECT_EQ(0, mde.total_series());
}

TEST(MarketDataEngineTest, AggregationViaEngine) {
  MarketDataEngine mde;
  OHLCVContainer source("XAUUSD", Timeframe::M1);
  for (int i = 0; i < 10; ++i) {
    Candle c; c.timestamp = make_time(2024, 1, 1, 9, i);
    c.open = c.high = c.low = c.close = 100.0; c.volume = 100;
    source.append(c);
  }
  mde.register_series("XAUUSD", Timeframe::M1, std::move(source));

  auto agg = mde.aggregate("XAUUSD", Timeframe::M1, Timeframe::M5);
  ASSERT_TRUE(agg.is_ok());
  EXPECT_EQ(2, agg.value().size());

  // Check caching: second call returns same data
  auto agg2 = mde.aggregate("XAUUSD", Timeframe::M1, Timeframe::M5);
  ASSERT_TRUE(agg2.is_ok());
  EXPECT_EQ(2, agg2.value().size());
}

// ===== QuantEngine Integration Test =====

TEST(QuantEngineMarketTest, EngineProvidesMarketDataAccess) {
  QuantEngine engine;
  Config cfg = Config::object();
  auto r = engine.initialize(cfg);
  ASSERT_TRUE(r.is_ok());

  auto& mde = engine.market_data();
  EXPECT_EQ(0, mde.total_series());

  OHLCVContainer c("XAUUSD", Timeframe::M1);
  Candle candle; candle.timestamp = make_time(2024, 1, 1, 9, 0);
  candle.open = 2000; candle.high = 2010; candle.low = 1990;
  candle.close = 2005; candle.volume = 5000;
  c.append(candle);
  mde.register_series("XAUUSD", Timeframe::M1, std::move(c));

  auto series = mde.get_series("XAUUSD", Timeframe::M1);
  ASSERT_TRUE(series.is_ok());
  EXPECT_DOUBLE_EQ(2000.0, series.value()[0].open);
}

// ===== Timestamp Ordering Test =====

TEST(TimestampOrderingTest, StrictlyIncreasing) {
  OHLCVContainer c;
  TimePoint last;
  for (int i = 0; i < 100; ++i) {
    Candle candle; candle.timestamp = make_time(2024, 1, 1, i / 60, i % 60);
    candle.open = 100; candle.high = 105; candle.low = 95;
    candle.close = 101; candle.volume = 100;
    if (i > 0) EXPECT_LT(last, candle.timestamp);
    last = candle.timestamp;
    EXPECT_TRUE(c.append(candle).is_ok());
  }
  EXPECT_EQ(100, c.size());
}

// ===== Large Dataset Performance Test =====

TEST(LargeDatasetTest, Append100KCandles) {
  OHLCVContainer c("XAUUSD", Timeframe::M1);
  std::vector<Candle> batch;
  batch.reserve(100000);
  for (int i = 0; i < 100000; ++i) {
    Candle candle;
    candle.timestamp = make_time(2024, 1, i / 1440 + 1, (i % 1440) / 60, i % 60);
    candle.open = 2000.0 + (std::sin(i * 0.01) * 10.0);
    candle.high = candle.open + 5.0;
    candle.low = candle.open - 5.0;
    candle.close = candle.open + (std::cos(i * 0.01) * 3.0);
    candle.volume = 1000.0 + (i % 1000);
    batch.push_back(candle);
  }
  auto start = std::chrono::steady_clock::now();
  auto r = c.append_batch(batch);
  auto end = std::chrono::steady_clock::now();
  ASSERT_TRUE(r.is_ok());
  EXPECT_EQ(100000, c.size());

  auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
  EXPECT_LT(elapsed, 5000); // should be well under 5s

  // Verify index works on large data
  auto idx = c.find_index(make_time(2024, 2, 1));
  EXPECT_TRUE(idx.has_value());
}

TEST(LargeDatasetTest, RangeQuery100K) {
  OHLCVContainer c("XAUUSD", Timeframe::M1);
  for (int i = 0; i < 100000; ++i) {
    Candle candle;
    candle.timestamp = make_time(2024, 1, i / 1440 + 1, (i % 1440) / 60, i % 60);
    candle.open = 2000.0; candle.high = 2005.0; candle.low = 1995.0;
    candle.close = 2002.0; candle.volume = 1000.0;
    c.append(candle);
  }
  auto start = std::chrono::steady_clock::now();
  auto sub = c.range_by_time(make_time(2024, 1, 15), make_time(2024, 1, 20));
  auto end = std::chrono::steady_clock::now();
  EXPECT_GT(sub.size(), 0);
  auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
  EXPECT_LT(elapsed, 1000);
}

TEST(LargeDatasetTest, Aggregate100K) {
  OHLCVContainer c("XAUUSD", Timeframe::M5);
  for (int i = 0; i < 100000; ++i) {
    Candle candle;
    candle.timestamp = make_time(2024, 1, i / 288 + 1, (i % 288) / 12, (i % 12) * 5);
    candle.open = 2000.0; candle.high = 2005.0; candle.low = 1995.0;
    candle.close = 2002.0; candle.volume = 1000.0;
    c.append(candle);
  }
  auto start = std::chrono::steady_clock::now();
  auto agg = TimeframeAggregator::aggregate(c, Timeframe::H1);
  auto end = std::chrono::steady_clock::now();
  ASSERT_TRUE(agg.is_ok());
  EXPECT_GT(agg.value().size(), 0);
  auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
  EXPECT_LT(elapsed, 5000);
}
