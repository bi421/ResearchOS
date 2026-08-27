/**
 * @file quant_engine.cpp
 * @brief Implementation of market data processing functions.
 *
 * Provides:
 *   - Returns: absolute, percentage, log
 *   - Volatility: rolling, change
 *   - Risk: maximum drawdown, recovery duration
 */

#include "quant_engine.hpp"
#include <vector>
#include <cmath>
#include <algorithm>
#include <stdexcept>

namespace quant_engine {
namespace market_data {

// ── Absolute Returns ───────────────────────────────────────────────────────

std::vector<double> absolute_returns(const std::vector<double>& prices) {
    if (prices.size() < 2) {
        throw InsufficientDataError(
            "Need at least 2 prices for absolute returns, got " +
            std::to_string(prices.size())
        );
    }

    std::vector<double> returns;
    returns.reserve(prices.size() - 1);
    for (size_t i = 1; i < prices.size(); ++i) {
        returns.push_back(prices[i] - prices[i - 1]);
    }
    return returns;
}

// ── Percentage Returns ─────────────────────────────────────────────────────

std::vector<double> percentage_returns(const std::vector<double>& prices) {
    if (prices.size() < 2) {
        throw InsufficientDataError(
            "Need at least 2 prices for percentage returns, got " +
            std::to_string(prices.size())
        );
    }

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
    return returns;
}

// ── Log Returns ────────────────────────────────────────────────────────────

std::vector<double> log_returns(const std::vector<double>& prices) {
    if (prices.size() < 2) {
        throw InsufficientDataError(
            "Need at least 2 prices for log returns, got " +
            std::to_string(prices.size())
        );
    }

    std::vector<double> returns;
    returns.reserve(prices.size() - 1);
    for (size_t i = 1; i < prices.size(); ++i) {
        double prev = prices[i - 1];
        double curr = prices[i];
        if (prev <= 0.0 || curr <= 0.0) {
            returns.push_back(0.0);
        } else {
            returns.push_back(std::log(curr / prev));
        }
    }
    return returns;
}

// ── Rolling Volatility ─────────────────────────────────────────────────────

std::vector<double> rolling_volatility_series(
    const std::vector<double>& returns,
    size_t window
) {
    if (returns.size() < window) {
        throw InsufficientDataError(
            "Window size " + std::to_string(window) +
            " exceeds data length " + std::to_string(returns.size())
        );
    }

    std::vector<double> vols;
    vols.reserve(returns.size() - window + 1);

    for (size_t i = 0; i <= returns.size() - window; ++i) {
        std::vector<double> window_returns(
            returns.begin() + static_cast<long>(i),
            returns.begin() + static_cast<long>(i + window)
        );
        vols.push_back(quant_engine::statistics::standard_deviation(window_returns));
    }

    return vols;
}

// ── Rolling Volatility (single value — last window) ────────────────────────

double rolling_volatility(const std::vector<double>& returns, size_t window) {
    auto series = rolling_volatility_series(returns, window);
    if (series.empty()) return 0.0;
    return series.back();
}

// ── Volatility Change ──────────────────────────────────────────────────────

double volatility_change(const std::vector<double>& returns, size_t window) {
    size_t min_required = window * 2;
    if (returns.size() < min_required) {
        throw InsufficientDataError(
            "Need at least " + std::to_string(min_required) +
            " returns for volatility change, got " +
            std::to_string(returns.size())
        );
    }

    std::vector<double> early(
        returns.begin(),
        returns.begin() + static_cast<long>(window)
    );
    std::vector<double> recent(
        returns.end() - static_cast<long>(window),
        returns.end()
    );

    double early_vol = quant_engine::statistics::standard_deviation(early);
    double recent_vol = quant_engine::statistics::standard_deviation(recent);

    if (early_vol == 0.0) {
        if (recent_vol > 0.0) {
            return std::numeric_limits<double>::infinity();
        }
        return 0.0;
    }

    return (recent_vol - early_vol) / early_vol;
}

// ── Maximum Drawdown ───────────────────────────────────────────────────────

DrawdownResult max_drawdown(const std::vector<double>& equity_curve) {
    if (equity_curve.size() < 2) {
        throw InsufficientDataError(
            "Need at least 2 equity values, got " +
            std::to_string(equity_curve.size())
        );
    }

    double peak = equity_curve[0];
    double max_dd = 0.0;
    size_t max_dd_end_idx = 0;
    size_t max_dd_peak_idx = 0;

    for (size_t i = 0; i < equity_curve.size(); ++i) {
        double value = equity_curve[i];
        if (value > peak) {
            peak = value;
            max_dd_peak_idx = i;
        }

        double dd = (peak != 0.0) ? (value - peak) / peak : 0.0;
        if (dd < max_dd) {
            max_dd = dd;
            max_dd_end_idx = i;
        }
    }

    // Calculate recovery period
    int recovery_period = 0;
    if (max_dd < 0.0) {
        double peak_before_dd = equity_curve[max_dd_peak_idx];
        for (size_t i = max_dd_end_idx; i < equity_curve.size(); ++i) {
            if (equity_curve[i] >= peak_before_dd) {
                recovery_period = static_cast<int>(i - max_dd_end_idx);
                break;
            }
        }
    }

    DrawdownResult result;
    result.max_drawdown = max_dd;
    result.max_drawdown_pct = max_dd * 100.0;
    result.recovery_period = recovery_period;
    return result;
}

std::unordered_map<std::string, double> DrawdownResult::to_dict() const {
    return {
        {"max_drawdown", max_drawdown},
        {"max_drawdown_pct", max_drawdown_pct},
        {"recovery_period", static_cast<double>(recovery_period)}
    };
}

} // namespace market_data
} // namespace quant_engine
