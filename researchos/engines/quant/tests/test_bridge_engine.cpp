#include <gtest/gtest.h>
#include "bridge_test_util.h"
#include "bridge_interface.h"
#include <chrono>
#include <cmath>

using namespace quant;
using namespace quant::bridge;
using namespace quant::bridge::test;

namespace {

const auto kStart = std::chrono::system_clock::time_point{};

std::shared_ptr<IBridgeBackend> make_backend() { return create_backend(); }

TEST(BridgeEngine, MetaVersionAndProtocol) {
  auto backend = make_backend();
  const auto meta = backend->meta();
  EXPECT_EQ(kBridgeName, meta.engine_name);
  EXPECT_EQ(kBridgeVersion, meta.bridge_version);
  EXPECT_EQ(kBridgeProtocolVersion, meta.protocol_version);
  EXPECT_EQ(kDefaultCalculationVersion, meta.calculation_version);
  EXPECT_FALSE(meta.engine_version.empty());
  EXPECT_EQ(meta.engine_version, backend->version());
}

TEST(BridgeEngine, StatisticsMatchesEngine) {
  auto backend = make_backend();
  StatisticsRequest req;
  req.data = {1.0, 2.0, 3.0, 4.0, 5.0};
  const auto res = backend->statistics_compute(req);
  EXPECT_EQ(5u, res.count);
  EXPECT_DOUBLE_EQ(3.0, res.mean);
  EXPECT_DOUBLE_EQ(2.0, res.variance);
  EXPECT_DOUBLE_EQ(std::sqrt(2.0), res.stddev);
  EXPECT_DOUBLE_EQ(1.0, res.min);
  EXPECT_DOUBLE_EQ(5.0, res.max);
  EXPECT_DOUBLE_EQ(3.0, res.median);
  EXPECT_EQ(64u, res.input_hash.size());
  EXPECT_EQ(64u, res.result_hash.size());
  EXPECT_EQ(res.result_hash, res.compute_result_hash());
}

TEST(BridgeEngine, StatisticsDeterministic) {
  auto backend = make_backend();
  StatisticsRequest req;
  req.data = {1.5, -2.0, 0.25, 3.75, 9.0, -4.5};
  const auto a = backend->statistics_compute(req);
  const auto b = backend->statistics_compute(req);
  EXPECT_EQ(a.input_hash, b.input_hash);
  EXPECT_EQ(a.result_hash, b.result_hash);
  EXPECT_DOUBLE_EQ(a.mean, b.mean);
  EXPECT_EQ(a.result_hash, a.compute_result_hash());
}

TEST(BridgeEngine, RiskKnownDrawdown) {
  auto backend = make_backend();
  RiskRequest req;
  req.returns = {0.01, -0.02, 0.03, -0.01, 0.005};
  req.equity_curve = {100.0, 105.0, 102.0, 99.0, 101.0, 100.0};
  const auto res = backend->risk_compute(req);
  EXPECT_EQ(64u, res.input_hash.size());
  EXPECT_EQ(64u, res.result_hash.size());
  EXPECT_EQ(res.result_hash, res.compute_result_hash());
  // Peak 105 -> trough 99 => 5.7142857...% (reported as positive magnitude)
  EXPECT_NEAR(5.7142857143, res.max_drawdown_pct, 1e-6);
  EXPECT_EQ(1u, res.peak_index);
  EXPECT_EQ(3u, res.trough_index);
  EXPECT_NE(0.0, res.var_95);
  EXPECT_NE(0.0, res.cvar_95);
}

TEST(BridgeEngine, SimulationBasicShapeAndHashes) {
  auto backend = make_backend();
  SimulationRequest req;
  req.dataset_reference = "XAUUSD";
  req.prices = {100.0, 101.0, 102.0, 101.5, 103.0};
  const auto res = backend->simulation_run(req);
  EXPECT_EQ(4u, res.returns.size());       // n - 1
  EXPECT_EQ(5u, res.equity_curve.size());  // n
  EXPECT_DOUBLE_EQ(100'000.0, res.equity_curve.front());
  EXPECT_EQ("sim_" + res.input_hash.substr(0, 16), res.simulation_id);
  EXPECT_EQ(64u, res.input_hash.size());
  EXPECT_EQ(64u, res.result_hash.size());
  EXPECT_EQ(res.result_hash, res.compute_result_hash());
  EXPECT_TRUE(res.metrics.contains("final_equity"));
  EXPECT_TRUE(res.statistics.contains("mean"));
  EXPECT_TRUE(res.performance.contains("max_drawdown_pct"));
  EXPECT_FALSE(res.execution_timestamp.empty());
}

TEST(BridgeEngine, SimulationDeterministic) {
  auto backend = make_backend();
  SimulationRequest req;
  req.dataset_reference = "XAUUSD";
  req.prices = {100.0, 102.0, 99.0, 104.0, 103.0, 105.0, 107.0};
  const auto a = backend->simulation_run(req);
  const auto b = backend->simulation_run(req);
  EXPECT_EQ(a.simulation_id, b.simulation_id);
  EXPECT_EQ(a.input_hash, b.input_hash);
  EXPECT_EQ(a.result_hash, b.result_hash);
  EXPECT_EQ(a.equity_curve, b.equity_curve);
  EXPECT_EQ(a.returns, b.returns);
  EXPECT_EQ(a.metrics, b.metrics);
}

TEST(BridgeEngine, SimulationEquityFromCapital) {
  auto backend = make_backend();
  SimulationRequest req;
  req.dataset_reference = "TEST";
  req.initial_capital = 1000.0;
  req.prices = {100.0, 110.0, 99.0};
  const auto res = backend->simulation_run(req);
  EXPECT_DOUBLE_EQ(1000.0, res.equity_curve[0]);
  EXPECT_DOUBLE_EQ(1100.0, res.equity_curve[1]);  // +10%
  // 110 -> 99 is -10% => 990
  EXPECT_DOUBLE_EQ(990.0, res.equity_curve[2]);
  EXPECT_DOUBLE_EQ(-1.0, res.metrics.at("total_return_pct"));
}

TEST(BridgeEngine, MarketDataLoadValid) {
  auto backend = make_backend();
  MarketDataRequest req;
  req.symbol = "EURUSD";
  req.timeframe = "M5";
  req.candles = make_bridge_candles(10, kStart);
  const auto res = backend->market_data_load(req);
  EXPECT_TRUE(res.valid);
  EXPECT_EQ(10u, res.size);
  EXPECT_EQ("EURUSD", res.symbol);
  EXPECT_EQ("M5", res.timeframe);
  EXPECT_EQ(64u, res.input_hash.size());
  EXPECT_EQ(64u, res.result_hash.size());
  EXPECT_EQ(res.result_hash, res.compute_result_hash());
  EXPECT_FALSE(res.first_timestamp.empty());
  EXPECT_FALSE(res.last_timestamp.empty());
}

TEST(BridgeEngine, MarketDataLoadEngineValidationReportsInvalid) {
  auto backend = make_backend();
  MarketDataRequest req;
  req.symbol = "EURUSD";
  auto candles = make_bridge_candles(5, kStart);
  // All-zero candle passes request-level structural checks but is rejected by
  // the engine's stricter validity rules -> reported via valid=false.
  candles[4] = make_bridge_candle(4, kStart);
  candles[4].open = 0.0; candles[4].high = 0.0;
  candles[4].low = 0.0; candles[4].close = 0.0; candles[4].volume = 0.0;
  req.candles = candles;
  const auto res = backend->market_data_load(req);
  EXPECT_FALSE(res.valid);
  EXPECT_FALSE(res.validation_message.empty());
  // Result hashes are still stable and self-consistent.
  EXPECT_EQ(res.result_hash, res.compute_result_hash());
}

TEST(BridgeEngine, MarketDataLoadMalformedThrows) {
  auto backend = make_backend();
  MarketDataRequest req;
  req.symbol = "EURUSD";
  auto candles = make_bridge_candles(3, kStart);
  candles[0].open = std::numeric_limits<double>::quiet_NaN();
  req.candles = candles;
  EXPECT_THROW(backend->market_data_load(req), BridgeError);
  try {
    backend->market_data_load(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::MalformedData, e.code());
  }
}

TEST(BridgeEngine, BacktestNoOpSignalProducesNoTrades) {
  auto backend = make_backend();
  BacktestRequest req;
  req.symbol = "BTCUSD";
  req.candles = make_bridge_candles(50, kStart);
  const auto res = backend->backtest_run(req);
  EXPECT_EQ(50u, res.total_bars);
  EXPECT_EQ(50u, res.equity_curve.size());
  EXPECT_EQ(50u, res.drawdown_curve.size());
  EXPECT_EQ(0u, res.num_trades);
  EXPECT_DOUBLE_EQ(100'000.0, res.final_equity);
  EXPECT_EQ(64u, res.input_hash.size());
  EXPECT_EQ(64u, res.result_hash.size());
  EXPECT_EQ(res.result_hash, res.compute_result_hash());
}

TEST(BridgeEngine, BacktestWithSignalTradesAndDeterministic) {
  auto backend = make_backend();
  BacktestRequest req;
  req.symbol = "BTCUSD";
  req.candles = make_bridge_candles(200, kStart);
  BridgeSignalFn buy_upticks = [](size_t, const std::vector<OHLCV>& history) {
    SignalResult s;
    if (history.empty()) return s;
    if (history.back().close > history.back().open) {
      s.direction = TradeDirection::Buy;
      s.quantity = 1.0;
    }
    return s;
  };
  const auto a = backend->backtest_run(req, buy_upticks);
  const auto b = backend->backtest_run(req, buy_upticks);
  EXPECT_GT(a.num_trades, 0u);
  EXPECT_EQ(a.num_trades, b.num_trades);
  EXPECT_EQ(a.equity_curve, b.equity_curve);
  EXPECT_EQ(a.input_hash, b.input_hash);
  EXPECT_EQ(a.result_hash, b.result_hash);
  EXPECT_EQ(a.result_hash, a.compute_result_hash());
}

TEST(BridgeEngine, BacktestHashDiffersWhenSignalReferenceChanges) {
  auto backend = make_backend();
  BacktestRequest req;
  req.symbol = "BTCUSD";
  req.candles = make_bridge_candles(20, kStart);
  const auto a = backend->backtest_run(req);
  req.signal_reference = "strategy://buy-and-hold/v1";
  const auto b = backend->backtest_run(req);
  EXPECT_NE(a.input_hash, b.input_hash);
  EXPECT_NE(a.result_hash, b.result_hash);
}

TEST(BridgeEngine, PerformanceKnownCurve) {
  auto backend = make_backend();
  PerformanceRequest req;
  req.equity_curve = {100.0, 110.0, 99.0, 108.9, 119.79};
  req.initial_capital = 100.0;
  const auto res = backend->performance_analyze(req);
  EXPECT_DOUBLE_EQ(19.79, res.total_return);
  EXPECT_NEAR(19.79, res.total_return_pct, 1e-6);
  EXPECT_NE(0.0, res.annualized_volatility);
  EXPECT_EQ(64u, res.input_hash.size());
  EXPECT_EQ(64u, res.result_hash.size());
  EXPECT_EQ(res.result_hash, res.compute_result_hash());
}

TEST(BridgeEngine, PerformanceWithBarsBuckets) {
  auto backend = make_backend();
  PerformanceRequest req;
  for (size_t i = 0; i < 500; ++i) {
    double eq = 100.0 + static_cast<double>(i);
    if (i >= 200 && i < 300) eq -= 50.0;  // drawdown episode
    req.equity_curve.push_back(eq);
  }
  req.bars = make_bridge_candles(500, kStart, "D1");
  req.initial_capital = 100.0;
  const auto res = backend->performance_analyze(req);
  EXPECT_GT(res.num_yearly_periods, 0u);
  EXPECT_GT(res.num_monthly_periods, 0u);
  EXPECT_GT(res.max_drawdown_pct, 0.0);
  EXPECT_GT(res.max_drawdown_recovery_bars, 0u);
  EXPECT_EQ(res.result_hash, res.compute_result_hash());
}

TEST(BridgeEngine, RoundTripResultHashesSelfConsistent) {
  auto backend = make_backend();

  MarketDataRequest md;
  md.symbol = "EURUSD";
  md.candles = make_bridge_candles(20, kStart);
  auto md_res = backend->market_data_load(md);
  EXPECT_EQ(md_res.result_hash, md_res.compute_result_hash());

  StatisticsRequest st;
  st.data = {1.0, 2.0, 3.0, 4.0, 5.0};
  auto st_res = backend->statistics_compute(st);
  EXPECT_EQ(st_res.result_hash, st_res.compute_result_hash());

  RiskRequest rk;
  rk.returns = {0.01, -0.02, 0.03, -0.01, 0.005, 0.01};
  rk.equity_curve = {100.0, 105.0, 102.0, 99.0, 101.0, 100.0, 101.0};
  auto rk_res = backend->risk_compute(rk);
  EXPECT_EQ(rk_res.result_hash, rk_res.compute_result_hash());

  SimulationRequest sim;
  sim.dataset_reference = "XAUUSD";
  sim.prices = {100.0, 101.0, 102.0, 101.5, 103.0, 102.0};
  auto sim_res = backend->simulation_run(sim);
  EXPECT_EQ(sim_res.result_hash, sim_res.compute_result_hash());

  BacktestRequest bt;
  bt.symbol = "BTCUSD";
  bt.candles = make_bridge_candles(30, kStart);
  auto bt_res = backend->backtest_run(bt);
  EXPECT_EQ(bt_res.result_hash, bt_res.compute_result_hash());

  PerformanceRequest pf;
  pf.equity_curve = {100.0, 101.0, 100.5, 102.0};
  auto pf_res = backend->performance_analyze(pf);
  EXPECT_EQ(pf_res.result_hash, pf_res.compute_result_hash());
}

TEST(BridgeEngine, InputHashSensitivity) {
  auto backend = make_backend();

  StatisticsRequest base;
  base.data = {1.0, 2.0, 3.0};
  const auto h = base.compute_input_hash();
  StatisticsRequest changed = base;
  changed.data = {1.0, 2.0, 3.001};
  EXPECT_NE(h, changed.compute_input_hash());

  SimulationRequest sim;
  sim.dataset_reference = "D";
  sim.prices = {10.0, 11.0, 12.0};
  const auto sh = sim.compute_input_hash();
  SimulationRequest sim2 = sim;
  sim2.prices = {10.0, 11.0, 12.0, 13.0};
  EXPECT_NE(sh, sim2.compute_input_hash());
  SimulationRequest sim3 = sim;
  sim3.seed = 7;
  EXPECT_NE(sh, sim3.compute_input_hash());
}

} // namespace
