#ifndef QUANT_BRIDGE_MODELS_H
#define QUANT_BRIDGE_MODELS_H

// Bridge data models shared by the C++ backend, the pybind11 adapter, and the
// Python contract layer (python/cpp_quant_engine/models.py).
//
// Every model is a plain value type that can be converted losslessly to/from a
// Python BaseObject (a dict of primitives). Round-trip guarantees are:
//   * fields are strongly typed on the C++ side,
//   * timestamps are ISO-8601 strings,
//   * hashes are SHA-256 over a canonical JSON representation that is byte-for-
//     byte reproducible from Python (see bridge.cpp / models.py).
//
// The canonical serialization contract:
//   * a JSON object with alphabetically sorted keys,
//   * numbers formatted as fixed-point with 10 decimals ({:.10f}),
//   * strings JSON-escaped, no whitespace.

#include <cstddef>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

namespace quant::bridge {

inline constexpr const char* kDefaultCalculationVersion = "CALCULATION_V1";

// ── Canonical serialization / hashing primitives ───────────────────────────
// Implemented in src/bridge/bridge.cpp. Mirrored byte-for-byte in Python.

std::string canonical_float(double v);
std::string canonical_json_escape(const std::string& s);
// Builds a compact canonical JSON object. Each entry value must already be
// rendered canonically (canonical_float for numbers, quoted+escaped for strings).
std::string canonical_object(
    std::initializer_list<std::pair<std::string, std::string>> fields);
std::string canonical_float_array(const std::vector<double>& values);
std::string canonical_string_array(const std::vector<std::string>& values);
std::string canonical_double_map(
    const std::unordered_map<std::string, double>& m);
std::string sha256_hex(const std::string& input);
std::string iso8601_now();  // audit timestamp (never included in hashes)

// ── Candle ─────────────────────────────────────────────────────────────────

struct CandleModel {
  std::string timestamp;  // ISO-8601
  double open{0.0};
  double high{0.0};
  double low{0.0};
  double close{0.0};
  double volume{0.0};
  std::string timeframe{"M1"};

  std::string to_canonical() const;
};

// ── MarketData ─────────────────────────────────────────────────────────────

struct MarketDataRequest {
  std::string symbol;
  std::string timeframe{"M1"};
  std::vector<CandleModel> candles;
  std::string calculation_version{kDefaultCalculationVersion};

  std::string compute_input_hash() const;
};

struct MarketDataResult {
  std::string symbol;
  std::string timeframe;
  size_t size{0};
  std::string first_timestamp;
  std::string last_timestamp;
  bool valid{false};
  std::string validation_message;
  std::string input_hash;
  std::string result_hash;
  std::string calculation_version{kDefaultCalculationVersion};
  std::string engine_version;
  std::string bridge_version;

  std::string compute_result_hash() const;
};

// ── Statistics ─────────────────────────────────────────────────────────────

struct StatisticsRequest {
  std::vector<double> data;
  std::string calculation_version{kDefaultCalculationVersion};

  std::string compute_input_hash() const;
};

struct StatisticsResult {
  size_t count{0};
  double sum{0.0};
  double mean{0.0};
  double variance{0.0};
  double stddev{0.0};
  double skewness{0.0};
  double kurtosis{0.0};
  double min{0.0};
  double max{0.0};
  double q1{0.0};
  double median{0.0};
  double q3{0.0};
  double iqr{0.0};
  std::string input_hash;
  std::string result_hash;
  std::string calculation_version{kDefaultCalculationVersion};
  std::string engine_version;
  std::string bridge_version;

  std::string compute_result_hash() const;
};

// ── Risk ───────────────────────────────────────────────────────────────────

struct RiskRequest {
  std::vector<double> returns;       // period returns for VaR / ratios
  std::vector<double> equity_curve;  // equity curve for drawdown
  double risk_free_rate{0.0};
  std::string calculation_version{kDefaultCalculationVersion};

  std::string compute_input_hash() const;
};

struct RiskResult {
  double var_95{0.0};
  double var_99{0.0};
  double cvar_95{0.0};
  double cvar_99{0.0};
  double max_drawdown_pct{0.0};
  size_t peak_index{0};
  size_t trough_index{0};
  size_t recovery_index{0};
  double sharpe_ratio{0.0};
  double sortino_ratio{0.0};
  std::string input_hash;
  std::string result_hash;
  std::string calculation_version{kDefaultCalculationVersion};
  std::string engine_version;
  std::string bridge_version;

  std::string compute_result_hash() const;
};

// ── Simulation ─────────────────────────────────────────────────────────────

struct SimulationRequest {
  std::string dataset_reference;
  std::string dataset_version{"1.0.0"};
  std::string calculation_version{kDefaultCalculationVersion};
  double initial_capital{100'000.0};
  double risk_free_rate{0.0};
  int seed{42};  // reserved; historical simulation is deterministic
  std::string start_time;  // ISO-8601 (audit only)
  std::string end_time;    // ISO-8601 (audit only)
  std::vector<double> prices;

  std::string compute_input_hash() const;
};

struct SimulationResult {
  std::string simulation_id;
  std::string dataset_reference;
  std::string dataset_version;
  std::string calculation_version;
  std::string start_time;
  std::string end_time;
  std::string input_hash;
  std::string result_hash;
  std::string execution_timestamp;  // audit only (not hashed)
  std::vector<double> returns;
  std::vector<double> equity_curve;
  std::unordered_map<std::string, double> metrics;
  std::unordered_map<std::string, double> statistics;
  std::unordered_map<std::string, double> performance;
  std::string engine_version;
  std::string bridge_version;

  std::string compute_result_hash() const;
};

// ── Backtest ───────────────────────────────────────────────────────────────

struct BacktestRequest {
  std::string symbol;
  std::string timeframe{"M1"};
  std::vector<CandleModel> candles;
  double initial_capital{100'000.0};
  double commission_pct{0.001};
  double slippage_pct{0.0005};
  bool allow_short{true};
  // Opaque, versioned token describing the signal supplied by the Python layer.
  // The bridge itself implements NO trading logic; the token is audit metadata.
  std::string signal_reference;
  std::string calculation_version{kDefaultCalculationVersion};

  std::string compute_input_hash() const;
};

struct BacktestResult {
  std::vector<double> equity_curve;
  std::vector<double> drawdown_curve;
  double final_equity{0.0};
  double total_return_pct{0.0};
  double max_drawdown_pct{0.0};
  size_t total_bars{0};
  size_t num_trades{0};
  std::string signal_reference;
  std::string input_hash;
  std::string result_hash;
  std::string calculation_version{kDefaultCalculationVersion};
  std::string engine_version;
  std::string bridge_version;

  std::string compute_result_hash() const;
};

// ── Performance ────────────────────────────────────────────────────────────

struct PerformanceRequest {
  std::vector<double> equity_curve;
  std::vector<CandleModel> bars;  // optional, for calendar bucketing
  double initial_capital{100'000.0};
  double trading_days_per_year{252.0};
  std::string calculation_version{kDefaultCalculationVersion};

  std::string compute_input_hash() const;
};

struct PerformanceResult {
  double total_return{0.0};
  double total_return_pct{0.0};
  double annualized_return{0.0};
  double annualized_volatility{0.0};
  double sharpe_ratio{0.0};
  double sortino_ratio{0.0};
  double calmar_ratio{0.0};
  double max_drawdown_pct{0.0};
  double win_rate{0.0};
  double profit_factor{0.0};
  double downside_deviation_annualized{0.0};
  double var_95{0.0};
  double var_99{0.0};
  double cvar_95{0.0};
  double cvar_99{0.0};
  double time_in_drawdown_pct{0.0};
  size_t total_trades{0};
  size_t winning_trades{0};
  size_t losing_trades{0};
  size_t num_drawdown_periods{0};
  size_t num_yearly_periods{0};
  size_t num_monthly_periods{0};
  size_t max_drawdown_recovery_bars{0};
  std::string input_hash;
  std::string result_hash;
  std::string calculation_version{kDefaultCalculationVersion};
  std::string engine_version;
  std::string bridge_version;

  std::string compute_result_hash() const;
};

} // namespace quant::bridge
#endif
