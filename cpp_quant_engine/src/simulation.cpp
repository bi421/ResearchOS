/**
 * @file simulation.cpp
 * @brief Implementation of historical replay simulation engine.
 *
 * Every simulation is:
 *   - Deterministic: Same inputs → same outputs
 *   - Reproducible: Full provenance tracking
 *   - Version-compatible: Calculation version is tracked
 */

#include "quant_engine.hpp"
#include <string>
#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <functional>
#include <cstring>

namespace quant_engine {
namespace simulation {

// ── Simple SHA-256-like hash for deterministic IDs ─────────────────────────
// Uses a deterministic FNV-1a hash (not cryptographic, but deterministic)

static std::string fnv1a_hash(const std::string& input) {
    const uint64_t FNV_OFFSET_BASIS = 14695981039346656037ULL;
    const uint64_t FNV_PRIME = 1099511628211ULL;

    uint64_t hash = FNV_OFFSET_BASIS;
    for (unsigned char c : input) {
        hash ^= static_cast<uint64_t>(c);
        hash *= FNV_PRIME;
    }

    std::ostringstream oss;
    oss << std::hex << std::setfill('0') << std::setw(16) << hash;
    return oss.str();
}

static std::string serialize_sorted(const std::unordered_map<std::string, double>& map) {
    std::vector<std::pair<std::string, double>> items(map.begin(), map.end());
    std::sort(items.begin(), items.end());
    std::ostringstream oss;
    for (const auto& [k, v] : items) {
        oss << k << ":" << std::fixed << std::setprecision(10) << v << "|";
    }
    return oss.str();
}

static std::string serialize_vector(const std::vector<double>& vec) {
    std::ostringstream oss;
    for (double v : vec) {
        oss << std::fixed << std::setprecision(10) << v << ",";
    }
    return oss.str();
}

// ── Input Hash ─────────────────────────────────────────────────────────────

std::string SimulationInput::compute_input_hash() const {
    std::ostringstream oss;
    oss << dataset_reference << "|"
        << dataset_version << "|"
        << calculation_version << "|"
        << initial_capital << "|"
        << risk_free_rate << "|"
        << seed;
    return fnv1a_hash(oss.str());
}

// ── Result Hash ────────────────────────────────────────────────────────────

std::string SimulationOutput::compute_result_hash() const {
    std::ostringstream oss;
    oss << input_hash << "|"
        << serialize_vector(returns) << "|"
        << serialize_vector(equity_curve) << "|"
        << serialize_sorted(metrics) << "|"
        << serialize_sorted(statistics) << "|"
        << serialize_sorted(performance);
    return fnv1a_hash(oss.str());
}

// ── Build Equity Curve ─────────────────────────────────────────────────────

static std::vector<double> build_equity_curve(
    const std::vector<double>& returns,
    double initial_capital
) {
    std::vector<double> equity;
    equity.reserve(returns.size() + 1);
    equity.push_back(initial_capital);
    for (double r : returns) {
        equity.push_back(equity.back() * (1.0 + r));
    }
    return equity;
}

// ── Run Simulation ─────────────────────────────────────────────────────────

SimulationOutput run_simulation(
    const SimulationInput& input,
    const std::vector<double>& prices
) {
    if (prices.size() < 2) {
        throw InsufficientDataError(
            "Need at least 2 prices for simulation, got " +
            std::to_string(prices.size())
        );
    }

    // Compute input hash
    std::string input_hash = input.compute_input_hash();

    // Calculate percentage returns
    std::vector<double> returns;
    returns.reserve(prices.size() - 1);
    for (size_t i = 1; i < prices.size(); ++i) {
        double prev = prices[i - 1];
        if (prev == 0.0) {
            returns.push_back(0.0);
        } else {
            returns.push_back((prices[i] - prev) / prev);
        }
    }

    // Build equity curve
    std::vector<double> equity_curve = build_equity_curve(returns, input.initial_capital);

    // Compute metrics
    auto metrics = quant_engine::metrics::compute_all_metrics(
        returns, equity_curve, input.risk_free_rate, 252
    );

    // Compute statistics
    auto stats = quant_engine::statistics::distribution_summary(returns);
    std::unordered_map<std::string, double> statistics = stats.to_dict();

    // Compute performance analytics
    double win_rate = quant_engine::metrics::win_rate(returns);
    double avg_ret = quant_engine::metrics::average_return(returns);
    double pf = quant_engine::metrics::profit_factor(returns);

    std::unordered_map<std::string, double> performance;
    performance["win_rate"] = win_rate;
    performance["loss_rate"] = 1.0 - win_rate;
    performance["average_return"] = avg_ret;
    performance["profit_factor"] = pf;

    // Build output
    SimulationOutput output;
    output.returns = returns;
    output.equity_curve = equity_curve;
    output.metrics = metrics;
    output.statistics = statistics;
    output.performance = performance;
    output.input_hash = input_hash;
    output.result_hash = "";

    // Compute result hash
    output.result_hash = output.compute_result_hash();

    return output;
}

} // namespace simulation
} // namespace quant_engine
