#include <gtest/gtest.h>
#include "bridge_test_util.h"
#include "bridge_validation.h"
#include <chrono>

using namespace quant;
using namespace quant::bridge;
using namespace quant::bridge::test;

namespace {

const auto kStart = std::chrono::system_clock::time_point{};

TEST(BridgeValidation, UnsupportedCalculationVersionThrows) {
  StatisticsRequest req;
  req.data = {1.0, 2.0, 3.0};
  req.calculation_version = "CALCULATION_V2";
  EXPECT_THROW(validate_statistics_request(req), BridgeError);
  try {
    validate_statistics_request(req);
    FAIL() << "expected throw";
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::UnsupportedVersion, e.code());
  }
}

TEST(BridgeValidation, SupportedVersionAccepted) {
  StatisticsRequest req;
  req.data = {1.0, 2.0, 3.0};
  EXPECT_NO_THROW(validate_statistics_request(req));
}

TEST(BridgeValidation, StatisticsEmptyThrowsInsufficientData) {
  StatisticsRequest req;
  EXPECT_THROW(validate_statistics_request(req), BridgeError);
  try {
    validate_statistics_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InsufficientData, e.code());
  }
}

TEST(BridgeValidation, StatisticsSinglePointThrows) {
  StatisticsRequest req;
  req.data = {1.0};
  try {
    validate_statistics_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InsufficientData, e.code());
  }
}

TEST(BridgeValidation, StatisticsNaNThrows) {
  StatisticsRequest req;
  req.data = {1.0, std::numeric_limits<double>::quiet_NaN()};
  try {
    validate_statistics_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, RiskEmptyReturnsThrows) {
  RiskRequest req;
  req.equity_curve = {100.0};
  try {
    validate_risk_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InsufficientData, e.code());
  }
}

TEST(BridgeValidation, RiskEmptyEquityThrows) {
  RiskRequest req;
  req.returns = {0.01};
  try {
    validate_risk_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InsufficientData, e.code());
  }
}

TEST(BridgeValidation, RiskInfThrows) {
  RiskRequest req;
  req.returns = {0.01, std::numeric_limits<double>::infinity()};
  req.equity_curve = {100.0, 101.0};
  try {
    validate_risk_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, SimulationTooFewPricesThrows) {
  SimulationRequest req;
  req.dataset_reference = "XAUUSD";
  req.prices = {100.0};
  try {
    validate_simulation_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InsufficientData, e.code());
  }
}

TEST(BridgeValidation, SimulationNonPositiveCapitalThrows) {
  SimulationRequest req;
  req.dataset_reference = "XAUUSD";
  req.initial_capital = 0.0;
  req.prices = {100.0, 101.0};
  try {
    validate_simulation_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, SimulationEmptyReferenceThrows) {
  SimulationRequest req;
  req.prices = {100.0, 101.0};
  try {
    validate_simulation_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, MarketDataEmptySymbolThrows) {
  MarketDataRequest req;
  req.candles = make_bridge_candles(3, kStart);
  try {
    validate_market_data_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, MarketDataEmptyCandlesThrows) {
  MarketDataRequest req;
  req.symbol = "EURUSD";
  try {
    validate_market_data_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::EmptyData, e.code());
  }
}

TEST(BridgeValidation, MarketDataBadTimeframeThrows) {
  MarketDataRequest req;
  req.symbol = "EURUSD";
  req.timeframe = "M7";
  req.candles = make_bridge_candles(3, kStart);
  try {
    validate_market_data_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, MarketDataBadOhlcThrows) {
  MarketDataRequest req;
  req.symbol = "EURUSD";
  auto candles = make_bridge_candles(3, kStart);
  candles[1].high = 0.0;  // high < low -> invalid
  req.candles = candles;
  std::string reason;
  EXPECT_EQ(1u, validate_candles(req.candles, &reason));
  EXPECT_FALSE(reason.empty());
  try {
    validate_market_data_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::MalformedData, e.code());
  }
}

TEST(BridgeValidation, MarketDataNonIncreasingTimestampsThrow) {
  MarketDataRequest req;
  req.symbol = "EURUSD";
  auto candles = make_bridge_candles(3, kStart);
  candles[2].timestamp = candles[1].timestamp;  // duplicate -> non-increasing
  req.candles = candles;
  EXPECT_EQ(1u, validate_candles(req.candles, nullptr));
  try {
    validate_market_data_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::MalformedData, e.code());
  }
}

TEST(BridgeValidation, BacktestBadCommissionThrows) {
  BacktestRequest req;
  req.symbol = "BTCUSD";
  req.candles = make_bridge_candles(3, kStart);
  req.commission_pct = 2.0;  // > 1
  try {
    validate_backtest_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, BacktestNegativeSlippageThrows) {
  BacktestRequest req;
  req.symbol = "BTCUSD";
  req.candles = make_bridge_candles(3, kStart);
  req.slippage_pct = -0.01;
  try {
    validate_backtest_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, PerformanceEmptyEquityThrows) {
  PerformanceRequest req;
  try {
    validate_performance_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InsufficientData, e.code());
  }
}

TEST(BridgeValidation, PerformanceBadTradingDaysThrows) {
  PerformanceRequest req;
  req.equity_curve = {100.0, 101.0};
  req.trading_days_per_year = 0.0;
  try {
    validate_performance_request(req);
    FAIL();
  } catch (const BridgeError& e) {
    EXPECT_EQ(BridgeErrorCode::InvalidParameter, e.code());
  }
}

TEST(BridgeValidation, TimeframeFromStringCoverage) {
  EXPECT_TRUE(timeframe_from_string("M1").has_value());
  EXPECT_TRUE(timeframe_from_string("MN1").has_value());
  EXPECT_FALSE(timeframe_from_string("m1").has_value());
  EXPECT_FALSE(timeframe_from_string("").has_value());
  EXPECT_FALSE(timeframe_from_string("BOGUS").has_value());
}

} // namespace
