#include "monte_carlo.h"
#include <random>
#include <numeric>
#include <algorithm>
#include <cmath>

namespace cpp_quant {

double MonteCarlo::pValue(const std::vector<Trade>& actual_trades, int num_simulations) {
    if (actual_trades.empty()) return 1.0;
    
    std::vector<double> returns;
    for (const auto& t : actual_trades) returns.push_back(t.pnl);
    
    double actual_mean = std::accumulate(returns.begin(), returns.end(), 0.0) / returns.size();
    double actual_std = 0.0;
    for (double r : returns) actual_std += (r - actual_mean) * (r - actual_mean);
    actual_std = std::sqrt(actual_std / returns.size());
    if (actual_std == 0) return 1.0;
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<> dist(0.0, actual_std);
    
    int count_better = 0;
    for (int sim = 0; sim < num_simulations; ++sim) {
        double sim_mean = 0.0;
        for (size_t i = 0; i < returns.size(); ++i) {
            sim_mean += dist(gen);
        }
        sim_mean /= returns.size();
        if (sim_mean > actual_mean) count_better++;
    }
    return (double)count_better / num_simulations;
}

std::vector<double> MonteCarlo::bootstrapEquity(const std::vector<double>& returns, int num_paths) {
    std::vector<double> final_equities;
    final_equities.reserve(num_paths);
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dist(0, (int)returns.size() - 1);
    
    for (int i = 0; i < num_paths; ++i) {
        double equity = 10000.0;
        for (size_t j = 0; j < returns.size(); ++j) {
            double r = returns[dist(gen)];
            equity *= (1 + r);
        }
        final_equities.push_back(equity);
    }
    return final_equities;
}

} // namespace cpp_quant

