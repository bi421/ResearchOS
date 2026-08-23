#include <gtest/gtest.h>
#include "quant/market/types.h"
#include "quant/market/order_book.h"
#include <chrono>

using namespace quant;

TEST(OHLCTest, ValidBar) {
  OHLCV bar;
  bar.open = 100.0; bar.high = 110.0; bar.low = 95.0; bar.close = 105.0; bar.volume = 1000.0;
  EXPECT_TRUE(bar.is_valid());
  EXPECT_DOUBLE_EQ(15.0, bar.spread());
  EXPECT_DOUBLE_EQ(5.0, bar.change());
  EXPECT_DOUBLE_EQ(5.0, bar.change_pct());
}

TEST(OHLCTest, InvalidBar) {
  OHLCV bar;
  bar.open = 100.0; bar.high = 90.0; bar.low = 80.0; bar.close = 85.0;
  EXPECT_FALSE(bar.is_valid());
}

TEST(TickTest, Ordering) {
  Tick t1, t2;
  t1.timestamp = std::chrono::system_clock::from_time_t(100);
  t2.timestamp = std::chrono::system_clock::from_time_t(200);
  EXPECT_LT(t1, t2);
}

TEST(PositionTest, LongPnl) {
  Position p;
  p.quantity = 100.0;
  p.entry_price = 50.0;
  p.current_price = 55.0;
  EXPECT_DOUBLE_EQ(500.0, p.pnl());
  EXPECT_DOUBLE_EQ(10.0, p.pnl_pct());
  EXPECT_TRUE(p.is_long());
  EXPECT_FALSE(p.is_short());
}

TEST(PositionTest, ShortPnl) {
  Position p;
  p.quantity = -100.0;
  p.entry_price = 50.0;
  p.current_price = 45.0;
  EXPECT_DOUBLE_EQ(500.0, p.pnl());
  EXPECT_TRUE(p.is_short());
}

TEST(OrderBookTest, EmptyBook) {
  OrderBook ob("BTCUSD");
  EXPECT_EQ("BTCUSD", ob.symbol());
  EXPECT_DOUBLE_EQ(0.0, ob.best_bid());
  EXPECT_DOUBLE_EQ(0.0, ob.best_ask());
  EXPECT_DOUBLE_EQ(0.0, ob.mid_price());
  EXPECT_DOUBLE_EQ(0.0, ob.spread());
  EXPECT_EQ(0, ob.bid_depth());
  EXPECT_EQ(0, ob.ask_depth());
}

TEST(OrderBookTest, SetBidsAndAsks) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}, {99.0, 20.0, 2}});
  ob.set_asks({{101.0, 15.0, 1}, {102.0, 25.0, 2}});
  EXPECT_DOUBLE_EQ(100.0, ob.best_bid());
  EXPECT_DOUBLE_EQ(101.0, ob.best_ask());
  EXPECT_DOUBLE_EQ(100.5, ob.mid_price());
  EXPECT_DOUBLE_EQ(1.0, ob.spread());
}

TEST(OrderBookTest, UpdateBid) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}});
  ob.update_bid(100.0, 15.0);
  EXPECT_DOUBLE_EQ(15.0, ob.bids()[0].volume);
  ob.update_bid(99.0, 5.0);
  EXPECT_EQ(2, ob.bid_depth());
  EXPECT_DOUBLE_EQ(100.0, ob.best_bid());
}

TEST(OrderBookTest, UpdateBidRemove) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}});
  ob.update_bid(100.0, 0.0);
  EXPECT_EQ(0, ob.bid_depth());
}

TEST(OrderBookTest, UpdateAsk) {
  OrderBook ob;
  ob.set_asks({{101.0, 10.0, 1}});
  ob.update_ask(102.0, 5.0);
  EXPECT_EQ(2, ob.ask_depth());
}

TEST(OrderBookTest, VolumeMetrics) {
  OrderBook ob;
  ob.set_bids({{100.0, 100.0, 1}, {99.0, 50.0, 1}});
  ob.set_asks({{101.0, 80.0, 1}, {102.0, 40.0, 1}});
  EXPECT_DOUBLE_EQ(150.0, ob.bid_volume());
  EXPECT_DOUBLE_EQ(120.0, ob.ask_volume());
  EXPECT_DOUBLE_EQ((150.0 - 120.0) / 270.0, ob.imbalance());
}

TEST(OrderBookTest, WeightedMidPrice) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}, {99.0, 20.0, 1}});
  ob.set_asks({{101.0, 15.0, 1}, {102.0, 25.0, 1}});
  double wmp = ob.weighted_mid_price(2);
  EXPECT_GT(wmp, 0.0);
}

TEST(OrderBookTest, MicroPrice) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}});
  ob.set_asks({{101.0, 20.0, 1}});
  double mp = ob.micro_price();
  EXPECT_NEAR(mp, (100.0 * 20.0 + 101.0 * 10.0) / 30.0, 1e-10);
}

TEST(OrderBookTest, GetLevelOutOfRange) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}});
  auto level = ob.get_bid_level(5);
  EXPECT_FALSE(level.has_value());
}

TEST(OrderBookTest, GetLevel) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}});
  auto level = ob.get_bid_level(0);
  EXPECT_TRUE(level.has_value());
  EXPECT_DOUBLE_EQ(100.0, level->price);
}

TEST(OrderBookTest, Clear) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}});
  ob.set_asks({{101.0, 10.0, 1}});
  ob.clear();
  EXPECT_EQ(0, ob.bid_depth());
  EXPECT_EQ(0, ob.ask_depth());
}

TEST(OrderBookTest, SpreadPct) {
  OrderBook ob;
  ob.set_bids({{100.0, 10.0, 1}});
  ob.set_asks({{101.0, 10.0, 1}});
  EXPECT_DOUBLE_EQ(1.0 / 100.5 * 100.0, ob.spread_pct());
}
