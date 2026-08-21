#ifndef QUANT_ENGINE_HPP
#define QUANT_ENGINE_HPP

/**
 * @file quant_engine.hpp
 * @brief Master header for the C++ Quant Computation Engine.
 *
 * This is a NUMERICAL COMPUTATION LAYER only — NOT a trading engine,
 * NOT execution logic, NOT a signal generator. It provides high-performance
 * C++20 implementations of the performance-critical numerical calculations
 * used by ResearchOS.
 *
 * Architecture:
 *   ResearchOS Python
 *       |
 *       v
 *   QuantComputationInterface (abstract)
 *       |
 *       ├── PythonQuantBackend (reference)
 *       └── CppQuantBackend (this — C++20 via pybind11)
 *
 * Design Principles:
 *   - Deterministic: Same inputs → same outputs (no random unless seeded)
 *   - Pure C++20: No external numerical libraries
 *   - Audit-compatible: All calculations are reproducible
 *   - No ML: Pure numerical computation only
 *
 * Based on Article XVII: Object Model — Quant Engine Layer.
 */

#include <cstdint>
#include <string>
#include <vector>
#include <unordered_map>
#include <stdexcept>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <limits>

namespace quant_engine {

// ── Version ────────────────────────────────────────────────────────────────
constexpr const char* ENGINE_VERSION = "1.0.0";

// ── Calculation Version Constants ──────────────────────────────────────────
constexpr const char* CALCULATION_V1 = "CALCULATION_V1";

// ── Exceptions ─────────────────────────────────────────────────────────────
class QuantEngineError : public std::runtime_error {
public:
    explicit QuantEngineError(const std::string& msg)
        : std::runtime_error(msg) {}
};

class InsufficientDataError : public QuantEngineError {
public:
    explicit InsufficientDataError(const std::string& msg)
        : QuantEngineError(msg) {}
};

class InvalidArgumentError : public QuantEngineError {
public:
    explicit InvalidArgumentError(const std::string& msg)
        : QuantEngineError(msg) {}
};

// ── Statistics Engine ──────────────────────────────────────────────────────
namespace statistics {

    double mean(const std::vector<double>& returns);
    double variance(const std::vector<double>& returns, int ddof = 1);
    double standard_deviation(const std::vector<double>& returns, int ddof = 1);
    double z_score(double value, double population_mean, double population_std);

    struct DistributionSummary {
        double mean;
        double std;
        double variance;
        double min;
        double max;
        double skewness;
        double kurtosis;
        size_t count;
        double sum;

        std::unordered_map<std::string, double> to_dict() const;
    };

    DistributionSummary distribution_summary(const std::vector<double>& returns);

} // namespace statistics

// ── Market Data Processing ─────────────────────────────────────────────────
namespace market_data {

    // Returns
    std::vector<double> absolute_returns(const std::vector<double>& prices);
    std::vector<double> percentage_returns(const std::vector<double>& prices);
    std::vector<double> log_returns(const std::vector<double>& prices);

    // Volatility
    double rolling_volatility(const std::vector<double>& returns, size_t window = 21);
    std::vector<double> rolling_volatility_series(const std::vector<double>& returns, size_t window = 21);
    double volatility_change(const std::vector<double>& returns, size_t window = 21);

    // Risk
    struct DrawdownResult {
        double max_drawdown;
        double max_drawdown_pct;
        int recovery_period;

        std::unordered_map<std::string, double> to_dict() const;
    };

    DrawdownResult max_drawdown(const std::vector<double>& equity_curve);

} // namespace market_data

// ── Simulation Engine ──────────────────────────────────────────────────────
namespace simulation {

    struct SimulationInput {
        std::string dataset_reference;
        std::string dataset_version;
        std::string calculation_version;
        double initial_capital;
        double risk_free_rate;
        int seed;

        std::string compute_input_hash() const;
    };

    struct SimulationOutput {
        std::vector<double> returns;
        std::vector<double> equity_curve;
        std::unordered_map<std::string, double> metrics;
        std::unordered_map<std::string, double> statistics;
        std::unordered_map<std::string, double> performance;
        std::string input_hash;
        std::string result_hash;

        std::string compute_result_hash() const;
    };

    SimulationOutput run_simulation(
        const SimulationInput& input,
        const std::vector<double>& prices
    );

} // namespace simulation

// ── Metrics Engine ─────────────────────────────────────────────────────────
namespace metrics {

    double sharpe_ratio(
        const std::vector<double>& returns,
        double risk_free_rate = 0.0,
        int periods_per_year = 252
    );

    double sortino_ratio(
        const std::vector<double>& returns,
        double risk_free_rate = 0.0,
        int periods_per_year = 252
    );

    double calmar_ratio(
        const std::vector<double>& returns,
        const std::vector<double>& equity_curve,
        int periods_per_year = 252
    );

    double profit_factor(const std::vector<double>& returns);
    double win_rate(const std::vector<double>& returns);
    double average_return(const std::vector<double>& returns);

    std::unordered_map<std::string, double> compute_all_metrics(
        const std::vector<double>& returns,
        const std::vector<double>& equity_curve,
        double risk_free_rate = 0.0,
        int periods_per_year = 252
    );

} // namespace metrics

} // namespace quant_engine

#endif // QUANT_ENGINE_HPP
