#ifndef QUANT_BRIDGE_VALIDATION_H
#define QUANT_BRIDGE_VALIDATION_H

// Validation rules for bridge inputs. Every public bridge entry point runs its
// request through the matching validate_* function before any computation.
//
// Validation is deterministic: the same request always passes or fails with the
// same BridgeErrorCode and message. Invalid inputs never reach the engine.

#include "bridge_interface.h"
#include "bridge_models.h"
#include "quant/market/candle.h"
#include <cmath>
#include <optional>
#include <string>

namespace quant::bridge {

// Internal: parse a timeframe name to the engine enum; nullopt if unsupported.
std::optional<quant::Timeframe> timeframe_from_string(const std::string& s);

// Generic guards -----------------------------------------------------------

void validate_calculation_version(const std::string& version);
void require_non_empty(const std::vector<double>& data,
                       const std::string& field,
                       BridgeErrorCode code = BridgeErrorCode::EmptyData);
void require_finite(double v, const std::string& field);
void require_positive(double v, const std::string& field);
void require_valid_timestamp(const std::string& iso, const std::string& field);

// Request-level validators -------------------------------------------------

// Returns the number of rejected candles or 0 when all candles are valid.
// Details of the first failure are written to `reason` when non-null.
size_t validate_candles(const std::vector<CandleModel>& candles,
                        std::string* reason = nullptr);

void validate_market_data_request(const MarketDataRequest& req);
void validate_statistics_request(const StatisticsRequest& req);
void validate_risk_request(const RiskRequest& req);
void validate_simulation_request(const SimulationRequest& req);
void validate_backtest_request(const BacktestRequest& req);
void validate_performance_request(const PerformanceRequest& req);

} // namespace quant::bridge
#endif
