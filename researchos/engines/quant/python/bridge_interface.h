#ifndef QUANT_BRIDGE_INTERFACE_H
#define QUANT_BRIDGE_INTERFACE_H

// Stable integration contract between the ResearchOS Python layer and the C++
// computation engine (pybind11 adapter).
//
// Ownership: C++ backend owns all engine state for the duration of a call.
// All models are passed by value; large payloads (candle series, price series)
// are moved/copied across the boundary and released when the call returns.
//
// Errors: bridge operations throw BridgeError (a std::runtime_error subclass)
// with a stable numeric code. The pybind11 adapter translates BridgeError into
// a typed Python exception (see exceptions.py).

#include "bridge_models.h"
#include "quant/backtest/backtest_engine.h"
#include <cstdint>
#include <functional>
#include <stdexcept>
#include <string>
#include <vector>

namespace quant::bridge {

// ── Versioning ─────────────────────────────────────────────────────────────
inline constexpr const char* kBridgeName = "cpp_quant_engine";
inline constexpr const char* kBridgeVersion = "1.0.0";
inline constexpr uint32_t kBridgeProtocolVersion = 1;

// Supported calculation version tokens (single source of truth).
inline const std::vector<std::string>& supported_calculation_versions() {
  static const std::vector<std::string> versions{kDefaultCalculationVersion};
  return versions;
}

bool is_supported_calculation_version(const std::string& v);

// ── Error model ────────────────────────────────────────────────────────────
// Stable numeric codes shared with python/cpp_quant_engine/exceptions.py.

enum class BridgeErrorCode : uint32_t {
  None = 0,

  InvalidArgument = 100,
  InvalidParameter = 101,
  InvalidType = 102,

  InsufficientData = 200,
  EmptyData = 201,
  MalformedData = 202,
  OutOfBounds = 203,

  UnsupportedVersion = 300,
  ValidationFailed = 301,
  HashMismatch = 302,

  InternalError = 500,
};

const char* bridge_error_name(BridgeErrorCode code);

class BridgeError : public std::runtime_error {
public:
  BridgeError(BridgeErrorCode code, std::string message);
  BridgeErrorCode code() const { return code_; }
  uint32_t code_value() const { return static_cast<uint32_t>(code_); }

private:
  BridgeErrorCode code_;
};

// ── Audit metadata ─────────────────────────────────────────────────────────

struct BridgeMeta {
  std::string engine_name{kBridgeName};
  std::string engine_version{"0.0.0"};
  std::string bridge_version{kBridgeVersion};
  uint32_t protocol_version{kBridgeProtocolVersion};
  std::string calculation_version{kDefaultCalculationVersion};

  static BridgeMeta current();
  std::string to_json() const;
};

// ── Signal contract (Backtest) ─────────────────────────────────────────────
// The Python layer supplies trading logic as a callable; the bridge only
// transports it. Default nullptr means "no trades" (deterministic no-op).
using BridgeSignalFn = std::function<quant::SignalResult(
    size_t bar_index, const std::vector<quant::OHLCV>& history)>;

// ── Stable bridge contract ─────────────────────────────────────────────────
// Implemented by BridgeBackend (src/bridge/bridge.cpp) and mirrored 1:1 by
// python/cpp_quant_engine/backend.py so the ResearchOS layer can swap the
// numerical backend without changing its own code.
class IBridgeBackend {
public:
  virtual ~IBridgeBackend() = default;

  virtual BridgeMeta meta() const = 0;
  virtual std::string version() const = 0;

  // MarketData: validate + register a series, returning audit metadata.
  virtual MarketDataResult market_data_load(const MarketDataRequest& req) = 0;

  // Statistics: descriptive statistics over a data series.
  virtual StatisticsResult statistics_compute(const StatisticsRequest& req) = 0;

  // Risk: VaR/CVaR, drawdown, Sharpe/Sortino over returns + equity.
  virtual RiskResult risk_compute(const RiskRequest& req) = 0;

  // Simulation: deterministic historical simulation (prices -> returns ->
  // equity -> metrics/statistics/performance) with provenance hashes.
  virtual SimulationResult simulation_run(const SimulationRequest& req) = 0;

  // Backtest: run the backtest engine. The signal function (if any) is
  // supplied by the caller/Python layer; signal_reference is audit metadata.
  virtual BacktestResult backtest_run(const BacktestRequest& req,
                                      const BridgeSignalFn& signal = nullptr) = 0;

  // Performance: full performance analysis over a backtest equity curve.
  virtual PerformanceResult performance_analyze(const PerformanceRequest& req) = 0;
};

// Factory: creates a shared backend instance (implemented in src/bridge/bridge.cpp).
std::shared_ptr<IBridgeBackend> create_backend();

} // namespace quant::bridge
#endif
