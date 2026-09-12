#include <gtest/gtest.h>

#include "quant/fast/fast_numeric.h"

TEST(FastNumeric, SimpleReturns) {
  const auto r = quant::fast::simple_returns({100.0, 110.0, 99.0});
  ASSERT_EQ(r.size(), 2u);
  EXPECT_NEAR(r[0], 0.10, 1e-12);
  EXPECT_NEAR(r[1], -0.10, 1e-12);
}

TEST(FastNumeric, Drawdown) {
  const auto dd = quant::fast::drawdown_pct({100.0, 110.0, 99.0, 121.0});
  ASSERT_EQ(dd.size(), 4u);
  EXPECT_NEAR(dd[0], 0.0, 1e-12);
  EXPECT_NEAR(dd[1], 0.0, 1e-12);
  EXPECT_NEAR(dd[2], 10.0, 1e-12);
  EXPECT_NEAR(dd[3], 0.0, 1e-12);
}

TEST(FastNumeric, LongBacktestIsCausalAndClosesAtEnd) {
  const std::vector<double> open{100, 101, 102, 103};
  const std::vector<double> close{100, 102, 103, 104};
  const std::vector<int> signal{1, 0, 0, 0};
  const std::vector<double> qty{1, 1, 1, 1};
  const auto r = quant::fast::backtest_next_open(open, close, signal, qty,
                                                   1000.0, 0.0, 0.0, false);
  EXPECT_NEAR(r.final_equity, 1003.0, 1e-12);
  EXPECT_NEAR(r.total_return_pct, 0.3, 1e-12);
  EXPECT_EQ(r.trades, 1u);
  EXPECT_EQ(r.wins, 1u);
}

TEST(FastNumeric, RiskScan) {
  const auto r = quant::fast::risk_scan({-0.10, -0.05, 0.02, 0.03, 0.04},
                                        {100, 95, 97, 99, 103});
  EXPECT_GT(r.stddev, 0.0);
  EXPECT_LT(r.sharpe, 0.0);
  EXPECT_NEAR(r.max_drawdown_pct, 5.0, 1e-12);
  EXPECT_GT(r.var95, 0.0);
  EXPECT_GT(r.cvar95, 0.0);
}

TEST(FastNumeric, RejectsMismatchedVectors) {
  EXPECT_THROW(
      quant::fast::backtest_next_open({100, 101}, {100}, {1, 0}, {1, 1},
                                      1000.0, 0.0, 0.0, false),
      std::invalid_argument);
}
