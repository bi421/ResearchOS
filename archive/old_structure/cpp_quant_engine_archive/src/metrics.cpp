/**
 * @file metrics.cpp
 * @brief Implementation of research performance metrics.
 *
 * All metrics are RESEARCH METRICS ONLY — NOT trading signals or decisions.
 *
 * Formulas (CALCULATION_V1):
 *   - Sharpe Ratio: (mean(R) - R_f) / std(R) * sqrt(periods_per_year)
 *   - Sortino Ratio: (mean(R) - R_f) / downside_deviation(R) * sqrt(periods_per_year)
 *   - Calmar Ratio: mean(R) * periods_per_year / |max_drawdown|
 *   - Profit Factor: sum(wins) / |sum(losses)|
 */

#include "quant_engine.hpp"
#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>
#include <stdexcept>

namespace quant_engine {
namespace metrics {

// ── Downside Deviation ─────────────────────────────────────────────────────

static double downside_deviation(const std::vector<double>& returns, int ddof = 1) {
    std::vector<double> negative_returns;
    negative_returns.reserve(returns.size());
    for (double r : returns) {
        if (r < 0.0) {
            negative_returns.push_back(r);
        }
    }

    if (negative_returns.size() < 2) {
        return 0.0;
    }

    return quant_engine::statistics::standard_deviation(negative_returns, ddof);
}

// ── Sharpe Ratio ───────────────────────────────────────────────────────────

double sharpe_ratio(
    const std::vector<double>& returns,
    double risk_free_rate,
    int periods_per_year
) {
    if (returns.empty()) {
        throw InsufficientDataError("Cannot compute Sharpe ratio on empty dataset");
    }

    double std = quant_engine::statistics::standard_deviation(returns);
    if (std == 0.0) return 0.0;

    double periodic_rf = risk_free_rate / static_cast<double>(periods_per_year);
    double excess_return = quant_engine::statistics::mean(returns) - periodic_rf;

    return excess_return / std * std::sqrt(static_cast<double>(periods_per_year));
}

// ── Sortino Ratio ──────────────────────────────────────────────────────────

double sortino_ratio(
    const std::vector<double>& returns,
    double risk_free_rate,
    int periods_per_year
) {
    if (returns.empty()) {
        throw InsufficientDataError("Cannot compute Sortino ratio on empty dataset");
    }

    double dd = downside_deviation(returns);
    if (dd == 0.0) return 0.0;

    double periodic_rf = risk_free_rate / static_cast<double>(periods_per_year);
    double excess_return = quant_engine::statistics::mean(returns) - periodic_rf;

    return excess_return / dd * std::sqrt(static_cast<double>(periods_per_year));
}

// ── Calmar Ratio ───────────────────────────────────────────────────────────

double calmar_ratio(
    const std::vector<double>& returns,
    const std::vector<double>& equity_curve,
    int periods_per_year
) {
    if (returns.empty()) {
        throw InsufficientDataError("Cannot compute Calmar ratio on empty dataset");
    }
    if (equity_curve.size() < 2) {
        throw InsufficientDataError(
            "Need at least 2 equity values for Calmar ratio, got " +
            std::to_string(equity_curve.size())
        );
    }

    auto dd = quant_engine::market_data::max_drawdown(equity_curve);
    if (dd.max_drawdown == 0.0) return 0.0;

    double annual_return = quant_engine::statistics::mean(returns) *
                           static_cast<double>(periods_per_year);
    return annual_return / std::abs(dd.max_drawdown);
}

// ── Profit Factor ──────────────────────────────────────────────────────────

double profit_factor(const std::vector<double>& returns) {
    double total_wins = 0.0;
    double total_losses = 0.0;

    for (double r : returns) {
        if (r > 0.0) total_wins += r;
        else if (r < 0.0) total_losses += std::abs(r);
    }

    if (total_losses == 0.0) {
        if (total_wins > 0.0) return std::numeric_limits<double>::infinity();
        return 0.0;
    }

    return total_wins / total_losses;
}

// ── Win Rate ───────────────────────────────────────────────────────────────

double win_rate(const std::vector<double>& returns) {
    if (returns.empty()) return 0.0;
    size_t wins = 0;
    for (double r : returns) {
        if (r > 0.0) ++wins;
    }
    return static_cast<double>(wins) / static_cast<double>(returns.size());
}

// ── Average Return ─────────────────────────────────────────────────────────

double average_return(const std::vector<double>& returns) {
    if (returns.empty()) return 0.0;
    double sum = std::accumulate(returns.begin(), returns.end(), 0.0);
    return sum / static_cast<double>(returns.size());
}

// ── Compute All Metrics ────────────────────────────────────────────────────

std::unordered_map<std::string, double> compute_all_metrics(
    const std::vector<double>& returns,
    const std::vector<double>& equity_curve,
    double risk_free_rate,
    int periods_per_year
) {
    if (returns.empty()) {
        throw InsufficientDataError("Cannot compute metrics on empty dataset");
    }

    auto dd = quant_engine::market_data::max_drawdown(equity_curve);
    double std = quant_engine::statistics::standard_deviation(returns);
    double mean_ret = quant_engine::statistics::mean(returns);

    std::unordered_map<std::string, double> metrics;
    metrics["total_return"] = std::accumulate(returns.begin(), returns.end(), 0.0);
    metrics["mean_return"] = mean_ret;
    metrics["std_return"] = std;
    metrics["downside_deviation"] = downside_deviation(returns);
    metrics["max_drawdown"] = dd.max_drawdown;
    metrics["sharpe_ratio"] = sharpe_ratio(returns, risk_free_rate, periods_per_year);
    metrics["sortino_ratio"] = sortino_ratio(returns, risk_free_rate, periods_per_year);
    metrics["calmar_ratio"] = calmar_ratio(returns, equity_curve, periods_per_year);
    metrics["profit_factor"] = profit_factor(returns);
    metrics["win_rate"] = win_rate(returns);

    // Annualised metrics
    metrics["annualised_return"] = mean_ret * static_cast<double>(periods_per_year);
    metrics["annualised_volatility"] = std * std::sqrt(static_cast<double>(periods_per_year));

    return metrics;
}

} // namespace metrics
} // namespace quant_engine
