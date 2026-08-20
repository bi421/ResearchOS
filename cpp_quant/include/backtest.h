#pragma once
#include <vector>
#include <tuple>

std::tuple<double, double, double, double, int> 
run_ml_backtest_cpp(
    const std::vector<double>& prices,
    const std::vector<double>& probabilities,
    double threshold,
    double initial_capital = 100000.0,
    double commission = 0.001,
    double slippage = 0.0005
);
