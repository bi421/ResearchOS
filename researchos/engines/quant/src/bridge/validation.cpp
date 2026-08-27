#include "bridge_validation.h"
#include "quant/backtest/serialization.h"
#include <limits>

namespace quant::bridge {

namespace {

bool iso8601_like(const std::string& s) {
  if (s.size() < 19) return false;
  const auto is_digit = [](char c) { return c >= '0' && c <= '9'; };
  return is_digit(s[0]) && is_digit(s[1]) && is_digit(s[2]) && is_digit(s[3]) &&
         s[4] == '-' && is_digit(s[5]) && is_digit(s[6]) && s[7] == '-' &&
         is_digit(s[8]) && is_digit(s[9]) && s[10] == 'T' && is_digit(s[11]) &&
         is_digit(s[12]) && s[13] == ':' && is_digit(s[14]) && is_digit(s[15]) &&
         s[16] == ':' && is_digit(s[17]) && is_digit(s[18]);
}

} // namespace

std::optional<quant::Timeframe> timeframe_from_string(const std::string& s) {
  if (s == "M1") return quant::Timeframe::M1;
  if (s == "M5") return quant::Timeframe::M5;
  if (s == "M15") return quant::Timeframe::M15;
  if (s == "M30") return quant::Timeframe::M30;
  if (s == "H1") return quant::Timeframe::H1;
  if (s == "H4") return quant::Timeframe::H4;
  if (s == "D1") return quant::Timeframe::D1;
  if (s == "W1") return quant::Timeframe::W1;
  if (s == "MN1") return quant::Timeframe::MN1;
  return std::nullopt;
}

void validate_calculation_version(const std::string& version) {
  if (!is_supported_calculation_version(version)) {
    throw BridgeError(BridgeErrorCode::UnsupportedVersion,
                      "unsupported calculation version '" + version +
                          "' (supported: " + supported_calculation_versions()[0] +
                          ")");
  }
}

void require_non_empty(const std::vector<double>& data, const std::string& field,
                       BridgeErrorCode code) {
  if (data.empty()) {
    throw BridgeError(code, field + " must not be empty");
  }
}

void require_finite(double v, const std::string& field) {
  if (!std::isfinite(v)) {
    throw BridgeError(BridgeErrorCode::InvalidParameter,
                      field + " must be finite");
  }
}

void require_positive(double v, const std::string& field) {
  if (!(v > 0.0) || !std::isfinite(v)) {
    throw BridgeError(BridgeErrorCode::InvalidParameter,
                      field + " must be finite and > 0");
  }
}

void require_valid_timestamp(const std::string& iso, const std::string& field) {
  if (!iso8601_like(iso)) {
    throw BridgeError(BridgeErrorCode::MalformedData,
                      field + " is not an ISO-8601 timestamp: '" + iso + "'");
  }
}

size_t validate_candles(const std::vector<CandleModel>& candles,
                        std::string* reason) {
  size_t rejected = 0;
  std::string first_reason;
  TimePoint prev{};
  bool have_prev = false;
  for (const auto& c : candles) {
    bool bad = false;
    std::string why;
    if (!iso8601_like(c.timestamp)) {
      bad = true;
      why = "invalid timestamp '" + c.timestamp + "'";
    }
    if (!bad && (!std::isfinite(c.open) || !std::isfinite(c.high) ||
                 !std::isfinite(c.low) || !std::isfinite(c.close) ||
                 !std::isfinite(c.volume))) {
      bad = true;
      why = "non-finite OHLCV value";
    }
    if (!bad && (c.high < c.low || c.high < c.open || c.high < c.close ||
                 c.low > c.open || c.low > c.close)) {
      bad = true;
      why = "invalid OHLC ordering (high/low bounds violated)";
    }
    if (!bad && c.volume < 0.0) {
      bad = true;
      why = "negative volume";
    }
    if (!bad) {
      const TimePoint tp = serialization::from_iso8601(c.timestamp);
      if (have_prev && tp <= prev) {
        bad = true;
        why = "non-increasing timestamps";
      } else {
        prev = tp;
        have_prev = true;
      }
    }
    if (bad) {
      ++rejected;
      if (first_reason.empty()) first_reason = why;
    }
  }
  if (reason) *reason = first_reason;
  return rejected;
}

void validate_market_data_request(const MarketDataRequest& req) {
  validate_calculation_version(req.calculation_version);
  if (req.symbol.empty()) {
    throw BridgeError(BridgeErrorCode::InvalidParameter, "symbol must not be empty");
  }
  if (req.candles.empty()) {
    throw BridgeError(BridgeErrorCode::EmptyData, "market data requires at least one candle");
  }
  if (!timeframe_from_string(req.timeframe)) {
    throw BridgeError(BridgeErrorCode::InvalidParameter,
                      "unsupported timeframe '" + req.timeframe + "'");
  }
  std::string reason;
  if (validate_candles(req.candles, &reason) > 0) {
    throw BridgeError(BridgeErrorCode::MalformedData,
                      "invalid candle in market data: " + reason);
  }
}

void validate_statistics_request(const StatisticsRequest& req) {
  validate_calculation_version(req.calculation_version);
  require_non_empty(req.data, "statistics data", BridgeErrorCode::InsufficientData);
  if (req.data.size() < 2) {
    throw BridgeError(BridgeErrorCode::InsufficientData,
                      "statistics require at least 2 data points");
  }
  for (size_t i = 0; i < req.data.size(); ++i) {
    require_finite(req.data[i], "statistics data[" + std::to_string(i) + "]");
  }
}

void validate_risk_request(const RiskRequest& req) {
  validate_calculation_version(req.calculation_version);
  require_non_empty(req.returns, "risk returns", BridgeErrorCode::InsufficientData);
  require_non_empty(req.equity_curve, "risk equity curve",
                    BridgeErrorCode::InsufficientData);
  for (size_t i = 0; i < req.returns.size(); ++i) {
    require_finite(req.returns[i], "risk returns[" + std::to_string(i) + "]");
  }
  for (size_t i = 0; i < req.equity_curve.size(); ++i) {
    require_finite(req.equity_curve[i], "risk equity_curve[" + std::to_string(i) + "]");
  }
  require_finite(req.risk_free_rate, "risk_free_rate");
}

void validate_simulation_request(const SimulationRequest& req) {
  validate_calculation_version(req.calculation_version);
  if (req.dataset_reference.empty()) {
    throw BridgeError(BridgeErrorCode::InvalidParameter,
                      "dataset_reference must not be empty");
  }
  if (req.prices.size() < 2) {
    throw BridgeError(BridgeErrorCode::InsufficientData,
                      "simulation requires at least 2 prices");
  }
  require_positive(req.initial_capital, "initial_capital");
  require_finite(req.risk_free_rate, "risk_free_rate");
  for (size_t i = 0; i < req.prices.size(); ++i) {
    require_finite(req.prices[i], "prices[" + std::to_string(i) + "]");
  }
}

void validate_backtest_request(const BacktestRequest& req) {
  validate_calculation_version(req.calculation_version);
  if (req.symbol.empty()) {
    throw BridgeError(BridgeErrorCode::InvalidParameter, "symbol must not be empty");
  }
  if (req.candles.empty()) {
    throw BridgeError(BridgeErrorCode::EmptyData,
                      "backtest requires at least one candle");
  }
  if (!timeframe_from_string(req.timeframe)) {
    throw BridgeError(BridgeErrorCode::InvalidParameter,
                      "unsupported timeframe '" + req.timeframe + "'");
  }
  require_positive(req.initial_capital, "initial_capital");
  require_finite(req.commission_pct, "commission_pct");
  require_finite(req.slippage_pct, "slippage_pct");
  if (req.commission_pct < 0.0 || req.commission_pct > 1.0) {
    throw BridgeError(BridgeErrorCode::InvalidParameter,
                      "commission_pct must be in [0, 1]");
  }
  if (req.slippage_pct < 0.0 || req.slippage_pct > 1.0) {
    throw BridgeError(BridgeErrorCode::InvalidParameter,
                      "slippage_pct must be in [0, 1]");
  }
  std::string reason;
  if (validate_candles(req.candles, &reason) > 0) {
    throw BridgeError(BridgeErrorCode::MalformedData,
                      "invalid candle in backtest: " + reason);
  }
}

void validate_performance_request(const PerformanceRequest& req) {
  validate_calculation_version(req.calculation_version);
  require_non_empty(req.equity_curve, "performance equity curve",
                    BridgeErrorCode::InsufficientData);
  require_positive(req.initial_capital, "initial_capital");
  require_positive(req.trading_days_per_year, "trading_days_per_year");
  for (size_t i = 0; i < req.equity_curve.size(); ++i) {
    require_finite(req.equity_curve[i], "equity_curve[" + std::to_string(i) + "]");
  }
  std::string reason;
  if (validate_candles(req.bars, &reason) > 0) {
    throw BridgeError(BridgeErrorCode::MalformedData,
                      "invalid bar in performance request: " + reason);
  }
}

} // namespace quant::bridge
