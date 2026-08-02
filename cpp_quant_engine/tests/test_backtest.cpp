#include <gtest/gtest.h>
#include "quant/backtest/trade_book.h"
#include "quant/backtest/backtest_engine.h"
#include "quant/backtest/performance.h"
#include "quant/core/config.h"
#include <chrono>

using namespace quant;

auto now() { return std::chrono::system_clock::now(); }

TEST(TradeTest, OpenTradePnlZero) {
  Trade t;
  t.status = TradeStatus::Open;
  t.quantity = 100.0;
  t.entry_price = 50.0;
  EXPECT_DOUBLE_EQ(0.0, t.pnl());
}

TEST(TradeTest, LongProfitableTrade) {
  Trade t;
  t.direction = TradeDirection::Buy;
  t.quantity = 100.0;
  t.entry_price = 50.0;
  t.exit_price = 55.0;
  t.status = TradeStatus::Closed;
  EXPECT_DOUBLE_EQ(500.0, t.pnl());
  EXPECT_TRUE(t.is_profitable());
}

TEST(TradeTest, ShortProfitableTrade) {
  Trade t;
  t.direction = TradeDirection::Sell;
  t.quantity = 100.0;
  t.entry_price = 50.0;
  t.exit_price = 45.0;
  t.status = TradeStatus::Closed;
  EXPECT_DOUBLE_EQ(500.0, t.pnl());
  EXPECT_TRUE(t.is_profitable());
}

TEST(TradeTest, PnlWithCommission) {
  Trade t;
  t.direction = TradeDirection::Buy;
  t.quantity = 100.0;
  t.entry_price = 50.0;
  t.exit_price = 55.0;
  t.entry_commission = 25.0;
  t.exit_commission = 27.5;
  t.status = TradeStatus::Closed;
  EXPECT_DOUBLE_EQ(500.0 - 52.5, t.pnl());
  EXPECT_DOUBLE_EQ(52.5, t.total_commission());
}

TEST(TradeTest, DurationHours) {
  Trade t;
  t.entry_time = now();
  t.exit_time = t.entry_time + std::chrono::hours(24);
  t.status = TradeStatus::Closed;
  EXPECT_DOUBLE_EQ(24.0, t.duration_hours());
}

TEST(TradeBookTest, AddAndGetTrade) {
  TradeBook book("AAPL");
  Trade t;
  t.quantity = 100.0;
  t.entry_price = 150.0;
  book.add_trade(t);
  EXPECT_EQ("AAPL", book.symbol());
  EXPECT_EQ(1, book.total_trades());
  auto gt = book.get_trade(1);
  ASSERT_TRUE(gt.has_value());
  EXPECT_DOUBLE_EQ(100.0, gt->quantity);
}

TEST(TradeBookTest, CloseTrade) {
  TradeBook book;
  Trade t;
  t.quantity = 100.0;
  t.entry_price = 50.0;
  book.add_trade(t);
  book.close_trade(1, 55.0, now(), 0.0);
  EXPECT_EQ(1, book.closed_trades().size());
  EXPECT_TRUE(book.get_trade(1)->is_profitable());
}

TEST(TradeBookTest, CancelTrade) {
  TradeBook book;
  book.add_trade(Trade{});
  book.cancel_trade(1);
  EXPECT_TRUE(book.open_trades().empty());
}

TEST(TradeBookTest, WinRate) {
  TradeBook book;
  for (int i = 0; i < 10; ++i) {
    Trade t;
    t.direction = TradeDirection::Buy;
    t.quantity = 1.0;
    t.entry_price = 100.0;
    t.exit_price = 100.0 + (i < 6 ? 10.0 : -10.0);
    t.status = TradeStatus::Closed;
    book.add_trade(t);
  }
  EXPECT_EQ(6, book.winning_trades());
  EXPECT_EQ(4, book.losing_trades_count());
  EXPECT_DOUBLE_EQ(60.0, book.win_rate());
}

TEST(TradeBookTest, TotalPnl) {
  TradeBook book;
  for (int i = 0; i < 3; ++i) {
    Trade t;
    t.direction = TradeDirection::Buy;
    t.quantity = 1.0;
    t.entry_price = 100.0;
    t.exit_price = 110.0;
    t.status = TradeStatus::Closed;
    book.add_trade(t);
  }
  EXPECT_DOUBLE_EQ(30.0, book.total_pnl());
}

TEST(TradeBookTest, Clear) {
  TradeBook book;
  book.add_trade(Trade{});
  book.clear();
  EXPECT_EQ(0, book.total_trades());
}

TEST(BacktestEngineTest, RunWithSignal) {
  InMemoryOHLCVSource data;
  for (int i = 0; i < 100; ++i) {
    data.data.push_back(OHLCV{
      .timestamp = now(),
      .open = 100.0 + i * 0.1,
      .high = 101.0 + i * 0.1,
      .low = 99.0 + i * 0.1,
      .close = 100.5 + i * 0.1,
      .volume = 1000.0
    });
  }

  BacktestEngine engine;
  BacktestConfig cfg;
  cfg.initial_capital = 100000.0;
  cfg.commission_pct = 0.001;
  engine.set_config(cfg);

  auto result = engine.run(data, [](size_t, const std::vector<OHLCV>&) -> SignalResult {
    return {TradeDirection::Buy, 10.0};
  });

  ASSERT_TRUE(result.is_ok());
  EXPECT_GT(result.value().equity_curve.size(), 0);
  EXPECT_EQ(100, result.value().total_bars);
}

TEST(BacktestEngineTest, EmptyData) {
  InMemoryOHLCVSource data;
  BacktestEngine engine;
  auto result = engine.run(data, [](size_t, const std::vector<OHLCV>&) -> SignalResult {
    return {TradeDirection::Buy, 0.0};
  });
  ASSERT_TRUE(result.is_ok());
  EXPECT_EQ(0, result.value().total_bars);
}

TEST(PerformanceReportTest, ComputeBasic) {
  BacktestResult bt_result;
  bt_result.config.initial_capital = 100000.0;
  bt_result.final_equity = 110000.0;
  bt_result.total_return_pct = 10.0;
  bt_result.equity_curve = {100000.0, 101000.0, 102000.0, 105000.0, 110000.0};
  bt_result.total_bars = 5;
  bt_result.max_drawdown_pct = 0.0;

  auto report = PerformanceReport::compute(bt_result);
  EXPECT_GT(report.total_return, 0.0);
  EXPECT_DOUBLE_EQ(10.0, report.total_return_pct);
}

TEST(PerformanceReportTest, SummaryGenerated) {
  BacktestResult bt_result;
  bt_result.config.initial_capital = 100000.0;
  bt_result.final_equity = 105000.0;
  bt_result.total_return_pct = 5.0;
  bt_result.equity_curve = {100000.0, 105000.0};

  auto report = PerformanceReport::compute(bt_result);
  auto summary = report.summary();
  EXPECT_TRUE(summary.find("PerformanceReport") != std::string::npos);
  EXPECT_TRUE(summary.find("5.00%") != std::string::npos);
}

TEST(ConfigBacktestTest, ConfigIntegration) {
  Config cfg = Config::object();
  cfg.set("initial_capital", Config(100000.0));
  cfg.set("commission", Config(0.001));

  BacktestConfig bt_cfg;
  bt_cfg.initial_capital = cfg.get("initial_capital").value().get_double().value_or(0.0);
  bt_cfg.commission_pct = cfg.get("commission").value().get_double().value_or(0.0);

  EXPECT_DOUBLE_EQ(100000.0, bt_cfg.initial_capital);
  EXPECT_DOUBLE_EQ(0.001, bt_cfg.commission_pct);
}
