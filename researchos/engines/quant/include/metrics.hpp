#ifndef QUANT_ENGINE_METRICS_HPP
#define QUANT_ENGINE_METRICS_HPP

/**
 * @file metrics.hpp
 * @brief Research performance metrics for the Quant Computation Engine.
 *
 * All metrics are RESEARCH METRICS ONLY — NOT trading signals or decisions.
 *
 * Formulas (CALCULATION_V1):
 *   - Sharpe Ratio: (mean(R) - R_f) / std(R) * sqrt(periods_per_year)
 *   - Sortino Ratio: (mean(R) - R_f) / downside_deviation(R) * sqrt(periods_per_year)
 *   - Calmar Ratio: mean(R) / |max_drawdown|
 *   - Profit Factor: sum(wins) / |sum(losses)|
 *
 * Based on Article XVII: Object Model — Quant Engine Layer.
 */

#include "quant_engine.hpp"

#endif // QUANT_ENGINE_METRICS_HPP
