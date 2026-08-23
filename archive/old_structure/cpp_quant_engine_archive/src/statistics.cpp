/**
 * @file statistics.cpp
 * @brief Implementation of statistical functions for the Quant Computation Engine.
 *
 * All calculations are:
 *   - Deterministic: Same inputs → same outputs
 *   - Safe: Handles empty datasets, insufficient samples, zero variance
 *   - Pure C++20: No external numerical libraries
 */

#include "quant_engine.hpp"
#include <string>
#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>
#include <stdexcept>

namespace quant_engine {
namespace statistics {

// ── Validation ─────────────────────────────────────────────────────────────

static void validate_returns(const std::vector<double>& returns, size_t min_samples = 2) {
    if (returns.empty()) {
        throw InsufficientDataError("Cannot compute statistics on empty dataset");
    }
    if (returns.size() < min_samples) {
        throw InsufficientDataError(
            "Insufficient samples: need at least " + std::to_string(min_samples) +
            ", got " + std::to_string(returns.size())
        );
    }
}

// ── Mean ───────────────────────────────────────────────────────────────────

double mean(const std::vector<double>& returns) {
    validate_returns(returns, 1);
    double sum = std::accumulate(returns.begin(), returns.end(), 0.0);
    return sum / static_cast<double>(returns.size());
}

// ── Variance ───────────────────────────────────────────────────────────────

double variance(const std::vector<double>& returns, int ddof) {
    if (ddof == 0) {
        validate_returns(returns, 1);
    } else {
        validate_returns(returns, 2);
    }

    double avg = mean(returns);
    double sq_sum = 0.0;
    for (double r : returns) {
        double diff = r - avg;
        sq_sum += diff * diff;
    }
    return sq_sum / static_cast<double>(returns.size() - ddof);
}

// ── Standard Deviation ─────────────────────────────────────────────────────

double standard_deviation(const std::vector<double>& returns, int ddof) {
    return std::sqrt(variance(returns, ddof));
}

// ── Z-Score ────────────────────────────────────────────────────────────────

double z_score(double value, double population_mean, double population_std) {
    if (population_std <= 0.0) {
        throw InvalidArgumentError(
            "Cannot compute z-score with non-positive std: " +
            std::to_string(population_std)
        );
    }
    return (value - population_mean) / population_std;
}

// ── Skewness ───────────────────────────────────────────────────────────────

static double skewness(const std::vector<double>& returns) {
    validate_returns(returns, 3);
    double avg = mean(returns);
    double std = standard_deviation(returns, 0);

    if (std == 0.0) return 0.0;

    double n = static_cast<double>(returns.size());
    double cubed_sum = 0.0;
    for (double r : returns) {
        double dev = (r - avg) / std;
        cubed_sum += dev * dev * dev;
    }
    return (n / ((n - 1.0) * (n - 2.0))) * cubed_sum;
}

// ── Kurtosis ───────────────────────────────────────────────────────────────

static double kurtosis(const std::vector<double>& returns, bool excess = true) {
    validate_returns(returns, 4);
    double avg = mean(returns);
    double std = standard_deviation(returns, 0);

    if (std == 0.0) return 0.0;

    double n = static_cast<double>(returns.size());
    double fourth_sum = 0.0;
    for (double r : returns) {
        double dev = (r - avg) / std;
        fourth_sum += dev * dev * dev * dev;
    }

    double numerator = n * (n + 1.0) * fourth_sum;
    double denominator = (n - 1.0) * (n - 2.0) * (n - 3.0);
    double result = (denominator != 0.0) ? numerator / denominator : 0.0;

    if (excess) {
        double correction = (n > 3.0)
            ? (3.0 * (n - 1.0) * (n - 1.0)) / ((n - 2.0) * (n - 3.0))
            : 3.0;
        result -= correction;
    }

    return result;
}

// ── Distribution Summary ──────────────────────────────────────────────────

DistributionSummary distribution_summary(const std::vector<double>& returns) {
    validate_returns(returns, 1);

    size_t n = returns.size();
    double sum = std::accumulate(returns.begin(), returns.end(), 0.0);
    double avg = sum / static_cast<double>(n);
    auto [min_it, max_it] = std::minmax_element(returns.begin(), returns.end());

    DistributionSummary summary;
    summary.mean = avg;
    summary.count = n;
    summary.sum = sum;
    summary.min = *min_it;
    summary.max = *max_it;

    if (n >= 2) {
        summary.variance = variance(returns, 1);
        summary.std = standard_deviation(returns, 1);
    } else {
        summary.variance = 0.0;
        summary.std = 0.0;
    }

    if (n >= 3) {
        summary.skewness = skewness(returns);
    } else {
        summary.skewness = 0.0;
    }

    if (n >= 4) {
        summary.kurtosis = kurtosis(returns, true);
    } else {
        summary.kurtosis = 0.0;
    }

    return summary;
}

std::unordered_map<std::string, double> DistributionSummary::to_dict() const {
    return {
        {"mean", mean},
        {"std", std},
        {"variance", variance},
        {"min", min},
        {"max", max},
        {"skewness", skewness},
        {"kurtosis", kurtosis},
        {"count", static_cast<double>(count)},
        {"sum", sum}
    };
}

} // namespace statistics
} // namespace quant_engine
