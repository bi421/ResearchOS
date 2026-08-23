#include <gtest/gtest.h>
#include "candle_factory.h"
#include "quant/backtest/performance_analyzer.h"
#include "quant/backtest/backtest_engine.h"
#include <cmath>
#include <chrono>

using namespace quant;
using namespace quant::test;

namespace {

TimePoint at_date(int y, int m, int d) {
  return std::chrono::sys_days{
      std::chrono::year{y} / std::chrono::month{static_cast<unsigned>(m)} /
      std::chrono::day{static_cast<unsigned>(d)}};
}

BacktestResult make_result(const std::vector<double>& equity,
                           const std::vector<OHLCV>& bars,
                           double initial_capital) {
  BacktestResult r;
  r.config.initial_capital = initial_capital;
  r.equity_curve = equity;
  r.bars_used = bars;
  r.final_equity = equity.empty() ? initial_capital : equity.back();
  r.total_bars = bars.size();
  r.total_return_pct =
      initial_capital > 0.0
          ? (r.final_equity - initial_capital) / initial_capital * 100.0
          : 0.0;
  return r;
}

} // namespace

TEST(PerformanceAnalyzerTest, NoDrawdownForMonotonic) {
  auto periods = PerformanceAnalyzer::drawdown_periods({100, 102, 104, 106, 108});
  EXPECT_TRUE(periods.empty());
}

TEST(PerformanceAnalyzerTest, SingleDrawdownDetected) {
  auto periods = PerformanceAnalyzer::drawdown_periods({100, 120, 100, 90, 120});
  ASSERT_EQ(1u, periods.size());
  const auto& d = periods[0];
  EXPECT_DOUBLE_EQ(120.0, d.peak);
  EXPECT_DOUBLE_EQ(90.0, d.trough);
  EXPECT_EQ(1u, d.start_index);
  EXPECT_EQ(3u, d.trough_index);
  EXPECT_EQ(4u, d.end_index);
  EXPECT_TRUE(d.recovered);
  EXPECT_DOUBLE_EQ(25.0, d.max_drawdown_pct);
  EXPECT_EQ(3u, d.length_bars);
}

TEST(PerformanceAnalyzerTest, MultipleDrawdowns) {
  auto periods = PerformanceAnalyzer::drawdown_periods({100, 110, 90, 100, 130, 120});
  ASSERT_EQ(2u, periods.size());
  EXPECT_DOUBLE_EQ(18.18181818181818, periods[0].max_drawdown_pct);
  EXPECT_TRUE(periods[0].recovered);
  EXPECT_FALSE(periods[1].recovered);
  EXPECT_EQ(6u, periods[1].end_index);
  EXPECT_DOUBLE_EQ(7.692307692307692, periods[1].max_drawdown_pct);
}

TEST(PerformanceAnalyzerTest, UnrecoveredDrawdownEndsAtSeriesEnd) {
  auto periods = PerformanceAnalyzer::drawdown_periods({100, 90, 80, 85});
  ASSERT_EQ(1u, periods.size());
  EXPECT_FALSE(periods[0].recovered);
  EXPECT_EQ(4u, periods[0].end_index);
  EXPECT_EQ(0u, periods[0].start_index);
  EXPECT_DOUBLE_EQ(20.0, periods[0].max_drawdown_pct);
}

TEST(PerformanceAnalyzerTest, DrawdownLengthBars) {
  auto periods = PerformanceAnalyzer::drawdown_periods({100, 95, 90, 92, 100, 101});
  ASSERT_EQ(1u, periods.size());
  EXPECT_EQ(0u, periods[0].start_index);
  EXPECT_EQ(4u, periods[0].end_index);
  EXPECT_EQ(4u, periods[0].length_bars);
}

TEST(PerformanceAnalyzerTest, DownsideMetricsWithNegativeReturns) {
  auto m = PerformanceAnalyzer::downside_metrics({0.01, -0.02, 0.03, -0.01, 0.02});
  EXPECT_DOUBLE_EQ(0.01, m.downside_deviation);  // sqrt(0.0005 / 5)
  EXPECT_GT(m.downside_deviation_annualized, 0.0);
  EXPECT_GT(m.var_95, 0.0);
  EXPECT_GT(m.var_99, 0.0);
  EXPECT_GT(m.cvar_95, 0.0);
  EXPECT_GT(m.annualized_volatility, 0.0);
}

TEST(PerformanceAnalyzerTest, DownsideMetricsNoNegativeReturns) {
  auto m = PerformanceAnalyzer::downside_metrics({0.01, 0.02, 0.015});
  EXPECT_DOUBLE_EQ(0.0, m.downside_deviation);
  EXPECT_DOUBLE_EQ(0.0, m.downside_deviation_annualized);
}

TEST(PerformanceAnalyzerTest, DownsideMetricsEmpty) {
  auto m = PerformanceAnalyzer::downside_metrics({});
  EXPECT_DOUBLE_EQ(0.0, m.downside_deviation);
  EXPECT_DOUBLE_EQ(0.0, m.var_95);
  EXPECT_DOUBLE_EQ(0.0, m.annualized_volatility);
}

TEST(PerformanceAnalyzerTest, DownsideMetricsVaROrdering) {
  std::vector<double> returns(95, 0.001);
  returns.push_back(-0.05);
  returns.push_back(-0.05);
  returns.push_back(-0.05);
  returns.push_back(-0.05);
  returns.push_back(-0.05);
  auto m = PerformanceAnalyzer::downside_metrics(returns);
  EXPECT_GT(m.var_99, m.var_95);
  EXPECT_GT(m.cvar_99, m.cvar_95);
}

TEST(PerformanceAnalyzerTest, YearlyReturnsBuckets) {
  std::vector<OHLCV> bars;
  bars.push_back(OHLCV{at_date(2020, 1, 1), 100, 101, 99, 100, 1});
  bars.push_back(OHLCV{at_date(2020, 6, 1), 100, 101, 99, 105, 1});
  bars.push_back(OHLCV{at_date(2021, 1, 1), 105, 106, 104, 110, 1});
  bars.push_back(OHLCV{at_date(2021, 7, 1), 110, 111, 109, 120, 1});
  auto yearly = PerformanceAnalyzer::yearly_returns(
      {100, 105, 110, 120}, bars, /*initial_capital=*/100.0);
  ASSERT_EQ(2u, yearly.size());
  EXPECT_EQ(2020, yearly[0].year);
  EXPECT_FALSE(yearly[0].monthly);
  EXPECT_NEAR(5.0, yearly[0].return_pct, 1e-9);
  EXPECT_EQ(2u, yearly[0].bars);
  EXPECT_EQ(2021, yearly[1].year);
  EXPECT_NEAR((120.0 - 105.0) / 105.0 * 100.0, yearly[1].return_pct, 1e-9);
}

TEST(PerformanceAnalyzerTest, MonthlyReturnsBuckets) {
  std::vector<OHLCV> bars;
  bars.push_back(OHLCV{at_date(2020, 1, 15), 100, 101, 99, 100, 1});
  bars.push_back(OHLCV{at_date(2020, 1, 30), 100, 101, 99, 105, 1});
  bars.push_back(OHLCV{at_date(2020, 2, 15), 105, 106, 104, 110, 1});
  bars.push_back(OHLCV{at_date(2020, 3, 15), 110, 111, 109, 125, 1});
  auto monthly = PerformanceAnalyzer::monthly_returns(
      {100, 105, 110, 125}, bars, /*initial_capital=*/100.0);
  ASSERT_EQ(3u, monthly.size());
  EXPECT_TRUE(monthly[0].monthly);
  EXPECT_EQ(1, monthly[0].month);
  EXPECT_NEAR(5.0, monthly[0].return_pct, 1e-9);
  EXPECT_EQ(2u, monthly[0].bars);
  EXPECT_EQ(2, monthly[1].month);
  EXPECT_NEAR((110.0 - 105.0) / 105.0 * 100.0, monthly[1].return_pct, 1e-9);
  EXPECT_EQ(3, monthly[2].month);
  EXPECT_NEAR((125.0 - 110.0) / 110.0 * 100.0, monthly[2].return_pct, 1e-9);
}

TEST(PerformanceAnalyzerTest, AnalyzePopulatesDetailedReport) {
  auto candles = make_candles(120);
  MarketData md = make_market_data(candles);
  BacktestEngine engine;
  auto result = engine.run(md, [](size_t, const std::vector<OHLCV>& h) -> SignalResult {
    if (h.size() < 2) return {};
    const auto& last = h.back();
    SignalResult s;
    if (last.close > last.open) {
      s.direction = TradeDirection::Buy;
      s.quantity = 1.0;
    }
    return s;
  });
  ASSERT_TRUE(result.is_ok());

  auto rep = PerformanceAnalyzer::analyze(result.value());
  EXPECT_GT(rep.returns.size(), 0u);
  EXPECT_EQ(rep.base.total_trades, rep.base.total_trades);
  EXPECT_GE(rep.base.downside_deviation, 0.0);
  EXPECT_GE(rep.base.var_95, 0.0);
  EXPECT_GE(rep.base.max_drawdown_recovery_bars, 0u);
  EXPECT_GE(rep.time_in_drawdown_pct, 0.0);
  EXPECT_LE(rep.time_in_drawdown_pct, 100.0);
}

TEST(PerformanceAnalyzerTest, AnalyzeEmptyEquityNoCrash) {
  BacktestResult r;
  r.config.initial_capital = 1000.0;
  r.bars_used = {};
  auto rep = PerformanceAnalyzer::analyze(r);
  EXPECT_TRUE(rep.returns.empty());
  EXPECT_TRUE(rep.drawdowns.empty());
  EXPECT_DOUBLE_EQ(0.0, rep.time_in_drawdown_pct);
}

TEST(PerformanceAnalyzerTest, TimeInDrawdownPct) {
  std::vector<OHLCV> bars;
  for (int i = 0; i < 5; ++i)
    bars.push_back(OHLCV{at_date(2020, 1, 1) + std::chrono::days(i), 100, 101, 99, 100, 1});
  auto rep = PerformanceAnalyzer::analyze(make_result(
      {100, 95, 90, 95, 110}, bars, 100.0));
  // Underwater bars: indices 1..3 (below running max of 100) → 3 of 5 bars.
  EXPECT_NEAR(60.0, rep.time_in_drawdown_pct, 1e-9);
  EXPECT_EQ(3u, rep.total_underwater_bars);
}

TEST(PerformanceAnalyzerTest, MaxDrawdownRecoveryBars) {
  std::vector<OHLCV> bars;
  for (int i = 0; i < 6; ++i)
    bars.push_back(OHLCV{at_date(2020, 1, 1) + std::chrono::days(i), 100, 101, 99, 100, 1});
  auto rep = PerformanceAnalyzer::analyze(make_result(
      {100, 90, 80, 100, 110, 105}, bars, 100.0));
  // Trough at index 2, recovery at index 3 → recovery of 1 bar; end-of-series
  // dip at index 5 is still underwater from index 4's peak.
  EXPECT_EQ(1u, rep.max_drawdown_recovery_bars);
}

TEST(PerformanceAnalyzerTest, AnalyzerMatchesRiskMetrics) {
  const std::vector<double> equity{100, 120, 100, 90, 120, 110};
  auto periods = PerformanceAnalyzer::drawdown_periods(equity);
  auto dd = RiskMetrics::max_drawdown(equity);
  ASSERT_FALSE(periods.empty());
  ASSERT_TRUE(dd.is_ok());
  EXPECT_NEAR(dd.value().max_drawdown_pct, periods[0].max_drawdown_pct, 1e-9);
}

TEST(PerformanceAnalyzerTest, AverageDrawdownRecovery) {
  std::vector<OHLCV> bars;
  for (int i = 0; i < 6; ++i)
    bars.push_back(OHLCV{at_date(2020, 1, 1) + std::chrono::days(i), 100, 101, 99, 100, 1});
  auto rep = PerformanceAnalyzer::analyze(make_result(
      {100, 80, 100, 90, 110, 100}, bars, 100.0));
  EXPECT_GT(rep.average_drawdown_recovery_bars, 0.0);
}
