/**
 * @file test_statistics.cpp
 * @brief C++ unit tests for the Quant Computation Engine.
 *
 * Tests:
 *   - Statistics accuracy (mean, variance, std, z-score)
 *   - Deterministic results
 *   - Edge cases (empty data, single value, zero variance)
 *   - Market data processing (returns, volatility, drawdown)
 *   - Metrics (Sharpe, Sortino, Calmar, Profit Factor)
 */

#define _SILENCE_ALL_CXX23_DEPRECATION_WARNINGS

#include "quant_engine.hpp"
#include <iostream>
#include <cassert>
#include <cmath>
#include <cstdlib>
#include <vector>
#include <string>

using namespace quant_engine;

// ── Test Counters ──────────────────────────────────────────────────────────
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name, expr)                                                       \
    do {                                                                       \
        try {                                                                  \
            expr;                                                              \
            std::cout << "  PASS: " << name << std::endl;                      \
            tests_passed++;                                                    \
        } catch (const std::exception& e) {                                    \
            std::cout << "  FAIL: " << name << " — " << e.what() << std::endl; \
            tests_failed++;                                                    \
        } catch (...) {                                                        \
            std::cout << "  FAIL: " << name << " — unknown error" << std::endl;\
            tests_failed++;                                                    \
        }                                                                      \
    } while(0)

#define ASSERT_NEAR(a, b, eps)                                                 \
    do {                                                                       \
        auto _x_a = static_cast<double>(a);                                    \
        auto _x_b = static_cast<double>(b);                                    \
        if (std::abs(_x_a - _x_b) > static_cast<double>(eps)) {                \
            throw std::runtime_error(                                          \
                std::string("Expected ") + std::to_string(_x_b) +               \
                " but got " + std::to_string(_x_a)                              \
            );                                                                 \
        }                                                                      \
    } while(0)

#define ASSERT_THROWS(expr)                                                    \
    do {                                                                       \
        bool threw = false;                                                    \
        try { expr; }                                                          \
        catch (...) { threw = true; }                                          \
        if (!threw) {                                                          \
            throw std::runtime_error("Expected exception but none thrown");    \
        }                                                                      \
    } while(0)

// ── Statistics Tests ───────────────────────────────────────────────────────

void test_statistics_mean() {
    std::vector<double> data = {1.0, 2.0, 3.0, 4.0, 5.0};
    ASSERT_NEAR(statistics::mean(data), 3.0, 1e-10);

    std::vector<double> single = {42.0};
    ASSERT_NEAR(statistics::mean(single), 42.0, 1e-10);
}

void test_statistics_empty_throws() {
    std::vector<double> empty;
    ASSERT_THROWS(statistics::mean(empty));
}

void test_statistics_variance() {
    std::vector<double> data = {1.0, 2.0, 3.0, 4.0, 5.0};
    double var = statistics::variance(data);
    ASSERT_NEAR(var, 2.5, 1e-10);

    // Population variance
    double var_pop = statistics::variance(data, 0);
    ASSERT_NEAR(var_pop, 2.0, 1e-10);
}

void test_statistics_std() {
    std::vector<double> data = {2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0};
    double std = statistics::standard_deviation(data);
    ASSERT_NEAR(std, 2.138089935299395, 1e-10);
}

void test_statistics_z_score() {
    double z = statistics::z_score(10.0, 5.0, 2.0);
    ASSERT_NEAR(z, 2.5, 1e-10);

    ASSERT_THROWS(statistics::z_score(1.0, 0.0, 0.0));
}

void test_statistics_deterministic() {
    std::vector<double> data = {0.01, -0.02, 0.03, -0.01, 0.02};
    double m1 = statistics::mean(data);
    double m2 = statistics::mean(data);
    ASSERT_NEAR(m1, m2, 1e-15);

    double s1 = statistics::standard_deviation(data);
    double s2 = statistics::standard_deviation(data);
    ASSERT_NEAR(s1, s2, 1e-15);
}

void test_statistics_distribution_summary() {
    std::vector<double> data = {1.0, 2.0, 3.0, 4.0, 5.0};
    auto summary = statistics::distribution_summary(data);
    ASSERT_NEAR(summary.mean, 3.0, 1e-10);
    ASSERT_NEAR(summary.count, 5, 1e-10);
    ASSERT_NEAR(summary.min, 1.0, 1e-10);
    ASSERT_NEAR(summary.max, 5.0, 1e-10);
}

// ── Market Data Tests ──────────────────────────────────────────────────────

void test_returns_absolute() {
    std::vector<double> prices = {100.0, 102.0, 101.0, 105.0};
    auto rets = market_data::absolute_returns(prices);
    ASSERT_NEAR(rets.size(), 3, 1e-10);
    ASSERT_NEAR(rets[0], 2.0, 1e-10);
    ASSERT_NEAR(rets[1], -1.0, 1e-10);
    ASSERT_NEAR(rets[2], 4.0, 1e-10);
}

void test_returns_percentage() {
    std::vector<double> prices = {100.0, 102.0, 101.0, 105.0};
    auto rets = market_data::percentage_returns(prices);
    ASSERT_NEAR(rets.size(), 3, 1e-10);
    ASSERT_NEAR(rets[0], 0.02, 1e-10);
    ASSERT_NEAR(rets[1], -0.00980392156862745, 1e-10);
    ASSERT_NEAR(rets[2], 0.0396039603960396, 1e-10);
}

void test_returns_log() {
    std::vector<double> prices = {100.0, 102.0, 101.0, 105.0};
    auto rets = market_data::log_returns(prices);
    ASSERT_NEAR(rets.size(), 3, 1e-10);
    ASSERT_NEAR(rets[0], 0.0198026272961797, 1e-10);
}

void test_returns_empty_throws() {
    std::vector<double> empty;
    ASSERT_THROWS(market_data::absolute_returns(empty));
    ASSERT_THROWS(market_data::percentage_returns(empty));
    ASSERT_THROWS(market_data::log_returns(empty));
}

void test_returns_deterministic() {
    std::vector<double> prices = {100.0, 102.0, 101.0, 105.0, 103.0, 107.0};
    auto rets1 = market_data::percentage_returns(prices);
    auto rets2 = market_data::percentage_returns(prices);
    for (size_t i = 0; i < rets1.size(); ++i) {
        ASSERT_NEAR(rets1[i], rets2[i], 1e-15);
    }
}

void test_volatility_rolling() {
    std::vector<double> returns = {0.01, -0.02, 0.03, -0.01, 0.02};
    double vol = market_data::rolling_volatility(returns, 3);
    // Last window of 3: [-0.01, 0.02] — wait, window=3 so last window covers indices 2,3,4: [0.03, -0.01, 0.02]
    ASSERT_NEAR(vol > 0, true, 1e-10);
}

void test_volatility_change() {
    // Increasing volatility → positive change
    std::vector<double> returns(30, 0.001);
    for (int i = 0; i < 10; ++i) {
        returns.push_back(0.05);
        returns.push_back(-0.04);
        returns.push_back(0.06);
        returns.push_back(-0.05);
    }
    double vc = market_data::volatility_change(returns, 10);
    // Early vol is 0, recent vol > 0 → inf
    ASSERT_NEAR(vc, std::numeric_limits<double>::infinity(), 1e-10);
}

void test_drawdown() {
    // Strictly increasing → no drawdown
    std::vector<double> equity = {100.0, 102.0, 104.0, 106.0, 108.0};
    auto dd = market_data::max_drawdown(equity);
    ASSERT_NEAR(dd.max_drawdown, 0.0, 1e-10);

    // With a loss
    std::vector<double> equity2 = {100.0, 110.0, 90.0, 95.0, 100.0};
    auto dd2 = market_data::max_drawdown(equity2);
    ASSERT_NEAR(dd2.max_drawdown, -0.1818181818181818, 1e-10);
    ASSERT_NEAR(dd2.recovery_period, 2, 1e-10);
}

void test_drawdown_empty_throws() {
    std::vector<double> single = {100.0};
    ASSERT_THROWS(market_data::max_drawdown(single));
}

// ── Metrics Tests ──────────────────────────────────────────────────────────

void test_sharpe_ratio() {
    std::vector<double> returns = {0.01, 0.02, 0.015, -0.005, 0.01};
    std::vector<double> equity = {100.0};
    for (double r : returns) equity.push_back(equity.back() * (1.0 + r));

    double sr = metrics::sharpe_ratio(returns, 0.0, 252);
    ASSERT_NEAR(sr > 0, true, 1e-10);
}

void test_sharpe_zero_vol() {
    std::vector<double> returns = {0.01, 0.01, 0.01};
    double sr = metrics::sharpe_ratio(returns, 0.0, 252);
    ASSERT_NEAR(sr, 0.0, 1e-10);
}

void test_sortino_ratio() {
    std::vector<double> returns = {0.01, 0.02, -0.01, 0.015, -0.005};
    std::vector<double> equity = {100.0};
    for (double r : returns) equity.push_back(equity.back() * (1.0 + r));

    double sortino = metrics::sortino_ratio(returns, 0.0, 252);
    // Should be valid since there are negative returns
    ASSERT_NEAR(std::isfinite(sortino), true, 1e-10);
}

void test_calmar_ratio() {
    std::vector<double> returns = {0.01, 0.02, 0.015, -0.005, 0.01};
    std::vector<double> equity = {100.0};
    for (double r : returns) equity.push_back(equity.back() * (1.0 + r));

    double cr = metrics::calmar_ratio(returns, equity, 252);
    ASSERT_NEAR(std::isfinite(cr), true, 1e-10);
}

void test_profit_factor() {
    std::vector<double> returns = {0.01, -0.005, 0.02, -0.01, 0.015};
    double pf = metrics::profit_factor(returns);
    ASSERT_NEAR(pf > 1.0, true, 1e-10);
}

void test_profit_factor_no_losses() {
    std::vector<double> returns = {0.01, 0.02, 0.015};
    double pf = metrics::profit_factor(returns);
    ASSERT_NEAR(pf, std::numeric_limits<double>::infinity(), 1e-10);
}

void test_profit_factor_no_wins() {
    std::vector<double> returns = {-0.01, -0.02, -0.015};
    double pf = metrics::profit_factor(returns);
    ASSERT_NEAR(pf, 0.0, 1e-10);
}

void test_win_rate() {
    std::vector<double> returns = {0.01, -0.005, 0.02, -0.01, 0.015};
    double wr = metrics::win_rate(returns);
    ASSERT_NEAR(wr, 0.6, 1e-10);
}

void test_win_rate_empty() {
    std::vector<double> empty;
    double wr = metrics::win_rate(empty);
    ASSERT_NEAR(wr, 0.0, 1e-10);
}

void test_compute_all_metrics() {
    std::vector<double> returns = {0.01, -0.005, 0.02, -0.01, 0.015};
    std::vector<double> equity = {100.0};
    for (double r : returns) equity.push_back(equity.back() * (1.0 + r));

    auto metrics_result = metrics::compute_all_metrics(returns, equity, 0.0, 252);

    // Verify all expected keys exist
    ASSERT_NEAR(metrics_result.count("sharpe_ratio"), 1, 1e-10);
    ASSERT_NEAR(metrics_result.count("sortino_ratio"), 1, 1e-10);
    ASSERT_NEAR(metrics_result.count("calmar_ratio"), 1, 1e-10);
    ASSERT_NEAR(metrics_result.count("profit_factor"), 1, 1e-10);
    ASSERT_NEAR(metrics_result.count("win_rate"), 1, 1e-10);
    ASSERT_NEAR(metrics_result.count("total_return"), 1, 1e-10);
    ASSERT_NEAR(metrics_result.count("max_drawdown"), 1, 1e-10);
}

void test_metrics_deterministic() {
    std::vector<double> returns = {0.01, -0.005, 0.02, -0.01, 0.015};
    std::vector<double> equity = {100.0};
    for (double r : returns) equity.push_back(equity.back() * (1.0 + r));

    auto m1 = metrics::compute_all_metrics(returns, equity, 0.0, 252);
    auto m2 = metrics::compute_all_metrics(returns, equity, 0.0, 252);

    for (const auto& [key, val] : m1) {
        ASSERT_NEAR(val, m2.at(key), 1e-15);
    }
}

// ── Simulation Tests ───────────────────────────────────────────────────────

void test_simulation_basic() {
    simulation::SimulationInput input;
    input.dataset_reference = "TEST";
    input.initial_capital = 100000.0;
    input.risk_free_rate = 0.0;
    input.seed = 42;

    std::vector<double> prices = {100.0, 102.0, 101.0, 105.0, 103.0, 107.0};

    auto output = simulation::run_simulation(input, prices);

    // Verify output structure
    ASSERT_NEAR((int)output.returns.size(), 5, 1e-10);
    ASSERT_NEAR((int)output.equity_curve.size(), 6, 1e-10);
    ASSERT_NEAR(output.equity_curve[0], 100000.0, 1e-10);
    ASSERT_NEAR((int)output.metrics.count("sharpe_ratio"), 1, 1e-10);
    ASSERT_NEAR((int)output.statistics.count("mean"), 1, 1e-10);
    ASSERT_NEAR(output.input_hash.size() > 0, true, 1e-10);
    ASSERT_NEAR(output.result_hash.size() > 0, true, 1e-10);
}

void test_simulation_deterministic() {
    simulation::SimulationInput input;
    input.dataset_reference = "DETERM_TEST";
    input.initial_capital = 100000.0;
    input.risk_free_rate = 0.0;
    input.seed = 42;

    std::vector<double> prices = {100.0, 102.0, 101.0, 105.0, 103.0, 107.0};

    auto output1 = simulation::run_simulation(input, prices);
    auto output2 = simulation::run_simulation(input, prices);

    // String hashes must match exactly (deterministic)
    if (output1.input_hash != output2.input_hash) {
        throw std::runtime_error("input_hash mismatch");
    }
    if (output1.result_hash != output2.result_hash) {
        throw std::runtime_error("result_hash mismatch");
    }

    for (size_t i = 0; i < output1.returns.size(); ++i) {
        ASSERT_NEAR(output1.returns[i], output2.returns[i], 1e-15);
    }
}

void test_simulation_insufficient_data() {
    simulation::SimulationInput input;
    input.dataset_reference = "EMPTY_TEST";
    std::vector<double> single_price = {100.0};

    ASSERT_THROWS(simulation::run_simulation(input, single_price));
}

void test_simulation_version_tracking() {
    simulation::SimulationInput input;
    input.dataset_reference = "VER_TEST";
    input.calculation_version = "CALCULATION_V1";
    input.initial_capital = 100000.0;
    input.risk_free_rate = 0.0;
    input.seed = 42;

    std::vector<double> prices = {100.0, 102.0, 101.0, 105.0, 103.0, 107.0};

    auto output = simulation::run_simulation(input, prices);
    ASSERT_NEAR(output.input_hash.size() > 0, true, 1e-10);
    ASSERT_NEAR(output.result_hash.size() > 0, true, 1e-10);
}

// ── Main ───────────────────────────────────────────────────────────────────

int main() {
    std::cout << "C++ Quant Computation Engine — Unit Tests" << std::endl;
    std::cout << "=========================================" << std::endl;

    // Statistics
    std::cout << "\n[Statistics]" << std::endl;
    TEST("Mean", test_statistics_mean());
    TEST("Empty throws", test_statistics_empty_throws());
    TEST("Variance", test_statistics_variance());
    TEST("Standard deviation", test_statistics_std());
    TEST("Z-score", test_statistics_z_score());
    TEST("Deterministic output", test_statistics_deterministic());
    TEST("Distribution summary", test_statistics_distribution_summary());

    // Market Data
    std::cout << "\n[Market Data]" << std::endl;
    TEST("Absolute returns", test_returns_absolute());
    TEST("Percentage returns", test_returns_percentage());
    TEST("Log returns", test_returns_log());
    TEST("Empty returns throws", test_returns_empty_throws());
    TEST("Deterministic returns", test_returns_deterministic());
    TEST("Rolling volatility", test_volatility_rolling());
    TEST("Volatility change", test_volatility_change());
    TEST("Max drawdown", test_drawdown());
    TEST("Drawdown empty throws", test_drawdown_empty_throws());

    // Metrics
    std::cout << "\n[Metrics]" << std::endl;
    TEST("Sharpe ratio", test_sharpe_ratio());
    TEST("Sharpe zero volatility", test_sharpe_zero_vol());
    TEST("Sortino ratio", test_sortino_ratio());
    TEST("Calmar ratio", test_calmar_ratio());
    TEST("Profit factor", test_profit_factor());
    TEST("Profit factor no losses", test_profit_factor_no_losses());
    TEST("Profit factor no wins", test_profit_factor_no_wins());
    TEST("Win rate", test_win_rate());
    TEST("Win rate empty", test_win_rate_empty());
    TEST("Compute all metrics", test_compute_all_metrics());
    TEST("Deterministic metrics", test_metrics_deterministic());

    // Simulation
    std::cout << "\n[Simulation]" << std::endl;
    TEST("Basic simulation", test_simulation_basic());
    TEST("Deterministic simulation", test_simulation_deterministic());
    TEST("Insufficient data throws", test_simulation_insufficient_data());
    TEST("Version tracking", test_simulation_version_tracking());

    // Summary
    std::cout << "\n=========================================" << std::endl;
    std::cout << "Results: " << (tests_passed + tests_failed)
              << " total, " << tests_passed << " passed, "
              << tests_failed << " failed" << std::endl;

    return tests_failed > 0 ? 1 : 0;
}

